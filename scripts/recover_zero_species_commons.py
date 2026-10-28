#!/usr/bin/env python3
"""Recover exact previously-held Commons files for photo-empty Asteraceae taxa.

Strict targeting: two MathKnight Heterotheca images and one Pseudoanas safflower
image. Source photographer and applicable license must match current Commons
file metadata or file wikitext. Perceptual match + original Git blob SHA.
Staging only, never GitHub Pages. Fails closed on any ambiguity.
"""
import hashlib, html, io, json, re, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageOps

ROOT=Path(sys.argv[1]).resolve(); PIN=Path(sys.argv[2]).resolve()
assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()=="staging/asteraceae-metadata"
cfg=json.loads((ROOT/"config/collection.json").read_text())
idx=json.loads((ROOT/"data/collection-index.json").read_text())
assert cfg["publication"]["enabled"] is False and idx["authority"]=="STAGING_ONLY"
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=PIN,text=True).strip()==idx["source_commit_sha"]
source={x["path"]:x for x in json.loads((ROOT/"migration/asteraceae-source-file-ledger.json").read_text())}
all_photo=json.loads((ROOT/"migration/asteraceae-full-image-asset-reconciliation.json").read_text())
by_path={x["source_path"]:x for x in all_photo}
targets={
 "content/taxa/Asteraceae/Heterotheca/heterotheca-subaxillaris/images/heterotheca-subaxillaris-extra-recognition.jpg":{
  "page":"File:Heterotheca_subaxillaris001.jpg","author":"MathKnight","license":"CC BY-SA 4.0","role":"Habit and flowering head"},
 "content/taxa/Asteraceae/Heterotheca/heterotheca-subaxillaris/images/heterotheca-subaxillaris-habit.jpg":{
  "page":"File:Heterotheca_subaxillaris002.jpg","author":"MathKnight","license":"CC BY-SA 4.0","role":"Whole plant habit"},
 "content/taxa/Asteraceae/Carthamus/carthamus-tinctorius/images/carthamus-tinctorius-pseudoanas.jpg":{
  "page":"File:Carthamus_tinctorius_050709c.JPG","author":"Pseudoanas","license":"CC0 1.0","role":"Flower head and habit"}
}
assert len(targets)==3
def norm(s):
 s=html.unescape(re.sub(r"<[^>]+>"," ",str(s or "")))
 return re.sub(r"[^a-z0-9]","",s.casefold())
def fetch(url,binary=False):
 if not url.startswith("https://"):raise ValueError("HTTPS source only")
 headers={"Accept":"image/*" if binary else "application/json","User-Agent":"HaysBotanyAsteraceaePhotoLicenseAudit/0.6 (source-based educational file rights validation)"}
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=35) as res:
  return res.read(14000000) if binary else json.load(res)
