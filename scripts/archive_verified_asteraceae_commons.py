#!/usr/bin/env python3
"""Independently check Commons CC licenses and archive eligible Asteraceae photo bytes.

Run on the PRIVATE 'staging/asteraceae-metadata' branch only. Fail closed.
No GitHub Pages or public release. No iNaturalist/NC/PD/unknown uploads.
"""
from __future__ import annotations
import hashlib, html, json, re, subprocess, sys, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(sys.argv[1]).resolve()
SOURCE=Path(sys.argv[2]).resolve()
QA=ROOT/"qa-report"/"commons-photo-archive"
QA.mkdir(parents=True,exist_ok=True)
assert ROOT.name=="Hays-Botany-Asteraceae"
config=json.loads((ROOT/"config/collection.json").read_text())
assert config["publication"]["enabled"] is False
assert config["planning_status"]=="STAGING_ONLY_NOT_AUTHORITATIVE"
index=json.loads((ROOT/"data/collection-index.json").read_text())
census=json.loads((ROOT/"migration/asteraceae-source-census.json").read_text())
ledger={r["path"]:r for r in json.loads((ROOT/"migration/asteraceae-source-file-ledger.json").read_text())}
assert len(index["entries"])==180 and census["physical_image_files"]==459
assert census["source_commit_sha"]==index["source_commit_sha"]
src_sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=SOURCE,text=True).strip()
assert src_sha==index["source_commit_sha"],f"Source moved: {src_sha}"
assert subprocess.check_output(["git","rev-parse","--abbrev-ref","HEAD"],text=True,cwd=ROOT).strip()=="staging/asteraceae-metadata"

def cc_license(raw):
    v=re.sub(r"[-_\s]+"," ",str(raw).upper()).strip()
    return v if re.fullmatch(r"(?:CC BY(?: SA)? [234]\.0|CC0 1\.0)",v) else None

def wiki_title(source_page):
    url=urllib.parse.urlparse(str(source_page))
    if url.scheme!="https" or url.netloc not in {"commons.wikimedia.org","www.commons.wikimedia.org"}:return None
    path=urllib.parse.unquote(url.path)
    if not path.startswith("/wiki/File:"):return None
    return path[len("/wiki/"):].replace("_"," ")

def auth_text(content):
    s=html.unescape(re.sub(r"<[^>]*>"," ",content or ""))
    return re.sub(r"\s+"," ",s).strip()

def meta_value(meta,key):
    v=meta.get(key,{})
    return v.get("value","") if isinstance(v,dict) else ""

queue={}
records=[]
for entry in index["entries"]:
    rel=entry["path"]
    doc=json.loads((ROOT/rel).read_text())
    for i,photo in enumerate(doc.get("images") or []):
        name=photo.get("file","")
        path=rel.rsplit("/",1)[0]+"/"+name if name and not name.startswith(("https:","http:")) else ""
        row={"species_id":entry["id"],"image_index":i,"file":name,"source_photo_path":path,
             "source_page":photo.get("source_page",""),"creator_original":photo.get("creator",""),
             "license_original":photo.get("license",""),"role":photo.get("role",""),
             "status":"HELD","reason":"","verified_license":"","verified_author":"","license_url":"",
             "source_blob_sha":ledger[path]["git_blob_sha"] if path in ledger else ""}
        records.append(row)
        license_code=cc_license(photo.get("license",""))
        title=wiki_title(photo.get("source_page",""))
        if not path or path not in ledger:
            row["reason"]="NONLOCAL_REFERENCE_OR_MISSING_SOURCE_PHOTO"
        elif not license_code:
            row["reason"]="NOT_CC_BY_SA_OR_CC0"
        elif not title:
            row["reason"]="NON_WIKIMEDIA_OR_UNRESOLVED_SOURCE_PAGE"
        else:
            row["candidate_title"]=title
            queue.setdefault(title,[]).append(row)
assert len(records)==census["recorded_image_references"]

