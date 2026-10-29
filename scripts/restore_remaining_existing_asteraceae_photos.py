#!/usr/bin/env python3
"""Recover missing existing-source Asteraceae CC photos from exact staged original files.
Retains all 153 previously reviewed photos. No new searches or media downloads.
"""
import hashlib,json,re,shutil,sys
from collections import Counter
from pathlib import Path
SRC=Path(sys.argv[1]);ROOT=Path(sys.argv[2]);SITE=ROOT/"site"
index_path=SITE/"data/collection-index.json"
index=json.loads(index_path.read_text())
assert len(index["entries"])==180
reason=Counter();held={};extra=0;already=0;source_records=0;source_bytes=0
def permission(p):
    license=str(p.get("license") or "").strip()
    if re.search(r"NC|ND|review|private|unknown|unverified|not verified|all rights reserved",license,re.I):return None
    if re.fullmatch(r"CC0(?: 1\.0)?",license,re.I):return ("CC0 1.0","https://creativecommons.org/publicdomain/zero/1.0/")
    if re.fullmatch(r"Public [Dd]omain(?: \(U\.S\. federal work\))?",license,re.I):
        return ("Public Domain","https://creativecommons.org/publicdomain/mark/1.0/")
    m=re.fullmatch(r"CC BY(-SA)? (2\.0|2\.5|3\.0|4\.0)(?: US)?",license,re.I)
    if m:
        return (("CC BY-SA " if m.group(1) else "CC BY ")+m.group(2),
                "https://creativecommons.org/licenses/"+("by-sa" if m.group(1) else "by")+"/"+m.group(2)+"/")
    return None
for row in index["entries"]:
    sid=row["id"];fam=row["family"];genus=row["genus"]
    path=SRC/"content/taxa"/fam/genus/sid/"species.json"
    assert path.is_file(),sid
    source=json.loads(path.read_text())
    assert source["id"]==sid and source["family"]==fam
    publicpath=SITE/"data/species"/(sid+".json")
    public=json.loads(publicpath.read_text())
    photos=public.get("verified_photos",[])
    assert isinstance(photos,list)
    seen_hashes={p.get("source_blob_sha") for p in photos}
    seen_sources={p.get("source_page") for p in photos}
    species_holds=[]
    for i,photo in enumerate(source.get("images",[]) if isinstance(source.get("images",[]),list) else []):
        source_records+=1
        f=str(photo.get("file") or "")
        if not re.fullmatch(r"images/[A-Za-z0-9._-]+\.(jpg|jpeg|png|webp)",f,re.I):
            species_holds.append({"record":i,"reason":"remote_or_invalid_original_path"});continue
        lic=permission(photo)
        if not lic:
            species_holds.append({"record":i,"reason":"license_not_strict_cc_or_public_domain"});continue
        creator=str(photo.get("creator") or "").strip()
        page=str(photo.get("source_page") or "")
        reuse=str(photo.get("public_reuse") or "").lower()
        if not creator or re.search(r"unknown|unverified|resolve|source account",creator,re.I):
            species_holds.append({"record":i,"reason":"creator_unverified"});continue
        if reuse in ("no","false") or "review" in reuse or "private" in reuse or "noncommercial" in reuse:
            species_holds.append({"record":i,"reason":"public_permission_not_documented"});continue
        if not page.startswith("https://commons.wikimedia.org/wiki/File:"):
            if not (page.startswith("https://www.inaturalist.org/photos/") and creator=="Glass Root Garden"
                    and "Direct license from photographer" in str(photo.get("license_basis") or "")
                    and lic[0]=="CC BY 4.0" and reuse=="yes"):
                species_holds.append({"record":i,"reason":"image_specific_source_not_public_verified"});continue
        original=SRC/"content/taxa"/fam/genus/sid/f
        if not original.is_file():
            species_holds.append({"record":i,"reason":"source_bytes_not_in_staged_archive"});continue
        raw=original.read_bytes()
        ext=original.suffix.lower()
        valid=raw.startswith(b"\xff\xd8\xff") if ext in (".jpg",".jpeg") else raw.startswith(b"\x89PNG\r\n\x1a\n") if ext==".png" else raw[:4]==b"RIFF" and raw[8:12]==b"WEBP"
        if not valid or len(raw)<500 or len(raw)>25*1024*1024:
            species_holds.append({"record":i,"reason":"image_bytes_not_valid"});continue
        sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
        if sha in seen_hashes or page in seen_sources:
            already+=1;continue
        dest="media/"+sid+"/source-"+sha[:12]+ext
        output=SITE/dest
        output.parent.mkdir(parents=True,exist_ok=True)
        if output.exists():assert output.read_bytes()==raw
        else:shutil.copyfile(original,output)
        photos.append({"src":dest,"creator":creator,"license":lic[0],"license_url":lic[1],
                       "source_page":page,"role":str(photo.get("role") or "Original field photograph")[:480],
                       "source_page_is_exact":True,"noncommercial_only":False,
                       "private_rights_review_only":False,"source_blob_sha":sha,
                       "modified":"Original source photograph copied without alteration",
                       "rights_note":"Exact historical licensed source; anatomy arrows remain separately reviewed"})
        seen_hashes.add(sha);seen_sources.add(page)
        extra+=1;source_bytes+=len(raw)
    for v in species_holds:reason[v["reason"]]+=1
    if species_holds:held[sid]=species_holds
    public["verified_photos"]=photos
    public["media_status"]="VERIFIED_PUBLIC_STRICT_CC_ONLY" if photos else "SOURCE_PHOTO_RIGHTS_HELD"
    publicpath.write_text(json.dumps(public,ensure_ascii=False,indent=2)+"\n")
    row["photo_count"]=len(photos)
    row["photo_publication_status"]="RELEASED_CC_GALLERY" if photos else "NO_CC_PHOTOS_RELEASED"
