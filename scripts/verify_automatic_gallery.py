#!/usr/bin/env python3
"""Validate a growing family gallery, not a frozen one-time migration report."""
import argparse,hashlib,json
from pathlib import Path
def git_sha(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def validate(site):
    data=site/"data"
    idx=json.loads((data/"collection-index.json").read_text())
    gal=json.loads((data/"gallery-index.json").read_text())
    meta=json.loads((data/"collection-meta.json").read_text())
    rows=idx["entries"];ids=[r["id"] for r in rows]
    assert len(ids)==len(set(ids))==gal["species"]
    assert set(ids)==set(gal["entries"])
    assert gal["status"]=="ONLY_EXISTING_PUBLIC_RIGHTS_CLEARED_SITE_IMAGES"
    assert {p.stem for p in (data/"species").glob("*.json")}==set(ids)
    assigned=set(meta["family_assignments"])
    paths=set();photo_total=0;photo_species=0
    for row in rows:
        sid=row["id"]
        c=json.loads((data/"species"/(sid+".json")).read_text())
        assert c["id"]==sid and c["family"]==row["family"] and c["family"] in assigned
        assert c["genus"]==row["genus"] and c["scientific_name"]==row["scientific_name"]
        photos=c["verified_photos"]
        assert isinstance(photos,list) and len(photos)==row["photo_count"]==gal["entries"][sid]["count"],sid
        assert gal["entries"][sid]["first_src"]==(photos[0]["src"] if photos else None),sid
        photo_species+=bool(photos);photo_total+=len(photos)
        for p in photos:
            src=p["src"]
            assert src.startswith("media/"+sid+"/") and ".." not in Path(src).parts
            f=site/src
            assert f.is_file() and not f.is_symlink() and src not in paths,src
            paths.add(src)
            binary=f.read_bytes()
            # Legacy scaled/converted display copies may preserve an original-source blob SHA;
            # do not overwrite or misinterpret that historical provenance.
            # For all newly installed unmodified originals, require exact original SHA256
            # and the actual Git blob SHA to agree with the public file bytes.
            if p.get("display_sha256"):
                # The original hashes refer to the immutable archived source.
                # Display hashes refer to the web-size derivative currently served.
                assert hashlib.sha256(binary).hexdigest()==p["display_sha256"],src
                assert git_sha(binary)==p["display_blob_sha"],src
                assert p.get("display_original_archive_commit") or p.get("display_original_intake_path"),src
                assert p.get("display_original_site_sha256"),src
            elif p.get("sha256"):
                assert hashlib.sha256(binary).hexdigest()==p["sha256"],src
                assert git_sha(binary)==p["source_blob_sha"],src
            assert p.get("creator") and p.get("source_page","").startswith("https://")
            assert p.get("license_url","").startswith("https://")
            assert not p.get("private_rights_review_only")
            nc=p.get("license") in {"CC BY-NC 4.0","CC BY-NC-SA 4.0"}
            assert p.get("noncommercial_only") is nc
            if nc:assert meta.get("photo_license_policy",{}).get("noncommercial_educational_use") is True
    files={p.relative_to(site).as_posix() for p in (site/"media").rglob("*") if p.is_file()}
    assert paths==files,{"orphan":sorted(files-paths)[:5],"missing":sorted(paths-files)[:5]}
    assert gal["photo_count"]==photo_total and gal["photo_species"]==photo_species
    site_bytes=sum(p.stat().st_size for p in site.rglob("*") if p.is_file())
    if site_bytes >= 800_000_000:
        print(json.dumps({"status":"ASTERACEAE_PUBLIC_SITE_SIZE_WARNING",
                          "site_bytes":site_bytes, "warning_bytes":800_000_000}))
    # Before the first optimization we allow the existing oversized release to be
    # checked; afterward enforce a hard ceiling before publishing future batches.
    if (data/"web-display-optimization.json").exists():
        assert site_bytes <= 950_000_000, (
            "PUBLIC_WEBSITE_SIZE_GUARD: optimize new images before publishing",site_bytes)
    print(json.dumps({"status":"PASS_GROWING_FAMILY_GALLERY","species":len(ids),
                      "photos":photo_total,"photographed_species":photo_species,
                      "site_bytes":site_bytes}))
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--site-root",type=Path,default=Path("site"))
    a=ap.parse_args()
    validate(a.site_root.resolve())
