#!/usr/bin/env python3
"""Assemble a private, nondeployed Asteraceae test site with real source-verified CC photos.
The 2026-10-28 preview preserves NC photo restrictions and never publishes Pages.
"""
import hashlib, json, os, re, shutil, sys
from collections import Counter
from pathlib import Path
from PIL import Image, ImageOps

SHELL=Path(__file__).resolve().parents[1]
STAGING=Path(sys.argv[1]).resolve()
STRICT_PUBLIC_CC=os.environ.get("HAYS_ASTERACEAE_PUBLIC_STRICT")=="1"
DEST=SHELL/"dist"
config=json.loads((STAGING/"config/collection.json").read_text())
index=json.loads((STAGING/"data/collection-index.json").read_text())
census=json.loads((STAGING/"migration/asteraceae-source-census.json").read_text())
ledger_path=STAGING/"migration/asteraceae-verified-commons-photo-ledger.json"
assert ledger_path.is_file(),"No independently verified Commons images archived yet"
commons_approved=json.loads(ledger_path.read_text())
inat_path=STAGING/"migration/asteraceae-verified-inat-photo-ledger.json"
inat_approved=json.loads(inat_path.read_text()) if inat_path.is_file() else {}
assert not (set(commons_approved)&set(inat_approved)), "Overlapping license sources require review"
author_path=STAGING/"migration/asteraceae-author-permitted-private-photo-ledger.json"
author_private=json.loads(author_path.read_text()) if author_path.is_file() else {}
upstream_path=STAGING/"migration/asteraceae-upstream-commons-120-ledger.json"
upstream_verified=json.loads(upstream_path.read_text()) if upstream_path.is_file() else {}
inat_taxon_path=STAGING/"migration/asteraceae-upstream-inat-taxon-120-ledger.json"
inat_taxon_verified=json.loads(inat_taxon_path.read_text()) if inat_taxon_path.is_file() else {}
gbif_path=STAGING/"migration/asteraceae-upstream-gbif-120-ledger.json"
gbif_verified=json.loads(gbif_path.read_text()) if gbif_path.is_file() else {}
nc84_path=STAGING/"migration/asteraceae-verified-84-nc-photo-ledger.json"
nc84_verified=json.loads(nc84_path.read_text()) if nc84_path.is_file() else {}
assert all(v.get("noncommercial_only") is True for v in nc84_verified.values()), "NC84 rights restriction absent"
orphan_path=STAGING/"migration/asteraceae-orphan11-verified-photo-ledger.json"
orphan_verified=json.loads(orphan_path.read_text()) if orphan_path.is_file() else {}
zero_path=STAGING/"migration/asteraceae-zero-species-commons-recovery-ledger.json"
zero_verified=json.loads(zero_path.read_text()) if zero_path.is_file() else {}
overrides_path=STAGING/"migration/asteraceae-orphan11-gallery-overrides.json"
orphan_overrides=json.loads(overrides_path.read_text()) if overrides_path.is_file() else {}
assert {x["source_path"] for values in orphan_overrides.values() for x in values}==set(orphan_verified), "Orphan source photos not exactly mapped to gallery entries"
all_ledgers=[set(commons_approved),set(inat_approved),set(author_private),set(upstream_verified),set(inat_taxon_verified),set(gbif_verified),set(nc84_verified),set(orphan_verified),set(zero_verified)]
assert sum(map(len,all_ledgers))==len(set().union(*all_ledgers)), "Photo rights ledgers overlap; needs human review"
approved={**commons_approved,**inat_approved,**author_private,**upstream_verified,**inat_taxon_verified,**gbif_verified,**nc84_verified,**orphan_verified,**zero_verified}
# Fresh research-grade observation photographs live outside the canonical 459-file
# original-photo audit. They have individual iNat photo licenses and full metadata.
fresh_path=STAGING/"migration/asteraceae-new-texas-inat-cc-photo-ledger.json"
new_external=json.loads(fresh_path.read_text()) if fresh_path.is_file() else {}
assert not (set(approved)&set(new_external)), "New and original source photo ledgers overlap"
assert all(
    v.get("license") in ("CC0 1.0","CC BY 4.0","CC BY-SA 4.0")
    and v.get("noncommercial_only") is False
    and v.get("exact_observation_taxon_match") is True
    for v in new_external.values()
), "A new photo license, observation identity or public-safety condition failed"
all_approved={**approved,**new_external}
assert config["publication"]["enabled"] is False and index["authority"]=="STAGING_ONLY"
assert len(index["entries"])==180 and len(approved)>=2
# No archived picture may evade the per-photo rights ledger, even in private.
source_images=[
    x for x in (STAGING/"content/taxa/Asteraceae").rglob("*")
    if x.is_file() and x.suffix.lower() in {".jpg",".jpeg",".png",".webp",".gif",".tif",".tiff"}
]
assert len(source_images)==len(approved), (
    f"Untracked staging photo bytes or incomplete rights ledger: {len(source_images)}/{len(approved)}"
)
fresh_root=STAGING/"external-media/asteraceae/texas-inat"
fresh_staged={x.relative_to(STAGING).as_posix() for x in fresh_root.rglob("*.jpg")} if fresh_root.exists() else set()
assert fresh_staged==set(new_external), (
    f"Untracked external staged photos or incomplete new-media ledger: {len(fresh_staged)}/{len(new_external)}"
)
assert all(v["species_id"] in {r["id"] for r in index["entries"]} for v in new_external.values())
assert index["source_commit_sha"]==census["source_commit_sha"]
if DEST.exists():shutil.rmtree(DEST)
(DEST/"data/species").mkdir(parents=True)
for name in ("index.html","styles.css","app.js","RUN_ASTERACEAE_REVIEW.bat"):
    shutil.copyfile(SHELL/"site"/name,DEST/name)
