#!/usr/bin/env python3
"""Copy source-matched Asteraceae TEXT ONLY to a private staging branch.

Never copies photos, changes the hub, grants public rights, or publishes a site.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

SOURCE = Path(sys.argv[1]).resolve()
TARGET = Path(__file__).resolve().parents[1]
REPORT = TARGET / "qa-report/asteraceae-source-audit"
summary = json.loads((REPORT / "summary.json").read_text(encoding="utf-8"))
ledger = json.loads((REPORT / "source-file-ledger.json").read_text(encoding="utf-8"))
species = json.loads((REPORT / "species-report.json").read_text(encoding="utf-8"))
assert summary["species_records"] == 180
assert summary["text_metadata_files"] == 678
assert summary["source_repository"] == "Crking92/Hays-County-Botany"
assert summary["destination_repository"] == "Crking92/Hays-Botany-Asteraceae"
assert summary["canonical_authority_unchanged"] is True

allowed = {".json", ".txt", ".csv"}
copied = 0
copied_bytes = 0
for entry in ledger:
    relative = Path(entry["path"])
    if relative.suffix.lower() not in allowed:
        continue
    assert str(relative).startswith("content/taxa/Asteraceae/")
    src = SOURCE / relative
    assert src.is_file(), f"Sparse checkout omitted {relative}"
    content = src.read_bytes()
    blob_hash = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
    assert blob_hash == entry["git_blob_sha"], f"Blob mismatch {relative}"
    dst = TARGET / relative
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(content)
    copied += 1
    copied_bytes += len(content)
assert copied == summary["text_metadata_files"]
assert copied_bytes == summary["text_metadata_bytes"]

index = json.loads((TARGET / "data/collection-index.json").read_text(encoding="utf-8"))
assert index["authority"] == "STAGING_ONLY"
entries = []
for row in species:
    entries.append({
        "id": row["id"],
        "scientific_name": row["scientific_name"],
        "common_name": row["common_name"],
        "family": "Asteraceae",
        "genus": row["genus"],
        "path": row["source_path"],
        "photo_publication_status": "SOURCE_METADATA_ONLY_NOT_CLEARED",
    })
index["entries"] = sorted(entries, key=lambda r: r["id"])
index["source_repository"] = summary["source_repository"]
index["source_commit_sha"] = summary["source_commit_sha"]
index["public_website_ready"] = False
(TARGET / "data/collection-index.json").write_text(
    json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)
dest = TARGET / "migration"
dest.mkdir(parents=True, exist_ok=True)
(dest / "asteraceae-source-snapshot.json").write_text(
    json.dumps({k: v for k, v in summary.items() if k not in {"license_claims_not_reuse_verification"}}, indent=2) + "\n",
    encoding="utf-8"
)
shutil.copyfile(REPORT / "source-file-ledger.json", dest / "asteraceae-source-file-ledger.json")
shutil.copyfile(REPORT / "photo-rights-triage.csv", dest / "asteraceae-photo-rights-triage.csv")
shutil.copyfile(REPORT / "summary.json", dest / "asteraceae-source-census.json")
# No photo files in the new private staging source.
local_photos = [p for p in (TARGET / "content/taxa/Asteraceae").rglob("*")
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".gif", ".webp"}]
assert not local_photos, f"Unexpected image bytes in private migration staging: {local_photos[:5]}"
print(json.dumps({
    "stage": "PRIVATE_TEXT_ONLY_BRANCH_NOT_CANONICAL",
    "source_sha": summary["source_commit_sha"],
    "scientific_metadata_files": copied,
    "verified_git_blob_hashes": copied,
    "metadata_bytes": copied_bytes,
    "species_in_staging_index": len(entries),
    "photographs_copied": 0,
    "source_photo_files_held_for_rights_review": summary["physical_image_files"],
    "hub_unchanged": True,
    "pages_deployment": False,
}, sort_keys=True))
