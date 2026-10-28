#!/usr/bin/env python3
"""Authoritative Asteraceae private learner handoff audit, never public deploy."""
from pathlib import Path
from collections import Counter
import json,sys
ROOT=Path(sys.argv[1]).resolve()
def read(p):return json.loads((ROOT/p).read_text())
index=read("data/collection-index.json")
assets=read("migration/asteraceae-full-image-asset-reconciliation.json")
source=read("migration/asteraceae-full-image-reconciliation-summary.json")
texas=read("migration/asteraceae-new-texas-inat-cc-photo-ledger.json")
other=read("migration/asteraceae-new-commons-field-photo-ledger.json")
syn=read("migration/asteraceae-last-four-new-synonym-cc-ledger.json")
assert len(index["entries"])==180 and len(assets)==459
assert source["archived_original_images_in_private_staging"]==323
assert source["remaining_source_originals_held_and_indexed"]==136
assert source["source_images_without_a_migration_disposition"]==0
assert source["staging_photos_without_a_source_or_rights_ledger"]==0
assert len(texas)==36 and len(other)==1 and len(syn)==2
additional={**texas,**other,**syn}
assert len(additional)==39
source_species=set()
for p in assets:
 if p["archived_in_private_staging"]:source_species.update(p["referenced_by_species"])
