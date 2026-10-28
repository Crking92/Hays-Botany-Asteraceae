#!/usr/bin/env python3
"""Reconcile EVERY source Asteraceae image and species-photo reference.

The 459-image pinned source file list and source blob SHA are authoritative.
Archived 210 image blobs must exactly match. Held images stay in original hub,
not copied into a repo that may become public. No files moved or published.
Writes a permanent complete per-file and per-reference ledger for handoff.
"""
from __future__ import annotations
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(sys.argv[1]).resolve()
assert (ROOT / "migration/asteraceae-source-file-ledger.json").is_file()
SOURCE_REPO="Crking92/Hays-County-Botany"
IMAGE_EXT={".jpg",".jpeg",".png",".webp",".gif",".tif",".tiff"}
out=ROOT/"migration"
qa=ROOT/"qa-report/asteraceae-asset-reconciliation"
qa.mkdir(parents=True,exist_ok=True)
def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))
def write(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
source=read("migration/asteraceae-source-file-ledger.json")
census=read("migration/asteraceae-source-census.json")
index=read("data/collection-index.json")
commons=read("migration/asteraceae-verified-commons-photo-ledger.json")
inat=read("migration/asteraceae-verified-inat-photo-ledger.json")
author=read("migration/asteraceae-author-permitted-private-photo-ledger.json")
upstream_path=ROOT/"migration/asteraceae-upstream-commons-120-ledger.json"
upstream_commons=json.loads(upstream_path.read_text()) if upstream_path.exists() else {}
assert index["authority"]=="STAGING_ONLY"
assert index["source_commit_sha"]==census["source_commit_sha"]
assert census["source_repository"]==SOURCE_REPO
assert len(index["entries"])==180

photos={e["path"]:e for e in source if Path(e["path"]).suffix.lower() in IMAGE_EXT}
assert len(photos)==459 and census["physical_image_files"]==459
rights_ledger={}
for name,records in [("commons",commons),("inat",inat),("author_private",author),("upstream_commons",upstream_commons)]:
    for file,info in records.items():
        assert file not in rights_ledger,f"Multiple rights ledgers cover {file}"
        assert file in photos,f"Archived file has no source original: {file}"
        assert info["source_git_blob_sha"]==photos[file]["git_blob_sha"],f"Source mismatch: {file}"
        rights_ledger[file]={"ledger":name,"details":info}
assert 210<=len(rights_ledger)<=459,f"Unexpected staged rights ledger count: {len(rights_ledger)}"

# Obtain the destination repo's real Git tree: no need to fetch original hub image bytes.
def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
branch=git("branch","--show-current")
assert branch=="staging/asteraceae-metadata",f"Do not run on {branch}"
head=git("rev-parse","HEAD")
staged={}
for line in git("ls-tree","-r","HEAD","content/taxa/Asteraceae").splitlines():
    if "\t" not in line:continue
    info,p=line.split("\t",1)
    mode,typ,sha=info.split()
    if typ=="blob" and Path(p).suffix.lower() in IMAGE_EXT:
        staged[p]=sha
assert len(staged)==len(rights_ledger),f"Staged images vs rights ledgers mismatch: {len(staged)}/{len(rights_ledger)}"
assert set(staged)==set(rights_ledger),(
    f"Staging/rights ledger mismatch: missing {list(set(rights_ledger)-set(staged))[:8]}, "
    f"extra {list(set(staged)-set(rights_ledger))[:8]}")
for path,sha in staged.items():
    assert sha==photos[path]["git_blob_sha"],f"Staged Git blob differs from original: {path}"

refs=defaultdict(list)
missing_refs=[]
recorded_refs=0
sources_by_folder=defaultdict(dict)
for species in index["entries"]:
    path=species["path"]
    doc=read(path)
    assert doc["id"]==species["id"] and doc["family"]=="Asteraceae"
    folder=Path(path).parent
    csv_path=ROOT/folder/"image-sources.csv"
    if csv_path.is_file():
        try:
            with csv_path.open(encoding="utf-8-sig",newline="") as f:
                reader=csv.DictReader(f)
                for row in reader:
                    key=(row.get("file_name") or row.get("file") or "").strip()
                    if key:
                        sources_by_folder[folder.as_posix()][key]=row
        except (OSError,csv.Error,UnicodeError) as ex:
            raise AssertionError(f"Metadata CSV cannot be read: {csv_path}: {ex}")
    for i,photo in enumerate(doc.get("images") or []):
        recorded_refs+=1
        raw=photo.get("file","") or ""
        rel=raw
        if isinstance(rel,str) and rel and not rel.startswith(("http://","https://")):
            target=(folder/rel).as_posix()
            if target in photos:
                refs[target].append({
                    "species_id":species["id"],"image_index":i,
                    "role":str(photo.get("role","")),"creator":str(photo.get("creator","")),
                    "license_claim":str(photo.get("license","")),"source_page":str(photo.get("source_page","")),
                    "metadata_csv_present":csv_path.is_file()
                })
                continue
            reason="SOURCE_FILE_PATH_NOT_IN_PINNED_GIT_TREE"
            resolved=target
        elif isinstance(rel,str) and rel.startswith(("http://","https://")):
            reason="EXTERNAL_IMAGE_URL_NOT_A_LOCAL_SOURCE_BLOB"
            resolved=""
        else:
            reason="BLANK_OR_UNEXPECTED_IMAGE_FILE_REFERENCE"
            resolved=""
        missing_refs.append({
            "species_id":species["id"],"image_index":i,
            "file_field":raw,"computed_source_path":resolved,"reason":reason,
            "creator":str(photo.get("creator","")),"license_claim":str(photo.get("license","")),
            "source_page":str(photo.get("source_page","")),
            "source_species_path":path
        })
assert recorded_refs==477 and len(missing_refs)==29
assert sum(map(len,refs.values()))==448
assert len(set(photos)-set(refs))==11

def license_bucket(s):
    q=str(s or "").upper().replace("_","-").replace(" ","-")
    if not q:return "UNRECORDED"
    if "BY-NC" in q or "NONCOMMERCIAL" in q:return "NC_CLAIM_UNVERIFIED"
    if "CC0" in q:return "CC0_CLAIM_UNVERIFIED"
    if "CC-BY-SA" in q or "CC-BY" in q:return "CC_ATTRIBUTION_CLAIM_UNVERIFIED"
    if "PUBLIC-DOMAIN" in q or q in {"PD","PDM"}:return "PUBLIC_DOMAIN_CLAIM_UNVERIFIED"
    if "ALL-RIGHTS-RESERVED" in q or "ALL RIGHTS RESERVED" in str(s).upper():return "ALL_RIGHTS_RESERVED"
    return "OTHER_OR_UNKNOWN_RIGHTS"

all_files=[]
counts=Counter()
by_species=defaultdict(lambda:Counter())
for path in sorted(photos):
    original=photos[path]
    links=refs.get(path,[])
    ledger=rights_ledger.get(path)
    if ledger:
        cls=ledger["ledger"]
        if cls=="commons":
            decision="ARCHIVED_EXACT_CC_COMMONS_SOURCE_VERIFIED"
            public_gate="SOURCE_CC_REVIEWED_BUT_SITE_RELEASE_AND_DERIVATIVE_CHECK_REQUIRED"
        elif cls=="inat":
            details=ledger["details"]
            decision="ARCHIVED_EXACT_INAT_SOURCE_VERIFIED_CC_BY_NC" if details.get("noncommercial_only") else "ARCHIVED_EXACT_INAT_SOURCE_VERIFIED_REUSABLE_CC"
            public_gate="NONCOMMERCIAL_ONLY; HELD_FROM_STRICT_PUBLIC_CANDIDATE" if details.get("noncommercial_only") else "SOURCE_CC_REVIEWED_BUT_SITE_RELEASE_REQUIRED"
        elif cls=="upstream_commons":
            details=ledger["details"]
            decision="ARCHIVED_UPSTREAM_COMMONS_CURRENT_CC_OR_PD_VISUALLY_MATCHED"
            public_gate="SOURCE_CURRENT_PERMISSION_AND_IMAGE_MATCHED; FINAL DERIVATIVE AND PUBLIC RELEASE QA REQUIRED"
        else:
            details=ledger["details"]
            decision="ARCHIVED_PRIVATE_CALVIN_AUTHOR_PERMISSION" if details.get("creator")=="Calvin King" else "ARCHIVED_PRIVATE_JOEY_SOURCE_LICENSE_CLAIM"
            public_gate="PRIVATE_AUTHOR_PERMISSION_ONLY" if details.get("creator")=="Calvin King" else "PRIVATE_NC_PREVIEW_ONLY; CURRENT_SOURCE_RIGHTS_PENDING"
        assert path in staged
    else:
        decision="HELD_ORIGINAL_HUB_SOURCE_NOT_IMPORTED"
        public_gate="DO_NOT_COPY_TO_PUBLIC_OR_PUBLISH_WITHOUT_SOURCE_RIGHTS_REVIEW"
        assert path not in staged
    folder=(Path(path).parent.parent).as_posix()
    basename=Path(path).name
    meta=sources_by_folder.get(folder,{}).get(basename,{})
    meta_links=[{
        "species_id":link["species_id"],"role":link["role"],
        "creator":link["creator"],"license_claim":link["license_claim"],
        "source_page":link["source_page"]
    } for link in links]
    candidates=meta_links or ([{
        "species_id":"", "role":str(meta.get("role","")),
        "creator":str(meta.get("creator","")),"license_claim":str(meta.get("license","")),
        "source_page":str(meta.get("source_page",""))
    }] if meta else [])
    claim_bucket=license_bucket(candidates[0]["license_claim"]) if candidates else "NO_REFERENCE_OR_CSV_RIGHTS"
    if ledger:
        triage="DONE_PRIVATE_SOURCE_ARCHIVE; PRESERVE_RIGHTS_GATE"
    elif not links:
        triage="NEEDS_REFERENCE_RECONCILIATION_BEFORE_PROMOTION"
    elif claim_bucket in {"CC0_CLAIM_UNVERIFIED","CC_ATTRIBUTION_CLAIM_UNVERIFIED","PUBLIC_DOMAIN_CLAIM_UNVERIFIED"}:
        triage="FIRST_RECHECK_UPSTREAM_PERMISSION_AND_CREATOR"
    elif claim_bucket=="NC_CLAIM_UNVERIFIED":
        triage="RECHECK_NONCOMMERCIAL_LICENSE_AND_EXACT_SOURCE"
    else:
        triage="OWNER_OR_SOURCE_PERMISSION_NEEDED; LEAVE_IN_ORIGINAL"
    file_record={
        "source_path":path,
        "source_git_blob_sha":original["git_blob_sha"],
        "source_size_bytes":original["size_bytes"],
        "source_pinned_commit":census["source_commit_sha"],
        "source_repo":SOURCE_REPO,
        "source_blob_link":f"https://github.com/{SOURCE_REPO}/blob/{census['source_commit_sha']}/{path}",
        "destination_path":path if path in staged else "",
        "destination_git_blob_sha":staged.get(path,""),
        "destination_staging_commit_at_audit":head,
        "archived_in_private_staging":path in staged,
        "rights_decision":decision,
        "rights_ledger":ledger["ledger"] if ledger else "",
        "rights_review_state":public_gate,
        "source_license_claim_bucket":claim_bucket,
        "followup_priority":triage,
        "original_photo_references":len(links),
        "referenced_by_species":sorted(set(x["species_id"] for x in links)),
        "unreferenced_source_photo":not bool(links),
        "listed_in_species_image_sources_csv":bool(meta),
        "source_metadata":candidates,
        "collection_ownership_status":"HUB_CANONICAL; ASTERACEAE_STAGING_NOT_LIVE",
        "action":"MIGRATED_PRIVATE; PUBLIC_RIGHTS_GATE" if ledger else "HELD_IN_PINNED_SOURCE; VERIFY_RIGHTS_BEFORE_MIGRATION"
    }
    all_files.append(file_record)
    counts[decision]+=1
    for sp in file_record["referenced_by_species"]:
        by_species[sp]["physical_source_files"]+=1
        if path in staged:by_species[sp]["staged_source_photos"]+=1
        else:by_species[sp]["source_photos_still_held"]+=1
    if not links:counts["UNREFERENCED_SOURCE_IMAGES"]+=1

assert len(all_files)==459
assert sum(1 for p in all_files if p["archived_in_private_staging"])==len(rights_ledger)
assert sum(1 for p in all_files if not p["archived_in_private_staging"])==459-len(rights_ledger)
assert sum(p["source_size_bytes"] for p in all_files)==census["physical_image_bytes"]

summary={
    "status":"ALL_SOURCE_IMAGES_AND_REFERENCES_ACCOUNTED_FOR; NOT_ALL_PUBLICATION_READY",
    "source_repo":SOURCE_REPO,
    "source_pinned_commit_sha":census["source_commit_sha"],
    "staging_repo":"Crking92/Hays-Botany-Asteraceae",
    "staging_commit_sha_at_audit":head,
    "species":180,
    "physical_source_image_files":459,
    "source_image_bytes":census["physical_image_bytes"],
    "source_image_references":477,
    "source_image_references_resolving_to_source_files":448,
    "unresolved_or_external_source_image_references":29,
    "source_files_not_referenced_by_species_card":11,
    "archived_original_images_in_private_staging":len(rights_ledger),
    "remaining_source_originals_held_and_indexed":459-len(rights_ledger),
    "source_images_without_a_migration_disposition":0,
    "staging_photos_without_a_source_or_rights_ledger":0,
    "migrated_photo_categories":dict(Counter(p["rights_decision"] for p in all_files if p["archived_in_private_staging"])),
    "held_license_claim_buckets":dict(Counter(p["source_license_claim_bucket"] for p in all_files if not p["archived_in_private_staging"])),
    "held_followup_priority":dict(Counter(p["followup_priority"] for p in all_files if not p["archived_in_private_staging"])),
    "missing_reference_reasons":dict(Counter(r["reason"] for r in missing_refs)),
    "unreferenced_source_image_files":sum(p["unreferenced_source_photo"] for p in all_files),
    "public_release_allowed_by_audit":False,
    "original_hub_remains_authoritative":True,
    "assertions":"Source file paths, sizes, Git blob IDs, staged file IDs, rights ledgers, and all source references reconciled; rights claims for held images NOT verified."
}

all_refs=sorted(missing_refs,key=lambda r:(r["species_id"],r["image_index"]))
write(out/"asteraceae-full-image-asset-reconciliation.json",all_files)
write(out/"asteraceae-unresolved-image-references.json",all_refs)
write(out/"asteraceae-full-image-reconciliation-summary.json",summary)
write(out/"asteraceae-species-image-coverage.json",{r["id"]:dict(by_species[r["id"]]) for r in index["entries"]})
with (out/"asteraceae-full-image-asset-reconciliation.csv").open("w",encoding="utf-8",newline="") as f:
    fields=("source_path","source_git_blob_sha","source_size_bytes","archived_in_private_staging",
        "rights_decision","source_license_claim_bucket","original_photo_references",
        "unreferenced_source_photo","listed_in_species_image_sources_csv","followup_priority",
        "referenced_by_species","rights_review_state","action","source_blob_link")
    w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
    w.writeheader()
    for p in all_files:
        q={k:p[k] for k in fields}
        q["referenced_by_species"]="; ".join(q["referenced_by_species"])
        w.writerow(q)
write(qa/"summary.json",summary)
write(qa/"missing-reference-sample.json",all_refs[:29])
print("ASTERACEAE_ASSET_RECONCILIATION",json.dumps(summary,sort_keys=True),flush=True)
