# Asteraceae Photo Migration — Complete Source-Asset Closeout

**Reconciled October 28, 2026. All source files accounted for. The family is NOT yet completely migrated or public-photo-complete.**

## What "100% accounted for" means

The current `Hays-County-Botany` `main` branch at `666b0b08cd7627ec6ad9940f19f979005eb2de79` and the pinned species-source snapshot at `034f385e44cec18e8c29be96f83e22aaf78fe3f3` share the **identical** Asteraceae Git directory tree SHA: `394bb64d90c025a51a8d6e10dc4a19bce1aaf623`. No newer source image was omitted.

- **459 of 459 physical Asteraceae image files:** inventoried with original path, Git blob SHA, source size, source species references, license claims, rights-review state, holding decision and location.
- **210 files:** physically staged in the private `Hays-Botany-Asteraceae` branch `staging/asteraceae-metadata`, verified byte-identical by Git blob SHA and matched against exactly one rights ledger.
- **249 files:** **not copied**. Preserved and referenced by permanent source-commit blob URLs in the original hub. These are NOT considered public-rights approved; if hub source is ever removed, verify physical quarantine/rights before deleting it.
- **477 references in the 180 canonical species cards:** 448 point to pinned physical Asteraceae image files. The remaining **29 are external image URLs**, not broken/missing local files; separately indexed for later archiving decisions.
- **11 local physical photos are not referenced by any species `images` entry**, including five `Rudbeckia hirta` photos. They are explicitly listed in the full inventory and NOT silently discarded.
- **0 source images lack a migration disposition; 0 destination images lack original-source SHA and a rights ledger.**

## Permanent file-by-file tracking (authoritative for this snapshot)

1. [Full 459-row photo inventory — CSV](asteraceae-full-image-asset-reconciliation.csv): searchable in GitHub or export to spreadsheet; each row includes `archived_in_private_staging`, rights bucket, exact pinned source blob link, and next action.
2. [Full 459-entry photo inventory — JSON](asteraceae-full-image-asset-reconciliation.json): detailed metadata including source copyright/photographer claims and species association.
3. [Unresolved/external photo references — 29 rows](asteraceae-unresolved-image-references.json): all species names, source URL and reason; none represent a physical Asteraceae-source image.
4. [Photo coverage by each of 180 species](asteraceae-species-image-coverage.json): source-held and staged image counts.
5. [Reconciliation audit summary](asteraceae-full-image-reconciliation-summary.json): assert-backed counts and next-work triage.

## Rights of the 210 staged originals

| Group | Photos | Treatment |
|---|---:|---|
| Wikimedia Commons exact-file CC source verified | 82 | Private staging; public release still requires site/derivative/attribution gate |
| iNaturalist exact observation+photo CC BY-NC verified | 92 | Noncommercial-only, excludes strict unrestricted public snapshot |
| iNaturalist exact observation+photo reusable CC verified | 6 | Private staging; requires release gate |
| Calvin King permission for Hays Botany with credit | 6 | Keep author ownership and separate rights label, not CC |
| Joey Santore original source CC BY-NC claim, photo-specific recheck pending | 24 | Private preview only; not cleared for public candidate |
| **Total** | **210** | |

The private preview currently displays 210 actual optimized photographs across 106 species. The separately validated strict public-release candidate remains limited to 88 independently verified non-NC CC images (no Calvin or provisional Joey photos).

## Prioritized work on the remaining 249 source files

| Next action | Number | Explanation |
|---|---:|---|
| Check upstream license and creator first | 120 | CC BY/BY-SA, CC0 or public-domain **claims** in the source. No claim is automatically accepted |
| Recheck exact source and noncommercial restrictions | 84 | Mostly CC BY-NC or related claims; can be used only within the actual license scope |
| Obtain creator rights/source clarification | 34 | All-rights-reserved, unknown, missing or unusual source claims |
| Reconcile unreferenced files with species-card photo roles | 11 | Physical photos not attached to a current species gallery |
| **Total held** | **249** | Every original retained at pinned Git commit |

The original license-claim distributions for the 249 appear in the summary JSON; 120/84/34/11 are actionable **triage categories**, not a claim that 120 may be published right away.

## Guardrails
- All Asteraceae original source bytes and species files remain in the main hub. The hub remains canonical; no production routing changed and no original file was deleted.
- New Asteraceae repo is currently PRIVATE. Do not turn it public before auditing its full Git history: the private branch includes CC BY-NC and permission-limited images, even when the Pages snapshot excludes them.
- The separate, strict CC-only Pages preview and main site are not deployed or redirected by this audit.
- Original source refs are immutable Git SHAs. Recheck whenever any Asteraceae original source photo or species card changes. The snapshot is current as of the matching original directory tree SHA above.
- Future import workflow should first consult the 459-row ledger. Move a held image only after documented rights/attribution and image identity review, then rerun `scripts/reconcile_asteraceae_all_source_photos.py` so the 459-row ledger reflects the newly staged file.
- Do not claim arrow completeness or photo-role diagnostic readiness simply from this archival accounting.

**Result:** 100% of original source photos *accounted for*, 46% physically moved. Rights and diagnostic-photo gap filling remain separate work.
