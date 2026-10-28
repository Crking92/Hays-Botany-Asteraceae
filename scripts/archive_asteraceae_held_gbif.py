#!/usr/bin/env python3
"""Verify GBIF occurrence *individual multimedia records* and original image pixels.

Source license on the occurrence may differ from multimedia.photo license; use
exact media element and photographer. Private staging only, not public approval.
"""
import hashlib, html, io, json, re, subprocess, sys, time, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(sys.argv[1]).resolve();SOURCE=Path(sys.argv[2]).resolve()
assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()=="staging/asteraceae-metadata"
cfg=json.loads((ROOT/"config/collection.json").read_text());assert cfg["publication"]["enabled"] is False
index=json.loads((ROOT/"data/collection-index.json").read_text());assert index["authority"]=="STAGING_ONLY"
sha=index["source_commit_sha"]
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=SOURCE,text=True).strip()==sha
gitfile={x["path"]:x for x in json.loads((ROOT/"migration/asteraceae-source-file-ledger.json").read_text())}
assets=json.loads((ROOT/"migration/asteraceae-full-image-asset-reconciliation.json").read_text())
cases=[]
for x in assets:
 if x["followup_priority"]!="FIRST_RECHECK_UPSTREAM_PERMISSION_AND_CREATOR" or x["archived_in_private_staging"]:continue
 m=next((z for z in x["source_metadata"] if re.match(r"^https://www\.gbif\.org/occurrence/\d+",str(z.get("source_page","")))),None)
 if not m:continue
 cases.append({"source_path":x["source_path"],"original_blob_sha":x["source_git_blob_sha"],
   "source_url":m["source_page"],"creator_claim":m.get("creator",""),"license_claim":m.get("license_claim",""),
   "status":"HOLD","reason":"","media_candidates_count":0})
assert len(cases)==58,f"Expected 58 GBIF original-source priority files, got {len(cases)}"
q=ROOT/"qa-report/asteraceae-gbif-media-rights";q.mkdir(parents=True,exist_ok=True)
def clean(s):
 t=re.sub(r"<[^>]*>"," ",str(s or ""));t=html.unescape(t)
 t=re.sub(r"(?i)\b(?:some rights reserved|no rights reserved|uploaded by|copyright|©|\(c\))\b"," ",t)
 return re.sub(r"\s+"," ",t).strip(" ,.-").casefold()
def lic(s):
 s=str(s or "").lower().replace("_","-").replace(" ","-")
 if "/publicdomain/zero/" in s or "cc0" in s:return "CC0"
 if "/publicdomain/mark/" in s or s in {"pd","public-domain"}:return "PD"
 if "by-nc" in s:return "NONCOMMERCIAL"
 if "by-sa" in s:return "CC BY-SA"
 if re.search(r"\bby(?:[-/\d.]|$)",s) or "by/" in s:return "CC BY"
 return "UNKNOWN"
