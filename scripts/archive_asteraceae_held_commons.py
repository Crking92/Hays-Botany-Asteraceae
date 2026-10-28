#!/usr/bin/env python3
"""Verify and stage held Commons 120-priority Asteraceae source images, private only.

Require exact Wikimedia Commons File page, current license match, credited author
match, and visual thumbnail agreement with the pinned original photograph.
Does not deploy Pages or change canonical hub records.
"""
import hashlib, html, io, json, re, subprocess, sys, time, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(sys.argv[1]).resolve()
SOURCE=Path(sys.argv[2]).resolve()
assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()=="staging/asteraceae-metadata"
config=json.loads((ROOT/"config/collection.json").read_text())
assert config["publication"]["enabled"] is False
index=json.loads((ROOT/"data/collection-index.json").read_text())
sha=index["source_commit_sha"]
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=SOURCE,text=True).strip()==sha
source_ledger={x["path"]:x for x in json.loads((ROOT/"migration/asteraceae-source-file-ledger.json").read_text())}
asset_rows=json.loads((ROOT/"migration/asteraceae-full-image-asset-reconciliation.json").read_text())
existing={}
for filename in ("asteraceae-verified-commons-photo-ledger.json","asteraceae-verified-inat-photo-ledger.json","asteraceae-author-permitted-private-photo-ledger.json"):
 for k in json.loads((ROOT/"migration"/filename).read_text()):existing[k]=filename
targets=[x for x in asset_rows if x["followup_priority"]=="FIRST_RECHECK_UPSTREAM_PERMISSION_AND_CREATOR"
         and not x["archived_in_private_staging"] and any("commons.wikimedia.org" in str(m.get("source_page","")) for m in x["source_metadata"])]
assert len(targets)==40, f"Expected 40 held Commons priority files, got {len(targets)}"
qa=ROOT/"qa-report"/"commons-120-priority"
qa.mkdir(parents=True,exist_ok=True)

def clean(s):
 return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",str(s or "")))).strip()
def license_code(s):
 v=re.sub(r"[\s_-]+"," ",str(s or "").lower()).strip().replace("creative commons","cc")
 m=re.search(r"cc\s+by\s+sa\s+([234]\.0)",v)
 if m:return "CC BY-SA "+m.group(1)
 m=re.search(r"cc\s+by\s+([234]\.0)",v)
 if m:return "CC BY "+m.group(1)
 if "cc0" in v or "cc zero" in v:return "CC0"
 if "public domain" in v or "public-domain" in v:return "PUBLIC DOMAIN"
 return "OTHER"
def artist_match(origin,artist):
 x=clean(origin).casefold(); y=clean(artist).casefold()
 if not x or not y:return False
 if x in y or y in x:return True
 aliases=[x]+[a.strip() for a in re.findall(r"\((.*?)\)",x)]+[a.strip() for a in x.split("/")]+[a.strip() for a in x.split(" / ")]
 return any(len(a)>=4 and a in y for a in aliases)
def title_from_url(url):
 v=urllib.parse.urlparse(str(url));p=urllib.parse.unquote(v.path)
 if v.scheme!="https" or v.hostname not in {"commons.wikimedia.org","www.commons.wikimedia.org"} or not p.startswith("/wiki/File:"):return None
 return p[6:].replace("_"," ")
def req_json(url):
 rq=urllib.request.Request(url,headers={"User-Agent":"HaysBotanyPhotoSourceAudit/0.3 (Hays Botany; original photo license validation)","Accept":"application/json"})
 with urllib.request.urlopen(rq,timeout=40) as r:return json.load(r)
def req_image(url):
 rq=urllib.request.Request(url,headers={"User-Agent":"HaysBotanyPhotoSourceAudit/0.3 (Hays Botany; exact source photo comparison)"})
 with urllib.request.urlopen(rq,timeout=45) as r:return r.read(15000000)