h=(DEST/"index.html").read_text()
h=h.replace("Layout prototype only.</strong> No botanical records or photographs have been transferred to this collection.",
    "Photo-rights review preview.</strong> Real source-backed botanical lessons and independently checked Commons CC photographs are included here for private testing. Some photos are still held.")
assert "Photo-rights review preview." in h
if STRICT_PUBLIC_CC:
    h=h.replace("PRIVATE STAGING · NOT PUBLISHED", "PUBLIC TEST · NOT FINALIZED")
    h=h.replace("for private testing.", "for a public field-learning test.")
assert '<meta name="robots" content="noindex,nofollow">' in h
(DEST/"index.html").write_text(h)
(DEST/"data/collection-meta.json").write_text(json.dumps(config,indent=2)+"\n")
(DEST/"data/collection-index.json").write_text(json.dumps(index,indent=2,ensure_ascii=False)+"\n")

def to_text(value):
    if isinstance(value,str):return value.strip()
    if isinstance(value,list):return "; ".join(str(v).strip() for v in value if isinstance(v,(str,int,float)))
    return ""

photo_count=0
photo_species=set()
nc_photo_count=0
private_author_photo_count=0
for row in index["entries"]:
    src=STAGING/row["path"]; assert src.is_file()
    doc=json.loads(src.read_text())
    assert doc["id"]==row["id"] and doc["family"]=="Asteraceae"
    traits=[]
    morph=doc.get("morphology_keys") or {}
    if isinstance(morph,dict):
        for k,v in morph.items():
            s=to_text(v)
            if s:traits.append({"label":k.replace("_"," ").capitalize(),"text":s[:950]})
    compared=doc.get("comparisons") or {}
    if isinstance(compared,dict):
        names=compared.get("confused_with") or []
        if isinstance(names,str):names=[names]
        names=[x for x in names if isinstance(x,str)][:12] if isinstance(names,list) else []
        diff=to_text(compared.get("key_distinctions"))
    else:names,diff=[],""
    photos=[]
    sourced_additions=[{"source_path":path,"role":meta.get("role","Texas research-grade observation photo")}
                       for path,meta in new_external.items() if meta["species_id"]==doc["id"]]
    for original in (doc.get("images") or []) + orphan_overrides.get(doc["id"],[]) + sourced_additions:
        rel=original.get("file","")
        full=original.get("source_path") or (row["path"].rsplit("/",1)[0]+"/"+rel if rel and not rel.startswith(("https:","http:")) else "")
        if full not in all_approved:continue
        if STRICT_PUBLIC_CC and (
            full in author_private or full in gbif_verified or all_approved[full].get("noncommercial_only",False)
            or not str(all_approved[full].get("license_url","")).replace("http://","https://").startswith("https://creativecommons.org/")
        ):continue
        info=all_approved[full]
        assert info["publication_approval"].startswith(("STAGING_IMAGE_ONLY","PRIVATE_EDUCATIONAL_PREVIEW_ONLY","PRIVATE_STAGING_SOURCE_VERIFIED","PRIVATE_GBIF_SOURCE_VERIFIED_ONLY","PRIVATE_NONCOMMERCIAL_STAGING_ONLY","STAGING_NEW_INAT_OBSERVATION_CC_SOURCE_VERIFIED"))
        source=STAGING/full
        assert source.is_file(),f"Missing archived source photo {full}"
        b=source.read_bytes()
        sha=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
        assert sha==info["source_git_blob_sha"],f"Staged image SHA mismatch: {full}"
        out_rel="media/"+doc["id"]+"/"+str(len(photos)+1).zfill(2)+".jpg"
        dest=DEST/out_rel; dest.parent.mkdir(parents=True,exist_ok=True)
        with Image.open(source) as im:
            img=ImageOps.exif_transpose(im)
            if img.mode not in ("RGB","L"):img=img.convert("RGB")
            elif img.mode=="L":img=img.convert("RGB")
            img.thumbnail((1600,1600),Image.Resampling.LANCZOS)
            img.save(dest,format="JPEG",quality=83,optimize=True,exif=b"")
        photos.append({"src":out_rel,"creator":info["creator"],"license":info["license"],"license_url":info["license_url"].replace("http://creativecommons.org/","https://creativecommons.org/"),
                       "source_page":info["source_page"],"role":original.get("role",""),
                       "modified":"Scaled/converted to JPEG, metadata removed; no anatomy overlays",
                       "source_blob_sha":sha,"noncommercial_only":bool(info.get("noncommercial_only",False)),
                       "private_rights_review_only":full in author_private or full in gbif_verified or (full in orphan_verified and orphan_verified[full].get("noncommercial_only",False)),
                       "source_page_is_exact":bool(info.get("source_page_verified",True)),
                       "rights_note":info.get("permission_basis","") or ("GBIF individual multimedia license and exact image verified; secondary current-source and public release check still required." if full in gbif_verified else "")})
        photo_count+=1;photo_species.add(doc["id"])
        if info.get("noncommercial_only",False):nc_photo_count+=1
        if full in author_private:private_author_photo_count+=1
    public_safe={"id":doc["id"],"scientific_name":doc["scientific_name"],"common_name":doc.get("common_name",""),
         "family":"Asteraceae","genus":doc["genus"],"look_here_first":to_text(doc.get("look_here_first")),
         "key_traits":traits,"lookalikes":{"names":names,"differences":diff},
         "verified_photos":photos,"media_status":"VERIFIED_PUBLIC_STRICT_CC_ONLY" if STRICT_PUBLIC_CC else "PRIVATE_MIXED_RIGHTS_PREVIEW_AND_AUTHOR_PERMISSION",
         "source_snapshot_sha":index["source_commit_sha"]}
    (DEST/"data/species"/(doc["id"]+".json")).write_text(json.dumps(public_safe,indent=2,ensure_ascii=False)+"\n")
