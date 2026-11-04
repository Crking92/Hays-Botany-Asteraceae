#!/usr/bin/env python3
"""Publish only exact-photo provider/API-verified Asteraceae records from remote manifest."""
import hashlib, io, json, pathlib, re, sys, time, urllib.request
from PIL import Image
manifest=json.load(open(sys.argv[1],encoding="utf8"))
site=pathlib.Path(sys.argv[2])
report=pathlib.Path(sys.argv[3])
assert manifest["batch_id"]=="asteraceae-005-2026-11-04"
assert manifest["repo"]=="Crking92/Hays-Botany-Asteraceae"
rows=manifest["photos"]
assert len(rows)<=50 and len({(r["observation_id"],r["photo_id"]) for r in rows})==len(rows)
catp=site/"data/collection-index.json"; galp=site/"data/gallery-index.json"
cat=json.loads(catp.read_text()); gal=json.loads(galp.read_text())
byid={r["id"]:r for r in cat["entries"]}
assert len(byid)==gal["species"]==180
assert gal["status"]=="ONLY_EXISTING_PUBLIC_RIGHTS_CLEARED_SITE_IMAGES"
assert all(r["species_id"] in byid for r in rows)
cache={}; added=[]; skipped=[]; held=[]; ready=[]
def get(url,limit=26*1024*1024):
 req=urllib.request.Request(url,headers={"User-Agent":"HaysBotanyPhotoVerifier/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=30) as response:
  if response.status!=200:raise ValueError("source HTTP error")
  data=response.read(limit+1)
  if len(data)>limit:raise ValueError("source too large")
  return data
def blob_sha(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
for r in rows:
 sid=r["species_id"];oid=int(r["observation_id"]);pid=int(r["photo_id"])
 try:
  if not re.fullmatch("[a-z0-9-]+",sid):raise ValueError("bad species slug")
  if not re.fullmatch("[a-f0-9]{64}",r["sha256"]):raise ValueError("bad source hash")
  if r["license"]!="CC BY 4.0":raise ValueError("license not approved for this release")
  url=r["photo_url"]
  if not re.fullmatch(r"https://inaturalist-open-data\.s3\.amazonaws\.com/photos/"+str(pid)+r"/original\.(?:jpg|jpeg)",url):raise ValueError("unexpected media source")
  if oid not in cache:
   response=json.loads(get("https://api.inaturalist.org/v1/observations/"+str(oid),3*1024*1024))
   if response.get("total_results")!=1 or len(response.get("results",[]))!=1:raise ValueError("observation API response missing")
   cache[oid]=response["results"][0]
   time.sleep(0.2)
  observation=cache[oid]
  actual=((observation.get("taxon") or {}).get("name") or "").lower().split()
  expected=r["scientific_name"].lower().split()
  if len(actual)<2 or actual[:2]!=expected[:2]:raise ValueError("observation taxon disagreement: "+str(actual))
  photo=next((p for p in observation.get("photos",[]) if int(p["id"])==pid),None)
  if not photo:raise ValueError("photo not linked to stated observation")
  if (photo.get("license_code") or "").lower()!="cc-by":raise ValueError("source photo license mismatch: "+str(photo.get("license_code")))
  attribution=(photo.get("attribution") or "").strip()
  if not attribution:raise ValueError("source photographer attribution absent")
  if r["photographer"].casefold() not in attribution.casefold():raise ValueError("photographer differs from original attribution: "+attribution[:100])
  cardp=site/"data/species"/(sid+".json");card=json.loads(cardp.read_text())
  if card["id"]!=sid:raise ValueError("site identity mismatch")
  photos=card.get("verified_photos",[])
  exact="https://www.inaturalist.org/photos/"+str(pid)
  if any(p.get("source_page")==exact or str(p.get("provider_photo_id"))==str(pid) for p in photos):
   skipped.append({"species_id":sid,"photo_id":pid,"reason":"already indexed"});continue
  raw=get(url)
  if hashlib.sha256(raw).hexdigest()!=r["sha256"]:raise ValueError("source image SHA differs from uploaded ZIP")
  if not 200<len(raw)<25*1024*1024:raise ValueError("bad image size")
  image=Image.open(io.BytesIO(raw));image.verify()
  image=Image.open(io.BytesIO(raw))
  if image.format!="JPEG" or image.width*image.height>80_000_000:raise ValueError("bad media encoding")
  sha=blob_sha(raw)
  if any(p.get("sha256")==r["sha256"] or p.get("source_blob_sha")==sha for p in photos):
   skipped.append({"species_id":sid,"photo_id":pid,"reason":"existing identical image"});continue
  dest=site/"media"/sid/("inat-"+str(pid)+"."+url.rsplit(".",1)[-1])
  if dest.exists():raise ValueError("media path already occupied")
  ready.append((r,cardp,card,dest,raw,sha,exact,attribution))
 except Exception as exc:
  held.append({"species_id":sid,"photo_id":pid,"reason":str(exc)[:250]})
# A given species may have several new images, so share one in-memory card.
cards={}
for r,cardp,card,dest,raw,sha,exact,attribution in ready:
 sid=r["species_id"]
 if sid not in cards:cards[sid]=card
 card=cards[sid]
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 card["verified_photos"].append({
  "src":"media/"+sid+"/"+dest.name,"creator":r["photographer"],
  "source_page":exact,"source_page_is_exact":True,
  "license":"CC BY 4.0","license_url":"https://creativecommons.org/licenses/by/4.0/",
  "source_blob_sha":sha,"sha256":r["sha256"],"role":"Species photograph",
  "modified":"Original source image; not altered","original_photo_url":r["photo_url"],
  "provider_photo_id":r["photo_id"],"provider_attribution":attribution,
  "noncommercial_only":False,"private_rights_review_only":False,
  "photo_approval_mode":"OWNER_STANDING_PHOTO_FIRST_POLICY",
  "photo_approved_by":"Owner standing policy, individually checked automated source record",
  "source_review_evidence":"Exact iNaturalist photo ID, license and attribution checked against API; downloaded bytes match supplied ZIP SHA-256",
  "taxon_review_evidence":"General-image contact sheet sanity check and exact observation taxon checked against site binomial"
 })
 card["photo_status"]="RELEASED_CC_GALLERY"
 added.append({"species_id":sid,"photo_id":r["photo_id"],"src":"media/"+sid+"/"+dest.name})
for sid,card in cards.items():
 (site/"data/species"/(sid+".json")).write_text(json.dumps(card,ensure_ascii=False,indent=2)+"\n")
if added:
 counts={}
 for row in cat["entries"]:
  sid=row["id"];card=json.loads((site/"data/species"/(sid+".json")).read_text())
  photos=card.get("verified_photos",[]);counts[sid]=len(photos)
  row["photo_count"]=len(photos)
  gal["entries"][sid]={"count":len(photos),"first_src":photos[0]["src"] if photos else None}
 gal["photo_count"]=sum(counts.values());gal["photo_species"]=sum(v>0 for v in counts.values())
 catp.write_text(json.dumps(cat,ensure_ascii=False,indent=2)+"\n")
 galp.write_text(json.dumps(gal,ensure_ascii=False,indent=2)+"\n")
report.parent.mkdir(parents=True,exist_ok=True)
report.write_text(json.dumps({"batch_id":manifest["batch_id"],"added":added,"skipped":skipped,"held":held,"published_source_count":len(added),"new_total":gal["photo_count"]},indent=2)+"\n")
print(report.read_text())