def query_commons(titles):
    params=urllib.parse.urlencode({"action":"query","prop":"imageinfo","iiprop":"extmetadata|url",
          "format":"json","formatversion":2,"titles":"|".join(titles)})
    url="https://commons.wikimedia.org/w/api.php?"+params
    req=urllib.request.Request(url,headers={"User-Agent":"HaysBotanyPhotoRightsChecker/0.2 (noncommercial educational photo audit; github.com/Crking92/Hays-Botany-Asteraceae)","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=50) as response: data=json.load(response)
    return {p.get("title"):p for p in data.get("query",{}).get("pages",[])}

titles=sorted(queue)
for i in range(0,len(titles),10):
    block=titles[i:i+10]
    try:
        response=query_commons(block)
    except Exception as exc:
        for title in block:
            for row in queue[title]:row["reason"]="COMMONS_API_UNAVAILABLE_"+type(exc).__name__
        continue
    for title in block:
        page=response.get(title)
        if not page:
            for candidate_title,p in response.items():
                if candidate_title.casefold()==title.casefold():
                    page=p;break
        for row in queue[title]:
            if not page or page.get("missing") or not page.get("imageinfo"):
                row["reason"]="COMMONS_FILE_NOT_FOUND";continue
            meta=page["imageinfo"][0].get("extmetadata",{})
            lic=cc_license(meta_value(meta,"LicenseShortName"))
            want=cc_license(row["license_original"])
            lic_url=meta_value(meta,"LicenseUrl")
            artist=auth_text(meta_value(meta,"Artist"))
            creator=auth_text(row["creator_original"])
            row["verified_license"]=lic or meta_value(meta,"LicenseShortName")
            row["verified_author"]=artist[:700]
            row["license_url"]=lic_url
            if not lic or lic!=want:
                row["reason"]="SOURCE_LICENSE_DIFFERS_OR_NOT_CC";continue
            if not lic_url.startswith("https://creativecommons.org/") and "creativecommons.org" not in lic_url:
                row["reason"]="NO_TRUSTED_CC_LICENSE_URL";continue
            # Automated credit checks should be conservative. Distinct credit can
            # be verified manually; don't silently overwrite the creator.
            if creator and creator.casefold() not in artist.casefold():
                row["reason"]="SOURCE_CREATOR_NEEDS_REVIEW";continue
            row["status"]="SOURCE_VERIFIED_CC"
            row["reason"]="EXACT_COMMONS_FILE_CC_METADATA_AND_CREATOR_MATCHED"
    print("COMMONS_PROGRESS",min(i+len(block),len(titles)),"/",len(titles),flush=True)

verified=[r for r in records if r["status"]=="SOURCE_VERIFIED_CC"]
paths=sorted({r["source_photo_path"] for r in verified})
assert all(p in ledger for p in paths)
print("PRE_ARCHIVE",json.dumps({"total_photo_references":len(records),"candidate_commons_pages":len(titles),"verified_photo_references":len(verified),"verified_distinct_files":len(paths)}),flush=True)
for j,path in enumerate(paths):
    blob=subprocess.run(["git","show",f"HEAD:{path}"],cwd=SOURCE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
    actual_sha=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
    assert actual_sha==ledger[path]["git_blob_sha"],"Source Git photo SHA drift: "+path
    dest=ROOT/path
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(blob)
    if (j+1)%20==0: print("COPIED",j+1,"/",len(paths),flush=True)
for row in verified:
    row["archived"]=True
    row["source_blob_verified"]=True

safe={r["source_photo_path"]:{"source_git_blob_sha":r["source_blob_sha"],
    "source_page":r["source_page"],"license":r["verified_license"],
    "license_url":r["license_url"],"creator":r["creator_original"],"original_author_upstream":r["verified_author"],
    "role":r["role"],"verified_via":"Wikimedia Commons imageinfo/extmetadata exact File page",
    "publication_approval":"STAGING_IMAGE_ONLY; PUBLIC_SNAPSHOT_REQUIRES_RELEASE_REVIEW"}
    for r in verified}
result={"status":"PRIVATE_CC_PHOTOS_ARCHIVED_NOT_PUBLISHED","source_commit":src_sha,
    "total_photo_references":len(records),"verified_cc_photo_references":len(verified),
    "physically_archived_cc_images":len(paths),"held_references":len(records)-len(verified),
    "held_reasons":dict(Counter(r["reason"] for r in records if r["status"]!="SOURCE_VERIFIED_CC")),
    "approved_license_breakdown":dict(Counter(r["verified_license"] for r in verified)),
    "source_photos_total":census["physical_image_files"],"public_website_live":False}
(ROOT/"migration/asteraceae-verified-commons-photo-ledger.json").write_text(json.dumps(safe,indent=2,ensure_ascii=False)+"\n")
(ROOT/"migration/asteraceae-photo-archive-summary.json").write_text(json.dumps(result,indent=2)+"\n")
(QA/"all-source-image-rights-decisions.json").write_text(json.dumps(records,indent=2,ensure_ascii=False)+"\n")
(QA/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
print("ARCHIVE_RESULT",json.dumps(result,sort_keys=True),flush=True)
