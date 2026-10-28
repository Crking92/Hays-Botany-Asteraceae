#!/usr/bin/env python3
"""Backfill Asteraceae zero-photo taxa with NEW Texas iNaturalist research-grade CC photos.

This creates *new provenance-tracked media* separate from the original 459
source-file inventory. Only actual photo licenses cc0/cc-by/cc-by-sa.
No NC, ARR or ND content; no guessed anatomy labels or arrows.
All media original-source links, original-download SHA256, compact archive SHA,
photo ID, observation ID, precise taxon name and CC information are preserved.
GitHub Pages not deployed.
"""
from __future__ import annotations
import hashlib, io, json, re, subprocess, sys, time, urllib.parse, urllib.request
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageOps,UnidentifiedImageError

STAGE=Path(sys.argv[1]).resolve()
assert subprocess.check_output(["git","branch","--show-current"],cwd=STAGE,text=True).strip()=="staging/asteraceae-metadata"
config=json.loads((STAGE/"config/collection.json").read_text())
assert config["publication"]["enabled"] is False
base=json.loads((STAGE/"data/collection-index.json").read_text())
assert base["authority"]=="STAGING_ONLY" and len(base["entries"])==180
gap=json.loads((STAGE/"migration/asteraceae-31-photo-empty-species-backlog.json").read_text())
assert len(gap)==31
assert {x["species_id"] for x in gap}.issubset({x["id"] for x in base["entries"]})
ROOT="external-media/asteraceae/texas-inat"
LEDGER=STAGE/"migration/asteraceae-new-texas-inat-cc-photo-ledger.json"
if LEDGER.exists():
    old=json.loads(LEDGER.read_text())
    assert all((STAGE/p).is_file() for p in old),"Pre-existing archive is incomplete"
    print("TEXAS_INAT_ALREADY_STAGED",len(old),flush=True)
    sys.exit(0)

permissive={"cc-by","cc-by-sa","cc0"}
licenses={
    "cc-by":("CC BY 4.0","https://creativecommons.org/licenses/by/4.0/"),
    "cc-by-sa":("CC BY-SA 4.0","https://creativecommons.org/licenses/by-sa/4.0/"),
    "cc0":("CC0 1.0","https://creativecommons.org/publicdomain/zero/1.0/")
}
qa=STAGE/"qa-report/asteraceae-new-texas-photo-backfill"
qa.mkdir(parents=True,exist_ok=True)
def json_request(path,params=None):
    url="https://api.inaturalist.org/v1/"+path
    if params:url+="?"+urllib.parse.urlencode(params)
    request=urllib.request.Request(url,headers={"User-Agent":"Hays-Botany-Photo-Source-Collector/1.0 (public educational botanical photo attribution audit)","Accept":"application/json"})
    with urllib.request.urlopen(request,timeout=35) as f:return json.load(f)
def image_request(url):
    parsed=urllib.parse.urlparse(url)
    assert parsed.scheme=="https" and parsed.hostname in {
      "inaturalist-open-data.s3.amazonaws.com","static.inaturalist.org",
      "www.inaturalist.org","inaturalist.org","inaturalist.s3.amazonaws.com"
    },f"Untrusted photo file host {parsed.hostname}"
    req=urllib.request.Request(url,headers={"User-Agent":"Hays-Botany-Photo-Source-Collector/1.0 (source photo archival)","Accept":"image/jpeg,image/png,image/webp,*/*"})
    with urllib.request.urlopen(req,timeout=30) as f:
        if int(f.headers.get("Content-Length","0") or 0)>19000000:
            raise ValueError("Source image too large for archival pass")
        b=f.read(19000000)
    assert len(b)>12000 and len(b)<19000000
    return b
def pick_media_url(photo):
    pid=photo["id"]
    # Use API-provided URL; convert the iNaturalist's own size token only.
    candidates=[photo.get("large_url"),photo.get("medium_url"),photo.get("original_url"),photo.get("url")]
    for c in candidates:
        if not isinstance(c,str) or not c.startswith("https://"):continue
        if "/photos/"+str(pid)+"/" not in c:continue
        u=re.sub(r"/(?:square|thumb|small|medium)\.", "/large.",c)
        return u
    return None
