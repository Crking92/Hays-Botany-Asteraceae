#!/usr/bin/env python3
"""Isolated photo intake integration tests; never modifies real website or staging."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/publish_approved_family_photos.py"
SRC_PHOTO=ROOT/"site/media/achillea-millefolium/01.jpg"
SPECIES="achillea-millefolium"

def run(source,site,expect_pass=True,check=False):
    argv=[sys.executable,str(SCRIPT),"--source-root",str(source),"--site-root",str(site)]
    if check:argv.append("--check")
    process=subprocess.run(argv,text=True,capture_output=True)
    if expect_pass and process.returncode!=0:
        raise AssertionError("Expected intake success, got "+process.stdout+process.stderr)
    if not expect_pass and process.returncode==0:
        raise AssertionError("Expected rights-safe rejection, got "+process.stdout)
    return process

def main():
    before_gallery=json.loads((ROOT/"site/data/gallery-index.json").read_text())
    before_count=before_gallery["photo_count"]
    original=json.loads((ROOT/"site/data/species"/(SPECIES+".json")).read_text())
    photo=original["verified_photos"][0]
    with tempfile.TemporaryDirectory(prefix="fabaceae-qa-") as temp:
        folder=Path(temp)
        source=folder/"source"
        target=folder/"site"
        shutil.copytree(ROOT/"site",target)
        inbox=source/"photo-intake/approved"/SPECIES
        inbox.mkdir(parents=True)
        image=inbox/"qa-yarrow-crop.jpg"
        with Image.open(SRC_PHOTO) as src:
            w,h=src.size
            src.crop((0,0,min(w,620),min(h,440))).convert("RGB").save(image,quality=89)
        sidecar=image.with_name(image.name+".json")
        meta={
            "species_id":SPECIES,"photo_file":image.name,
            "status":"APPROVED_FOR_PUBLIC_FAMILY_SITE",
            "rights_approved_for_public":True,"taxon_reviewed":True,
            "approved_by":"Automated isolated QA fixture (not a live approval)",
            "approval_note":"Isolated end-to-end QA using a permitted crop of an already-published CC BY image; not added to real repo",
            "creator":photo["creator"],"source_page":photo["source_page"],
            "source_page_is_exact":True,"license":photo["license"],
            "license_url":photo["license_url"],
            "role":"QA crop test of existing approved Yarrow photograph",
            "modifications":"Crop from an existing licensed photograph; QA only"
        }
        sidecar.write_text(json.dumps(meta))
        dry=run(source,target,check=True)
        assert json.loads(dry.stdout)["installed"]==1
        assert not (target/"media"/SPECIES/image.name).exists(),"dry run unexpectedly wrote image"
        release=run(source,target)
        result=json.loads(release.stdout)
        assert result["installed"]==1 and result["photo_count"]==before_count+1,result
        newcard=json.loads((target/"data/species"/(SPECIES+".json")).read_text())
        assert len(newcard["verified_photos"])==len(original["verified_photos"])+1
        assert newcard["verified_photos"][-1]["creator"]==photo["creator"]
        assert (target/"media"/SPECIES/image.name).is_file()
        assert json.loads((target/"data/gallery-index.json").read_text())["photo_count"]==before_count+1
        repeat=run(source,target)
        assert json.loads(repeat.stdout)["installed"]==0,"idempotence failed"
        meta["rights_approved_for_public"]=False
        sidecar.write_text(json.dumps(meta))
        run(source,target,expect_pass=False,check=True)
        meta["rights_approved_for_public"]=True
        meta["license"]="CC BY-NC 4.0"
        sidecar.write_text(json.dumps(meta))
        run(source,target,expect_pass=False,check=True)
        meta["license"]=photo["license"]
        meta["species_id"]="wrong-plant"
        sidecar.write_text(json.dumps(meta))
        run(source,target,expect_pass=False,check=True)
        # Orphan source image without metadata must be rejected.
        meta["species_id"]=SPECIES
        sidecar.write_text(json.dumps(meta))
        orphan=inbox/"orphan-source-photo.jpg"
        shutil.copyfile(image,orphan)
        run(source,target,expect_pass=False,check=True)
    assert json.loads((ROOT/"site/data/gallery-index.json").read_text())["photo_count"]==before_count
    print("PASS: dry-run, new approved photo, published bytes, index counts, repeat idempotence, rights/license/taxon/orphan rejection")
if __name__=="__main__":main()
