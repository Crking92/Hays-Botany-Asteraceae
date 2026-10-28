#!/usr/bin/env python3
"""Assemble a private, nondeployed Asteraceae test site with real source-verified CC photos."""
import hashlib, json, re, shutil, sys
from collections import Counter
from pathlib import Path
from PIL import Image, ImageOps

SHELL=Path(__file__).resolve().parents[1]
STAGING=Path(sys.argv[1]).resolve()
DEST=SHELL/"dist"
config=json.loads((STAGING/"config/collection.json").read_text())
index=json.loads((STAGING/"data/collection-index.json").read_text())
census=json.loads((STAGING/"migration/asteraceae-source-census.json").read_text())
ledger_path=STAGING/"migration/asteraceae-verified-commons-photo-ledger.json"
assert ledger_path.is_file(),"No independently verified Commons images archived yet"
approved=json.loads(ledger_path.read_text())
assert config["publication"]["enabled"] is False and index["authority"]=="STAGING_ONLY"
assert len(index["entries"])==180 and len(approved)>=2
assert index["source_commit_sha"]==census["source_commit_sha"]
if DEST.exists():shutil.rmtree(DEST)
(DEST/"data/species").mkdir(parents=True)
for name in ("index.html","styles.css","app.js","RUN_ASTERACEAE_REVIEW.bat"):
    shutil.copyfile(SHELL/"site"/name,DEST/name)
h=(DEST/"index.html").read_text()
h=h.replace("Layout prototype only.</strong> No botanical records or photographs have been transferred to this collection.",
    "Photo-rights review preview.</strong> Real source-backed botanical lessons and independently checked Commons CC photographs are included here for private testing. Some photos are still held.")
assert "Photo-rights review preview." in h
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
    for original in doc.get("images") or []:
        rel=original.get("file","")
        full=row["path"].rsplit("/",1)[0]+"/"+rel if rel and not rel.startswith(("https:","http:")) else ""
        if full not in approved:continue
        info=approved[full]
        assert info["publication_approval"].startswith("STAGING_IMAGE_ONLY")
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
        photos.append({"src":out_rel,"creator":info["creator"],"license":info["license"],"license_url":info["license_url"],
                       "source_page":info["source_page"],"role":original.get("role",""),
                       "modified":"Scaled/converted to JPEG, metadata removed; no anatomy overlays",
                       "source_blob_sha":sha})
        photo_count+=1;photo_species.add(doc["id"])
    public_safe={"id":doc["id"],"scientific_name":doc["scientific_name"],"common_name":doc.get("common_name",""),
         "family":"Asteraceae","genus":doc["genus"],"look_here_first":to_text(doc.get("look_here_first")),
         "key_traits":traits,"lookalikes":{"names":names,"differences":diff},
         "verified_photos":photos,"media_status":"PARTIAL_VERIFIED_COMMONS_ONLY",
         "source_snapshot_sha":index["source_commit_sha"]}
    (DEST/"data/species"/(doc["id"]+".json")).write_text(json.dumps(public_safe,indent=2,ensure_ascii=False)+"\n")
jpgs=list(DEST.rglob("*.jpg"))
assert len(jpgs)==photo_count and photo_count>=2
assert len(list((DEST/"data/species").glob("*.json")))==180
assert not (DEST/"content").exists()
summary={"status":"PRIVATE_PHOTO_REVIEW_PREVIEW_NOT_DEPLOYED","species":180,
         "species_with_cc_photos":len(photo_species),"verified_photo_copies":photo_count,
         "source_verified_distinct_archives":len(approved),"source_commit_sha":index["source_commit_sha"],
         "output_jpegs":len(jpgs),"public_pages_enabled":False}
(DEST/"data/preview-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("ASTERACEAE_PHOTO_SITE",json.dumps(summary,sort_keys=True),flush=True)
