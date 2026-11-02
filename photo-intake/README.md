**Current photo-first instructions (November 2, 2026):** [Shared publishing policy](../workflow/PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02.md). Prioritize useful credited general photographs over detailed anatomy. The publisher now also supports the owner's standing-photo-first mode using `approval_mode: OWNER_STANDING_PHOTO_FIRST_POLICY`, `policy_ref: PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02`, and genuine `review_operator`, `source_review_evidence`, `taxon_review_evidence` and `approval_note`. The old named-human option remains. `rights_approved_for_public` and `taxon_reviewed` must still be true only after actual photo-specific checks. For NC licensing, `noncommercial_site_use_confirmed` must also be true. Never invent evidence or place uncertain-rights bytes into public Git history.

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

Allowed licenses: exact-version CC0, CC BY and CC BY-SA, with CC BY-NC and CC BY-NC-SA 4.0 conditional on documented noncommercial-site and exact-photo verification. No ND, vague rights, false credits or unverified arrows. Source URL must be exact-photo HTTPS. Media limit 25 MB. If any approval field is missing or a photo lacks its matching sidecar, the automatic publish fails safely. New species need a separate reviewed installation first.
