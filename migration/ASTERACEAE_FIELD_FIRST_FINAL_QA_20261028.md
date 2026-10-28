# Asteraceae — final field-first gallery QA and maintenance handoff

**Date:** 2026-10-28  
**Decision:** **PASS for private photo/content-migration handoff and Fabaceae progression. HOLD for public release, independent live family routing, and finished botanical anatomy lessons.**

## Verified original-source continuity

- Original authoritative hub `Crking92/Hays-County-Botany` currently retains the identical Asteraceae subtree `394bb64d90c025a51a8d6e10dc4a19bce1aaf623` used for the full source-photo reconciliation.
- Exact source snapshot `034f385e44cec18e8c29be96f83e22aaf78fe3f3` is pinned in the family source index. All 180 species and 678 original scientific/provenance text records are preserved in private staging.
- All 459 original image files have explicit source Git blob, disposition and licensing decision. 323 source originals are byte-verified in private staging; 136 remain pinned/held in canonical hub. Zero original images were deleted.
- An additional 39 separately sourced credited images are staged. Thus **362 physically archived gallery copies** span **179 of 180** exact taxa, prior to field-first gallery curation.
- 29 external source URLs are separately tracked; 11 historically unreferenced original files remain held. Neither class was silently promoted into displayed galleries.

## Latest private field-first learner: PASS

[GitHub Actions run 40785673710](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40785673710) — **PASS** on Chromium desktop and mobile.

- **334 displayed photo instances across 169 of 180 species.** Zero untraceable or provisional-license instances remain *in the generated preview*.
- 28 previously eligible instances excluded without erasing source provenance: **24** exact-image license not independently reverified; **4** creator/source/license untraceable.
- Private preview still contains **111 noncommercial-only photo instances**, explicitly labeled, and 6 Calvin King owner-permitted photo instances. Neither class is automatically cleared for unrestricted public release.
- The live image-loading, deep-link, attribution captions/source links, and mobile scrolling automated checks passed. This is **not** an independent human species-by-species visual-anatomy approval.
- [Download the tested field-first learner and screenshots](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40785673710/artifacts/12858194558).

## Latest strict public-compatible photo build: PASS, NOT DEPLOYED

[Strict-CC test](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40785673532) passed with photo-license and source preflight, and **no Pages deployment**. The preceding strict candidate verified **153 photos across 112 taxa, with zero NC/individual-owner-only photos**; current strict build uses the same curation logic. A successful strict static output check does **not** authorize making the repository public: private Git history may include restricted source media.

## Exact 11 cards without a displayed field-first photo

Ten currently have photos archived but deliberately withheld from the displayed gallery because individual licensing is not independently confirmed; one has no accepted exact-variety image.

| Scientific name | Blocker |
|---|---|
| Chloracantha spinosa | Individual-photo rights/source recheck |
| Diaperia prolifera | Individual-photo rights/source recheck |
| Diaperia verna | Individual-photo rights/source recheck |
| Dysodiopsis tagetoides | Individual-photo rights/source recheck |
| Elephantopus carolinianus | Individual-photo rights/source recheck |
| Hymenopappus tenuifolius | Individual-photo rights/source recheck |
| Lygodesmia texana | Individual-photo rights/source recheck |
| **Pectis angustifolia var. fastigiata** | Exact-variety identity + source rights unresolved; never substitute species-level image without taxonomic proof |
| Pluchea odorata | Individual-photo rights/source recheck |
| Porophyllum scoparium | Individual-photo rights/source recheck |
| Wedelia acapulcensis var. hispida | Individual-photo rights/source recheck |

Machine-readable source-of-truth: [per-species field-first exclusions and empty-gallery audit](asteraceae-field-first-gallery-curation-summary.json), [all individual excluded image dispositions](asteraceae-field-first-gallery-exclusions.json), and [original image reconciliation](asteraceae-full-image-asset-reconciliation.csv).

## Outstanding gates — carry as maintenance rather than blocking the next family

1. Rights/individual-license review for 136 held original images, the 11 displayed-photo-empty species, and the 29 external-only source references; no forced replacement or invented attribution.
2. Revisit **49 source genus folders without standalone genus lessons**, plus species-specific diagnostic image roles, accurate visible anatomy arrows, and look-alike teaching.
3. Actual deployed hub → family → glossary/quiz → hub navigation cannot be tested while independent collection Pages remains unpublished.
4. Before any public release: independently audit repository **history/visibility**, restrictive rights, GitHub plan eligibility, strict Pages output, mobile URLs, release approval, and rollback. Do not move or modify original hub routes or authoritative plant records yet.

**Migration lane result:** Asteraceae private source/text/photo accounting and field-first browser QA are ready for maintenance mode. **Next primary family: Fabaceae** (91 source species; 291 metadata files, 200 original images held pending rights checks). Source/photo holds remain durable and visible, not quietly passed.
