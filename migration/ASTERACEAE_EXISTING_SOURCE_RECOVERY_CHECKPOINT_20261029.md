# Asteraceae source-archive photo recovery — October 29, 2026

## Scope and verified release

This is a **photo presence and source-accounting checkpoint**, not a declaration that all Asteraceae botanical anatomy and identification has been expert confirmed.

| Metric | Before this pass | Current |
| --- | ---: | ---: |
| Species records published | 180 | **180** |
| Species with any public gallery photo | 116 | **124** |
| Species without an eligible published photo | 64 | **56** |
| Public gallery photo files | 162 | **172** |
| Newly promoted from already-staged archive during this turn | — | **10** |
| Source media records inspected by current full sweep | — | **477** |
| Source media records held after filter | — | **356** |
| New media sourced/downloaded from the internet | 0 | **0** |

The [full public GitHub Pages smoke run](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40933112050) returned **SUCCESS** and fetched every one of the **172** displayed JPG files, comparing each against the file already present in the Asteraceae repository. It also read the 180 species cards. This tests URL delivery and byte identity, **not** independent visual species determinations.

Prior migration reporting documents 1,137/1,137 historical source files including 459 original images on the Asteraceae staging branch. This pass did **not** regenerate all 1,137 original SHA checks; retain that historical source-audit provenance. Importantly, the staging/hold branches are inside a now-public repository and **not actually private**.

### Specifically recovered original photos

- **Brickellia eupatorioides** — original archive CC BY 2.0 Commons/USFWS photo of false boneset
- **Chaetopappa effusa** — original exact photo-level iNaturalist CC0
- **Cirsium ochrocentrum** — original USDA NRCS photograph by Clarence A. Rechenthin, public domain
- **Gutierrezia texana** — two Jim Conrad public-domain photographs of flowering habit and composite head, from his original newsletter; both recovered from historical hold folder
- **Lindheimera texana** — original staged photo with exact iNaturalist-origin GBIF media ID and archived CC0 license
- **Rudbeckia hirta** — original Brady Reed Commons CC0 photograph, recovered from historical hold folder
- **Solidago nemoralis** — exact source-photo archived CC0 with GBIF original-media URL
- **Vernonia lindheimeri** — original Commons author-public-domain photo by Mason Brock
- **Helenium elegans** — an additional existing strict-license image already attached to a photographed species

The new source-only rights gate is `scripts/review_existing_asteraceae_photo_rights.py`. The original photos and credit records have not been overwritten. The publisher copy is retained in `site/media` with the source blob SHA recorded. A direct source page, named photographer, actual license, and rights note accompany each photo.

### Current hold reasons — media records, NOT distinct missing-species counts

- `license_not_strict_cc_or_public_domain`: **300** original image records
- `remote_or_invalid_original_path`: **29** original image records
- `public_permission_not_documented`: **7** original image records
- `image_specific_source_not_public_verified`: **10** original image records
- `source_bytes_not_in_staged_archive`: **10** original image records

The individual source records remain preserved and are not automatically considered public-licensable because the repository itself is public. CC BY-NC may be suitable for a clearly noncommercial site with attribution **if the original individual photo license supports it**, but NC/ND/unknown/license-pending files have not been promoted under this strict existing-photo release. No blanket CC grant is inferred from photo credits, iNaturalist observation data rights, or GBIF occurrence metadata.

### Species still missing a public-gallery photograph (56)

