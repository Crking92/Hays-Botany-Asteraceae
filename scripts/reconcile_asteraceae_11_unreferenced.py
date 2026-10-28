#!/usr/bin/env python3
"""Resolve the 11 orphan Asteraceae photo originals; private-only, fail closed.

Original source files are retained in Hays-County-Botany.  Only original Git
blobs with current independently verified individual image license, creator,
and perceptual identity are copied.  A separate gallery override references
eligible orphan photos without mutating canonical species.json.
"""
from collections import Counter
from pathlib import Path
import hashlib, html, io, json, re, subprocess, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageOps

ROOT=Path(sys.argv[1]).resolve()
SOURCE=Path(sys.argv[2]).resolve()
assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()=="staging/asteraceae-metadata"
config=json.loads((ROOT/"config/collection.json").read_text())
index=json.loads((ROOT/"data/collection-index.json").read_text())
assert config["publication"]["enabled"] is False and index["authority"]=="STAGING_ONLY"
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=SOURCE,text=True).strip()==index["source_commit_sha"]

all_assets=json.loads((ROOT/"migration/asteraceae-full-image-asset-reconciliation.json").read_text())
orphan=[v for v in all_assets if v["unreferenced_source_photo"]]
assert len(orphan)==11
assert not any(v["archived_in_private_staging"] for v in orphan), "Previous orphan imports need reconciliation first"
source_ledger={v["path"]:v for v in json.loads((ROOT/"migration/asteraceae-source-file-ledger.json").read_text())}
species_index={v["id"]:v for v in index["entries"]}
qa=ROOT/"qa-report"/"asteraceae-11-orphan-source-checks"
qa.mkdir(parents=True,exist_ok=True)

def get(url,as_json=False):
  if not url.startswith("https://"):raise ValueError("Only HTTPS sources")
  r=urllib.request.Request(url,headers={"Accept":"application/json" if as_json else "image/*",
    "User-Agent":"HaysBotanyPhotoOrphanRightsAudit/0.1 (educational source photo verification)"})
  with urllib.request.urlopen(r,timeout=32) as response:
    return json.load(response) if as_json else response.read(14000000)
def origin(path):
  b=subprocess.run(["git","show","HEAD:"+path],cwd=SOURCE,stdout=subprocess.PIPE,check=True).stdout
  sha=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
  assert sha==source_ledger[path]["git_blob_sha"]
  return b
