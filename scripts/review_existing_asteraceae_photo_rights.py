"""Exact, narrowly scoped existing-source photo review for missing Asteraceae cards.

No new photos, no URL downloads, no rights-unknown media, no NC/ND photos.
Return the explicit class/link only when archived PHOTO evidence supports it.
Do not treat a GBIF occurrence's dataset license as a photo license.
"""
import re

PD_MANUAL={
 ("cirsium-ochrocentrum","images/cirsium-ochrocentrum-provisional-face.jpg"):
   ("Clarence A. Rechenthin","https://commons.wikimedia.org/wiki/File:Cirsiumochrocentrum.jpg","Public domain (USDA NRCS / U.S. federal work)"),
 ("gutierrezia-texana","images/01-uvalde-flowering-canopy.jpg"):
   ("Jim Conrad","https://backyardnature.net/n/h/gut-tex.htm","Public domain — original photographer Jim Conrad"),
 ("gutierrezia-texana","images/02-uvalde-composite-head.jpg"):
   ("Jim Conrad","https://backyardnature.net/n/h/gut-tex.htm","Public domain — original photographer Jim Conrad"),
 ("vernonia-lindheimeri","images/vernonia-lindheimeri-provisional-face.jpg"):
   ("Mason Brock (Masebrock)","https://commons.wikimedia.org/wiki/File:Vernonia_lindheimeri.jpg","Public domain — author dedication (PD-user-en)")
}
def reviewed(photo,sid,strict_license):
    f=photo.get("file");license=str(photo.get("license") or "")
    page=str(photo.get("source_page") or "")
    creator=str(photo.get("creator") or "").strip()
    reuse=str(photo.get("public_reuse") or "")
    if not isinstance(f,str) or not re.fullmatch(r"images/[A-Za-z0-9._-]+\.jpg",f):
        return None
    if not creator or re.search(r"\b(?:nc|nd)\b|all rights|unknown|not verified|unverified",license,re.I):
        return None
    # The exact previously archived Commons or author's self-owned image only.
    pd=PD_MANUAL.get((sid,f))
    if pd is not None:
        if (creator,page,license)!=pd or not (reuse in ("yes","public-domain","public_domain")):
            return None
        return ("Public Domain","https://creativecommons.org/publicdomain/mark/1.0/",
                "Photographer/source-specific public-domain evidence; original archived source photo, not general license for third-party photos.")
    # Two accessible license-classes from the source card's exact photo record.
    # A taxon or observation page alone does not suffice.
    if (license.upper()=="CC0 1.0"
        and page.startswith("https://www.inaturalist.org/photos/")
        and str(photo.get("photo_id"))==page.rstrip("/").split("/")[-1]
        and str(photo.get("source_recorded_photo_license_at_download") or "").lower()=="cc0"
        and str(photo.get("license_url") or "")=="https://creativecommons.org/publicdomain/zero/1.0/"
        and reuse.startswith("yes")):
        return ("CC0 1.0","https://creativecommons.org/publicdomain/zero/1.0/",
                "Archived image-specific iNaturalist CC0 photo ID and original photo license; no anatomical voucher claim.")
    # GBIF-backed individual media whose precise original image URL and photo-level
    # license are recorded in the old source card. CC0 only, never general CC BY.
    # Excludes photo libraries marked REVIEW/PRIVATE and all source-domain-only claims.
    media=str(photo.get("media_source_url") or "")
    if (license.upper()=="CC0 1.0" and
        str(photo.get("license_url") or "")=="https://creativecommons.org/publicdomain/zero/1.0/"
        and re.fullmatch(r"https://www\.gbif\.org/occurrence/[0-9]+",page)
        and re.fullmatch(r"https://inaturalist-open-data\.s3\.amazonaws\.com/photos/[0-9]+/original\.(?:jpg|jpeg)",media)
        and str(photo.get("source_determination") or "").lower().startswith(
            sid.replace("-"," ").split(" var ")[0].split(" subsp ")[0])
        and "review" not in reuse.lower() and "private" not in reuse.lower()
        and "license" in reuse.lower()):
        return ("CC0 1.0","https://creativecommons.org/publicdomain/zero/1.0/",
                "Exact archived GBIF photographic media URL with CC0 photo record and matching species label; no independent voucher determination.")
    return None