| Species ID | Source image records held | Recorded reasons |
| --- | ---: | --- |
| `ambrosia-trifida` | 4 | license_not_strict_cc_or_public_domain (4) |
| `amphiachyris-dracunculoides` | 5 | license_not_strict_cc_or_public_domain (5) |
| `aphanostephus-riddellii` | 3 | license_not_strict_cc_or_public_domain (3) |
| `baccharis-neglecta` | 5 | license_not_strict_cc_or_public_domain (5) |
| `baccharis-salicifolia` | 5 | license_not_strict_cc_or_public_domain (4), image_specific_source_not_public_verified (1) |
| `boltonia-diffusa` | 3 | license_not_strict_cc_or_public_domain (3) |
| `brickellia-dentata` | 2 | license_not_strict_cc_or_public_domain (2) |
| `chloracantha-spinosa` | 2 | license_not_strict_cc_or_public_domain (2) |
| `cirsium-texanum` | 5 | license_not_strict_cc_or_public_domain (4), remote_or_invalid_original_path (1) |
| `cirsium-undulatum` | 6 | license_not_strict_cc_or_public_domain (5), remote_or_invalid_original_path (1) |
| `coreopsis-basalis` | 5 | license_not_strict_cc_or_public_domain (5) |
| `coreopsis-tinctoria` | 5 | license_not_strict_cc_or_public_domain (5) |
| `coreopsis-wrightii` | 5 | remote_or_invalid_original_path (3), license_not_strict_cc_or_public_domain (2) |
| `diaperia-prolifera` | 1 | license_not_strict_cc_or_public_domain (1) |
| `diaperia-verna` | 1 | license_not_strict_cc_or_public_domain (1) |
| `dysodiopsis-tagetoides` | 1 | license_not_strict_cc_or_public_domain (1) |
| `eclipta-prostrata` | 3 | license_not_strict_cc_or_public_domain (3) |
| `elephantopus-carolinianus` | 1 | license_not_strict_cc_or_public_domain (1) |
| `erigeron-geiseri` | 2 | public_permission_not_documented (1), license_not_strict_cc_or_public_domain (1) |
| `gaillardia-pulchella` | 5 | license_not_strict_cc_or_public_domain (4), image_specific_source_not_public_verified (1) |
| `gaillardia-suavis` | 6 | remote_or_invalid_original_path (1), license_not_strict_cc_or_public_domain (4), public_permission_not_documented (1) |
| `gamochaeta-purpurea` | 3 | source_bytes_not_in_staged_archive (1), license_not_strict_cc_or_public_domain (2) |
| `grindelia-lanceolata` | 5 | license_not_strict_cc_or_public_domain (5) |
| `gymnosperma-glutinosum` | 4 | license_not_strict_cc_or_public_domain (4) |
| `helenium-quadridentatum` | 2 | source_bytes_not_in_staged_archive (1), license_not_strict_cc_or_public_domain (1) |
| `helianthus-annuus` | 7 | license_not_strict_cc_or_public_domain (5), remote_or_invalid_original_path (2) |
| `helianthus-maximiliani` | 7 | license_not_strict_cc_or_public_domain (5), remote_or_invalid_original_path (2) |
| `hymenopappus-scabiosaeus` | 2 | license_not_strict_cc_or_public_domain (2) |
| `hymenopappus-tenuifolius` | 1 | license_not_strict_cc_or_public_domain (1) |
| `iva-annua` | 3 | license_not_strict_cc_or_public_domain (3) |
| `liatris-punctata` | 3 | license_not_strict_cc_or_public_domain (3) |
| `lygodesmia-texana` | 3 | license_not_strict_cc_or_public_domain (3) |
| `marshallia-caespitosa` | 3 | license_not_strict_cc_or_public_domain (3) |
| `melampodium-leucanthum` | 4 | license_not_strict_cc_or_public_domain (4) |
| `palafoxia-callosa` | 2 | license_not_strict_cc_or_public_domain (2) |
| `pectis-angustifolia-var-fastigiata` | 1 | license_not_strict_cc_or_public_domain (1) |
| `pluchea-camphorata` | 5 | remote_or_invalid_original_path (2), license_not_strict_cc_or_public_domain (1), public_permission_not_documented (2) |
| `pluchea-odorata` | 3 | license_not_strict_cc_or_public_domain (3) |
| `porophyllum-scoparium` | 1 | license_not_strict_cc_or_public_domain (1) |
| `silybum-marianum` | 3 | license_not_strict_cc_or_public_domain (3) |
| `solidago-altissima` | 5 | license_not_strict_cc_or_public_domain (5) |
| `solidago-canadensis` | 2 | license_not_strict_cc_or_public_domain (2) |
| `solidago-juliae` | 4 | remote_or_invalid_original_path (1), public_permission_not_documented (1), license_not_strict_cc_or_public_domain (2) |
| `solidago-radula` | 2 | license_not_strict_cc_or_public_domain (2) |
| `sphagneticola-trilobata` | 3 | license_not_strict_cc_or_public_domain (3) |
| `symphyotrichum-divaricatum` | 5 | license_not_strict_cc_or_public_domain (5) |
| `symphyotrichum-drummondii` | 5 | remote_or_invalid_original_path (3), license_not_strict_cc_or_public_domain (2) |
| `symphyotrichum-lanceolatum-subsp-lanceolatum` | 2 | license_not_strict_cc_or_public_domain (2) |
| `symphyotrichum-sericeum` | 5 | remote_or_invalid_original_path (3), license_not_strict_cc_or_public_domain (2) |
| `symphyotrichum-subulatum` | 2 | remote_or_invalid_original_path (1), license_not_strict_cc_or_public_domain (1) |
| `tetraneuris-scaposa` | 5 | license_not_strict_cc_or_public_domain (5) |
| `thelesperma-filifolium` | 5 | license_not_strict_cc_or_public_domain (5) |
| `thelesperma-megapotamicum-var-ambiguum` | 3 | license_not_strict_cc_or_public_domain (3) |
| `verbesina-lindheimeri` | 3 | license_not_strict_cc_or_public_domain (3) |
| `viguiera-dentata` | 2 | license_not_strict_cc_or_public_domain (2) |
| `wedelia-acapulcensis-var-hispida` | 1 | license_not_strict_cc_or_public_domain (1) |

## Routing and handoff

Asteraceae's **180 source text/metadata cards remain in `Crking92/Hays-Botany-Asteraceae`**, with the active original-write branch `staging/asteraceae-metadata` per `AGENTS.md`; the derived live learner is `main/site`. The old unified learner stays functional. Neither the original GitHub repo nor unrelated family repositories was written to during the Asteraceae source recovery. No paused photo-gathering automations restarted.

- [Live Asteraceae Visual Learner](https://crking92.github.io/Hays-Botany-Asteraceae/site/)
- [Current photo and species gallery census](https://github.com/Crking92/Hays-Botany-Asteraceae/blob/main/site/data/gallery-index.json)
- [Source media holds by record, with exact reasons](https://github.com/Crking92/Hays-Botany-Asteraceae/blob/main/site/existing-photo-source-sweep-report.json)
- [Full 172-image live byte QA](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/40933112050)

**Next passes:** review exact image-level licenses (including optional NC-specific noncommercial use conditions), verify any historical Commons originals whose source filename has only an external URL rather than a local byte copy, then address missing anatomy closeups. Do not claim 180/180 public-photo completeness at this checkpoint.
