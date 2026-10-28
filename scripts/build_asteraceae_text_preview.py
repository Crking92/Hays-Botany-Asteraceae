#!/usr/bin/env python3
"""Build a rights-safe, NONPUBLISHED text-only family learner from staging metadata.

Outputs actual botanical look-here-first lessons, no photo bytes, no source image
URLs, no Pages deployment. Original hub remains canonical.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGED = Path(sys.argv[1]).resolve()
DEST = ROOT / "dist"
source_index = json.loads((STAGED / "data/collection-index.json").read_text(encoding="utf-8"))
config = json.loads((STAGED / "config/collection.json").read_text(encoding="utf-8"))
source_census = json.loads((STAGED / "migration/asteraceae-source-census.json").read_text(encoding="utf-8"))
assert source_index["authority"] == "STAGING_ONLY"
assert source_index.get("public_website_ready") is False
assert config["publication"]["enabled"] is False
assert config["planning_status"] == "STAGING_ONLY_NOT_AUTHORITATIVE"
assert len(source_index["entries"]) == 180
assert source_census["species_records"] == 180
assert source_index["source_commit_sha"] == source_census["source_commit_sha"]
assert not list((STAGED / "content/taxa/Asteraceae").rglob("*.jpg"))
if DEST.exists():
    shutil.rmtree(DEST)
(DEST / "data/species").mkdir(parents=True)
for name in ("index.html", "styles.css", "app.js"):
    shutil.copyfile(ROOT / "site" / name, DEST / name)

html = (DEST / "index.html").read_text(encoding="utf-8")
html = html.replace(
    "Layout prototype only.</strong> No botanical records or photographs have been transferred to this collection.",
    "Staging botanical preview.</strong> 180 original species records are available as text. Photographs and finished arrows remain held for a separate review."
)
assert "Staging botanical preview." in html
assert '<meta name="robots" content="noindex,nofollow">' in html
(DEST / "index.html").write_text(html, encoding="utf-8")
(DEST / "data/collection-meta.json").write_text(json.dumps(config, indent=2)+"\n", encoding="utf-8")
(DEST / "data/collection-index.json").write_text(json.dumps(source_index, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def to_text(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "; ".join(str(v).strip() for v in value if isinstance(v, (str, int, float)))
    return ""


for row in source_index["entries"]:
    src = STAGED / row["path"]
    assert src.is_file(), f"Missing imported species record: {row['path']}"
    doc = json.loads(src.read_text(encoding="utf-8"))
    assert doc.get("id") == row["id"] and doc.get("family") == "Asteraceae"
    traits = []
    morphology = doc.get("morphology_keys") or {}
    if isinstance(morphology, dict):
        for key, raw in morphology.items():
            wording = to_text(raw)
            if wording:
                traits.append({"label": key.replace("_", " ").capitalize(), "text": wording[:950]})
    comparisons = doc.get("comparisons") or {}
    if isinstance(comparisons, dict):
        names = comparisons.get("confused_with") or []
        if isinstance(names, str):
            names = [names]
        names = [s for s in names if isinstance(s, str) and s.strip()][:12] if isinstance(names, list) else []
        diff = to_text(comparisons.get("key_distinctions"))
    else:
        names, diff = [], ""
    public_safe = {
        "id": doc["id"],
        "scientific_name": doc.get("scientific_name", ""),
        "common_name": doc.get("common_name", ""),
        "family": doc["family"],
        "genus": doc["genus"],
        "look_here_first": to_text(doc.get("look_here_first")),
        "key_traits": traits,
        "lookalikes": {"names": names, "differences": diff},
        "media_status": "HELD_FOR_RIGHTS_AND_VISUAL_REVIEW",
        "source_snapshot_sha": source_index["source_commit_sha"],
    }
    assert "images" not in public_safe and "source_page" not in public_safe
    (DEST / "data/species" / (row["id"]+".json")).write_text(
        json.dumps(public_safe, ensure_ascii=False, indent=2)+"\n", encoding="utf-8"
    )
files = [p for p in DEST.rglob("*") if p.is_file()]
assert len(files) == 185, f"Expected 180 lessons + 5 shell files; got {len(files)}"
assert not any(p.suffix.lower() in {".png",".jpg",".jpeg",".webp",".gif",".tif",".tiff"} for p in files)
print(json.dumps({"status":"PASS_NONPUBLISHED_TEXT_ONLY_PREVIEW", "species":180,
                  "files":len(files), "image_bytes":0, "canonical_owner_unchanged":True,
                  "source_sha":source_index["source_commit_sha"]}, sort_keys=True))
