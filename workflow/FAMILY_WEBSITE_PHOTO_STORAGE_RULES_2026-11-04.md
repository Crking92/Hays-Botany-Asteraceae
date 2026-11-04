# Family gallery size safety — Asteraceae pilot (2026-11-04)

The owner wants many more general, credited photos (perhaps 200–500 per family)
without moving the existing collections to new GitHub repositories or manually
re-uploading old images. **No original file deletion and no Git history rewrite.**

## Now

- Same 180-species family website, same original source URLs and attribution.
- Initial web photos (759) optimized, but later photo batches increased the
  gallery to 892 and some new large originals were published.
- Standard approved-photo route now makes a display copy BEFORE writing
  site/media: <=650,000 bytes where safely achievable. It retains the true
  original sha256/Git blob source hashes and separately records the actual
  display hashes, modifications, and intake provenance.
- Warning at 750 MB; block a proposed new site publication above 850 MB.
  Source photos remain intact on a failed size check.
- Photo-specific rights, taxon and attribution gates remain in effect.
- Website/gallery and live photo byte checks remain required.

## Future originals without a second repository

- Keep existing archived originals and historical files in place; the owner
  should not have to transfer them.
- For future incoming original ZIP batches, the **preferred next automation**
  is to attach a checksum-verified original ZIP plus photo credits/rights
  manifest as a **GitHub Release asset in the same family repository**, and
  publish only compressed website copies to Git. This avoids putting another
  entire round of multi-megabyte originals in Git history.
- Release attachment automation is not active in every intake workflow yet.
  Never claim the original was backed up to Releases unless the asset was
  uploaded and its checksum checked. Keep all approved source photos until
  that preservation step is done.
- Continue original-photo selection and copyright screening; don't use
  resized web copies as substitutes for originals in anatomy work.

## Site sizing with additional 200–500 photos

- At <=650 KB each, 200 new display photos add at most 130 MB,
  while 500 add at most 325 MB.
- The original 1 GB Pages published-site cap and the **different** repository
  recommended-size guidelines are separate constraints.
- For Asteraceae, optimize the remaining large display JPEGs before the
  next 500-photo batch if the 850 MB website safety budget would be reached.
- This workflow change is an Asteraceae pilot. Other family publishers need
  individual checks before adopting it. Do not touch the legacy hub.

## Preserve provenance

Both source and display hashes exist in the photo records if compression is
performed. Publish the photo's creator, exact source URL, license and the
modification statement. Respect CC BY-SA/NC/NC-SA conditions where applicable.
Never silently replace existing media or re-label an unverified image.
