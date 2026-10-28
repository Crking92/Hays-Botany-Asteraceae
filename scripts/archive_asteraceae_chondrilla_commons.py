#!/usr/bin/env python3
"""Archive independently verified Commons Chondrilla juncea habit image.

The species is in the Texas learner; Commons photo is an Australian observation,
which is explicitly labelled. Original source migration 459 counts stay intact.
"""
import hashlib,html,io,json,re,subprocess,sys,urllib.parse,urllib.request
from pathlib import Path
from PIL import Image,ImageOps
ROOT=Path(sys.argv[1]).resolve()
assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()=="staging/asteraceae-metadata"
cfg=json.loads((ROOT/"config/collection.json").read_text())
assert cfg["publication"]["enabled"] is False
out=ROOT/"migration/asteraceae-new-commons-field-photo-ledger.json"
if out.exists():raise AssertionError("Source new-media ledger already installed; avoid duplication")
page="File:Chondrilla juncea plant1 (12112259833).jpg"
url="https://commons.wikimedia.org/wiki/"+urllib.parse.quote(page.replace(" ","_"),safe=":()")
api="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({
 "action":"query","format":"json","formatversion":2,"prop":"imageinfo",
 "iiprop":"extmetadata|url","iiurlwidth":960,"titles":page})
def get(u,binary=False):
 if not u.startswith("https://"):raise ValueError("HTTPS source only")
 req=urllib.request.Request(u,headers={"Accept":"image/*" if binary else "application/json",
      "User-Agent":"HaysBotanyVisualLearnerCommons/0.3 (source-file license verification)"})
 with urllib.request.urlopen(req,timeout=38) as f:
  return f.read(14000000) if binary else json.load(f)
pages=get(api).get("query",{}).get("pages",[])
assert pages and pages[0].get("imageinfo"),"Exact Commons File page unavailable"
info=pages[0]["imageinfo"][0];e=info.get("extmetadata",{})
def val(k):
  x=e.get(k,{})
  return x.get("value","") if isinstance(x,dict) else ""
artist=html.unescape(re.sub(r"<[^>]*>"," ",val("Artist"))).strip()
short=val("LicenseShortName")
licurl=val("LicenseUrl").replace("http://creativecommons.org/","https://creativecommons.org/")
assert "Harry Rose" in artist or "Macleay Grass Man" in artist,(artist,short)
assert "CC BY 2.0" in short.upper(),short
assert "creativecommons.org/licenses/by/2.0" in licurl,licurl
raw=get(info.get("thumburl") or info["url"],binary=True)
with Image.open(io.BytesIO(raw)) as im:
 im=ImageOps.exif_transpose(im).convert("RGB")
 assert im.width>=800 and im.height>=600
 im.thumbnail((1500,1500),Image.Resampling.LANCZOS)
 bio=io.BytesIO()
 im.save(bio,"JPEG",quality=88,optimize=True,exif=b"")
 content=bio.getvalue()
assert len(content)>10000 and len(content)<25000000
path="external-media/asteraceae/new-commons/chondrilla-juncea/commons-12112259833.jpg"
dest=ROOT/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
sha=hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()
data={path:{
 "source_git_blob_sha":sha,
 "archive_sha256":hashlib.sha256(content).hexdigest(),
 "download_source_sha256":hashlib.sha256(raw).hexdigest(),
 "species_id":"chondrilla-juncea","scientific_name":"Chondrilla juncea",
 "source_page":url,"license":"CC BY 2.0","license_url":"https://creativecommons.org/licenses/by/2.0/",
 "creator":artist,"noncommercial_only":False,
 "role":"Introduced rush skeletonweed field habit (Australian reference; not a Texas observation)",
 "modified":"Source image downscaled and metadata removed; no anatomical arrows added",
 "source_image_original_url":info.get("url"),
 "source_site":"Wikimedia Commons; Flickr license reviewed by FlickreviewR",
 "provenance":"Wikimedia Commons exact File metadata current CC BY 2.0 and named artist checked 2026-10-28",
 "publication_approval":"STAGING_NEW_COMMONS_EXACT_CC_VERIFIED; FIELD_VISUAL_AND_PUBLIC_RELEASE_PENDING"
}}
out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
summary={"new_external_commons_photos":len(data),"source_species":["chondrilla-juncea"],"license":"CC BY 2.0",
 "source_creator":artist,"not_texas_observation":True,
 "original_459_source_files_unchanged":True,"public_site_published":False}
(ROOT/"migration/asteraceae-new-commons-field-photo-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("COMMONS_CHONDRILLA_BACKFILL",json.dumps(summary,sort_keys=True),flush=True)