def dhash(raw):
 with Image.open(io.BytesIO(raw)) as im:
  z=ImageOps.exif_transpose(im).convert("L").resize((9,8),Image.Resampling.LANCZOS)
  px=list(z.getdata())
 return sum((1<<i) for i in range(64) if px[(i//8)*9+i%8]>px[(i//8)*9+i%8+1])
def verified_photo_pair(blob, thumb):
 a=dhash(blob);b=dhash(thumb);dist=(a^b).bit_count()
 return dist,dist<=12

rows=[]
for x in targets:
 m=next((m for m in x["source_metadata"] if title_from_url(m.get("source_page"))),x["source_metadata"][0] if x["source_metadata"] else {})
 t=title_from_url(m.get("source_page"))
 rows.append({"source_path":x["source_path"],"git_blob_sha":x["source_git_blob_sha"],"source_page":m.get("source_page",""),
   "source_artist_claim":m.get("creator",""),"source_license_claim":m.get("license_claim",""),
   "commons_title":t,"status":"HOLD","reason":"","license":"","artist_current":"","license_url":"","visual_dhash_distance":None})
queue={r["commons_title"]:r for r in rows if r["commons_title"]}
for i in range(0,len(queue),8):
 block=list(queue)[i:i+8]
 params=urllib.parse.urlencode({"action":"query","prop":"imageinfo","iiprop":"extmetadata|url","iiurlwidth":"800","format":"json","formatversion":2,"titles":"|".join(block)})
 url="https://commons.wikimedia.org/w/api.php?"+params
 data=None
 for attempt in range(3):
  try:data=req_json(url);break
  except Exception as e:
   print("COMMONS_GROUP_RETRY",i,type(e).__name__,flush=True);time.sleep(1+attempt)
 if not data:
  for k in block:queue[k]["reason"]="UPSTREAM_COMMONS_API_UNAVAILABLE"
  continue
 pages={p["title"].casefold():p for p in data.get("query",{}).get("pages",[])}
 for title in block:
  r=queue[title];page=pages.get(title.casefold())
  if not page or not page.get("imageinfo"):r["reason"]="UPSTREAM_FILE_NOT_RESOLVED";continue
  ii=page["imageinfo"][0]
  meta=ii.get("extmetadata",{})
  def val(k):
   x=meta.get(k,{})
   return x.get("value","") if isinstance(x,dict) else ""
  want=license_code(r["source_license_claim"]);got=license_code(val("LicenseShortName"))
  artist=clean(val("Artist"));r["artist_current"]=artist[:700];r["license"]=got
  url_license=val("LicenseUrl")
  r["license_url"]=url_license.replace("http://creativecommons.org/","https://creativecommons.org/")
  if want not in ("CC0","PUBLIC DOMAIN") and not want.startswith("CC BY"):r["reason"]="SOURCE_LICENSE_CLAIM_NOT_STANDARD";continue
  if want!=got:r["reason"]="UPSTREAM_LICENSE_DIFFERS_FROM_SOURCE";continue
  if not artist_match(r["source_artist_claim"],artist):
   r["reason"]="CREATOR_CREDIT_DIFFERS_NEEDS_REVIEW";continue
  if got=="PUBLIC DOMAIN":
   if str(val("Copyrighted")).strip().lower()!="false" or "public domain" not in val("UsageTerms").lower():
    r["reason"]="PD_ORIGIN_OR_RIGHTS_NOT_SUFFICIENT";continue
   r["license_url"]="https://commons.wikimedia.org/wiki/"+urllib.parse.quote(page["title"].replace(" ","_"),safe=":_()/")
  elif "creativecommons.org/" not in r["license_url"]:
   r["reason"]="UPSTREAM_CC_LICENSE_LINK_UNAVAILABLE";continue
  thumb=ii.get("thumburl") or ii.get("url")
  if not thumb:r["reason"]="UPSTREAM_IMAGE_URL_UNAVAILABLE";continue
  path=r["source_path"]
  try:
   blob=subprocess.run(["git","show","HEAD:"+path],cwd=SOURCE,stdout=subprocess.PIPE,check=True).stdout
   sha_blob=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
   assert sha_blob==r["git_blob_sha"],"Source blob changed"
   remote=req_image(thumb)
   dist,agree=verified_photo_pair(blob,remote)
   r["visual_dhash_distance"]=dist
   if not agree:r["reason"]="UPSTREAM_IMAGE_DIFFERS_FROM_ARCHIVED_PHOTO";continue
  except Exception as e:r["reason"]="UPSTREAM_PHOTO_COMPARISON_FAILED_"+type(e).__name__;continue
  r["status"]="VERIFIED_SOURCE_CC_OR_PD_AND_IMAGE"
  r["reason"]="SOURCE_CREATOR_LICENSE_AND_VISUAL_IMAGE_MATCH"
  r["upstream_file_title"]=page["title"]
  r["blob_bytes"]=len(blob)
  (ROOT/path).parent.mkdir(parents=True,exist_ok=True)
  (ROOT/path).write_bytes(blob)
 print("COMMONS_120_PROGRESS",min(i+len(block),len(queue)),"/",len(queue),flush=True)
valid=[r for r in rows if r["status"]=="VERIFIED_SOURCE_CC_OR_PD_AND_IMAGE"]
new={}
for r in valid:
 path=r["source_path"]
 new[path]={
  "source_git_blob_sha":r["git_blob_sha"],"source_page":r["source_page"],
  "creator":r["source_artist_claim"],"upstream_verified_artist":r["artist_current"],
  "license":r["license"],"license_url":r["license_url"],"noncommercial_only":False,
  "visual_dhash_distance":r["visual_dhash_distance"],
  "rights_basis":"Wikimedia Commons current File metadata matched original credit, license and source image dHash",
  "publication_approval":"STAGING_IMAGE_ONLY; PUBLIC_SNAPSHOT_REQUIRES_RELEASE_REVIEW"
 }
(ROOT/"migration/asteraceae-upstream-commons-120-ledger.json").write_text(json.dumps(new,indent=2,ensure_ascii=False)+"\n")
summary={"status":"COMPLETE_RIGHTS_RECHECK_PRIVATE_STAGING_NO_DEPLOY","source_sha":sha,
 "source_priority_commons_candidates":len(rows),"verified_and_archived":len(valid),
 "held":len(rows)-len(valid),"held_reasons":dict(Counter(r["reason"] for r in rows if r["status"]!="VERIFIED_SOURCE_CC_OR_PD_AND_IMAGE")),
 "verified_license_count":dict(Counter(r["license"] for r in valid)),"public_site_published":False}
(ROOT/"migration/asteraceae-upstream-commons-120-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
(qa/"all-40-commons-source-checks.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n")
(qa/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("UPSTREAM_COMMONS_120_ARCHIVE",json.dumps(summary,sort_keys=True),flush=True)
