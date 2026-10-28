#!/usr/bin/env python3
"""Audit an exact public-hub Asteraceae snapshot without copying photographs.

The main hub retains canonical authority. Licensing flags are claims in source
metadata, NEVER confirmation of reuse rights.
"""
import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

SOURCE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("../hays-hub").resolve()
TARGET = Path(__file__).resolve().parents[1]
OUT = TARGET / "qa-report" / "asteraceae-source-audit"
EXT_IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff"}


def command(*args):
    return subprocess.check_output(list(args), cwd=SOURCE, text=True).strip()


def classify_license(item):
    license_label = str(item.get("license") or item.get("photo_license") or "").lower().strip()
    if "by-nc" in license_label or "noncommercial" in license_label:
        return "NC_REQUIRES_NONCOMMERCIAL_AND_SOURCE_REVIEW"
    if "cc0" in license_label:
        return "CC0_CLAIM_REQUIRES_SOURCE_REVIEW"
    if "cc by" in license_label or "cc-by" in license_label:
        return "CC_ATTRIBUTION_CLAIM_REQUIRES_SOURCE_REVIEW"
    if "public domain" in license_label or license_label in {"pd", "pdm"}:
        return "PD_CLAIM_REQUIRES_ORIGIN_REVIEW"
    if not license_label:
        return "NO_DOCUMENTED_LICENSE"
    return "OTHER_LICENSE_PERMISSION_REVIEW"


