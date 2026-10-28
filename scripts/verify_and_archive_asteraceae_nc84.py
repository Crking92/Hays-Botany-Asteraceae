#!/usr/bin/env python3
"""Check pinned Asteraceae NC photo originals against individual live photo licenses.

Only exact source/photo identities matched by creator, NC CC license and
perceptual image fingerprint are archived to private Asteraceae staging.
Never relabel CC BY-NC as CC BY. No public Pages publication.
"""
import hashlib,html,io,json,re,subprocess,sys,time,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image,ImageOps

STAGE=Path(sys.argv[1]).resolve()
PINNED=Path(sys.argv[2]).resolve()
MAIN=Path(sys.argv[3]).resolve()
assert subprocess.check_output(["git","branch","--show-current"],cwd=STAGE,text=True).strip()=="staging/asteraceae-metadata"
meta=json.loads((STAGE/"data/collection-index.json").read_text())
assert len(meta["entries"])==180 and meta["authority"]=="STAGING_ONLY"
config=json.loads((STAGE/"config/collection.json").read_text())
assert config["publication"]["enabled"] is False
pinned_sha=meta["source_commit_sha"]
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=PINNED,text=True).strip()==pinned_sha
manifest=json.loads((MAIN/"planning/asteraceae-priority84-nc-source-baseline.json").read_text())
assert manifest["source_sha"]==pinned_sha and len(manifest["files"])==84
existing=set()
for name in ["asteraceae-verified-commons-photo-ledger.json","asteraceae-verified-inat-photo-ledger.json",
             "asteraceae-author-permitted-private-photo-ledger.json","asteraceae-upstream-commons-120-ledger.json",
             "asteraceae-upstream-inat-taxon-120-ledger.json","asteraceae-upstream-gbif-120-ledger.json"]:
 existing.update(json.loads((STAGE/"migration"/name).read_text()))
assert not any(x["path"] in existing for x in manifest["files"]), "Source staging changed; reconcile baseline before import"
qa=STAGE/"qa-report"/"asteraceae-84-nc-photo-rights";qa.mkdir(parents=True,exist_ok=True)

def credit(s):
 s=html.unescape(re.sub(r"<[^>]*>"," ",str(s or "")))
 s=re.sub(r"(?i)\b(?:some rights reserved|no rights reserved|uploaded by|copyright)\b"," ",s)
 s=s.replace("(c)"," ").replace("©"," ")
 s=re.sub(r"\([^)]*CC BY[^)]*\)"," ",s,flags=re.I)
 return re.sub(r"\s+"," ",s).strip(" ,-.;").casefold()
def match_name(a,b):
 a=credit(a);b=credit(b)
 if not a or not b:return False
 if a in b or b in a:return True
 aa=[x.strip() for x in a.split(" / ")]
 return any(len(x)>=4 and x in b for x in aa)
def normalized_license(s):
 s=str(s or "").strip().lower().replace("_","-").replace(" ","-")
 if "by-nc-nd" in s:return "CC BY-NC-ND"
 if "by-nc-sa" in s:return "CC BY-NC-SA"
 if "by-nc" in s:return "CC BY-NC"
 return "OTHER"
def api(url):
 request=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"HaysBotanyNCPhotoRightsVerifier/0.5 (educational source verification)"})
 with urllib.request.urlopen(request,timeout=28) as r:return json.load(r)
def image(url):
 if not url.startswith("https://"):raise ValueError("Non HTTPS media URL")
 request=urllib.request.Request(url,headers={"Accept":"image/*","User-Agent":"HaysBotanyNCPhotoRightsVerifier/0.5 (source image comparison)"})
 with urllib.request.urlopen(request,timeout=34) as r:return r.read(18000000)
