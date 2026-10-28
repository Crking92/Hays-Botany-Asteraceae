#!/usr/bin/env python3
"""Check iNaturalist *current taxon default image* against pinned source photo.

A taxon page alone is not photo identification. Requires photo-level current
license, creator and visual image match; private staging only, no public deploy.
"""
import hashlib, html, io, json, re, subprocess, sys, time, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(sys.argv[1]).resolve();SOURCE=Path(sys.argv[2]).resolve()
assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()=="staging/asteraceae-metadata"
cfg=json.loads((ROOT/"config/collection.json").read_text());assert cfg["publication"]["enabled"] is False
idx=json.loads((ROOT/"data/collection-index.json").read_text())
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=SOURCE,text=True).strip()==idx["source_commit_sha"]
ledger={x["path"]:x for x in json.loads((ROOT/"migration/asteraceae-source-file-ledger.json").read_text())}
assets=json.loads((ROOT/"migration/asteraceae-full-image-asset-reconciliation.json").read_text())
candidates=[]
for x in assets:
 if x["followup_priority"]!="FIRST_RECHECK_UPSTREAM_PERMISSION_AND_CREATOR" or x["archived_in_private_staging"]:continue
 meta=next((m for m in x["source_metadata"] if re.match(r"^https://www\.inaturalist\.org/taxa/\d+",m.get("source_page",""))),None)
 if meta is None:continue
 candidates.append({"path":x["source_path"],"sha":x["source_git_blob_sha"],"source_page":meta["source_page"],"creator_claim":meta["creator"],"license_claim":meta["license_claim"],"state":"HOLD","reason":""})
assert len(candidates)==19,f"Expected 19 iNaturalist taxon-source priority files, got {len(candidates)}"
qa=ROOT/"qa-report/asteraceae-inat-taxon-rights"
qa.mkdir(parents=True,exist_ok=True)
def clean(s):
 v=re.sub(r"<[^>]*>"," ",str(s or ""));v=html.unescape(v)
 v=v.replace("©","").replace("(c)","").replace("some rights reserved","").replace("no rights reserved","")
 return re.sub(r"\s+"," ",v).strip(" ,.-").casefold()
def want_license(s):
 v=str(s or "").lower().replace("_","-").replace(" ","-").strip()
 if v in ("cc0","pd","public-domain"):return "cc0" if v=="cc0" else "public_domain"
 for t in ("cc-by-nc-sa","cc-by-nc","cc-by-sa","cc-by"):
  if v==t or v.startswith(t+"-"):return t
 return v
def get(url,media=False):
 request=urllib.request.Request(url,headers={"User-Agent":"HaysBotanyPhotoRightsChecker/0.3","Accept":"image/*" if media else "application/json"})
 with urllib.request.urlopen(request,timeout=25) as f:
  if media:return f.read(18000000)
  return json.load(f)