photo_species=source_species|{x["species_id"] for x in additional.values()}
ids={x["id"] for x in index["entries"]}
assert photo_species<=ids
assert len(photo_species)==179,f"Unexpected photo species coverage: {len(photo_species)}"
empty=ids-photo_species
assert empty=={"pectis-angustifolia-var-fastigiata"},empty
assert sum(1 for x in assets if x["archived_in_private_staging"])+len(additional)==362
held_source={x["source_path"] for x in assets if not x["archived_in_private_staging"]}
assert len(held_source)==136
held_pectis=[x for x in assets if "pectis-angustifolia-var-fastigiata" in x["referenced_by_species"] and not x["archived_in_private_staging"]]
assert len(held_pectis)>=1
final={
 "status":"PHOTO_ACCOUNTING_AND_PRIVATE_LEARNER_CONTENT_HANDOFF_READY; NOT_PUBLICATION_APPROVAL",
 "original_source_physical_photos":459,
 "original_source_photos_archived":323,
 "original_source_photos_held_with_explicit_decisions":136,
 "new_third_party_licensed_photos_staged_separately":39,
 "preview_total_image_copies":362,
 "species_total":180,
 "species_with_at_least_one_staged_gallery_photo":179,
 "species_without_exact_taxon_staged_gallery_photo":1,
 "photo_gap_species":["Pectis angustifolia var. fastigiata"],
 "last_species_hold_provenance": [{
   "path":p["source_path"],"git_blob_sha":p["source_git_blob_sha"],
   "source_page":p["source_metadata"][0].get("source_page") if p["source_metadata"] else None,
   "license_claim":p["source_metadata"][0].get("license_claim") if p["source_metadata"] else None,
   "next_action":p["followup_priority"]
 } for p in held_pectis],
 "separate_external_photo_urls_still_to_triage":29,
 "historical_unreferenced_source_originals_held":11,
 "strict_public_pages_preview_from_last_qa":{"confirmed_photos":154,"confirmed_species":112,
   "workflow_url":"https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40781698540",
   "deployed":False},
 "private_repo_contains_noncommercial_and_author_permission_photos":True,
 "production_pages_approved":False,
 "original_hub_authority_changed":False,
 "project_rules_changed":False,
 "final_qa_must_still_pass_for_source_sha":"034f385e44cec18e8c29be96f83e22aaf78fe3f3",
 "separate_release_gates":[
  "Inspect public/private Git history and NC/ARR provenance prior to any repo visibility change",
  "Complete full family genus-module coverage and hub glossary/quiz navigation assessment",
  "Visually confirm real field anatomy arrows instead of assuming photograph presence equals anatomy readiness",
  "Obtain owner approval for Pages rollout, hub redirects and rollback"
 ],
 "recommendation":"Move primary content migration lane to Fabaceae after final visual and rights/handoff QA; retain Pectis variety and 136 source hold decisions as tracked maintenance."
}
out=ROOT/"migration"
(out/"asteraceae-photo-handoff-readiness-20261028.json").write_text(json.dumps(final,indent=2,ensure_ascii=False)+"\n")
md=f"""# Asteraceae Visual Learner — content-migration handoff, Oct 28 2026

**Status: source photos fully accounted for; private learner nearly fully illustrated; public launch is NOT approved.**

## Final photograph inventory
- **459** physically archived originals in canonical Hays County hub. **323** byte-identical originals have been copied and checked in PRIVATE Asteraceae staging; **136** are immutably pinned in the hub with file-by-file rights/identity hold reasons.
- **39 newly sourced, creator-credited, public-compatible CC photographs** are **separate** from the 459 original-source inventory: 36 Texas iNaturalist research-grade photos, 1 Australian source-identified Commons rush skeletonweed image, 2 Texas records identified under Kew-verified taxonomic synonyms.
- Private Asteraceae learner now has **362 real image copies across 179/180 species**. The one zero-photo card is **Pectis angustifolia var. fastigiata** (species-level photos cannot be claimed as verified variety photos without stronger evidence).
- The original 477 source image references include 29 external URLs not represented by an original Git blob; 11 historical original photos are not linked to active species cards, and none was wrongly introduced into the learner.
- All attribution claims (including Joey Santore NC and Calvin King original owner permission) remain individually labelled. Noncommercial rights were never upgraded to unrestricted rights.
- Strict public-use CC test build (not deployed): **154 photos on 112 species**, **0 noncommercial-only**, **0 private-owner-authorized images**. [Passing strict source release-candidate QA](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40781698540).

## Photo migration progression
1. Private Asteraceae seed: 180 species and 210 original images, then full 459-file inventory.
2. Exact-source Commons, GBIF and iNat license passes → 319 original images.
3. Two original camphorweed + one safflower → 322, 149 species illustrated.
4. Texas research-grade alternative CC backfill → 36 new images across 26 formerly empty taxa, 175 species.
5. Commons rush skeletonweed habit photo → 176 species.
6. Kew-supported synonyms and exact original old-plainsman source image recovery → **323 original + 39 new = 362**, **179 illustrated species**.

## Single zero-photo species
\`Pectis angustifolia var. fastigiata\`: the old original is claimed CC BY-NC but exact photo rights could not be independently verified. Its species parent \`Pectis angustifolia\` is NOT an adequate automatic proof for the named variety. Keep on a flagged maintenance queue until an exact variety photograph and its license can be verified.

## Release/field diagnostic gates still open
- This is **not** a 100% anatomy/arrow-complete workbook; validate diagnostic roles and arrows species-by-species. No invisible structures were annotated automatically.
- The full original Asteraceae genus lesson migration and hub Glossary / Quiz routing are separate QA gates.
- Do NOT change GitHub repository visibility, publish private media/history or redirect main hub Pages without a public rights and rollback review.
- Main hub source-of-truth and project rules unchanged.

## Suggested next action
**One final QA-and-handoff pass**, then begin **Fabaceae** while leaving the single Pectis variety and the 136 source-photo rights holds in ongoing Asteraceae maintenance. This does NOT mean all 180 species have full anatomical image roles or that the independent family website is publicly live.

See [machine-readable handoff readiness](asteraceae-photo-handoff-readiness-20261028.json), [complete original-file migration records](asteraceae-full-image-asset-reconciliation.csv), and [new Texas CC photo provenance](asteraceae-new-texas-inat-cc-photo-ledger.json).
"""
(out/"ASTERACEAE_PHOTO_PASS2_HANDOFF_20261028.md").write_text(md)
print("ASTERACEAE_PASS2_HANDOFF",json.dumps(final,sort_keys=True),flush=True)