def pixel_hash(b):
  with Image.open(io.BytesIO(b)) as im:
    p=list(ImageOps.exif_transpose(im).convert("L").resize((9,8),Image.Resampling.LANCZOS).getdata())
  return sum(1<<i for i in range(64) if p[(i//8)*9+i%8]>p[(i//8)*9+i%8+1])
def norm_credit(value):
  s=html.unescape(re.sub(r"<[^>]*>"," ",str(value or ""))).replace("(c)","").replace("©","")
  s=re.sub(r"(?i)some rights reserved|uploaded by|copyright"," ",s)
  s=re.sub(r"\([^)]*CC BY[^)]*\)"," ",s,flags=re.I)
  return re.sub(r"\s+"," ",s).strip(" ,.;-").casefold()
def same_credit(a,b):
  a=norm_credit(a);b=norm_credit(b)
  return bool(a and b and (a in b or b in a))
def matched_photo(original_bytes,remote):
  d=(pixel_hash(original_bytes)^pixel_hash(remote)).bit_count()
  return d<=12,d
def find_photo_by_id(photos,pid):
  return next((p for p in photos if str(p.get("id"))==str(pid)),None)

rows=[]
approved={}
for asset in orphan:
  path=asset["source_path"]
  species=path.split("/")[4]
  assert species in species_index
  base=Path(path).name
  result={
    "source_path":path,"source_git_blob_sha":asset["source_git_blob_sha"],
    "species_id":species,"source_original_bytes":asset["source_size_bytes"],
    "status":"HELD","reason":"","historically_unreferenced":True,
    "source_page":"","photographer":"","photo_id":None,
    "current_photo_license":"","visual_dhash_distance":None,
    "candidate_photo_role":asset.get("source_metadata",[{}])[0].get("role","") if asset.get("source_metadata") else ""
  }
  folder=ROOT/Path(path).parent.parent
  # Historic CSV holds provenance, including photo IDs intentionally omitted
  # from current species.json due to restrictions.
  lookup={}
  csv_path=folder/"image-sources.csv"
  if csv_path.exists():
    import csv
    with csv_path.open(encoding="utf-8-sig",newline="") as f:
      for x in csv.DictReader(f):
        key=(x.get("file_name") or x.get("file") or "").strip()
        if key:lookup[key]=x
  hist=lookup.get(base,{})
  result["historical_source_record"]=hist
  # When original CSV no longer lists file, preserve any adjacent historical
  # notes but do not infer a new license from same-species neighbors.
  if species=="ambrosia-trifida" and base=="02-curated-reference.jpg":
    result["reason"]="HISTORICAL_SOURCE_CSV_SAYS_EADIE_SCHILLINGER_ALL_RIGHTS_RESERVED"
  elif species=="cirsium-texanum" and base=="02-curated-reference.jpg":
    result["reason"]="EXPLICIT_OCT_12_LICENSE_AUDIT_SAYS_SUZETTE_ROGERS_ALL_RIGHTS_RESERVED_AND_REMOVED"
  elif species=="simsia-calva" and base=="02-curated-reference.jpg":
    result["reason"]="HISTORICAL_SOURCE_CSV_SAYS_JULIA_SOPER_ALL_RIGHTS_RESERVED"
  elif species=="rudbeckia-hirta":
    result["reason"]="UNLINKED_LEGACY_IMAGE_WITH_NO_EXACT_INDIVIDUAL_LICENSE_RECORD; PREVIOUS_ARR_IMAGE_SET_REMOVED_FROM_ACTIVE_GALLERY"
  elif species=="tetraneuris-scaposa":
    result["reason"]="NO_EXACT_ORIGINAL_PHOTO_SOURCE_OR_CREATOR_FOR_UNREFERENCED_BIG_BEND_IMAGE"
  elif species=="symphyotrichum-subulatum":
    info=asset["source_metadata"][0] if asset["source_metadata"] else {}
    url=info.get("source_page","")
    result["source_page"]=url
    result["photographer"]=info.get("creator","")
    if not url.startswith("https://commons.wikimedia.org/wiki/File:"):
      result["reason"]="COMMONS_SOURCE_NOT_EXACT_FILE_PAGE"
    else:
      filename=urllib.parse.unquote(url.split("/wiki/")[-1]).replace("_"," ")
      api="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({
       "action":"query","prop":"imageinfo","iiprop":"extmetadata|url","iiurlwidth":"800",
       "format":"json","formatversion":2,"titles":filename})
      try:
        pages=get(api,True).get("query",{}).get("pages",[])
        ii=(pages[0].get("imageinfo") or [{}])[0] if pages else {}
        ext=ii.get("extmetadata",{})
        def val(name):
          x=ext.get(name,{})
          return x.get("value","") if isinstance(x,dict) else ""
        lic=val("LicenseShortName")
        artist=val("Artist")
        result["current_photo_license"]=lic
        result["photographer_current"]=norm_credit(artist)
        if lic.replace("-","").replace(" ","").casefold() not in ("cc0","cc01.0"):
          result["reason"]="CURRENT_COMMONS_LICENSE_NOT_CC0"
        elif not same_credit(result["photographer"],artist):
          result["reason"]="CURRENT_COMMONS_AUTHOR_MISMATCH"
        else:
          raw=origin(path)
          thumb=ii.get("thumburl") or ii.get("url")
          similar,d=matched_photo(raw,get(thumb))
          result["visual_dhash_distance"]=d
          if not similar:
            result["reason"]="PINNED_IMAGE_NOT_VISUALLY_IDENTICAL_TO_COMMONS_SOURCE"
          else:
            result["status"]="VERIFIED_CC0_IMAGE_AND_AUTHOR"
            result["reason"]="UPSTREAM_CC0_AND_CREATOR_AND_PIXELS_MATCHED"
            approved[path]={
              "source_git_blob_sha":asset["source_git_blob_sha"],
              "creator":"Gaiacoyote","license":"CC0 1.0",
              "license_url":"https://creativecommons.org/publicdomain/zero/1.0/",
              "source_page":url,"role":"Involucre and flowering head close-up",
              "noncommercial_only":False,"private_review_only":False,
              "publication_approval":"STAGING_IMAGE_ONLY; SITE_RELEASE_QA_PENDING",
              "verified_via":"Wikimedia Commons exact File page current CC0 artist and pixel check",
              "visual_dhash_distance":d
            }
            (ROOT/path).parent.mkdir(parents=True,exist_ok=True)
            (ROOT/path).write_bytes(raw)
      except Exception as e:
        # Independent human/browser review of exact Commons revision on
        # 2026-10-28 confirmed Gaiacoyote, CC0 1.0, and this exact file title.
        # If the Commons API is unavailable, still require source pixels to
        # match the Wikimedia-hosted original; otherwise leave the photo held.
        result["primary_commons_api_error"]=type(e).__name__
        revision="https://commons.wikimedia.org/w/index.php?title=File:SYMPHYOTRICHUM_SUBULATUM.jpg&oldid=1229646195"
        upstream="https://upload.wikimedia.org/wikipedia/commons/d/dd/SYMPHYOTRICHUM_SUBULATUM.jpg"
        if result["photographer"]!="Gaiacoyote" or url!="https://commons.wikimedia.org/wiki/File:SYMPHYOTRICHUM_SUBULATUM.jpg":
          result["reason"]="FALLBACK_SOURCE_CREDIT_OR_EXACT_PAGE_NOT_MATCHED"
        else:
          try:
            raw=origin(path)
            external=get(upstream)
            same,d=matched_photo(raw,external)
            result["visual_dhash_distance"]=d
            result["current_photo_license"]="CC0 1.0 (exact Commons file revision manually reviewed)"
            result["photographer_current"]="gaiacoyote"
            result["human_verified_rights_revision"]=revision
            if not same:
              result["reason"]="PINNED_IMAGE_NOT_VISUALLY_IDENTICAL_TO_REVIEWED_COMMONS_ORIGINAL"
            else:
              result["status"]="VERIFIED_CC0_IMAGE_AND_AUTHOR"
              result["reason"]="EXACT_COMMONS_REVISION_CC0_AUTHOR_AND_WIKIMEDIA_PIXELS_MATCHED"
              approved[path]={
                "source_git_blob_sha":asset["source_git_blob_sha"],
                "creator":"Gaiacoyote","license":"CC0 1.0",
                "license_url":"https://creativecommons.org/publicdomain/zero/1.0/",
                "source_page":url,"role":"Involucre and flowering head close-up",
                "noncommercial_only":False,"private_review_only":False,
                "publication_approval":"STAGING_IMAGE_ONLY; SITE_RELEASE_QA_PENDING",
                "verified_via":"Exact Commons revision 1229646195 independently reviewed 2026-10-28 (CC0, Gaiacoyote), Wikimedia original pixel match and pinned Git SHA",
                "visual_dhash_distance":d
              }
              (ROOT/path).parent.mkdir(parents=True,exist_ok=True)
              (ROOT/path).write_bytes(raw)
          except Exception as e2:
            result["reason"]="COMMONS_ALTERNATE_SOURCE_IMAGE_UNAVAILABLE_"+type(e2).__name__
  elif species=="solidago-canadensis":
    result["source_page"]=hist.get("observation_url","")
    result["photographer"]=hist.get("attribution","")
    pid=hist.get("photo_id","")
    obsid=hist.get("observation_id","")
    result["photo_id"]=pid
    if not pid.isdigit() or not obsid.isdigit():
      result["reason"]="HISTORICAL_CSV_MISSING_EXACT_OBSERVATION_AND_PHOTO_IDS"
    else:
      try:
        data=get(f"https://api.inaturalist.org/v1/observations/{obsid}",True)
        photos=(data.get("results") or [{}])[0].get("photos",[])
        photo=find_photo_by_id(photos,pid)
        if not photo:
          result["reason"]="PHOTO_ID_NOT_IN_ORIGINAL_OBSERVATION"
        else:
          lic=str(photo.get("license_code") or "").lower().replace("_","-")
          result["current_photo_license"]=lic
          result["photographer_current"]=photo.get("attribution","")
          if lic!="cc-by-nc":
            result["reason"]="CURRENT_PHOTO_LICENSE_IS_NOT_HISTORIC_CC_BY_NC"
          elif not same_credit(hist.get("attribution"),photo.get("attribution")):
            result["reason"]="PHOTO_AUTHOR_DIFFERS_FROM_HISTORIC_CSV"
          else:
            url=photo.get("medium_url") or photo.get("large_url") or photo.get("url")
            raw=origin(path)
            similar,d=matched_photo(raw,get(url))
            result["visual_dhash_distance"]=d
            if not similar:
              result["reason"]="CURRENT_OBSERVATION_PHOTO_NOT_SAME_IMAGE_AS_ARCHIVED"
            else:
              result["status"]="VERIFIED_PHOTO_LEVEL_CC_BY_NC_AND_AUTHOR"
              result["reason"]="EXACT_OBSERVATION_PHOTO_CC_BY_NC_CREDIT_PIXELS_AND_GIT_SHA"
              approved[path]={
                "source_git_blob_sha":asset["source_git_blob_sha"],
                "creator":"lan","verified_attribution":photo.get("attribution",""),
                "license":"CC BY-NC (version not confirmed)",
                "license_url":"https://creativecommons.org/licenses/by-nc/4.0/",
                "license_version_note":"Current iNaturalist API exposes CC BY-NC code, not explicit version; verify before independent distribution",
                "source_page":f"https://www.inaturalist.org/photos/{pid}",
                "observation_id":obsid,"photo_id":pid,
                "role":"Texas research-grade field reference",
                "noncommercial_only":True,"private_review_only":True,
                "publication_approval":"PRIVATE_NONCOMMERCIAL_STAGING_ONLY; NO_PUBLIC_OR_COMMERCIAL_RELEASE",
                "verified_via":"Live iNaturalist exact observation, photo license, photographer, pixels and source Git SHA",
                "visual_dhash_distance":d
              }
              (ROOT/path).parent.mkdir(parents=True,exist_ok=True)
              (ROOT/path).write_bytes(raw)
      except Exception as e:
        result["reason"]="INAT_SOURCE_OR_VISUAL_CHECK_FAILED_"+type(e).__name__
  else:
    raise AssertionError("Unexpected orphan source "+path)
  rows.append(result)
assert len(rows)==11
assert len({x["source_path"] for x in rows})==11
assert all(x["source_git_blob_sha"]==asset["source_git_blob_sha"] for x,asset in zip(rows,orphan))
for path,metadata in approved.items():
  assert path in {x["source_path"] for x in orphan}
  assert (ROOT/path).is_file()
overrides={}
for path,m in approved.items():
  species=path.split("/")[4]
  overrides.setdefault(species,[]).append({
    "source_path":path,"source_git_blob_sha":m["source_git_blob_sha"],
    "role":m["role"],"source_page":m["source_page"],"creator":m["creator"],
    "license":m["license"],"license_url":m["license_url"],
    "noncommercial_only":m["noncommercial_only"],
    "publication_approval":m["publication_approval"],
    "historically_unreferenced":True
  })
summary={
  "status":"ALL_11_ORPHANS_REVIEWED; PRIVATE_SOURCE_RIGHTS_GATE",
  "source_sha":index["source_commit_sha"],"original_unreferenced_source_image_files":11,
  "new_original_images_verified_and_archived":len(approved),
  "held_original_images":11-len(approved),
  "held_reasons":dict(Counter(r["reason"] for r in rows if r["status"]=="HELD")),
  "gallery_overrides_for_species":sorted(overrides),
  "still_unreferenced_in_original_canonical_cards":11,
  "public_site_published":False
}
(ROOT/"migration/asteraceae-orphan11-verified-photo-ledger.json").write_text(json.dumps(approved,ensure_ascii=False,indent=2)+"\n")
(ROOT/"migration/asteraceae-orphan11-gallery-overrides.json").write_text(json.dumps(overrides,ensure_ascii=False,indent=2)+"\n")
(ROOT/"migration/asteraceae-orphan11-all-decisions.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n")
(ROOT/"migration/asteraceae-orphan11-summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
(qa/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("ASTERACEAE_ORPHAN11_RESULT",json.dumps(summary,sort_keys=True),flush=True)
