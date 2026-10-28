#!/usr/bin/env python3
"""Independently verify original iNaturalist PHOTO licenses by exact observation/photo ID.

Private staging only. NC images are labeled NONCOMMERCIAL-ONLY and may not be
published on a commercial site. Source Git SHA verified before archive.
"""
import hashlib,json,re,subprocess,sys,time,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve()
SOURCE=Path(sys.argv[2]).resolve()
config=json.loads((ROOT/"config/collection.json").read_text())
assert config["publication"]["enabled"] is False
index=json.loads((ROOT/"data/collection-index.json").read_text())
assert index["authority"]=="STAGING_ONLY"
census=json.loads((ROOT/"migration/asteraceae-source-census.json").read_text())
assert len(index["entries"])==180
srcsha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=SOURCE,text=True).strip()
assert srcsha==census["source_commit_sha"]
assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()=="staging/asteraceae-metadata"
git_ledger={x["path"]:x for x in json.loads((ROOT/"migration/asteraceae-source-file-ledger.json").read_text())}
candidates=defaultdict(list)
report=[]
def lic_code(original):
    v=str(original or "").upper().replace("_","-").replace(" ","-")
    for code in ["CC-BY-NC-SA","CC-BY-NC","CC-BY-SA","CC-BY","CC0"]:
        if v==code or v.startswith(code+"-"):
            if code=="CC-BY" and ("-NC" in v or "-SA" in v):continue
            if code=="CC-BY-NC" and "-SA" in v:continue
            return code.lower()
    return None
def verified_credit(original,attribution):
    org=re.sub(r"\s+"," ",str(original or "").strip()).casefold()
    attr=re.sub(r"\s+"," ",str(attribution or "").strip()).casefold()
    if org.startswith("(c) "):org=org[4:].split(", some rights")[0].strip()
    return len(org)>=3 and org in attr
for row in index["entries"]:
    rel=row["path"]
    d=json.loads((ROOT/rel).read_text())
    for i,p in enumerate(d.get("images") or []):
        code=lic_code(p.get("license"))
        pid=str(p.get("photo_id") or "").strip()
        obs=str(p.get("observation_id") or "").strip()
        local=p.get("file","")
        path=rel.rsplit("/",1)[0]+"/"+local if local and not str(local).startswith(("https:","http:")) else ""
        r={"species":row["id"],"image_index":i,"original_path":path,"photo_id":pid,"observation_id":obs,
           "original_license":p.get("license",""),"original_creator":p.get("creator",""),
           "source_page":p.get("source_page",""),"role":p.get("role",""),
           "expected_license_code":code,"status":"HOLD","reason":""}
        if not path or path not in git_ledger:r["reason"]="NOT_ARCHIVED_SOURCE_PHOTO"
        elif not pid.isdigit() or not obs.isdigit():r["reason"]="NO_EXACT_OBSERVATION_AND_PHOTO_IDS"
        elif not code:r["reason"]="NOT_EXPLICIT_CC_LICENSE"
        elif "inaturalist.org" not in str(p.get("source_page","")) and "inaturalist" not in str(p.get("source_platform","")).lower():
            r["reason"]="NO_EXPLICIT_INAT_SOURCE"
        else:candidates[obs].append(r)
        report.append(r)
assert len(report)==census["recorded_image_references"]
obs_ids=sorted(candidates)
print("INAT_SOURCE_AUDIT_CANDIDATES",json.dumps({"observations":len(obs_ids),"references":sum(map(len,candidates.values()))}),flush=True)
QA=ROOT/"qa-report/inat-photo-archive";QA.mkdir(parents=True,exist_ok=True)
def fetch(obs):
    url=f"https://api.inaturalist.org/v1/observations/{obs}"
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"HaysBotanyVisualLearner/0.1 photo-specific copyright-verification"})
    with urllib.request.urlopen(req,timeout=30) as f:d=json.load(f)
    return (d.get("results") or [None])[0]
