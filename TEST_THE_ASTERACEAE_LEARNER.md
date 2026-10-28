# Asteraceae — Field-first Visual Learner (Private Test)

**Status: private review build passed desktop and mobile tests. Not a public Pages site or a production migration.** The original Hays Botany Visual Learner remains unchanged.

## Open the latest successfully tested Windows preview

1. [Download Asteraceae test site ZIP — October 28 field-first curated preview](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40785673710/artifacts/12858194558) (sign in to GitHub if necessary).
2. Extract the entire ZIP; do not run files while they are still zipped.
3. Open the extracted `dist` folder.
4. Double-click `RUN_ASTERACEAE_REVIEW.bat` and keep the server window running.
5. Browser opens `http://127.0.0.1:8767/?species=achillea-millefolium`.

Python 3 is required. Do not open `index.html` directly over `file://` because JSON fetching is blocked there.

## What is in this build?

| Inventory | Verified quantity |
|---|---:|
| Species records copied from the authoritative original | 180 |
| Original photographs accounted for in both repositories | 459 / 459 |
| Original photos physically byte-verified in private staging | 323 |
| Original photos held with rights/identity records in hub | 136 |
| Newly sourced photographs, separately archived | 39 |
| Species with at least one archived exact-taxon gallery photo | 179 / 180 |
| **Visible field-first preview photos** | **334** |
| **Species displaying at least one photo** | **169 / 180** |
| Individual unverified-license photo instances hidden | 24 |
| Untraceable creator/source/license photo instances hidden | 4 |
| Strict public-CC *test candidate* (NOT published) | 153 photos / 112 species |

The difference between 179 archived-photo species and 169 display-photo species is intentional. The field-first filter hides questionable photographs rather than accepting a weak creator/license claim. No source original has been deleted; exact decisions are in [the private curation ledger](https://github.com/Crking92/Hays-Botany-Asteraceae/blob/staging/asteraceae-metadata/migration/asteraceae-field-first-gallery-exclusions.json).

## Review checklist

- Search scientific/common names (yarrow, goldenrod, Coreopsis, Bidens); check Field ID and Learner.
- Inspect visible images and credit labels; open the **Photo source** and license links.
- Check that close-ups of diagnostic structures remain visible, not just distant whole-plant shots.
- Verify mobile horizontal scrolling, direct links to species, hub return, Glossary and Quiz.
- Observe **CC BY-NC / noncommercial-only** cautions where present.
- Flag inaccurate anatomy labels, missing macro views and look-alike shortcomings. No photo has been assigned a fabricated anatomy arrow.

**Important:** This workflow automatically tests deep links and gallery loading on desktop/mobile; a complete scientific identification and arrow-placement review has **not** passed species by species. 49 source genus folders lack dedicated standalone genus teaching lessons. The exact-variety photo for **Pectis angustifolia var. fastigiata** is still on hold pending provenance and identification proof.

## Source and QA links

- [Private photo learner QA run — desktop and mobile PASS](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40785673710)
- [Strict public-CC test workflow — PASS, no deployment](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40785673532)
- [Source-by-source original photo audit](https://github.com/Crking92/Hays-Botany-Asteraceae/blob/staging/asteraceae-metadata/migration/ASTERACEAE_ALL_459_PHOTOS_ACCOUNTED_20261028.md)
- [Collection handoff summary](https://github.com/Crking92/Hays-Botany-Asteraceae/blob/staging/asteraceae-metadata/migration/ASTERACEAE_PHOTO_PASS2_HANDOFF_20261028.md)
- [Original hub](https://crking92.github.io/Hays-County-Botany/)

**Next gate:** complete and preserve final per-species visible-photo gaps and curation QA; continue verified source migration to Fabaceae. Do not enable Pages, change visibility, publish restricted Git history or change hub routing without a separate release review.