jpgs=list(DEST.rglob("*.jpg"))
assert len(jpgs)==photo_count and photo_count>=2
if STRICT_PUBLIC_CC:
    assert private_author_photo_count==0, "Owner permission or provisional source photo leaked to strict CC output"
else:
    assert private_author_photo_count==len(author_private), "Private author photo archive not fully represented"
assert len(list((DEST/"data/species").glob("*.json")))==180
assert not (DEST/"content").exists()
summary={"status":"STRICT_PUBLIC_CC_RELEASE_CANDIDATE" if STRICT_PUBLIC_CC else "PRIVATE_PHOTO_REVIEW_PREVIEW_NOT_DEPLOYED","species":180,
         "species_with_cc_photos":len(photo_species),"verified_photo_copies":photo_count,
         "source_verified_distinct_archives":len(commons_approved)+len(inat_approved)+len(upstream_verified)+len(inat_taxon_verified)+len(gbif_verified)+len(nc84_verified)+len(orphan_verified),
         "verified_orphan11_gallery_photos":len(orphan_verified),
         "recovered_zero_photo_species_commons":len(zero_verified),
         "new_texas_cc_field_photo_copies":len(new_external),
         "new_texas_cc_field_species":len({x["species_id"] for x in new_external.values()}),
         "new_verified_upstream_commons_archives":len(upstream_verified),
         "new_verified_inat_taxon_archives":len(inat_taxon_verified),
         "new_verified_gbif_media_archives":len(gbif_verified),
         "new_exact_verified_nc84_archives":len(nc84_verified),
         "owner_or_source_record_only_private_photo_archives":len(author_private),
         "owner_or_source_record_only_private_photo_copies":private_author_photo_count,
         "species_with_any_review_photos":len(photo_species),
         "noncommercial_only_previews":nc_photo_count,"source_commit_sha":index["source_commit_sha"],
         "output_jpegs":len(jpgs),"public_pages_enabled":False,
         "strict_public_cc":STRICT_PUBLIC_CC}
(DEST/"data/preview-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("ASTERACEAE_PHOTO_SITE",json.dumps(summary,sort_keys=True),flush=True)
