# Asteraceae auto-photo publish — reviewed source to live family website

The photo-publishing system has passed an isolated end-to-end test on an existing Common Yarrow photograph. A committed original and matching approved JSON sidecar added under `photo-intake/approved/<species-id>/` on the `staging/asteraceae-metadata` branch trigger the publishing workflow.

- Always perform real individual-image **taxon identification and source-license** checks first. The approval fields are an auditable human claim, not an automatic source-verification service.
- These public repositories expose their Git history. Never upload private-only or rights-unclear originals to intake.
- Upload both `<name>.jpg` and `<name>.jpg.json` in the same species folder. Use the exact fields in [the sample](../photo-intake/README.md).
- The workflow checks actual JPEG/PNG/WebP image content, rights approvals, creator/source/licensing and exact registered species; it adds the hosted binary to `main/site/media/<species-id>/`, appends it to the corresponding species JSON, and updates both gallery and collection-index counts. It is idempotent and fails closed on conflicts.
- If changed, it commits with non-force push and requests a GitHub Pages rebuild. It does **not** change the original Hays-County-Botany learner, invent arrows, add a new taxon, or publish an image that lacks signed-off metadata.
- The central family hub's static collection counts may still need a refresh; the actual Asteraceae site/photo count is automatically updated.

[Watch publishing jobs](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/workflows/auto-publish-approved-photos.yml) · [Current family learner](https://crking92.github.io/Hays-Botany-Asteraceae/site/) · [Isolated passing intake test](https://github.com/Crking92/Hays-Botany-Asteraceae/actions/runs/41091142551)