index_path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+"\n")
allphotos=0;species_with=0;gallery={};actual=set()
for row in index["entries"]:
    sid=row["id"]
    card=json.loads((SITE/"data/species"/(sid+".json")).read_text())
    photos=card["verified_photos"];allphotos+=len(photos);species_with+=bool(photos)
    gallery[sid]={"count":len(photos),"first_src":photos[0]["src"] if photos else None}
    for photo in photos:
        assert photo["noncommercial_only"] is False and photo["private_rights_review_only"] is False
        assert photo["src"].startswith("media/"+sid+"/")
        path=SITE/photo["src"]
        assert path.is_file()
        actual.add(path.resolve())
source_files={p.resolve() for p in (SITE/"media").rglob("*") if p.is_file()}
assert actual==source_files,"Untracked photo file detected"
summary_path=SITE/"data/preview-summary.json"
summary=json.loads(summary_path.read_text())
assert summary["verified_photo_copies"]+extra==allphotos,(summary["verified_photo_copies"],extra,allphotos)
summary["previous_strict_release_photo_copies"]=summary.get("previous_strict_release_photo_copies",summary["verified_photo_copies"])
summary["existing_original_source_photo_copies_added"]=extra
summary["verified_photo_copies"]=allphotos
summary["species_with_cc_photos"]=species_with
summary["output_jpegs"]=len([x for x in source_files if x.suffix.lower() in (".jpg",".jpeg")])
summary["strict_public_cc"]=True
summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
(SITE/"data/gallery-index.json").write_text(json.dumps({
 "schema_version":1,"status":"ONLY_EXISTING_PUBLIC_RIGHTS_CLEARED_SITE_IMAGES",
 "species":180,"photo_species":species_with,"photo_count":allphotos,"entries":gallery
},ensure_ascii=False,indent=2)+"\n")
report={"status":"PASS_EXISTING_SOURCE_CC_PHOTO_BACKFILL","source_media_records":source_records,
 "newly_archived_original_cc_photo_copies":extra,"original_approved_photos_already_covered":already,
 "total_published_photo_copies":allphotos,"total_photographed_species":species_with,
 "remaining_held_source_records":sum(reason.values()),"hold_reason_counts":dict(reason),
 "held_by_species":held,"new_photos_collected":0,"staging_source_preserved":True,
 "original_legacy_learner_preserved":True,"additional_existing_source_bytes":source_bytes}
(SITE/"existing-photo-source-sweep-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
(SITE/"PHOTO_PUBLICATION_SCOPE.md").write_text(
 f"# Asteraceae existing-source public photo release\n\n{allphotos} individually source-credited "
 f"public-domain or strict CC photographs across {species_with} of 180 species. "
 f"An additional {extra} previously migrated source photos were published in this pass. "
 f"{sum(reason.values())} historical photo records remain held with their reasons recorded "
 "in existing-photo-source-sweep-report.json. No new images were downloaded or harvested; "
 "all existing source files and original hub records are preserved.\n")
print("ASTERACEAE_EXISTING_SOURCE_CC_SWEEP_PASS",json.dumps({k:v for k,v in report.items() if k not in ("held_by_species","hold_reason_counts")},sort_keys=True),flush=True)
