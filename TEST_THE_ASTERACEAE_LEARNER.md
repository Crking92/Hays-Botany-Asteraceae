# Asteraceae — Real-photo Visual Learner Test

**Status: tested private review, not a live GitHub Pages site.** The original Hays Botany learner is still canonical.

## Open the test on Windows
1. [Download the 180-photo test site ZIP](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40723638146/artifacts/12831212655).
2. Extract the entire ZIP — do not run a file from inside ZIP.
3. Open the extracted `dist` folder.
4. Double-click `RUN_ASTERACEAE_REVIEW.bat`. Keep the Asteraceae server window open while using the page.
5. The browser opens `http://127.0.0.1:8767/?species=achillea-millefolium`.

The test requires Python 3 installed (the same type of server as the main Hays Botany local launcher). Do not open `dist/index.html` directly; browsers block the JSON fetches on `file://`.

## What to check
- Search by common/scientific name, e.g. yarrow, goldenrod, Coreopsis, Bidens.
- Check Learner vs Field ID, current LOOK HERE FIRST, and look-alike notes.
- Scroll horizontally through photos where present; inspect captions, exact photo creator and original source/license links.
- Check desktop vs phone layout, all-plants link, Glossary and universal Quiz links.
- Note which species lack a photo or a needed macro; **90/180 have verified imagery** so far. Photos under CC BY-NC are marked NONCOMMERCIAL-ONLY; do not reuse them for commercial materials.
- No arrows have been added without verified actual image anatomy. Please report any missing arrows/incorrect labels for visual review.

## Current verified inventory
- Original Asteraceae source: 180 species records, 459 physically archived photos.
- New **private** Asteraceae staging: 180 species records and 180 byte-verified original images (82 Wikimedia Commons exact CC, 98 independently checked iNaturalist photo IDs; 92 of those are noncommercial-only).
- The downloadable **test** contains 180 optimized, EXIF-stripped photo copies across 90 species. All original photo permissions and source metadata remain in the private staging branch.
- 49 genera still need standalone teaching modules.
- No GitHub Pages publication, hub search redirect, production ownership transfer, or changes to the original source site have occurred.

## Links
- [Private staging branch](https://github.com/Crking92/Hays-Botany-Asteraceae/tree/staging/asteraceae-metadata)
- [Successful photo learner screenshot and QA run](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40723638146)
- [Public hub](https://crking92.github.io/Hays-County-Botany/)
- [Stage 3 review report](https://github.com/Crking92/Hays-County-Botany/blob/main/planning/MULTI_REPO_STAGE3_ASTERACEAE_PHOTO_PREVIEW_20261028.md)

**Next release gate:** check photo rights and images for an independent public Pages release, confirm the GitHub plan/private-repo Pages eligibility or change visibility only with owner approval, and then test hub↔family navigation in real deployment before rewriting project rules.
