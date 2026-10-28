#!/usr/bin/env python3
"""Stage original Calvin King and held Joey Santore photo references FOR PRIVATE REVIEW.

Source Git blobs checked byte exact. Does NOT relicense author works or approve
public site reuse; Calvin permission is recorded from owner instruction in chat,
Joey CC BY-NC is a source claim until independently reverified.
"""
import hashlib,json,re,subprocess,sys
from collections import Counter
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve()
SRC=Path(sys.argv[2]).resolve()
idx=json.loads((ROOT/"data/collection-index.json").read_text())
assert idx["authority"]=="STAGING_ONLY" and len(idx["entries"])==180
cfg=json.loads((ROOT/"config/collection.json").read_text())
assert cfg["publication"]["enabled"] is False
sha=idx["source_commit_sha"]
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=SRC,text=True).strip()==sha
assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()=="staging/asteraceae-metadata"
files={x["path"]:x for x in json.loads((ROOT/"migration/asteraceae-source-file-ledger.json").read_text())}
commons=json.loads((ROOT/"migration/asteraceae-verified-commons-photo-ledger.json").read_text())
inat=json.loads((ROOT/"migration/asteraceae-verified-inat-photo-ledger.json").read_text())
existing=set(commons)|set(inat)
new={}
found=Counter()
skipped=Counter()
for row in idx["entries"]:
    p=Path(row["path"])
    doc=json.loads((ROOT/p).read_text())
    for photo in doc.get("images") or []:
        creator=str(photo.get("creator",""))
        who="Calvin King" if re.search(r"\bCalvin\s+King\b",creator,re.I) else "Joey Santore" if re.search(r"\bJoey\s+Santore\b",creator,re.I) else None
        if who is None:continue
        found[who]+=1
        name=str(photo.get("file",""))
        rel=(p.parent/name).as_posix() if name and not name.startswith(("http:","https:")) else ""
        if rel in existing:
            skipped[who+" already independently verified"]+=1
            continue
        if rel not in files:
            skipped[who+" missing source file"]+=1
            continue
        source=str(photo.get("source_page",""))
        exact_photo_source=bool(re.fullmatch(r"https://www\.inaturalist\.org/photos/\d+",source))
        if not exact_photo_source and who=="Calvin King":
            skipped[who+" no exact photo source"]+=1
            continue
        if not exact_photo_source and not (
            "inaturalist.org" in source.lower()
            or re.search(r"(?:inat-|joey-)",name,re.I)
        ):
            skipped[who+" missing iNaturalist provenance"]+=1
            continue
        lic=str(photo.get("license",""))
        if who=="Joey Santore":
            if "CC BY-NC" not in lic.upper() and "CC-BY-NC" not in lic.upper():
                skipped["Joey requires manual license review"]+=1
                continue
            rights="SOURCE_RECORD_CC_BY_NC_PENDING_CURRENT_PHOTO_RECHECK"
            attribution="Joey Santore"
            license_label="CC BY-NC (source record; current photo license not rechecked)"
            license_url="https://creativecommons.org/licenses/by-nc/4.0/"
            permission="CC BY-NC claimed by pinned original source; photographer credit and noncommercial conditions required. Current individual photo license not independently rechecked." + (" Original source reference is not the exact photo page and must be reconciled before public publication." if not exact_photo_source else "")
        else:
            if "All rights reserved" not in lic:
                skipped["Calvin unusual source license"]+=1
                continue
            rights="OWNER_GRANTED_HAYS_BOTANY_REUSE_WITH_CREDIT_2026_10_28"
            attribution="Calvin King"
            license_label="Used with Calvin King's permission for Hays Botany; credit required"
            license_url=""
            permission="Owner explicitly authorizes Hays Botany project reuse with Calvin King attribution in conversation Oct 28 2026. Original iNaturalist photo remains all-rights-reserved, not CC licensed."
        raw=subprocess.run(["git","show","HEAD:"+rel],cwd=SRC,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        assert actual==files[rel]["git_blob_sha"],"Source original changed: "+rel
        dest=ROOT/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(raw)
        new[rel]={
          "source_git_blob_sha":actual,
          "creator":attribution,
          "license":license_label,
          "license_url":license_url,
          "source_page":source,
          "source_page_verified":exact_photo_source,
          "role":photo.get("role",""),
          "source_metadata_license":lic,
          "status":rights,
          "permission_basis":permission,
          "noncommercial_only":who=="Joey Santore",
          "public_website_approval":False,
          "private_review_only":True,
          "publication_approval":"PRIVATE_EDUCATIONAL_PREVIEW_ONLY; source rights gate before public release"
        }
counts=Counter(v["creator"] for v in new.values())
assert found["Calvin King"]==6,f"Unexpected Calvin source count {found}"
assert found["Joey Santore"]==76,f"Unexpected Joey source count {found}"
assert counts["Calvin King"]==6,f"Calvin image import incomplete {counts}"
assert 0<=counts["Joey Santore"]<=35,f"Unexpected Joey source count {counts}"
assert len(new)==counts["Calvin King"]+counts["Joey Santore"]
(ROOT/"migration/asteraceae-author-permitted-private-photo-ledger.json").write_text(json.dumps(new,indent=2,ensure_ascii=False)+"\n")
summary={"status":"PRIVATE_REVIEW_ONLY_NOT_PUBLIC_RIGHTS_APPROVED","source_commit":sha,
    "source_named_photo_references":dict(found),"already_independently_verified":dict(skipped),
    "newly_staged_calvin_author_permission":counts["Calvin King"],
    "newly_staged_joey_source_cc_by_nc_claim":counts["Joey Santore"],
    "newly_added_originals":len(new),"public_release_approval":False,
    "joey_missing_exact_photo_page_in_private_review":sum(v["creator"]=="Joey Santore" and not v["source_page_verified"] for v in new.values()),
    "additional_held_reasons":dict(skipped),
    "joey_source_photo_references_still_held":found["Joey Santore"]-skipped["Joey Santore already independently verified"]-counts["Joey Santore"]}
(ROOT/"migration/asteraceae-author-photo-additions-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("AUTHOR_PHOTO_IMPORT",json.dumps(summary,sort_keys=True),flush=True)