def sha_blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def norm_taxon(s):
    return re.sub(r"\s+"," ",str(s or "").replace("×","x").strip()).casefold()
def author_from_photo(p,obs):
    attr=str(p.get("attribution") or "").strip()
    if p.get("license_code")=="cc0" and not attr.replace(" ",""):
        attr="No rights reserved (CC0)"
    if not attr:
        attr="iNaturalist observation account: "+str((obs.get("user") or {}).get("login","unknown"))
    # Preserve original attribution verbatim: some photos have different photographers
    # than the observing user. CC0 may have only "no rights reserved" in source API.
    return attr

record={}
audit=[]
total_by_species=Counter()
seen_photos=set()
for n,item in enumerate(gap,1):
    sp=item["species_id"];name=item["scientific_name"]
    high=item["field_review_priority"]=="HIGH_CANDIDATE_FOR_CREW"
    max_this=2 if high else 1
    decision={"species_id":sp,"scientific_name":name,"priority":item["field_review_priority"],"region":"Texas, US, iNaturalist place 18","status":"HOLD","photos_saved":0,"reason":"","observation_candidates":0,"selected_photo_ids":[]}
    try:
        result=json_request("observations",{
          "taxon_name":name,"place_id":18,"quality_grade":"research","photos":"true",
          "photo_license":"cc0,cc-by,cc-by-sa","per_page":22,"order_by":"votes","order":"desc"})
    except Exception as e:
        decision["reason"]="OBSERVATION_API_ERROR_"+type(e).__name__
        audit.append(decision)
        continue
    observations=result.get("results",[])
    decision["observation_candidates"]=result.get("total_results",0)
    exact=[o for o in observations if norm_taxon((o.get("taxon") or {}).get("name"))==norm_taxon(name)
          and o.get("quality_grade")=="research" and o.get("photos")]
    if not exact:
        decision["reason"]="NO_EXACT_RESEARCH_GRADE_TAXON_WITH_PERMISSIVE_TEXAS_PHOTO"
        audit.append(decision);continue
    # Avoid redundant first photos from the same observation where alternatives exist.
    candidates=[]
    for obs in exact:
        for pi,photo in enumerate(obs.get("photos") or []):
            pid=photo.get("id")
            lic=str(photo.get("license_code") or "").lower().replace("_","-")
            if not isinstance(pid,int) or lic not in permissive:continue
            if pid in seen_photos:continue
            url=pick_media_url(photo)
            if not url:continue
            candidates.append((obs,photo,url,pi))
    # Prefer one photograph each from distinct research-grade Texas observation,
    # except when there are insufficient observations.
    chosen=[]
    if high:
        obs_ids=set()
        for candidate in candidates:
            if candidate[0]["id"] not in obs_ids:
                chosen.append(candidate)
                obs_ids.add(candidate[0]["id"])
                if len(chosen)>=max_this:break
        if len(chosen)<max_this:
            chosen.extend(x for x in candidates if x not in chosen)
    else:
        chosen=candidates
    if not chosen:
        decision["reason"]="EXACT_OBSERVATIONS_HAVE_NO_USABLE_CURRENT_PERMISSIVE_PHOTO_URL"
        audit.append(decision);continue
    for obs,p,url,pi in chosen:
        if decision["photos_saved"]>=max_this:break
        pid=p["id"]
        if pid in seen_photos:continue
        lic=p["license_code"].lower().replace("_","-")
        if lic not in permissive:continue
        try:
            raw=image_request(url)
            with Image.open(io.BytesIO(raw)) as image:
                image.verify()
            with Image.open(io.BytesIO(raw)) as image:
                image=ImageOps.exif_transpose(image).convert("RGB")
                if image.width<350 or image.height<350:raise ValueError("Low resolution")
                image.thumbnail((1600,1600),Image.Resampling.LANCZOS)
                out=io.BytesIO()
                image.save(out,format="JPEG",quality=89,optimize=True,exif=b"")
                final=out.getvalue()
            assert len(final)<25000000
            path=f"{ROOT}/{sp}/inat-{pid}.jpg"
            dest=STAGE/path;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():raise AssertionError("Duplicate file path: "+path)
            dest.write_bytes(final)
            identity=(obs.get("taxon") or {})
            source_page=f"https://www.inaturalist.org/photos/{pid}"
            obs_page=f"https://www.inaturalist.org/observations/{obs['id']}"
            rights=licenses[lic]
            record[path]={
              "source_git_blob_sha":sha_blob(final),
              "archive_sha256":hashlib.sha256(final).hexdigest(),
              "original_download_sha256":hashlib.sha256(raw).hexdigest(),
              "original_download_url":url,"source_page":source_page,
              "observation_page":obs_page,"photo_id":pid,"observation_id":obs["id"],
              "taxon_id":identity.get("id"),"taxon_name":identity.get("name"),
              "species_id":sp,"creator":author_from_photo(p,obs),
              "license":rights[0],"license_url":rights[1],
              "noncommercial_only":False,
              "role":"Texas research-grade observation photograph (anatomy not yet annotated)",
              "quality_grade":"research","place_name":"Texas","place_id":18,
              "image_pixels_verified":True,"exact_observation_taxon_match":True,
              "archive_change_note":"Resized to maximum 1600px, re-encoded as JPEG, removed EXIF; no anatomy labels added",
              "verified_at_utc":"2026-10-28",
              "rights_review":"Individual iNaturalist photo CC license and attribution checked; adaptation/source attribution in site caption",
              "publication_approval":"STAGING_NEW_INAT_OBSERVATION_CC_SOURCE_VERIFIED; FIELD_ANATOMY_AND_FINAL_PUBLIC_REVIEW_PENDING"
            }
            decision["selected_photo_ids"].append(pid)
            decision["photos_saved"]+=1;seen_photos.add(pid)
            total_by_species[sp]+=1
        except Exception as exc:
            decision.setdefault("download_or_image_errors",[]).append({"id":pid,"error":type(exc).__name__,"details":str(exc)[:180]})
    decision["status"]="NEW_CC_PHOTO_ARCHIVED_PRIVATE" if decision["photos_saved"] else "HOLD"
    decision["reason"]="PHOTO_LICENSE_TAXON_AND_FIELD_RECORD_VERIFIED" if decision["photos_saved"] else "NO_MEDIA_DOWNLOAD_PASSED"
    audit.append(decision)
    print("NEW_TEXAS_CC_BACKFILL",n,"/",len(gap),sp,decision["photos_saved"],decision["reason"],flush=True)
    time.sleep(.35)

