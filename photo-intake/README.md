# Approved image upload — Asteraceae

**This is a PUBLIC repository.** Do not upload photographs here unless each original is cleared for public source access and reuse. Keep unclear-rights photos outside the public repository.

Upload both `photo-intake/approved/achillea-millefolium/yarrow-new-view.jpg` and `photo-intake/approved/achillea-millefolium/yarrow-new-view.jpg.json` to branch `staging/asteraceae-metadata`. Name both files for the SAME photograph. Each real file requires a manual license and ID review.

Example sidecar structure (PLACEHOLDERS ONLY — not an actual approval):

```json
{
  "species_id": "achillea-millefolium",
  "photo_file": "yarrow-new-view.jpg",
  "status": "APPROVED_FOR_PUBLIC_FAMILY_SITE",
  "rights_approved_for_public": true,
  "taxon_reviewed": true,
  "approved_by": "Name of actual reviewer",
  "approval_note": "Describe verified exact photo source, license and taxonomic evidence",
  "creator": "Name of the real photographer",
  "source_page": "https://www.example.org/exact-individual-photo-page",
  "source_page_is_exact": true,
  "license": "CC BY 4.0",
  "license_url": "https://creativecommons.org/licenses/by/4.0/",
  "role": "Only morphological structures clearly visible in the uploaded image",
  "modifications": "Exact original or detailed alterations"
}
```

Allowed licenses: exact-version CC0, CC BY, and CC BY-SA only. Source URL must be exact-photo HTTPS. No NC/ND, vague rights, false credits, or unverified arrows. Media limit 25 MB. If any approval field is missing or a photo lacks its matching sidecar, the automatic publish fails safely. New species need a separate reviewed installation first.