def main():
    assert (SOURCE / ".git").exists(), "Supply an actual checked-out hub repository"
    source_sha = command("git", "rev-parse", "HEAD")
    # Git partial clone deliberately omits photographic blobs. "git ls-tree -l"
    # forces a lazy download of every photo just to calculate its size. Instead
    # obtain the content tree's immutable SHA, then one GitHub tree listing
    # containing both file sizes and blob SHAs; NO image bytes are fetched.
    from urllib.request import Request, urlopen
    subtree_sha = command("git", "rev-parse", "HEAD:content/taxa/Asteraceae")
    endpoint = ("https://api.github.com/repos/Crking92/Hays-County-Botany/git/trees/"
                + subtree_sha + "?recursive=1")
    request = Request(endpoint, headers={"Accept": "application/vnd.github+json",
                                         "User-Agent": "HaysBotany-Asteraceae-Staging-Audit"})
    with urlopen(request, timeout=60) as response:
        listing = json.load(response)
    assert listing.get("truncated") is False, "Truncated Asteraceae Git tree listing"
    ledger = {}
    for entry in listing["tree"]:
        if entry["type"] == "blob":
            path = "content/taxa/Asteraceae/" + entry["path"]
            ledger[path] = {"path": path, "git_blob_sha": entry["sha"],
                            "size_bytes": entry["size"]}
    manifest = json.loads((SOURCE / "data/manifest.json").read_text(encoding="utf-8"))
    manifest_rows = [r for r in manifest["species"] if r["path"].startswith("content/taxa/Asteraceae/")]
    source_cards = {r["path"]: r for r in manifest_rows}
    actual_cards = {p for p in ledger if p.endswith("/species.json")}
    assert len(manifest_rows) == 180, f"Expected 180 Asteraceae manifest rows, found {len(manifest_rows)}"
    assert len(source_cards) == 180, "Duplicate Asteraceae manifest paths"
    assert actual_cards == set(source_cards), (
        f"Manifest/card mismatch: missing {sorted(set(source_cards)-actual_cards)[:10]}, "
        f"unexpected {sorted(actual_cards-set(source_cards))[:10]}"
    )
    image_files = {p: m for p, m in ledger.items() if Path(p).suffix.lower() in EXT_IMAGE}
    text_files = {p: m for p, m in ledger.items() if Path(p).suffix.lower() in {".json", ".csv", ".txt"}}
    assert len(image_files) == 459, f"Physical image baseline changed: {len(image_files)}"
    assert len(text_files) == 678, f"Scientific and provenance source baseline changed: {len(text_files)}"
    assert "content/taxa/Asteraceae/family.json" in ledger, "Missing family module"
    cards, media_rows = [], []
    uses, usage_license = Counter(), Counter()
    referenced = set()
    genus_dirs = set()
    for path, row in sorted(source_cards.items()):
        data = json.loads((SOURCE / path).read_text(encoding="utf-8"))
        id_, genus = row["id"], path.split("/")[3]
        assert data.get("id") == id_, f"Species ID mismatch in {path}"
        assert data.get("family") == "Asteraceae", path
        assert data.get("genus") == genus, path
        assert data.get("scientific_name"), f"Missing accepted name for {id_}"
        genus_dirs.add(genus)
        photos = data.get("images") or []
        assert isinstance(photos, list), f"Invalid images list for {id_}"
        seen_local = set()
        for index, item in enumerate(photos):
            local = item.get("file", "") if isinstance(item, dict) else ""
            physical = path.rsplit("/", 1)[0] + "/" + local if local else ""
            exists = physical in image_files
            decision = classify_license(item if isinstance(item, dict) else {})
            usage_license[decision] += 1
            if exists:
                referenced.add(physical)
                uses[physical] += 1
            media_rows.append({
                "species_id": id_, "source_species_path": path, "image_index": index,
                "source_local_path": physical, "physically_present": exists,
                "creator": str(item.get("creator", "") if isinstance(item, dict) else ""),
                "license_claim": str(item.get("license", "") if isinstance(item, dict) else ""),
                "license_review_bucket": decision,
                "source_page": str(item.get("source_page", "") if isinstance(item, dict) else ""),
                "source_photo_id": str(item.get("photo_id", "") if isinstance(item, dict) else ""),
                "public_reuse_metadata": str(item.get("public_reuse", "") if isinstance(item, dict) else ""),
                "source_git_blob_sha": image_files[physical]["git_blob_sha"] if exists else "",
                "source_bytes": image_files[physical]["size_bytes"] if exists else "",
            })
            if physical in seen_local:
                raise AssertionError(f"Duplicate photo reference in same species: {id_}: {physical}")
            seen_local.add(physical)
        cards.append({
            "id": id_, "family": "Asteraceae", "genus": genus,
            "scientific_name": data["scientific_name"], "common_name": data.get("common_name", ""),
            "source_path": path,
            "recorded_images": len(photos),
            "physically_present_image_references": sum(x["physically_present"] for x in media_rows[-len(photos):]) if photos else 0,
        })
    broken = [m for m in media_rows if not m["physically_present"]]
    source_genus_modules = sorted(p for p in ledger if p.endswith("/genus.json"))
    assert len(genus_dirs) <= len(source_genus_modules), "More species genera than genus modules"
    image_bytes = sum(v["size_bytes"] for v in image_files.values())
    text_bytes = sum(v["size_bytes"] for v in text_files.values())
    summary = {
        "source_repository": "Crking92/Hays-County-Botany",
        "source_commit_sha": source_sha,
        "destination_repository": "Crking92/Hays-Botany-Asteraceae",
        "audit_stage": "SOURCE_TEXT_ONLY_PHOTO_RIGHTS_UNVERIFIED_NO_CUTOVER",
        "canonical_authority_unchanged": True,
        "family_modules": 1,
        "genus_modules": len(source_genus_modules),
        "species_records": len(cards),
        "source_total_files": len(ledger),
        "text_metadata_files": len(text_files),
        "text_metadata_bytes": text_bytes,
        "physical_image_files": len(image_files),
        "physical_image_bytes": image_bytes,
        "recorded_image_references": len(media_rows),
        "physical_image_references": len(media_rows) - len(broken),
        "missing_physical_image_references": len(broken),
        "unreferenced_physical_image_files": len(set(image_files) - referenced),
        "license_claims_not_reuse_verification": dict(usage_license),
        "separate_photo_archive_stage_required": True,
        "source_all_files_git_ledgers_included": True,
        "note": "Rights buckets reflect *unverified source fields*; no public-reuse photos have been selected or copied by this audit.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "source-file-ledger.json").write_text(json.dumps(list(ledger.values()), indent=2) + "\n", encoding="utf-8")
    (OUT / "species-report.json").write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")
    with (OUT / "photo-rights-triage.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(media_rows[0]) if media_rows else ["species_id"])
        wr.writeheader()
        wr.writerows(media_rows)
    print("ASTERACEAE_SOURCE_CENSUS " + json.dumps(summary, sort_keys=True))
    print("Missing photo references sample: " + json.dumps(broken[:8]))
    print("Next: stage only the 678 original metadata files, preserving image hold status.")


if __name__ == "__main__":
    main()