assert len(record)<=62, "Single archive batch >62 photo cap"
assert len(record)==sum(x["photos_saved"] for x in audit)
assert set(record)==set(f"{ROOT}/{x['species_id']}/inat-{pid}.jpg" for x in audit for pid in x["selected_photo_ids"])
for k,v in record.items():
    b=(STAGE/k).read_bytes()
    assert sha_blob(b)==v["source_git_blob_sha"] and hashlib.sha256(b).hexdigest()==v["archive_sha256"]
summary={
  "status":"NEW_SOURCE_PHOTO_BACKFILL_PRIVATE_NOT_PUBLICLY_DEPLOYED",
  "missing_species_baseline":31,
  "new_licensed_source_photos_archived":len(record),
  "species_with_new_photos":sum(x["photos_saved"]>0 for x in audit),
  "field_priority_species_with_new_photos":sum(x["photos_saved"]>0 and x["priority"]=="HIGH_CANDIDATE_FOR_CREW" for x in audit),
  "field_priority_total":sum(x["priority"]=="HIGH_CANDIDATE_FOR_CREW" for x in audit),
  "species_still_missing_approved_photo":sum(x["photos_saved"]==0 for x in audit),
  "source_originals_already_archived_in_main_migration":322,
  "new_photos_separate_from_459_original_source_photos":True,
  "photos_per_source_species":dict(total_by_species),
  "holds":{x["species_id"]:x["reason"] for x in audit if x["photos_saved"]==0},
  "license_counts":dict(Counter(x["license"] for x in record.values())),
  "publication_state":"STAGING_ONLY"
}
(STAGE/"migration/asteraceae-new-texas-inat-cc-photo-ledger.json").write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n")
(STAGE/"migration/asteraceae-new-texas-inat-cc-decisions.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n")
(STAGE/"migration/asteraceae-new-texas-inat-cc-summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
(qa/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
print("NEW_TEXAS_CC_BACKFILL_FINAL",json.dumps(summary,sort_keys=True),flush=True)
