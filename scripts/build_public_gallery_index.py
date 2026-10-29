#!/usr/bin/env python3
"""Build a photo count/thumbnail catalog only from existing public rights-cleared species cards.
Never imports archived, quarantined, NC or unreviewed images.
"""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
INDEX=json.loads((SITE/"data/collection-index.json").read_text(encoding="utf-8"))
assert INDEX["collection_id"]=="asteraceae" and len(INDEX["entries"])==180
data={}
photo_count=0
with_photos=0
seen=set()
for row in INDEX["entries"]:
    id=row["id"]
    assert id not in seen
    seen.add(id)
    path=SITE/"data/species"/(id+".json")
    assert path.is_file(),id
    card=json.loads(path.read_text(encoding="utf-8"))
    assert card["id"]==id and card["family"]==row["family"]
    photos=card.get("verified_photos",[])
    assert isinstance(photos,list)
    for photo in photos:
        assert photo.get("private_rights_review_only") is False and photo.get("noncommercial_only") is False,id
        license_name=photo.get("license","")
        assert re.match(r"^(CC BY(?: SA|-SA)? [234]\.0|CC0(?: 1\.0)?)$",license_name),id
        assert photo.get("creator") and photo.get("source_page","").startswith("https://"),id
        assert photo.get("license_url","").startswith(("https://creativecommons.org/licenses/","https://creativecommons.org/publicdomain/zero/")),id
        relative=photo.get("src","")
        assert re.fullmatch(r"media/[a-z0-9-]+/[A-Za-z0-9_-]+\.jpg",relative),id
        assert relative.startswith("media/"+id+"/")
        file=SITE/relative
        assert file.is_file() and file.stat().st_size>500,id+": "+relative
    data[id]={"count":len(photos),"first_src":photos[0]["src"] if photos else None}
    photo_count+=len(photos)
    with_photos+=int(bool(photos))
summary=json.loads((SITE/"data/preview-summary.json").read_text(encoding="utf-8"))
assert photo_count==summary["verified_photo_copies"],("Photo release differs from summary",photo_count,summary["verified_photo_copies"])
assert with_photos==summary["species_with_cc_photos"]
out={"schema_version":1,"status":"ONLY_EXISTING_PUBLIC_RIGHTS_CLEARED_SITE_IMAGES",
     "species":len(data),"photo_species":with_photos,"photo_count":photo_count,"entries":data}
destination=SITE/"data/gallery-index.json"
destination.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("ASTERACEAE_APPROVED_GALLERY_INDEX_PASS",json.dumps(
  {"species":len(data),"photographed_species":with_photos,"photos":photo_count,"rights_held_added":0},
  sort_keys=True))
