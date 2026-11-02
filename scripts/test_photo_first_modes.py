#!/usr/bin/env python3
"""Isolated policy integration test. Only synthetic photos; no website or GitHub photo writes."""
from __future__ import annotations
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
GRASS=(ROOT/"site/data/poaceae-index.json").exists()
PUB=ROOT/"scripts"/("publish_approved_grass_photos.py" if GRASS else "publish_approved_family_photos.py")
SID="schizachyrium-scoparium" if GRASS else json.loads((ROOT/"site/data/collection-index.json").read_text())["entries"][0]["id"]

def invoke(source:Path, site:Path, should_pass:bool=True, check:bool=True):
    args=[sys.executable,str(PUB),"--source-root",str(source),"--site-root",str(site)]
    if check: args.append("--check")
    p=subprocess.run(args,capture_output=True,text=True)
    if (p.returncode==0)!=should_pass:
        raise AssertionError(f"unexpected result {p.returncode}: {p.stdout} {p.stderr}")
    return json.loads(p.stdout) if should_pass else None

def main():
    with tempfile.TemporaryDirectory(prefix="photo-first-nc-standing-policy-") as temp:
        root=Path(temp)
        site=root/"site"
        source=root/"source"
        shutil.copytree(ROOT/"site/data",site/"data")
        if not GRASS:
            policy=json.loads((site/"data/collection-meta.json").read_text())["photo_license_policy"]
            assert policy["noncommercial_educational_use"] is True
        else:
            policy=json.loads((site/"data/photo-license-policy.json").read_text())
            assert policy["noncommercial_educational_use"] is True
        photo_dir=source/"photo-intake/approved"/SID
        photo_dir.mkdir(parents=True)
        img=photo_dir/"qa-synthetic-standing-nc-photo.jpg"
        Image.new("RGB",(340,260),(60,150,120)).save(img,quality=90)
        sidecar=img.with_name(img.name+".json")
        meta={
            "species_id":SID,"photo_file":img.name,
            "status":"APPROVED_FOR_PUBLIC_FAMILY_SITE",
            "rights_approved_for_public":True,"taxon_reviewed":True,
            "approval_mode":"OWNER_STANDING_PHOTO_FIRST_POLICY",
            "policy_ref":"PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02",
            "review_operator":"Automated synthetic fixture (not a real review)",
            "source_review_evidence":"Synthetic image created in a temporary test directory; no real external copyright rights are asserted.",
            "taxon_review_evidence":"Synthetic test shape is intentionally NOT a botanical specimen or identification. Never publish it.",
            "approval_note":"Isolated integration test of conditional noncommercial and evidence fields; no live-image approval.",
            "creator":"Test program - generated synthetic image",
            "source_page":"https://example.org/qa-only-synthetic-image-not-published",
            "source_page_is_exact":True,
            "license":"CC BY-NC 4.0",
            "license_url":"https://creativecommons.org/licenses/by-nc/4.0/",
            "noncommercial_site_use_confirmed":True,
            "role":"Test-only general view without anatomical labels",
            "modifications":"Synthetic QA pixels, never a published image"
        }
        sidecar.write_text(json.dumps(meta))
        first=invoke(source,site)
        assert first["installed"]==1,first
        assert not (site/"media"/SID/img.name).exists()
        actual=invoke(source,site,check=False)
        assert actual["installed"]==1,actual
        assert (site/"media"/SID/img.name).exists()
        record=json.loads((site/"data/species"/(SID+".json")).read_text())
        new=record["panels"][-1] if GRASS else record["verified_photos"][-1]
        assert new["license"]=="CC BY-NC 4.0"
        assert new["noncommercial_only"] is True
        assert new["photo_approval_mode"]=="OWNER_STANDING_PHOTO_FIRST_POLICY"
        assert new["source_review_evidence"]==meta["source_review_evidence"]
        assert invoke(source,site)["installed"]==0
        for field,bad in [("noncommercial_site_use_confirmed",False),
                          ("source_review_evidence",""),
                          ("taxon_reviewed",False),
                          ("license_url","https://creativecommons.org/licenses/by/4.0/")]:
            original=meta[field]
            meta[field]=bad
            sidecar.write_text(json.dumps(meta))
            invoke(source,site,should_pass=False)
            meta[field]=original
        print("PASS: isolated evidence-based standing policy, NC site gate, repeat and rejection tests for",SID)

if __name__=="__main__":
    main()
