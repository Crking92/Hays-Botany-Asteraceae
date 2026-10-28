#!/usr/bin/env python3
"""Recover three Asteraceae photo gaps through Kew-confirmed homotypic synonyms.

Three exact iNaturalist research-grade Texas photos; direct per-image license
and attribution checked. For Hymenopappus, prefer copying ORIGINAL pinned
source photo after photo-ID match over downloading a duplicate.
No parent species used to identify a variety. Private staging only.
"""
import hashlib,html,io,json,re,subprocess,sys,urllib.request
from pathlib import Path
from PIL import Image,ImageOps
ROOT=Path(sys.argv[1]).resolve();SOURCE=Path(sys.argv[2]).resolve()
assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()=="staging/asteraceae-metadata"
idx=json.loads((ROOT/"data/collection-index.json").read_text())
cfg=json.loads((ROOT/"config/collection.json").read_text())
assert cfg["publication"]["enabled"] is False and idx["authority"]=="STAGING_ONLY"
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=SOURCE,text=True).strip()==idx["source_commit_sha"]
assert len(idx["entries"])==180
orig={x["path"]:x for x in json.loads((ROOT/"migration/asteraceae-source-file-ledger.json").read_text())}
source_data={
 "leontodon-rhagadioloides":{
  "observed_taxon":"Hedypnois rhagadioloides","rank":"species",
  "obs_id":111455265,"photo_id":188150460,
  "accepted_taxon":"Leontodon rhagadioloides",
  "taxon_source":"https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:211686-1",
  "label":"Texas research-grade field photo (observed as synonym Hedypnois rhagadioloides)",
 },
 "iva-asperifolia-var-angustifolia":{
  "observed_taxon":"Iva angustifolia","rank":"species",
  "obs_id":94831007,"photo_id":157427419,
  "accepted_taxon":"Iva asperifolia var. angustifolia",
  "taxon_source":"https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:30361801-2",
  "label":"Texas narrowleaf sumpweed (observed under homotypic synonym Iva angustifolia)",
 },
 "hymenopappus-scabiosaeus-var-corymbosus":{
  "observed_taxon":"Hymenopappus scabiosaeus corymbosus","rank":"variety",
  "obs_id":159788922,"photo_id":276095449,
  "accepted_taxon":"Hymenopappus scabiosaeus var. corymbosus",
  "taxon_source":"https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:1022446-2",
  "label":"Texas research-grade exact variety (old plainsman, var. corymbosus)",
  "original_source_path":"content/taxa/Asteraceae/Hymenopappus/hymenopappus-scabiosaeus-var-corymbosus/images/inat-276095449.jpg"
 }}
def get_api(id):
 url="https://api.inaturalist.org/v1/observations/"+str(id)
 req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"HaysBotanyTaxonomicPhotoRightsVerifier/0.4"})
 with urllib.request.urlopen(req,timeout=30) as f:return json.load(f)
def get_image(u,pid):
 if not isinstance(u,str) or "/photos/"+str(pid)+"/" not in u:raise ValueError("Media URL not the selected photo")
 u=re.sub(r"/(?:square|thumb|small|medium)\.", "/large.",u)
 p=__import__("urllib.parse",fromlist=["urlparse"]).urlparse(u)
 assert p.scheme=="https" and p.hostname in ("inaturalist-open-data.s3.amazonaws.com","static.inaturalist.org","www.inaturalist.org","inaturalist.org")
 req=urllib.request.Request(u,headers={"Accept":"image/*","User-Agent":"HaysBotanyTaxonomicPhotoRightsVerifier/0.4"})
 with urllib.request.urlopen(req,timeout=30) as f:return f.read(18000000),u