def get_json(u):
 req=urllib.request.Request(u,headers={"User-Agent":"HaysBotanyVisualPhotoAudit/0.4 (rights research; low request frequency)","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=28) as f:return json.load(f)
def get_img(u):
 req=urllib.request.Request(u,headers={"User-Agent":"HaysBotanyVisualPhotoAudit/0.4 (source photo verification)","Accept":"image/*"})
 with urllib.request.urlopen(req,timeout=40) as f:return f.read(18000000)
def dhash(b):
 with Image.open(io.BytesIO(b)) as img:
  im=ImageOps.exif_transpose(img).convert("L").resize((9,8),Image.Resampling.LANCZOS)
  a=list(im.getdata())
 return sum(1<<k for k in range(64) if a[(k//8)*9+k%8]>a[(k//8)*9+k%8+1])
def media_list(d):
 return (d.get("extensions") or {}).get("http://rs.gbif.org/terms/1.0/Multimedia") or []
def norm_media(row):
 # fragment has short keys, verbatim has URI keys
 short={}
 for k,v in row.items():
  short[k.rsplit("/",1)[-1]]=v
 return short

approved={}
for i,case in enumerate(cases):
 id_=re.search(r"/occurrence/(\d+)",case["source_url"]).group(1)
 d=None
 for attempt in range(3):
  try:
   d=get_json(f"https://api.gbif.org/v1/occurrence/{id_}/fragment")
   break
  except Exception as ex:
   case["source_api_last_error"]=str(ex)[:160]
   time.sleep(1.0*(attempt+1))
 if not d:
  case["reason"]="GBIF_FRAGMENT_UNAVAILABLE_OR_RATE_LIMITED"
  continue
 mm=[norm_media(x) for x in media_list(d)]
 case["media_candidates_count"]=len(mm)
 wanted=lic(case["license_claim"])
 if wanted not in ("CC BY","CC BY-SA","CC0","PD"):
  case["reason"]="ORIGINAL_SOURCE_LICENSE_CLAIM_NOT_REUSABLE";continue
 blob=None
 for m in mm[:8]:
  remote_license=str(m.get("license") or "")
  got=lic(remote_license)
  if wanted!=got or got not in ("CC BY","CC BY-SA","CC0"):continue
  artist=clean(m.get("creator") or m.get("rightsHolder"))
  original=clean(case["creator_claim"])
  if not artist or not original or (artist not in original and original not in artist):
   continue
  media_url=str(m.get("identifier") or "")
  if not media_url.startswith("https://"):continue
  if not blob:
   try:
    blob=subprocess.run(["git","show","HEAD:"+case["source_path"]],cwd=SOURCE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
    sha_blob=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
    assert sha_blob==case["original_blob_sha"],"Original Git blob changed"
   except Exception:
    case["reason"]="PINNED_ORIGINAL_UNAVAILABLE_OR_MODIFIED";break
  try:
   remote=get_img(media_url)
   distance=(dhash(blob)^dhash(remote)).bit_count()
   case["closest_dhash_distance"]=min(distance,case.get("closest_dhash_distance",99))
   if distance>12:continue
  except Exception as exc:
   case["last_media_fetch_error"]=type(exc).__name__;continue
  case["status"]="VERIFIED_GBIF_MULTIMEDIA_LICENSE_CREDIT_AND_VISUAL_IMAGE"
  case["reason"]="EXACT_GBIF_MEDIA_LICENSE_CREATOR_AND_PIXELS"
  case["verified_license"]=got
  case["verified_media_license_url"]=remote_license
  case["verified_media_photo_url"]=m.get("references") or media_url
  case["verified_media_identifier"]=media_url
  case["verified_media_creator"]=m.get("creator") or m.get("rightsHolder")
  case["verified_dhash_distance"]=distance
  dest=ROOT/case["source_path"];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob)
  approved[case["source_path"]]={
   "source_git_blob_sha":case["original_blob_sha"],"source_page":case["verified_media_photo_url"],
   "gbif_occurrence":case["source_url"],"creator":case["creator_claim"],
   "upstream_verified_creator":case["verified_media_creator"],"license":got,
   "license_url":remote_license.replace("http://creativecommons.org/","https://creativecommons.org/"),
   "media_identifier":media_url,"visual_dhash_distance":distance,
   "noncommercial_only":False,
   "verified_via":"GBIF occurrence fragment multimedia individual media creator/license and same image pixels",
   "publication_approval":"PRIVATE_GBIF_SOURCE_VERIFIED_ONLY; SECONDARY_CURRENT_LICENSE_AND_PUBLIC_RELEASE_QA_REQUIRED"
  }
  break
 if case["status"]=="HOLD" and not case["reason"]:
  case["reason"]="NO_GBIF_MEDIA_MATCHED_SOURCE_LICENSE_CREDIT_AND_PIXELS"
 if (i+1)%10==0:print("GBIF_120_PROGRESS",i+1,"/",len(cases),"verified",len(approved),flush=True)
 time.sleep(0.24)
summary={"status":"GBIF_MEDIA_SOURCE_RIGHTS_CHECK_PRIVATE_ONLY","candidates":len(cases),
 "verified_and_archived":len(approved),"held":len(cases)-len(approved),
 "held_reasons":dict(Counter(r["reason"] for r in cases if r["status"]=="HOLD")),
 "license_types":dict(Counter(x["license"] for x in approved.values())),
 "source_sha":sha,"public_release":False}
(ROOT/"migration/asteraceae-upstream-gbif-120-ledger.json").write_text(json.dumps(approved,indent=2,ensure_ascii=False)+"\n")
(ROOT/"migration/asteraceae-upstream-gbif-120-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
(ROOT/"migration/asteraceae-upstream-gbif-120-all-decisions.json").write_text(json.dumps(cases,indent=2,ensure_ascii=False)+"\n")
(q/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("GBIF_120_RESULT",json.dumps(summary,sort_keys=True),flush=True)
