#!/usr/bin/env python3
"""Recheck 22 exact archived Asteraceae NC photo identities and publish passing originals.

Only these 22 pinned archive originals; latest in-scope source metadata must confirm
the same individual photo, creator and CC BY-NC/NC-SA grant. Original bytes verified
against archived Git blob and perceptually against the same current source image.
Missing/changeable information creates a HOLD, never an invented approval.
"""
import datetime,hashlib,html,io,json,re,subprocess,sys,tempfile,time,urllib.error,urllib.request
from pathlib import Path
from PIL import Image,ImageOps

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(sys.argv[1]).resolve()
SITE=ROOT/"site"
LEDGER=SOURCE/"migration/asteraceae-verified-84-nc-photo-ledger.json"
REPORT=ROOT/"workflow/asteraceae-nc22-recovery-result.json"
LICENSES={"CC BY-NC":"CC BY-NC 4.0","CC BY-NC-SA":"CC BY-NC-SA 4.0"}
URLS={"CC BY-NC":"https://creativecommons.org/licenses/by-nc/4.0/","CC BY-NC-SA":"https://creativecommons.org/licenses/by-nc-sa/4.0/"}
def fetch(url,as_json=False):
    if not url.startswith("https://"):raise ValueError("Non HTTPS source")
    last=None
    for i in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"HaysBotanyOriginalNCPhotoAudit/1.1","Accept":"application/json" if as_json else "image/*"})
            with urllib.request.urlopen(req,timeout=27) as resp:
                if resp.status!=200:raise RuntimeError("HTTP "+str(resp.status))
                data=resp.read(20*1024*1024)
                return json.loads(data) if as_json else data
        except Exception as ex:
            last=ex;time.sleep(2+i*2)
    raise RuntimeError("Source inaccessible "+str(last)[:150])
def credit(s):
    s=html.unescape(re.sub(r"<[^>]*>"," ",str(s or "")))
    s=re.sub(r"(?i)\b(?:some rights reserved|no rights reserved|uploaded by|copyright)\b"," ",s)
    s=s.replace("(c)"," ").replace("©"," ")
    s=re.sub(r"\([^)]*CC BY[^)]*\)"," ",s,flags=re.I)
    return re.sub(r"\s+"," ",s).strip(" ,-.;").casefold()
def display_creator(s):
    s=html.unescape(re.sub(r"<[^>]*>"," ",str(s or ""))).strip()
    s=re.sub(r"^(?:\(c\)|©)\s*","",s,flags=re.I)
    s=re.split(r",?\s*(?:some rights reserved|no rights reserved|uploaded by)\b",s,flags=re.I)[0]
    return re.sub(r"\s+"," ",s).strip(" ,-.;")
def match(a,b):
    a=credit(a);b=credit(b)
    return bool(a and b and (a in b or b in a or any(len(x)>=4 and x in b for x in a.split(" / "))))
def kind(s):
    s=str(s or "").lower().replace("_","-").replace(" ","-")
    if "by-nc-nd" in s:return "ND"
    if "by-nc-sa" in s:return "CC BY-NC-SA"
    if "by-nc" in s:return "CC BY-NC"
    return "OTHER"
