#!/usr/bin/env python3
"""Transfer 136 historically rights-held Asteraceae original files into PRIVATE quarantine.

Must preserve exact 1,137 source originals (678 text + 459 images), without changing
the 323 already approved archived images or including any held photo in the learner.
Not a website publication, taxonomy approval, or permission decision.
"""
import hashlib, json, subprocess, sys
from pathlib import Path
from collections import Counter
ROOT=Path(sys.argv[1]).resolve()
SOURCE=Path(sys.argv[2]).resolve()
MIG=ROOT/"migration"
source_census=json.loads((MIG/"asteraceae-source-census.json").read_text())
source_files=json.loads((MIG/"asteraceae-source-file-ledger.json").read_text())
reconcile=json.loads((MIG/"asteraceae-full-image-asset-reconciliation.json").read_text())
existing_summary=json.loads((MIG/"asteraceae-full-image-reconciliation-summary.json").read_text())
config=json.loads((ROOT/"config/collection.json").read_text())
index=json.loads((ROOT/"data/collection-index.json").read_text())
assert len(source_files)==source_census["source_total_files"]==1137
assert len(reconcile)==source_census["physical_image_files"]==459
assert source_census["text_metadata_files"]==678
assert config["publication"]["enabled"] is False
assert index["authority"]=="STAGING_ONLY" and len(index["entries"])==180
assert existing_summary["archived_original_images_in_private_staging"]==323
assert existing_summary["remaining_source_originals_held_and_indexed"]==136
expected_source_tree="394bb64d90c025a51a8d6e10dc4a19bce1aaf623"
head_tree=subprocess.check_output(["git","-C",str(SOURCE),"rev-parse","HEAD:content/taxa/Asteraceae"],text=True).strip()
assert head_tree==expected_source_tree,"Canonical Asteraceae source tree changed; recensus rather than copy"
def git_sha(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()
by_path={e["path"]:e for e in source_files}
by_photo={e["source_path"]:e for e in reconcile}
assert len(by_path)==1137 and len(by_photo)==459
images={p for p in by_path if Path(p).suffix.lower() in (".jpg",".jpeg",".png",".webp")}
texts=set(by_path)-images
assert len(images)==459 and len(texts)==678 and images==set(by_photo)
assert {x["source_path"] for x in reconcile if x["archived_in_private_staging"]}=={
    x["source_path"] for x in reconcile if x["rights_decision"].startswith("ARCHIVED")}
held={x["source_path"] for x in reconcile if not x["archived_in_private_staging"]}
assert len(held)==136
private_dir=MIG/"private-original-photo-holds"
private_dir.mkdir(parents=True,exist_ok=True)
records=[]
counts=Counter()
for path in sorted(by_path):
    r=by_path[path]
    a=SOURCE/path
    assert a.is_file(),f"Source file missing: {path}"
    original=a.read_bytes()
    assert len(original)==r["size_bytes"] and git_sha(original)==r["git_blob_sha"],path
    if path in texts:
        dest=ROOT/path
        assert dest.is_file() and dest.read_bytes()==original,"Text source mismatch "+path
        kind="ORIGINAL_SOURCE_TEXT_OR_CREDIT_BYTE_EXACT"
        counts["text"]+=1
    elif path in held:
        dest=private_dir/Path(path).relative_to("content/taxa/Asteraceae")
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert dest.read_bytes()==original,path
        else:dest.write_bytes(original)
        kind="PRIVATE_QUARANTINE_DO_NOT_DISPLAY_OR_PUBLISH"
        counts["held"]+=1
    else:
        dest=ROOT/path
        assert dest.is_file() and dest.read_bytes()==original,"Approved archived image missing "+path
        assert by_photo[path]["archived_in_private_staging"]
        kind="ALREADY_STAGED_APPROVED_PRIVATE_SOURCE_ARCHIVE"
        counts["approved"]+=1
    assert git_sha(dest.read_bytes())==r["git_blob_sha"]
    records.append({
        "source_path":path,
        "private_destination":dest.relative_to(ROOT).as_posix(),
        "git_blob_sha":r["git_blob_sha"],
        "size_bytes":r["size_bytes"],
        "preservation_class":kind,
        "public_pages_deployed":False,
        "source_licensing":(by_photo[path].get("source_license_claim_bucket") if path in images else None)
    })
assert counts=={"text":678,"held":136,"approved":323},counts
assert len(records)==1137 and len({x["private_destination"] for x in records})==1137
local_gallery_originals={p.relative_to(ROOT).as_posix() for p in (ROOT/"content/taxa/Asteraceae").rglob("*")
 if p.is_file() and p.suffix.lower() in (".jpg",".jpeg",".png",".webp")}
assert local_gallery_originals==images-held,"Wrong gallery original set"
local_quarantine={p.relative_to(ROOT).as_posix() for p in private_dir.rglob("*")
 if p.is_file() and p.suffix.lower() in (".jpg",".jpeg",".png",".webp")}
expected_held={x["private_destination"] for x in records if x["preservation_class"]=="PRIVATE_QUARANTINE_DO_NOT_DISPLAY_OR_PUBLISH"}
assert local_quarantine==expected_held
image_size=sum(by_path[p]["size_bytes"] for p in images)
assert image_size==source_census["physical_image_bytes"]==156804745
assert len(list((ROOT/"content/taxa/Asteraceae").glob("*/*/species.json")))==180
summary={
 "status":"ASTERACEAE_ALL_1137_ORIGINAL_SOURCE_FILES_PRIVATE_TRANSFER_PASS",
 "source_repo":"Crking92/Hays-County-Botany",
 "source_family_tree_sha":head_tree,
 "original_source_files_total":1137,
 "source_species":180,
 "original_text_files_byte_exact":counts["text"],
 "original_photos_total":459,
 "original_photos_byte_exact_in_private_repo":counts["approved"]+counts["held"],
 "original_source_photo_bytes":image_size,
 "existing_previously_staged_original_images":counts["approved"],
 "original_source_photos_quarantined_privately_no_gallery":counts["held"],
 "source_original_files_missing_from_private_repo":0,
 "separately_sourced_additional_photos_preserved_untouched":39,
 "held_photos_not_deployed":True,
 "original_hub_unchanged":True,
 "collection_pages_published":False,
 "source_authority_changed":False,
 "live_cutover_approved":False,
 "recorded_external_only_image_references":29
}
(MIG/"asteraceae-all-original-1137-file-transfer-manifest.json").write_text(
    json.dumps({"summary":summary,"files":records},indent=2,ensure_ascii=False)+"\n")
(MIG/"asteraceae-original-migration-completion-summary.json").write_text(
    json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
(private_dir/"DO_NOT_PUBLISH_README.txt").write_text(
    "PRIVATE ORIGINAL PHOTO HOLD ARCHIVE — never serve via GitHub Pages or site/dist.\n"
    "Original source image bytes are kept here to complete the family file migration.\n"
    "The original license/rights/credit hold decisions in the reconciliation ledger remain in force.\n"
    "This copy grants no new public reuse rights. Original hub unchanged.\n"
)
print("ASTERACEAE_ALL_1137_SOURCE_ORIGINAL_TRANSFER_PASS",json.dumps(summary,sort_keys=True),flush=True)
