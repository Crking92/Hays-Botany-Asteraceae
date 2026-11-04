#!/usr/bin/env python3
"""Rebuild growing Asteraceae gallery counts from genuinely published credited originals.

No frozen preview-summary counts, no strict-CC-only assumption: the
owner's noncommercial educational family site may display individually
verified CC BY-NC and CC BY-NC-SA originals with their true restriction.
Never import archives, holds or staged/unreviewed photos.
"""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
DATA=SITE/"data"
idx=json.loads((DATA/"collection-index.json").read_text())
gallery_path=DATA/"gallery-index.json"
gallery=json.loads(gallery_path.read_text())
meta=json.loads((DATA/"collection-meta.json").read_text())
assert meta["repository_full_name"]=="Crking92/Hays-Botany-Asteraceae"
assert idx["collection_id"]=="asteraceae" and len(idx["entries"])==180
assert gallery["status"]=="ONLY_EXISTING_PUBLIC_RIGHTS_CLEARED_SITE_IMAGES"
ids=[r["id"] for r in idx["entries"]]
assert len(ids)==len(set(ids))==180
assert {p.stem for p in (DATA/"species").glob("*.json")}==set(ids)
data={}
all_paths=set()
total=represented=0
for row in idx["entries"]:
    sid=row["id"]
    card=json.loads((DATA/"species"/(sid+".json")).read_text())
    assert card["id"]==sid and card["family"]==row["family"]=="Asteraceae"
    photos=card.get("verified_photos",[])
    assert isinstance(photos,list) and row["photo_count"]==len(photos),sid
    for photo in photos:
        relative=photo.get("src","")
        assert re.fullmatch(r"media/"+re.escape(sid)+r"/[A-Za-z0-9_.-]+\\.(?:jpg|jpeg|png|webp)",relative),sid
        assert relative not in all_paths,relative
        all_paths.add(relative)
        path=SITE/relative
        assert path.is_file() and not path.is_symlink(),relative
        original=path.read_bytes()
        blob=hashlib.sha1(b"blob "+str(len(original)).encode()+b"\\0"+original).hexdigest()
        assert blob==photo.get("source_blob_sha"),relative
        assert photo.get("creator") and photo.get("source_page","").startswith("https://"),relative
        assert photo.get("license_url","").startswith("https://"),relative
        assert not photo.get("private_rights_review_only"),relative
        nc=photo.get("license") in ("CC BY-NC 4.0","CC BY-NC-SA 4.0")
        assert photo.get("noncommercial_only") is nc,relative
        if nc: assert meta["photo_license_policy"]["noncommercial_educational_use"] is True
    count=len(photos)
    data[sid]={"count":count,"first_src":photos[0]["src"] if photos else None}
    total+=count
    represented+=bool(photos)
existing={p.relative_to(SITE).as_posix() for p in (SITE/"media").rglob("*") if p.is_file()}
assert existing==all_paths,{"orphan":sorted(existing-all_paths)[:5],"missing":sorted(all_paths-existing)[:5]}
out={"schema_version":1,"status":gallery["status"],"species":180,"photo_species":represented,"photo_count":total,"entries":data}
gallery_path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\\n")
print("ASTERACEAE_GROWING_GALLERY_INDEX_PASS",json.dumps({"species":180,"photos":total,"photographed_species":represented}))