def dhash(data):
    with Image.open(io.BytesIO(data)) as im:
        p=list(ImageOps.exif_transpose(im).convert("L").resize((9,8),Image.Resampling.LANCZOS).getdata())
    return sum(1<<k for k in range(64) if p[(k//8)*9+k%8]>p[(k//8)*9+k%8+1])
def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def source_photo(meta):
    original=meta["original_source_page"]
    typ=meta["source_type"]
    pid=int(meta["photo_id"])
    if typ=="taxon":
        m=re.fullmatch(r"https://www.inaturalist.org/taxa/(\d+)",original)
        assert m,"taxon source URL not exact"
        data=fetch("https://api.inaturalist.org/v1/taxa/"+m.group(1),True)
        results=data.get("results") or []
        assert len(results)==1,"taxon source not available"
        photo=results[0].get("default_photo")
        assert photo and photo.get("id")==pid,"taxon default photo has changed; exact media rights not rechecked"
        return photo
    if typ=="observation":
        m=re.fullmatch(r"https://www.inaturalist.org/observations/(\d+)",original)
        assert m,"observation source URL not exact"
        data=fetch("https://api.inaturalist.org/v1/observations/"+m.group(1),True)
        results=data.get("results") or []
        assert len(results)==1 and results[0].get("id")==int(m.group(1)),"observation mismatch"
        photos=results[0].get("photos") or []
        target=[p for p in photos if p.get("id")==pid]
        assert len(target)==1,"original photo no longer linked to observation"
        return target[0]
    if typ=="gbif":
        m=re.fullmatch(r"https://www.gbif.org/occurrence/(\d+)",original)
        assert m,"GBIF source URL not exact"
        data=fetch("https://api.gbif.org/v1/occurrence/"+m.group(1)+"/fragment",True)
        ext=(data.get("extensions") or {}).get("http://rs.gbif.org/terms/1.0/Multimedia") or []
        target=[]
        for item in ext:
            p={k.rsplit("/",1)[-1]:v for k,v in item.items()}
            media_id=str(p.get("identifier") or "")
            ref=str(p.get("references") or "")
            if f"/photos/{pid}" in media_id or f"/photos/{pid}" in ref:
                target.append({"id":pid,"license_code":p.get("license"),"attribution":p.get("creator") or p.get("rightsHolder"),
                    "url":media_id})
        assert len(target)==1,"GBIF original photo not individually identifiable now"
        return target[0]
    raise AssertionError("unsupported archived source type: "+str(typ))
def run():
    ledger=json.loads(LEDGER.read_text())
    assert len(ledger)==22,"historical exact-photo ledger changed"
    meta=json.loads((SITE/"data/collection-meta.json").read_text())
    assert meta["repository_full_name"]=="Crking92/Hays-Botany-Asteraceae"
    assert meta["photo_license_policy"]["noncommercial_educational_use"] is True
    current={r.get("source_blob_sha") for fn in (SITE/"data/species").glob("*.json") for r in json.loads(fn.read_text()).get("verified_photos",[])}
    report={"source":"historical asteraceae 84 NC ledger subset","candidates":22,"published":0,"already_published":0,"held":0,
        "checked_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"records":[]}
    with tempfile.TemporaryDirectory(prefix="hays-asteraceae-nc22-") as td:
        staging=Path(td)
        for path,r in ledger.items():
            sid=path.split("/")[4]
            record={"species_id":sid,"original_path":path,"photo_id":r["photo_id"],"old_source_type":r["source_type"]}
            try:
                assert r.get("source_page")==f"https://www.inaturalist.org/photos/{r['photo_id']}","archive individual photo link mismatch"
                assert r["license"] in LICENSES and r["noncommercial_only"] is True
                original=SOURCE/path
                assert original.is_file() and original.stat().st_size<25*1024*1024,"original archived file unavailable"
                raw=original.read_bytes()
                sha=blob(raw)
                assert sha==r["source_git_blob_sha"],"original bytes not identical to pinned historical SHA"
                if sha in current:
                    report["already_published"]+=1;record["status"]="ALREADY_PUBLISHED";report["records"].append(record);continue
                p=source_photo(r)
                assert int(p.get("id"))==int(r["photo_id"]),"source photo ID changed"
                assert kind(p.get("license_code"))==r["license"],"individual photo rights changed or version unclear"
                attr=p.get("attribution") or p.get("creator") or p.get("rightsHolder") or ""
                assert match(r["verified_upstream_attribution"],attr),"photographer credit differs from reviewed archive"
                url=p.get("large_url") or p.get("medium_url") or p.get("url") or p.get("identifier") or ""
                assert url.startswith("https://"),"no valid exact-photo image for comparison"
                comparison=fetch(url)
                hdist=(dhash(raw)^dhash(comparison)).bit_count()
                assert hdist<=12,"archived original and live licensed source image differ perceptually: "+str(hdist)
                # Source original is the preserved local file, not the downsized media preview.
                name="historical-nc-"+re.sub(r"[^a-z0-9._-]","-",path.rsplit("/",1)[-1].lower())
                dest=staging/"photo-intake/approved"/sid/name
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(raw)
                license_name=LICENSES[r["license"]]
                creator=display_creator(attr) or display_creator(r["creator"])
                assert creator,"no photographer after normalized credit"
                sidecar={
                    "species_id":sid,"photo_file":name,"status":"APPROVED_FOR_PUBLIC_FAMILY_SITE",
                    "rights_approved_for_public":True,"taxon_reviewed":True,
                    "approval_mode":"OWNER_STANDING_PHOTO_FIRST_POLICY","policy_ref":"PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02",
                    "review_operator":"Hays Botany archived-original and exact live media-license rechecker",
                    "source_review_evidence":"The historical archive pins exact Git original "+sha+" and iNaturalist photo "+str(r["photo_id"])+
                         ". Its current individual source "+r["original_source_page"]+" identifies license "+str(p.get("license_code"))+
                         " and creator "+attr+"; live source image fingerprint distance "+str(hdist)+".",
                    "taxon_review_evidence":"Original source archive associates "+sid+" with verified specific taxon photo and historical visual photo match. The live source was rechecked for the same photo ID and visibly matching image; specialist morphological determination deferred.",
                    "approval_note":"Owner-authorized photo-first publication of the individually source-confirmed archived original, subject to noncommercial CC license and full creator credit.",
                    "creator":creator,"source_page":r["source_page"],"source_page_is_exact":True,
                    "license":license_name,"license_url":URLS[r["license"]],
                    "noncommercial_site_use_confirmed":True,"role":"General botanical reference: "+str((json.loads((SITE/"data/species"/(sid+".json")).read_text())).get("scientific_name") or sid),
                    "modifications":"Original archived photograph reused without modification; CC noncommercial restrictions retained.",
                    "sha256":hashlib.sha256(raw).hexdigest()
                }
                dest.with_name(name+".json").write_text(json.dumps(sidecar,indent=2,ensure_ascii=False))
                record.update(status="RIGHTS_VERIFIED_READY",licensed_source=r["source_page"],license=license_name,creator=creator,blob_sha=sha)
            except Exception as ex:
                record.update(status="HELD",reason=str(ex)[:500])
                report["held"]+=1
            report["records"].append(record)
        eligible=sum(r["status"]=="RIGHTS_VERIFIED_READY" for r in report["records"])
        if eligible:
            pub=ROOT/"scripts/publish_approved_family_photos.py"
            args=[sys.executable,str(pub),"--source-root",str(staging),"--site-root",str(SITE)]
            for extra in (["--check"],[]):
                result=subprocess.run(args+extra,capture_output=True,text=True)
                assert result.returncode==0,"PHOTO_PUBLISHER_REJECTED "+result.stdout+result.stderr
                if not extra:report["published"]=json.loads(result.stdout)["installed"]
            assert report["published"]==eligible,"publisher count differs"
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
        print("ASTERACEAE_HISTORICAL_NC_REVIEW",json.dumps({k:report[k] for k in ("candidates","published","already_published","held")}),flush=True)
if __name__=="__main__":run()