def hash_blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def dhash(b):
 with Image.open(io.BytesIO(b)) as im:
  pixels=list(ImageOps.exif_transpose(im).convert("L").resize((9,8),Image.Resampling.LANCZOS).getdata())
 return sum(1<<i for i in range(64) if pixels[(i//8)*9+i%8]>pixels[(i//8)*9+i%8+1])
def neat(s):
 return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",str(s or "")))).casefold()
new={}; originals={}; decisions=[]
for species,s in source_data.items():
 d={"species_id":species,"accepted_taxon":s["accepted_taxon"],
    "observation_taxon":s["observed_taxon"],"rank":s["rank"],
    "observation":s["obs_id"],"photo_id":s["photo_id"],
    "taxonomy_source":s["taxon_source"],"status":"HOLD","reason":""}
 try:
  o=get_api(s["obs_id"])["results"][0]
  taxon=o.get("taxon") or {}
  assert taxon.get("name")==s["observed_taxon"] and taxon.get("rank")==s["rank"],(taxon.get("name"),taxon.get("rank"))
  assert o.get("quality_grade")=="research"
  p=next(x for x in o["photos"] if x["id"]==s["photo_id"])
  lic=(p.get("license_code") or "").lower().replace("_","-")
  assert lic=="cc-by",f"Photo license changed: {lic}"
  credit=p.get("attribution") or ""
  assert "CC BY" in credit.upper() and "rights reserved" in credit.casefold(),credit
  raw,u=get_image(p.get("large_url") or p.get("medium_url") or p.get("url"),p["id"])
  d["live_photo_attribution"]=credit;d["source_url"]=u
  d["live_photo_license"]=lic
  if "original_source_path" in s:
    path=s["original_source_path"];assert path in orig
    original=subprocess.run(["git","show","HEAD:"+path],cwd=SOURCE,stdout=subprocess.PIPE,check=True).stdout
    assert hash_blob(original)==orig[path]["git_blob_sha"],"Pinned blob mismatch"
    # Exact source photo ID and same image content make this safe to reconcile
    dist=(dhash(original)^dhash(raw)).bit_count()
    d["dhash_distance"]=dist
    assert dist<=12,f"Source original does not match current exact photo: {dist}"
    assert "Reid Hardin" in credit
    dest=ROOT/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(original)
    originals[path]={
      "source_git_blob_sha":hash_blob(original),
      "source_page":f"https://www.inaturalist.org/photos/{p['id']}",
      "observation_page":f"https://www.inaturalist.org/observations/{o['id']}",
      "creator":credit,
      "license":"CC BY (current iNaturalist photo license; version not explicit)",
      "license_url":"https://creativecommons.org/licenses/by/4.0/",
      "noncommercial_only":False,
      "verified_taxon":s["observed_taxon"],"verified_rank":s["rank"],
      "accepted_name":s["accepted_taxon"],"taxonomic_source":s["taxon_source"],
      "verified_via":"Exact observation photo ID, research-grade variety, photo CC BY and source original pixel dHash",
      "visual_dhash_distance":dist,
      "publication_approval":"PRIVATE_SOURCE_ORIGINAL_LICENSE_AND_TAXON_VERIFIED; FINAL_PUBLIC_RIGHTS_QA_PENDING"
    }
  else:
    with Image.open(io.BytesIO(raw)) as im:
      img=ImageOps.exif_transpose(im).convert("RGB")
      assert img.width>=400 and img.height>=400
      img.thumbnail((1600,1600),Image.Resampling.LANCZOS)
      dest_b=io.BytesIO()
      img.save(dest_b,"JPEG",quality=89,optimize=True,exif=b"")
      cooked=dest_b.getvalue()
    path=f"external-media/asteraceae/synonym-inat/{species}/inat-{p['id']}.jpg"
    dest=ROOT/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(cooked)
    new[path]={
      "source_git_blob_sha":hash_blob(cooked),
      "archive_sha256":hashlib.sha256(cooked).hexdigest(),
      "original_download_sha256":hashlib.sha256(raw).hexdigest(),
      "source_page":f"https://www.inaturalist.org/photos/{p['id']}",
      "observation_page":f"https://www.inaturalist.org/observations/{o['id']}",
      "original_download_url":u,
      "photo_id":p["id"],"observation_id":o["id"],
      "species_id":species,"accepted_name":s["accepted_taxon"],
      "observed_synonym":s["observed_taxon"],"observed_rank":s["rank"],
      "taxonomic_source":s["taxon_source"],
      "creator":credit,"license":"CC BY (iNaturalist current photo code)",
      "license_url":"https://creativecommons.org/licenses/by/4.0/",
      "noncommercial_only":False,
      "role":s["label"],
      "modified":"Resized and EXIF removed; no anatomy arrows added",
      "publication_approval":"STAGING_NEW_INAT_TAXONOMIC_SYNONYM_CC_VERIFIED; SPECIES_AND_PUBLIC_RELEASE_QA_PENDING"
    }
  d["status"]="VERIFIED_AND_STAGED";d["reason"]="TAXONOMIC_SYNONYM_PHOTO_LICENSE_ID_AND_ORIGINAL_VERIFIED"
 except Exception as e:
  d["reason"]=type(e).__name__+": "+str(e)[:200]
 decisions.append(d)
 print("FINAL_FOUR_SYNONYM_RECOVERY",species,d["status"],d["reason"],flush=True)
summary={
 "status":"EXACT_SYNONYM_ORIGINAL_SOURCE_CHECK_STAGING_ONLY",
 "candidates":3,"original_source_photos_recovered":len(originals),
 "new_external_cc_photos":len(new),"total_species_rescued":len(originals)+len(new),
 "remaining_species_without_photo":4-len(originals)-len(new),
 "taxonomic_synonyms_reviewed":{k:{"source_name":v["observed_taxon"],"accepted_name":v["accepted_taxon"],"authority_link":v["taxon_source"]} for k,v in source_data.items()},
 "decisions":decisions,"public_published":False}
m=ROOT/"migration"
(m/"asteraceae-last-four-original-photo-rights-ledger.json").write_text(json.dumps(originals,indent=2,ensure_ascii=False)+"\n")
(m/"asteraceae-last-four-new-synonym-cc-ledger.json").write_text(json.dumps(new,indent=2,ensure_ascii=False)+"\n")
(m/"asteraceae-last-four-taxonomic-photo-decisions.json").write_text(json.dumps(decisions,indent=2,ensure_ascii=False)+"\n")
(m/"asteraceae-last-four-taxonomic-photo-summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
print("FINAL_FOUR_SYNONYM_BACKFILL_SUMMARY",json.dumps(summary,sort_keys=True),flush=True)