for i,obs in enumerate(obs_ids):
    result=None
    for attempt in range(3):
        try:
            result=fetch(obs)
            break
        except Exception as exc:
            time.sleep(0.8*(attempt+1))
    if not result:
        for r in candidates[obs]:r["reason"]="INAT_OBSERVATION_NOT_VERIFIABLE"
        continue
    photos={str(x.get("id")):x for x in result.get("photos") or []}
    for r in candidates[obs]:
        p=photos.get(r["photo_id"])
        if not p:r["reason"]="PHOTO_NOT_IN_EXACT_OBSERVATION";continue
        observed=str(p.get("license_code") or "").lower()
        attr=p.get("attribution","")
        r["current_photo_license_code"]=observed
        r["current_photo_attribution"]=attr
        if observed!=r["expected_license_code"]:
            r["reason"]="INAT_PHOTO_LICENSE_DOES_NOT_MATCH_SOURCE";continue
        if not verified_credit(r["original_creator"],attr):
            r["reason"]="PHOTO_CREATOR_NEEDS_MANUAL_REVIEW";continue
        r["status"]="VERIFIED_INAT_PHOTO_CC"
        r["reason"]="EXACT_OBSERVATION_PHOTO_ID_LICENSE_AND_CREATOR_MATCHED"
    if (i+1)%15==0:print("INAT_PROGRESS",i+1,"/",len(obs_ids),flush=True)
    time.sleep(0.35)
verified=[r for r in report if r["status"]=="VERIFIED_INAT_PHOTO_CC"]
print("INAT_PRE_ARCHIVE",len(verified),flush=True)
commons=json.loads((ROOT/"migration/asteraceae-verified-commons-photo-ledger.json").read_text())
new={}
for i,r in enumerate(verified):
    path=r["original_path"]
    if path in commons:continue
    blob=subprocess.run(["git","show","HEAD:"+path],cwd=SOURCE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
    sha=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
    assert sha==git_ledger[path]["git_blob_sha"],"Original file SHA mismatch: "+path
    dest=ROOT/path;dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(blob)
    license_name=r["original_license"]
    license_url={
       "cc-by-nc":"https://creativecommons.org/licenses/by-nc/4.0/",
       "cc-by-nc-sa":"https://creativecommons.org/licenses/by-nc-sa/4.0/",
       "cc-by-sa":"https://creativecommons.org/licenses/by-sa/4.0/",
       "cc-by":"https://creativecommons.org/licenses/by/4.0/",
       "cc0":"https://creativecommons.org/publicdomain/zero/1.0/"
    }[r["current_photo_license_code"]]
    new[path]={"source_git_blob_sha":sha,"source_page":r["source_page"],
               "photo_id":r["photo_id"],"observation_id":r["observation_id"],
               "creator":r["original_creator"],"verified_attribution":r["current_photo_attribution"],
               "license":license_name,"license_url":license_url,"license_code":r["current_photo_license_code"],
               "role":r["role"],"verified_via":"iNaturalist v1 observation detail PHOTO id/current photo license/attribution",
               "noncommercial_only":r["current_photo_license_code"] in {"cc-by-nc","cc-by-nc-sa"},
               "publication_approval":"PRIVATE_EDUCATIONAL_PREVIEW_ONLY; RECHECK NC SITE ELIGIBILITY BEFORE PUBLIC_RELEASE"}
    if (i+1)%20==0:print("INAT_ARCHIVED",i+1,flush=True)
state={"status":"INAT_EXACT_PHOTOS_VERIFIED_PRIVATE_ONLY","source_sha":srcsha,
       "candidate_observations":len(obs_ids),"verified_photo_references":len(verified),
       "physically_archived_images":len(new),
       "noncommercial_only_images":sum(v["noncommercial_only"] for v in new.values()),
       "held_reasons":dict(Counter(r["reason"] for r in report if r["status"]!="VERIFIED_INAT_PHOTO_CC")),
       "public_release_approval":False}
(ROOT/"migration/asteraceae-verified-inat-photo-ledger.json").write_text(json.dumps(new,indent=2,ensure_ascii=False)+"\n")
(ROOT/"migration/asteraceae-inat-photo-archive-summary.json").write_text(json.dumps(state,indent=2)+"\n")
(QA/"inat-photo-decisions.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
(QA/"summary.json").write_text(json.dumps(state,indent=2)+"\n")
print("INAT_ARCHIVE_RESULT",json.dumps(state,sort_keys=True),flush=True)