def pic_hash(b):
 with Image.open(io.BytesIO(b)) as im:
  p=list(ImageOps.exif_transpose(im).convert("L").resize((9,8),Image.Resampling.LANCZOS).getdata())
 return sum(1<<i for i in range(64) if p[(i//8)*9+i%8]>p[(i//8)*9+i%8+1])
def remote_meta(title):
 u="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({
    "action":"query","format":"json","formatversion":2,"prop":"imageinfo|revisions",
    "iiprop":"extmetadata|url","iiurlwidth":900,
    "rvprop":"content","rvslots":"main","titles":title})
 data=fetch(u)
 ps=data.get("query",{}).get("pages",[])
 if not ps or not ps[0].get("imageinfo"):raise ValueError("Commons photo missing")
 return ps[0]
rows=[]; approved={}
for path,target in targets.items():
 assert path in source and path in by_path and not by_path[path]["archived_in_private_staging"]
 rec={"source_path":path,"expected_title":target["page"],"expected_creator":target["author"],
      "original_claim":target["license"],"decision":"HELD","reason":"UPSTREAM_CHECK_PENDING"}
 try:
  p=remote_meta(target["page"])
  info=p["imageinfo"][0];ext=info.get("extmetadata",{})
  def val(k):
   x=ext.get(k,{})
   return x.get("value","") if isinstance(x,dict) else ""
  artist=val("Artist");license_short=val("LicenseShortName");lic_url=val("LicenseUrl")
  contents=p.get("revisions",[{}])[0].get("slots",{}).get("main",{}).get("content","")
  rec["artist"]=re.sub(r"<[^>]*>"," ",artist).strip()
  rec["license_short"]=license_short
  rec["license_url"]=lic_url
  rec["page_title"]=p["title"]
  if norm(target["author"]) not in norm(artist):
   rec["reason"]="UPSTREAM_CREATOR_NOT_SAME_PERSON"
  elif target["license"]=="CC0 1.0":
   # Commons page may label this Public domain despite explicit CC0 deed.
   content_n=re.sub(r"\s+","",contents.lower())
   cc0_link=("creativecommons.org/publicdomain/zero" in lic_url.lower())
   cc0_wikitext=any(z in content_n for z in ("{{cc-zero","{{cc0","{{cc zero","{{cc-zero}}","{{cc-zero|"))
   pd_author_deed=("{{pd-self" in content_n or "{{pdself" in content_n)
   pd_current=(license_short.strip().lower()=="public domain" and val("Copyrighted").strip().lower()=="false")
   if cc0_link or cc0_wikitext:
    rec["license_verification"]="EXACT_FILE_CC0_DEDICATION"
   elif pd_author_deed and pd_current:
    rec["license_verification"]="CURRENT_FILE_AUTHOR_PUBLIC_DOMAIN_SELF_DEDICATION"
    rec["effective_license"]="Public domain (author dedication)"
   else:
    rec["reason"]="UPSTREAM_CC0_OR_AUTHOR_PD_DEDICATION_NOT_MACHINE_VERIFIED"
  elif target["license"]=="CC BY-SA 4.0":
   if "CC BY-SA 4.0" not in license_short.upper() or not ("by-sa/4.0" in lic_url):
    rec["reason"]="COMMONS_BY_SA_LICENSE_MISMATCH"
   else:rec["license_verification"]="EXACT_FILE_CC_BY_SA_4.0"
  else:raise AssertionError("Unexpected target license")
  if rec.get("license_verification"):
   original=subprocess.run(["git","show","HEAD:"+path],cwd=PIN,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
   h=hashlib.sha1(b"blob "+str(len(original)).encode()+b"\0"+original).hexdigest()
   assert h==source[path]["git_blob_sha"],"Source bytes differ"
   u=info.get("thumburl") or info.get("url")
   current=fetch(u,binary=True)
   diff=(pic_hash(original)^pic_hash(current)).bit_count()
   rec["dhash_distance"]=diff
   if diff>12:rec["reason"]="SOURCE_PHOTO_NOT_SAME_CURRENT_COMMONS_IMAGE"
   else:
    rec["decision"]="SOURCE_CC_PHOTO_VERIFIED_PRIVATE_STAGED"
    rec["reason"]="AUTHOR_LICENSE_AND_IMAGE_HASH_MATCHED"
    (ROOT/path).parent.mkdir(parents=True,exist_ok=True)
    (ROOT/path).write_bytes(original)
    approved[path]={
      "source_git_blob_sha":h,"creator":target["author"],"upstream_artist":rec["artist"],
      "license":rec.get("effective_license",target["license"]),
      "license_url":("https://commons.wikimedia.org/wiki/"+target["page"] if rec.get("effective_license") else ("https://creativecommons.org/publicdomain/zero/1.0/" if target["license"]=="CC0 1.0" else "https://creativecommons.org/licenses/by-sa/4.0/")),
      "source_page":"https://commons.wikimedia.org/wiki/"+target["page"],
      "role":target["role"],"noncommercial_only":False,"visually_matched_dhash_distance":diff,
      "verified_via":"Wikimedia Commons exact file current artist, license and original pixel comparison",
      "publication_approval":"STAGING_IMAGE_ONLY; FINAL_PUBLIC_IMAGE_AND_DERIVATIVE_REVIEW_PENDING"
    }
 except Exception as e:
  rec["reason"]="CURRENT_COMMONS_OR_PINNED_IMAGE_UNAVAILABLE_"+type(e).__name__
  rec["error_detail"]=str(e)[:280]
 rows.append(rec)
 print("ZERO_SPECIES_COMMONS_CHECK",path.split("/")[-1],rec["decision"],rec["reason"],flush=True)
summary={"status":"SOURCE_SPECIES_GAP_COMMONS_REVIEW_COMPLETE","source_sha":idx["source_commit_sha"],
 "target_files":len(targets),"files_verified_and_staged":len(approved),
 "files_remaining_held":len(targets)-len(approved),
 "source_verified_species":sorted({p.split("/")[4] for p in approved}),
 "all_decisions":[{"path":r["source_path"],"decision":r["decision"],"reason":r["reason"]} for r in rows],
 "public_release_approval":False}
folder=ROOT/"migration"
(folder/"asteraceae-zero-species-commons-recovery-ledger.json").write_text(json.dumps(approved,indent=2,ensure_ascii=False)+"\n")
(folder/"asteraceae-zero-species-commons-recovery-decisions.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n")
(folder/"asteraceae-zero-species-commons-recovery-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("ZERO_SPECIES_COMMONS_RESULT",json.dumps(summary,sort_keys=True),flush=True)
