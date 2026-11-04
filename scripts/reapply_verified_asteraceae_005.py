#!/usr/bin/env python3
"""Reapply only source-verified Asteraceae 005 originals after concurrent main writes.

The archive is an ephemeral, runner-local copy of originals already checked by the
photo-specific iNaturalist verifier in this SAME workflow run. It is never pushed
to GitHub. On retry, it merges these exact images and credits into current main
without replaying provider downloads or overwriting parallel gallery work.
"""
import argparse, hashlib, json, pathlib, re, shutil, sys

def fail(m): raise SystemExit("ASTER005_SAFE_MERGE_BLOCKED: "+str(m))
def load(p):return json.loads(pathlib.Path(p).read_text(encoding="utf8"))
def save(p,v):pathlib.Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def valid(root,sid,photo,record,bytes_):
    pid=int(record["photo_id"])
    src=photo.get("src","")
    if not re.fullmatch(r"media/[a-z0-9-]+/inat-\d+\.(?:jpg|jpeg)",src):fail("unexpected media path")
    if not src.startswith("media/"+sid+"/") or not src.rsplit("/",1)[-1].startswith("inat-"+str(pid)+"."):fail("wrong taxon/media file")
    if not photo.get("creator") or photo.get("source_page")!="https://www.inaturalist.org/photos/"+str(pid):fail("source/creator mismatch")
    if photo.get("license")!=record["license"]:fail("license differs from verified original")
    if photo.get("sha256")!=record["sha256"] or hashlib.sha256(bytes_).hexdigest()!=record["sha256"]:fail("original SHA256 mismatch")
    if photo.get("source_blob_sha")!=blob(bytes_):fail("original Git blob SHA mismatch")
    if photo.get("private_rights_review_only") or photo.get("noncommercial_only")!=(record["license"]=="CC BY-NC 4.0"):fail("rights flag mismatch")
    if photo.get("photo_approved_by")!="Owner standing policy, individually checked automated source record":fail("media was not checked by this workflow")
    if not photo.get("source_review_evidence") or not photo.get("taxon_review_evidence"):fail("missing photo review evidence")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("operation",choices=("archive","restore"))
    ap.add_argument("manifest",type=pathlib.Path)
    ap.add_argument("site",type=pathlib.Path)
    ap.add_argument("cache",type=pathlib.Path)
    a=ap.parse_args()
    m=load(a.manifest)
    if m.get("batch_id")!="asteraceae-005-2026-11-04":fail("wrong photo batch")
    records={int(x["photo_id"]):x for x in m["photos"]}
    if len(records)!=len(m["photos"]) or len(records)>160:fail("bad photo manifest")
    if not a.site.joinpath("data/gallery-index.json").is_file():fail("site is missing")
    site=a.site.resolve();cache=a.cache.resolve()
    if a.operation=="archive":
        if cache.exists():fail("refusing to overwrite a prior cache")
        approved=[]
        for cardpath in sorted((site/"data/species").glob("*.json")):
            card=load(cardpath);sid=card["id"]
            for photo in card.get("verified_photos",[]):
                pid=photo.get("provider_photo_id")
                if pid is None or int(pid) not in records:continue
                record=records[int(pid)]
                if sid!=record["species_id"]:fail("candidate assigned to another species")
                path=site/photo["src"]
                if not path.is_file():fail("verified media file missing")
                raw=path.read_bytes()
                valid(site,sid,photo,record,raw)
                cachepath=cache/photo["src"]
                cachepath.parent.mkdir(parents=True,exist_ok=True)
                cachepath.write_bytes(raw)
                approved.append({"species_id":sid,"photo_id":int(pid),"photo":photo})
        if not approved:fail("no checked images to archive")
        if len(approved)!=len({x["photo_id"] for x in approved}):fail("duplicate original archive ID")
        save(cache/"approved.json",{"batch":m["batch_id"],"photos":approved})
        print("ASTER005_SOURCE_APPROVED_CACHE_READY",len(approved),flush=True)
        return
    if not cache.joinpath("approved.json").is_file():fail("missing verified image cache")
    approved=load(cache/"approved.json")
    if approved.get("batch")!=m["batch_id"]:fail("wrong verified cache")
    catalogpath=site/"data/collection-index.json";gallerypath=site/"data/gallery-index.json"
    catalog=load(catalogpath);gallery=load(gallerypath)
    byid={x["id"]:x for x in catalog["entries"]}
    if len(byid)!=gallery["species"] or len(byid)!=180:fail("site inventory changed")
    if gallery.get("status")!="ONLY_EXISTING_PUBLIC_RIGHTS_CLEARED_SITE_IMAGES":fail("rights status changed")
    meta=load(site/"data/collection-meta.json")
    if meta["repository_full_name"]!="Crking92/Hays-Botany-Asteraceae":fail("wrong gallery")
    if any(x["photo"]["noncommercial_only"] for x in approved["photos"]) and meta["photo_license_policy"].get("noncommercial_educational_use") is not True:
        fail("NC site use not confirmed")
    cards={}
    added=0;already=0
    for row in approved["photos"]:
        sid=row["species_id"];pid=int(row["photo_id"]);photo=row["photo"]
        if pid not in records or sid!=records[pid]["species_id"] or sid not in byid:fail("source taxon not indexed")
        cached=cache/photo["src"]
        if not cached.is_file():fail("cached source original missing")
        raw=cached.read_bytes()
        valid(site,sid,photo,records[pid],raw)
        if sid not in cards:cards[sid]=load(site/"data/species"/(sid+".json"))
        card=cards[sid]
        photos=card.get("verified_photos",[])
        existing=[x for x in photos if x.get("source_page")==photo["source_page"] or x.get("sha256")==photo["sha256"]]
        if existing:
            if any(x.get("creator")!=photo["creator"] or x.get("license")!=photo["license"] for x in existing):fail("existing source credit differs")
            already+=1;continue
        dest=site/photo["src"]
        if dest.exists() and dest.read_bytes()!=raw:fail("public media path collision")
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(raw)
        photos.append(photo)
        card["photo_status"]="RELEASED_CC_GALLERY"
        added+=1
    for sid,card in cards.items():save(site/"data/species"/(sid+".json"),card)
    totals={}
    for row in catalog["entries"]:
        sid=row["id"]
        card=cards.get(sid)
        if card is None:card=load(site/"data/species"/(sid+".json"))
        photos=card.get("verified_photos",[])
        row["photo_count"]=len(photos)
        totals[sid]=len(photos)
        gallery["entries"][sid]={"count":len(photos),"first_src":photos[0]["src"] if photos else None}
    gallery["photo_count"]=sum(totals.values())
    gallery["photo_species"]=sum(x>0 for x in totals.values())
    save(catalogpath,catalog);save(gallerypath,gallery)
    print("ASTER005_SAFE_MERGE_COMPLETE",json.dumps({"new":added,"already":already,"site_photos":gallery["photo_count"],"photo_species":gallery["photo_species"]}),flush=True)
if __name__=="__main__":main()
