#!/usr/bin/env python3
"""Audit exact names in Asteraceae photo metadata and matched source rights.

Read-only; report source entries, verified archive, held causes, attribution and
current label. Does not grant/modify usage rights or publish photos.
"""
import csv
import json
import re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=json.loads((ROOT/"data/collection-index.json").read_text())
commons=json.loads((ROOT/"migration/asteraceae-verified-commons-photo-ledger.json").read_text())
inat=json.loads((ROOT/"migration/asteraceae-verified-inat-photo-ledger.json").read_text())
assert index["authority"]=="STAGING_ONLY"
assert len(index["entries"])==180
full={**commons,**inat}
assert not (set(commons)&set(inat))
people={
 "joey_santore":re.compile(r"\bjoey\s+santore\b",re.I),
 "calvin_king":re.compile(r"\bcalvin\s+king\b",re.I),
 "glass_root_garden":re.compile(r"\bglass\s+root\s+garden\b",re.I)
}
matches={p:[] for p in people}
missing=[]
all_photos=0
for row in index["entries"]:
 path=Path(row["path"])
 doc=json.loads((ROOT/path).read_text())
 for photo in doc.get("images") or []:
  all_photos+=1
  name=str(photo.get("file") or "")
  rel=(str(path.parent/name) if name and not name.startswith(("http:","https:")) else "")
  fields={k:str(v) for k,v in photo.items() if k in {"creator","attribution","author","photographer","copyright","source_page","credit","file","license","source_recorded_photo_attribution_at_download"}}
  original=" ".join(fields.values())
  status="ARCHIVED_CC_COMMONS" if rel in commons else "ARCHIVED_INAT_EXACT_PHOTO_LICENSE" if rel in inat else "NOT_IN_STRICT_VERIFIED_ARCHIVE"
  rec=inat.get(rel) or commons.get(rel) or {}
  for who,pat in people.items():
   if pat.search(original) or pat.search(" ".join(str(v) for v in rec.values())):
    matches[who].append({"species":row["id"],"filename":name,"path":rel,
      "status":status,"license_label":photo.get("license"),"photo_id":photo.get("photo_id"),
      "observation_id":photo.get("observation_id"),"source":photo.get("source_page"),
      "archive_noncommercial":rec.get("noncommercial_only"),
      "upstream_attribution":rec.get("verified_attribution",""),
      "creator":photo.get("creator","")})
for path in (ROOT/"content/taxa/Asteraceae").rglob("*"):
 if path.suffix.lower() not in {".csv",".json",".txt"}:continue
 if path.name=="species.json":continue
 s=path.read_text(encoding="utf-8",errors="replace")
 for who,pat in people.items():
  for m in list(pat.finditer(s))[:8]:
   nearby=s[max(0,m.start()-80):min(len(s),m.end()+100)].replace("\n"," ")
   if not any(x.get("metadata_file")==str(path) and x.get("excerpt")==nearby for x in matches[who]):
    matches[who].append({"metadata_file":str(path),"excerpt":nearby,"status":"TEXT_REFERENCE_NEEDS_REVIEW"})
out={}
for who,items in matches.items():
 photo_rows=[x for x in items if "species" in x]
 out[who]={"photo_entries":len(photo_rows),
  "photos_archived":sum(x["status"].startswith("ARCHIVED_") for x in photo_rows),
  "photos_held":sum(x["status"]=="NOT_IN_STRICT_VERIFIED_ARCHIVE" for x in photo_rows),
  "archive_statuses":dict(Counter(x["status"] for x in photo_rows)),
  "species":len(set(x["species"] for x in photo_rows)),
  "metadata_mentions":sum("metadata_file" in x for x in items),
  "records":items}
overview={"species":len(index["entries"]),"photo_references":all_photos,
  "commons_verified":len(commons),"inat_verified":len(inat),
  "name_audit":out,
  "permission_note":"Named credits do not override CC BY-NC terms; separate written permission needed for use outside license scope. User-owned photos need user-provided attribution/permission and direct original verification."}
dest=ROOT/"qa-report"/"author-rights-audit"
dest.mkdir(parents=True,exist_ok=True)
(dest/"joey-calvin-asteraceae.json").write_text(json.dumps(overview,indent=2,ensure_ascii=False)+"\n")
print("ASTERACEAE_AUTHOR_AUDIT_SUMMARY",json.dumps({k:{x:v for x,v in val.items() if x!="records"} for k,val in out.items()},sort_keys=True),flush=True)
for k,val in out.items():
 if val["photos_held"]:
  print("HELD_NAMED_PHOTOS",k,json.dumps([x for x in val["records"] if x.get("status")=="NOT_IN_STRICT_VERIFIED_ARCHIVE"][:15]),flush=True)
print("ASTERACEAE_AUTHOR_AUDIT_DONE",len(index["entries"]),all_photos)