def hash_pic(raw):
 with Image.open(io.BytesIO(raw)) as img:
  p=list(ImageOps.exif_transpose(img).convert("L").resize((9,8),Image.Resampling.LANCZOS).getdata())
 return sum((1<<i) for i in range(64) if p[(i//8)*9+i%8]>p[(i//8)*9+i%8+1])
verified={}
for i,r in enumerate(candidates):
 match=re.search(r"/taxa/(\d+)",r["source_page"])
 if not match:r["reason"]="UNRECOGNIZED_TAXON_PAGE";continue
 taxon=match.group(1)
 data=None
 for attempt in range(2):
  try:data=get(f"https://api.inaturalist.org/v1/taxa/{taxon}");break
  except Exception as ex:
   r["last_api_error"]=str(ex)[:160];time.sleep(1+attempt)
 if not data or not data.get("results"):
  r["reason"]="INAT_TAXON_CURRENT_METADATA_UNAVAILABLE";continue
 photo=(data["results"][0].get("default_photo") or {})
 r["current_photo_id"]=photo.get("id")
 current=want_license(photo.get("license_code"))
 claimed=want_license(r["license_claim"])
 r["current_license"]=current
 r["current_credit"]=photo.get("attribution","")
 if current!=claimed or current not in ("cc-by","cc-by-sa","cc0","public_domain"):
  r["reason"]="CURRENT_DEFAULT_PHOTO_LICENSE_DIFFERS_OR_RESTRICTED";continue
 old=clean(r["creator_claim"]);now=clean(photo.get("attribution",""))
 if not old or not now or (old not in now and now not in old):
  r["reason"]="CURRENT_DEFAULT_PHOTO_CREATOR_DIFFERS";continue
 u=photo.get("medium_url") or photo.get("large_url") or photo.get("url")
 if not u:r["reason"]="NO_CURRENT_DEFAULT_IMAGE_URL";continue
 try:
  blob=subprocess.run(["git","show","HEAD:"+r["path"]],cwd=SOURCE,check=True,stdout=subprocess.PIPE).stdout
  sha=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
  assert sha==r["sha"],"Source file changed"
  comp=get(u,media=True)
  distance=(hash_pic(comp)^hash_pic(blob)).bit_count()
  r["visual_dhash_distance"]=distance
  if distance>12:r["reason"]="SOURCE_IMAGE_NOT_CURRENT_TAXON_DEFAULT";continue
 except Exception as ex:r["reason"]="ORIGINAL_IMAGE_OR_MEDIA_CHECK_FAILED_"+type(ex).__name__;continue
 r["state"]="VERIFIED_DEFAULT_IMAGE_LICENSE_CREATOR_VISUAL_MATCH"
 r["reason"]="EXACT_CURRENT_INAT_DEFAULT_PHOTO_AND_ORIGINAL_BYTES"
 dest=ROOT/r["path"];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob)
 licenses={"cc-by":"https://creativecommons.org/licenses/by/4.0/","cc-by-sa":"https://creativecommons.org/licenses/by-sa/4.0/","cc0":"https://creativecommons.org/publicdomain/zero/1.0/","public_domain":"https://www.inaturalist.org/pages/help#photo-licenses"}
 verified[r["path"]]={"source_git_blob_sha":sha,"source_page":r["source_page"],"photo_id":photo.get("id"),
  "creator":r["creator_claim"],"upstream_attribution":photo.get("attribution",""),
  "license":current.upper().replace("-"," "),"license_url":licenses[current],"noncommercial_only":False,
  "verified_via":"iNaturalist current taxon default_photo ID, license, creator and exact pixel-thumbnail comparison",
  "visual_dhash_distance":distance,"publication_approval":"PRIVATE_STAGING_SOURCE_VERIFIED; PUBLIC_RELEASE_AND_DERIVATIVE_QA_PENDING"}
 print("INAT_TAXON_PROGRESS",i+1,"/",len(candidates),r["state"],r.get("reason",""),flush=True)
state={"status":"INAT_TAXON_EXACT_VISUAL_CHECK_PRIVATE_STAGING_ONLY","candidates":len(candidates),"verified":len(verified),
 "held":len(candidates)-len(verified),"held_reasons":dict(Counter(r["reason"] for r in candidates if r["state"]!="VERIFIED_DEFAULT_IMAGE_LICENSE_CREATOR_VISUAL_MATCH")),
 "public_release":False}
(ROOT/"migration/asteraceae-upstream-inat-taxon-120-ledger.json").write_text(json.dumps(verified,indent=2,ensure_ascii=False)+"\n")
(ROOT/"migration/asteraceae-upstream-inat-taxon-120-summary.json").write_text(json.dumps(state,indent=2)+"\n")
(qa/"all-19-inat-taxon-image-rights.json").write_text(json.dumps(candidates,indent=2,ensure_ascii=False)+"\n")
(qa/"summary.json").write_text(json.dumps(state,indent=2)+"\n")
print("INAT_TAXON_120_ARCHIVE",json.dumps(state,sort_keys=True),flush=True)
