# Asteraceae collection handoff gate — 2026-10-28

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
| Tetraneuris linearifolia | Fineleaf four-nerve daisy | SEARCH_NEW_LICENSED_IMAGE_OR_GET_RIGHTSHOLDER_PERMISSION |
| Amphiachyris amoena | Texas broomweed | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Carphochaete bigelovii | Bigelow's carphochaete | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Centaurea melitensis | Malta starthistle | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Heterotheca canescens | Hoary goldenaster | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Hymenopappus artemisiifolius | Hymenopappus artemisiifolius | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Plectocephalus americanus | American Basketflower | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Pyrrhopappus grandiflorus | Texas false dandelion | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Ratibida columnifera | Upright Prairie Coneflower | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Verbesina encelioides | Cowpen Daisy | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Tetragonotheca texana | Squarebud daisy | SEARCH_NEW_LICENSED_IMAGE_OR_GET_RIGHTSHOLDER_PERMISSION |
| Arnoglossum plantagineum | Plantainleaf Indian plantain | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Bradburia hirtella | Bradburia hirtella | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Chaptalia texana | Texas silverpuff | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Chondrilla juncea | Rush skeletonweed | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Heterotheca stenophylla | Narrowleaf goldenaster | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Iva asperifolia var. angustifolia | Narrowleaf sumpweed | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Leontodon rhagadioloides | Crete weed | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Packera tampicana | Packera tampicana | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Parthenium confertum | Parthenium confertum | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Pectis angustifolia var. fastigiata | Narrowleaf chinchweed, fastigiata variety | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Pseudognaphalium canescens | Woolly cudweed | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Pyrrhopappus carolinianus | Carolina false dandelion | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Senecio ampullaceus | Texas groundsel | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Sideranthus spinulosus | Sideranthus spinulosus | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Sidneya tenuifolia | Narrowleaf goldeneye | VERIFY_EXISTING_NC_OR_FIND_PUBLIC_SAFE_ALTERNATIVE |
| Berlandiera betonicifolia | Betonyleaf greeneyes | VERIFY_EXISTING_PERMISSIVE_SOURCE |
| Hymenopappus scabiosaeus var. corymbosus | Old plainsman (corymbose variety) | VERIFY_EXISTING_PERMISSIVE_SOURCE |
| Krigia occidentalis | Western dwarf dandelion | VERIFY_EXISTING_PERMISSIVE_SOURCE |
| Laphamia lindheimeri | Lindheimer's laphamia | VERIFY_EXISTING_PERMISSIVE_SOURCE |
| Wedelia acapulcensis | Wedelia acapulcensis | VERIFY_EXISTING_PERMISSIVE_SOURCE |

## Why this list is maintained
- Do not force restricted images into a public collection merely to improve percentages.
- The remaining photo-gap taxon list is durable JSON in \`migration/asteraceae-31-photo-empty-species-backlog.json\` and preserves the exact source SHA for each held original.
- This handoff does not change main-hub URLs, source ownership, GitHub Pages, project rules or existing grass workflows.
