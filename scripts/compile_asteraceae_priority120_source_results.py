#!/usr/bin/env python3
"""Permanent per-file closeout of original 120 Asteraceae upstream rights candidates.

Review source records remain in repo; temporary GitHub Actions artifacts are
transcribed before expiry. No media bytes moved by this report.
"""
import csv, json, re, sys
from collections import Counter
from pathlib import Path

MAIN=Path(sys.argv[1]).resolve()
STAGE=Path(sys.argv[2]).resolve()
REVIEWS=Path(sys.argv[3]).resolve()
batch=json.loads((MAIN/"planning/asteraceae-priority120-source-baseline.json").read_text())
assert batch["candidate_count"]==120
assert batch["pinned_source_sha"]=="034f385e44cec18e8c29be96f83e22aaf78fe3f3"
source=json.loads((STAGE/"migration/asteraceae-full-image-asset-reconciliation.json").read_text())
full={r["source_path"]:r for r in source}
commons=json.loads((STAGE/"migration/asteraceae-upstream-commons-120-ledger.json").read_text())
inat=json.loads((STAGE/"migration/asteraceae-upstream-inat-taxon-120-ledger.json").read_text())
gbif=json.loads((STAGE/"migration/asteraceae-upstream-gbif-120-ledger.json").read_text())
assert not (set(commons)&set(inat) or set(commons)&set(gbif) or set(inat)&set(gbif))
new={**commons,**inat,**gbif}
assert len(new)==len(set(new))
def from_file(p,kind):
 if not p.is_file():raise AssertionError(f"Missing permanent review detail for {kind}: {p}")
 return json.loads(p.read_text())
commons_checks=from_file(REVIEWS/"commons"/"all-40-commons-source-checks.json","Commons")
inat_checks=from_file(REVIEWS/"inat"/"all-19-inat-taxon-image-rights.json","iNaturalist taxon")
gbif_checks=from_file(STAGE/"migration/asteraceae-upstream-gbif-120-all-decisions.json","GBIF")
assert len(commons_checks)==40 and len(inat_checks)==9 and len(gbif_checks)==58
checks={}
for source_name,cases,key in [
 ("commons",commons_checks,"source_path"),("inat_taxon",inat_checks,"path"),("gbif",gbif_checks,"source_path")
]:
 for case in cases:
  p=case[key]
  assert p not in checks,"Duplicate source check"
  checks[p]={"verification_source":source_name,"source_status":case.get("status") or case.get("state"),
    "source_reason":case.get("reason"),"source_license_current":case.get("license") or case.get("current_license") or case.get("verified_license"),
    "source_photo_id":case.get("current_photo_id") or "",
    "source_visual_distance":case.get("visual_dhash_distance") if "visual_dhash_distance" in case else case.get("verified_dhash_distance",case.get("closest_dhash_distance")),
    "source_artist_current":case.get("artist_current") or case.get("current_credit") or case.get("verified_media_creator") or ""}
rows=[]
for b in batch["items"]:
 p=b["source_path"];current=full.get(p)
 assert current and current["source_git_blob_sha"]==b["source_git_blob_sha"]
 u=b["source_metadata"][0]["source_page"] if b["source_metadata"] else ""
 host=re.match(r"https?://([^/]+)",u)
 host=host.group(1) if host else "unknown"
 rec=checks.get(p,{})
 verified=p in new
 if verified:
  assert current["archived_in_private_staging"],"New verified image absent in source-file staging ledger: "+p
  decision="MIGRATED_PRIVATE_SOURCE_VERIFIED; PUBLIC_RIGHTS_GATE_PENDING"
  reason=rec.get("source_reason","SOURCE_VERIFIED")
 elif host=="www.gbif.org":
  decision="HELD_UPSTREAM_GBIF_MEDIA_RIGHTS_OR_IMAGE_MISMATCH"
  reason=rec.get("source_reason","GBIF_SOURCE_CHECK_NOT_AVAILABLE")
 elif host=="commons.wikimedia.org":
  decision="HELD_COMMONS_CREATOR_LICENSE_OR_IMAGE_NEEDS_MANUAL_REVIEW"
  reason=rec.get("source_reason","COMMONS_SOURCE_CHECK_INCOMPLETE")
 elif host=="www.inaturalist.org":
  decision="HELD_INAT_EXACT_PHOTO_OR_LICENSE_RECHECK"
  reason=rec.get("source_reason","SOURCE_IS_EXACT_PHOTO_OR_GUIDE_URL_WITHOUT_VALID_INDIVIDUAL_LICENSE_CONFIRMATION")
 else:
  decision="HELD_OTHER_SOURCE_RIGHTS_UNVERIFIED"
  reason="Source page or publisher permission to reuse this exact image not independently documented"
 if not verified and current["archived_in_private_staging"]:
  raise AssertionError("Non-new candidate already staged under another ledger: "+p)
 rows.append({
  "source_path":p,"pinned_git_blob_sha":b["source_git_blob_sha"],
  "source_page":u,"source_host":host,
  "source_creator_claim":b["source_metadata"][0].get("creator","") if b["source_metadata"] else "",
  "source_license_claim":b["source_metadata"][0].get("license_claim","") if b["source_metadata"] else "",
  "physical_archive_complete":verified,"decision":decision,
  "reason":reason,"source_checked":p in checks,
  "review_channel":rec.get("verification_source","other_pending"),
  "current_license_observed":rec.get("source_license_current"),
  "current_artist_observed":rec.get("source_artist_current"),
  "visual_dhash_distance":rec.get("source_visual_distance"),
  "original_hub_blob":b["source_blob_link"],
  "public_release_approved":False
 })
assert len(rows)==120 and len({r["source_path"] for r in rows})==120
n=sum(r["physical_archive_complete"] for r in rows)
assert n==len(new),f"New ledger count mismatch {n}/{len(new)}"
counts=dict(Counter(r["decision"] for r in rows))
hosts={host:{"original":sum(r["source_host"]==host for r in rows),
  "migrated":sum(r["source_host"]==host and r["physical_archive_complete"] for r in rows)}
 for host in sorted(set(r["source_host"] for r in rows))}
summary={
 "status":"PRIORITY_120_EXACT_SOURCE_CHECKS_ACCOUNTED_FOR; PUBLISHING_STILL_BLOCKED",
 "source_priority_photos":120,"moved_this_pass":n,"held_after_checks":120-n,
 "by_host":hosts,"decisions":counts,
 "full_family_source_photos":459,"full_family_staged_photo_count":210+n,
 "full_family_held_photo_count":249-n,"public_site_published":False,
 "source_snapshot":batch["pinned_source_sha"],
 "note":"Transferred files have individual current license/credit/visual verification in separate ledgers. Public source-rights and arrow QA are independent gates."
}
dest=STAGE/"migration"
(dest/"asteraceae-priority120-upstream-review-decisions.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n")
(dest/"asteraceae-priority120-review-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
cols=["source_path","source_host","source_creator_claim","source_license_claim","physical_archive_complete","decision","reason","current_license_observed","current_artist_observed","visual_dhash_distance","original_hub_blob"]
with (dest/"asteraceae-priority120-upstream-review-decisions.csv").open("w",newline="",encoding="utf-8") as f:
 w=csv.DictWriter(f,fieldnames=cols,lineterminator="\n");w.writeheader()
 for r in rows:w.writerow({k:r.get(k) for k in cols})
print("PRIORITY120_CLOSEOUT",json.dumps(summary,sort_keys=True),flush=True)