def dhash(b):
 with Image.open(io.BytesIO(b)) as im:
  p=list(ImageOps.exif_transpose(im).convert("L").resize((9,8),Image.Resampling.LANCZOS).getdata())
 return sum(1<<k for k in range(64) if p[(k//8)*9+k%8]>p[(k//8)*9+k%8+1])
def blob(row):
 p=row["path"]
 raw=subprocess.run(["git","show","HEAD:"+p],cwd=PINNED,check=True,stdout=subprocess.PIPE).stdout
 sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
 if sha!=row["sha"]:raise AssertionError("Pinned source Git image changed: "+p)
 return raw
def download_json(url):
 for i in range(3):
  try:return api(url)
  except Exception as exc:
   last=str(exc)[:160]
   time.sleep((i+1)*1.0)
 return None
def choose_image(row,photos):
 orig=blob(row)
 original_hash=dhash(orig)
 claim=normalized_license(row["meta"].get("license_claim",""))
 if claim=="CC BY-NC-ND":return None,"NC_ND_NO_DERIVATIVES_REVIEW_REQUIRED",0
 if claim not in ("CC BY-NC","CC BY-NC-SA"):return None,"SOURCE_CLAIM_NOT_SUPPORTED_NC_LICENSE",0
 considered=0
 best=None
 for p in photos[:30]:
  if not isinstance(p,dict):continue
  current=normalized_license(p.get("license_code",p.get("license","")))
  if current!=claim:continue
  artist=p.get("attribution") or p.get("creator") or p.get("rightsHolder") or ""
  if not match_name(row["meta"].get("creator",""),artist):continue
  u=p.get("medium_url") or p.get("large_url") or p.get("url") or p.get("identifier")
  if not u or not u.startswith("https://"):continue
  considered+=1
  try:
   im=image(u)
   diff=(original_hash^dhash(im)).bit_count()
   if diff<=12 and (best is None or diff<best["difference"]):
    best={"difference":diff,"photo":p,"credit":artist,"original":orig}
  except Exception as exc:
   row["media_error"]=type(exc).__name__
 if best:return best,"PHOTO_CC_NC_CREDIT_AND_PIXELS_MATCHED",considered
 return None,"NO_EXACT_MEDIA_PHOTO_WITH_CURRENT_LICENSE_CREDIT_AND_PIXELS",considered

items=[]
for src in manifest["files"]:
 m=(src.get("source_metadata") or [{}])[0]
 path=src["path"];url=str(m.get("source_page") or "")
 typ="gbif" if "gbif.org/occurrence/" in url else (
     "observation" if "/observations/" in url else (
     "taxon" if "/taxa/" in url else "direct_photo" if "/photos/" in url else "other"))
 items.append({"path":path,"sha":src["sha"],"meta":m,"original_source_url":url,
   "source_type":typ,"status":"HOLD","reason":"NOT_YET_CHECKED","photo_id":None,
   "current_license":None,"verified_credit":None,"dhash_distance":None,"media_examined":0})
by_url=defaultdict(list)
for row in items:by_url[(row["source_type"],row["original_source_url"])].append(row)
assert Counter(r["source_type"] for r in items)=={"taxon":37,"observation":15,"direct_photo":29,"gbif":3}
approved={}
for i,((typ,url),group) in enumerate(sorted(by_url.items())):
 if typ=="direct_photo":
  # API for exact /photos/ID is not public, HTML returns 403.
  # Never trust stale species-card claims as current license confirmation.
  for row in group:row["reason"]="EXACT_PHOTO_PAGE_METADATA_UNAVAILABLE_TO_VERIFY_CURRENT_RIGHTS"
  continue
 if typ=="taxon":
  m=re.search(r"/taxa/(\d+)",url)
  data=download_json("https://api.inaturalist.org/v1/taxa/"+m.group(1)) if m else None
  photos=[x.get("default_photo") for x in data.get("results",[]) if isinstance(x,dict)] if data else []
  photos=[p for p in photos if p]
 elif typ=="observation":
  m=re.search(r"/observations/(\d+)",url)
  data=download_json("https://api.inaturalist.org/v1/observations/"+m.group(1)) if m else None
  photos=(data.get("results") or [{}])[0].get("photos",[]) if data and data.get("results") else []
 elif typ=="gbif":
  m=re.search(r"/occurrence/(\d+)",url)
  data=download_json("https://api.gbif.org/v1/occurrence/"+m.group(1)+"/fragment") if m else None
  raw=((data.get("extensions") or {}).get("http://rs.gbif.org/terms/1.0/Multimedia") or []) if data else []
  photos=[]
  for item in raw:
   p={k.rsplit("/",1)[-1]:v for k,v in item.items()}
   p["license_code"]=p.get("license","")
   p["attribution"]=p.get("creator") or p.get("rightsHolder","")
   p["url"]=p.get("identifier","")
   p["photo_id"]=re.search(r"/photos/(\d+)",p.get("references","") or "")
   if p["photo_id"]:p["photo_id"]=p["photo_id"].group(1)
   photos.append(p)
 else:
  photos=[]
 for row in group:
  if normalized_license(row["meta"].get("license_claim",""))=="CC BY-NC-ND":
   row["reason"]="NC_ND_NO_DERIVATIVES_REVIEW_REQUIRED";continue
  if not photos:
   row["reason"]="UPSTREAM_INDIVIDUAL_PHOTO_METADATA_UNAVAILABLE";continue
  try:match,reason,n=choose_image(row,photos)
  except Exception as exc:
   match=None;reason="PINNED_IMAGE_OR_COMPARISON_FAILED_"+type(exc).__name__;n=0
  row["reason"]=reason;row["media_examined"]=n
  if not match:continue
  p=match["photo"];picid=p.get("id") or p.get("photo_id")
  if not picid and typ=="gbif":
   picid=re.search(r"/photos/(\d+)",p.get("references","") or "")
   picid=picid.group(1) if picid else None
  row["status"]="VERIFIED_PRIVATE_CC_NC_SOURCE_PHOTO"
  row["current_license"]=normalized_license(p.get("license_code",p.get("license","")))
  row["verified_credit"]=match["credit"]
  row["dhash_distance"]=match["difference"]
  row["photo_id"]=picid
  original=match["original"]
  dest=STAGE/row["path"];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(original)
  license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/" if row["current_license"]=="CC BY-NC-SA" else "https://creativecommons.org/licenses/by-nc/4.0/"
  approved[row["path"]]={
    "source_git_blob_sha":row["sha"],"source_page":f"https://www.inaturalist.org/photos/{picid}" if picid else url,
    "original_source_page":url,"creator":row["meta"]["creator"],
    "verified_upstream_attribution":match["credit"],"license":row["current_license"],
    "license_url":license_url,"photo_id":picid,"noncommercial_only":True,
    "source_type":typ,"dhash_distance":match["difference"],
    "verified_via":"Individual live photo license+credit and pinned source-image perceptual match",
    "publication_approval":"PRIVATE_NONCOMMERCIAL_STAGING_ONLY; PUBLIC_OR_COMMERCIAL_RELEASE_REQUIRES_SEPARATE_REVIEW"
  }
 if (i+1)%6==0:print("NC_RIGHTS_PROGRESS",i+1,"/",len(by_url),"verified",len(approved),flush=True)
 time.sleep(0.25)
assert all(x["source_git_blob_sha"] in {r["sha"] for r in items} for x in approved.values())
report={"status":"84_SOURCE_NC_IMAGES_CHECKED_PRIVATE_ONLY",
 "source_sha":pinned_sha,"total_candidates":len(items),"verified_and_archived":len(approved),
 "still_held":len(items)-len(approved),
 "by_source":dict(Counter(r["source_type"] for r in items)),
 "verified_by_source":dict(Counter(r["source_type"] for r in items if r["status"]=="VERIFIED_PRIVATE_CC_NC_SOURCE_PHOTO")),
 "hold_reasons":dict(Counter(r["reason"] for r in items if r["status"]!="VERIFIED_PRIVATE_CC_NC_SOURCE_PHOTO")),
 "noncommercial_only":True,"not_public_website_approved":True}
(STAGE/"migration/asteraceae-verified-84-nc-photo-ledger.json").write_text(json.dumps(approved,indent=2,ensure_ascii=False)+"\n")
(STAGE/"migration/asteraceae-84-nc-photo-audit-decisions.json").write_text(json.dumps(items,indent=2,ensure_ascii=False)+"\n")
(STAGE/"migration/asteraceae-84-nc-photo-audit-summary.json").write_text(json.dumps(report,indent=2)+"\n")
(qa/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
print("ASTERACEAE_NC84_RESULT",json.dumps(report,sort_keys=True),flush=True)
