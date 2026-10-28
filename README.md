# Hays Botany — Asteraceae

**Status: private staging learner and source-photo accounting verified; public release and hub cutover NOT approved.** Original Hays County Botany learner remains canonical.

The independent [Asteraceae](https://github.com/Crking92/Hays-Botany-Asteraceae/tree/staging/asteraceae-metadata) staging branch has all **180 species** and **678 original source text/metadata/lesson files**, including **45 existing genus lessons** and one family lesson, preserved from the original hub. Missing standalone genus lessons remain an explicit backlog (49).

## Source photo inventory and field-first photo curation (October 28, 2026)

- **459/459** original physical Asteraceae photographs are inventoried and reconciled by exact Git blob and disposition.
- **323** original source photographs are byte-verified in private staging; the other **136** are retained in the original repository with documented hold reasons. No original was deleted.
- **39** additional, separately licensed photos are staged outside the original 459-photo inventory.
- **179/180 species** have at least one *archived* exact-taxon gallery photograph. **Pectis angustifolia var. fastigiata** is held pending exact-variety identity and license verification.
- The latest **field-first private learner** intentionally shows **334 photos across 169 species** after excluding 24 individual unverified-license photos and four instances without traceable creator/source/license information. The other photos remain recorded, not erased. Some of the resulting 11 visibly photo-empty species have hidden source images; these are not necessarily unphotographed in the archive.
- The strictly filtered CC-only, non-deployed release candidate has **153 photographs across 112 species**, **zero NC-only images**, and **zero individual-author-permission-only photos** as of the latest successful gate.

These are **photo and content migration** metrics, not finished anatomy-arrow teaching or public website readiness.

## Test the learner

[Windows test instructions, latest verified ZIP and run](TEST_THE_ASTERACEAE_LEARNER.md). The mobile/desktop browser checks verify actual photo loading, attribution links, responsive galleries and deep links. All tests run on a private downloadable static site; **no GitHub Pages site is live for this collection**.

## Audit and maintenance

- [Private photo provenance and rights decisions](https://github.com/Crking92/Hays-Botany-Asteraceae/tree/staging/asteraceae-metadata/migration)
- [Original-asset reconciliation](https://github.com/Crking92/Hays-Botany-Asteraceae/blob/staging/asteraceae-metadata/migration/ASTERACEAE_ALL_459_PHOTOS_ACCOUNTED_20261028.md)
- [179-species private photo handoff](https://github.com/Crking92/Hays-Botany-Asteraceae/blob/staging/asteraceae-metadata/migration/ASTERACEAE_PHOTO_PASS2_HANDOFF_20261028.md)
- [Current gallery exclusions](https://github.com/Crking92/Hays-Botany-Asteraceae/blob/staging/asteraceae-metadata/migration/asteraceae-field-first-gallery-exclusions.json)

### Release restrictions

The repository contains restricted/noncommercial and author-permission materials in **private Git history**. Never make the whole repository public merely because the generated strict-CC site is filtered. Public publishing, any change to original site navigation, Pages enablement, and source-ownership cutover require separate approval, deployment QA, rollback and raw-history rights review. Keep photos with unverified rights off all displayed galleries.

**Next migration lane:** Fabaceae (91 species), initially text/metadata only, with original-source photo rights audited before any new image transfer.
