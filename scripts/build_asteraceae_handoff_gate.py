#!/usr/bin/env python3
"""Produce a transparent family handoff gate and ranked backlog, never a release approval."""
import json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(sys.argv[1]).resolve()
meta=json.loads((ROOT/"data/collection-index.json").read_text())
assets=json.loads((ROOT/"migration/asteraceae-full-image-asset-reconciliation.json").read_text())
source=json.loads((ROOT/"migration/asteraceae-full-image-reconciliation-summary.json").read_text())
ext=json.loads((ROOT/"migration/asteraceae-unresolved-image-references.json").read_text())
assert len(meta["entries"])==180 and source["physical_source_image_files"]==459
assert source["archived_original_images_in_private_staging"]+source["remaining_source_originals_held_and_indexed"]==459
assert source["source_images_without_a_migration_disposition"]==0
assert source["staging_photos_without_a_source_or_rights_ledger"]==0
assert len(ext)==29
assert source["archived_original_images_in_private_staging"]==322
zero=[]
priority={"amphiachyris-amoena","ratibida-columnifera","verbesina-encelioides","plectocephalus-americanus","pyrrhopappus-grandiflorus","centaurea-melitensis","tetraneuris-linearifolia","hymenopappus-artemisiifolius","carphochaete-bigelovii","heterotheca-canescens"}
for sp in meta["entries"]:
 linked=[x for x in assets if sp["id"] in x["referenced_by_species"]]
 archived=[x for x in linked if x["archived_in_private_staging"]]
 if archived:continue
 holds=[]
 for x in linked:
  m=x["source_metadata"][0] if x["source_metadata"] else {}
  holds.append({"source_path":x["source_path"],"creator_claim":m.get("creator",""),
    "license_claim":m.get("license_claim",""),"source_page":m.get("source_page",""),
    "next_action":x["followup_priority"],"original_source_git_blob_sha":x["source_git_blob_sha"]})
 external=[{"source":e["source_page"],"file":e["file_field"]} for e in ext if e["species_id"]==sp["id"]]
 if any("FIRST_RECHECK_UPSTREAM" in h["next_action"] for h in holds):
  lane="VERIFY_EXISTING_PERMISSIVE_SOURCE"
 elif any("RECHECK_NONCOMMERCIAL" in h["next_action"] for h in holds):
  lane="VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE"
 elif any("OWNER_OR_SOURCE_PERMISSION" in h["next_action"] for h in holds):
  lane="SEARCH_NEW_LICENSED_IMAGE_OR_GET_RIGHTSHOLDER_PERMISSION"
 else:
  lane="SOURCE_OR_SPECIES_ID_REVIEW_NEEDED"
 zero.append({"species_id":sp["id"],"scientific_name":sp["scientific_name"],"common_name":sp.get("common_name",""),
    "family":"Asteraceae","field_review_priority":"HIGH_CANDIDATE_FOR_CREW" if sp["id"] in priority else "STANDARD",
    "current_archived_gallery_photos":0,"source_original_photos_held":holds,
    "external_image_references":external,"next_action_lane":lane})
assert len(zero)==31,f"Expected 31 photo-empty species, got {len(zero)}"
zero.sort(key=lambda x:(0 if x["field_review_priority"].startswith("HIGH") else 1,x["next_action_lane"],x["scientific_name"]))
out=ROOT/"migration"
(out/"asteraceae-31-photo-empty-species-backlog.json").write_text(json.dumps(zero,indent=2,ensure_ascii=False)+"\n")
summary={"status":"ACCOUNTING_GREEN; PRIVATE_LEARNER_REVIEW_GATE_NOT_PUBLIC_RELEASE",
 "species":180,"species_with_verified_preview_photo":149,
 "species_without_approved_archived_photo":31,
 "original_physical_images":459,"physical_images_archived":322,"source_images_held":137,
 "all_source_images_accounted_for":True,"external_images_separate":29,
 "zero_photo_species_worklist":len(zero),
 "photo_gap_lanes":dict(Counter(z["next_action_lane"] for z in zero)),
 "field_priority_suggestions":sum(z["field_review_priority"].startswith("HIGH") for z in zero),
 "unverified_anatomy_annotation_gate":"REMAINS_OPEN",
 "public_pages_release_gate":"NOT_APPROVED; RESTRICTED_IMAGES_IN_PRIVATE_REPOSITORY",
 "recommended_transition":"Two additional focused QA/rights passes after photo-gap rescue; retain documented backlog and no forced public deployment"}
(out/"asteraceae-family-transition-readiness.json").write_text(json.dumps(summary,indent=2)+"\n")
table="\n".join("| "+x["scientific_name"]+" | "+x["common_name"].replace("|","/")+" | "+x["next_action_lane"]+" |" for x in zero)
report=f"""# Asteraceae collection handoff gate — 2026-10-28

**Current state:** 322/459 physical source photos safely staged, 137 held with individual records, 149/180 species have at least one source-checked gallery photo, 31 have no gallery photo. All 459 source photo files are fully accounted for.

## What would make Asteraceae good enough to leave in maintenance mode?
- [x] All 180 species and existing teaching-source text preserved.
- [x] Every original photo has source path, Git blob SHA, rights decision, and destination/hold.
- [x] Restriction-aware learner runs with credited Commons, GBIF, iNat, Calvin King and Joey Santore photos.
- [ ] Field-review the 31 image-empty species; add genuinely lawful verified examples where possible, and mark unfillable gaps explicitly.
- [ ] Finish targeted source/permissions decisions and record meaningful anatomy gaps; **do not** add invented arrows.
- [ ] Run final desktop/mobile, image loading, source-credit and strict public-permission regression.
- [ ] If an independent public Pages release is desired: separately verify raw-source repository visibility/history, final URLs, routing, release rights, and rollback. **Never assume private staging can safely become a public repository.**

**Recommended remaining passes after this first gap-rescue pass: two** — 1) prioritized recovery and rights decisions; 2) QA and handoff. A later specialized anatomy-photo enrichment program can continue without blocking work on other family repos. This is a proposal, not a guarantee of photo-perfect completeness or public release.

## All 31 currently image-empty species

These are zero transferred photos, not necessarily zero images anywhere on the Internet. Some source images are deliberately held because the owner or exact CC license cannot be confirmed.

| Scientific name | Common name | Next action |
|---|---|---|
{table}

## Why this list is maintained
- Do not force restricted images into a public collection merely to improve percentages.
- The remaining photo-gap taxon list is durable JSON in \`migration/asteraceae-31-photo-empty-species-backlog.json\` and preserves the exact source SHA for each held original.
- This handoff does not change main-hub URLs, source ownership, GitHub Pages, project rules or existing grass workflows.
"""
(out/"ASTERACEAE_REMAINING_PASSES_AND_EXIT_GATE_20261028.md").write_text(report)
print("ASTERACEAE_EXIT_GATE",json.dumps(summary,sort_keys=True),flush=True)
