#!/usr/bin/env python3
"""Make web-size Asteraceae display JPEGs without destroying original/source hashes.

The pre-optimization originals remain at an immutable commit on an archive branch.
This program deliberately keeps original sha256/source_blob_sha fields untouched;
display_sha256/display_blob_sha identify the new, derived JPEG website bytes.
"""
import argparse
import hashlib
import io
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_DISPLAY_BYTES = 760 * 1024
TARGET_SITE_BYTES = 650_000_000
IMAGE_EXTENSIONS = {".jpg", ".jpeg"}

def blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

def archive_blobs(commit):
    lines = git("ls-tree", "-r", commit, "--", "site/media").splitlines()
    result = {}
    for line in lines:
        if "\t" not in line:
            continue
        metadata, path = line.split("\t", 1)
        bits = metadata.split()
        if len(bits) == 3 and bits[1] == "blob":
            result[path] = bits[2]
    return result

def encode_display(data):
    try:
        with Image.open(io.BytesIO(data)) as source:
            source.load()
            image = ImageOps.exif_transpose(source)
            if image.mode != "RGB":
                image = image.convert("RGB")
            original_dimensions = (image.width, image.height)
            icc = source.info.get("icc_profile")
            if icc and len(icc) > 131072:
                icc = None
            best = None
            best_geometry = None
            for max_side, quality in ((2600, 85), (2400, 83), (2200, 81),
                                      (2050, 80), (1900, 78), (1750, 76),
                                      (1600, 74), (1450, 72)):
                display = image.copy()
                display.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
                target = io.BytesIO()
                display.save(target, format="JPEG", quality=quality,
                             optimize=True, progressive=True,
                             subsampling=0, icc_profile=icc)
                candidate = target.getvalue()
                if best is None or len(candidate) < len(best):
                    best = candidate
                    best_geometry = (display.width, display.height, quality)
                if len(candidate) <= MAX_DISPLAY_BYTES:
                    return candidate, original_dimensions, best_geometry
            return best, original_dimensions, best_geometry
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        raise RuntimeError("Image could not be safely optimized") from exc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-sha", required=True)
    parser.add_argument("--archive-branch", required=True)
    parser.add_argument("--site-root", default="site")
    args = parser.parse_args()
    site = Path(args.site_root)
    catalog = json.loads((site / "data/collection-index.json").read_text())
    gallery = json.loads((site / "data/gallery-index.json").read_text())
    assert len(catalog["entries"]) == gallery["species"] == 180
    previous_report = site / "data/web-display-optimization.json"
    if previous_report.is_file():
        previous = json.loads(previous_report.read_text())
        if previous.get("display_image_count") != gallery["photo_count"]:
            prior = site / "data/web-display-optimization-first-pass.json"
            if not prior.exists():
                prior.write_bytes(previous_report.read_bytes())
        if previous.get("display_image_count") == gallery["photo_count"]:
            print("ASTERACEAE_WEB_DISPLAY_ALREADY_OPTIMIZED " +
                  json.dumps({"photos": gallery["photo_count"],
                              "media_bytes": previous.get("optimized_media_bytes")}), flush=True)
            return
    archive = archive_blobs(args.archive_sha)
    assert len(archive) >= gallery["photo_count"], "Archive is missing photographs"
    rows = []
    total_before = 0
    total_after = 0
    modified = 0
    untouched = 0
    all_sources = set()
    for entry in catalog["entries"]:
        sid = entry["id"]
        card_path = site / "data/species" / (sid + ".json")
        card = json.loads(card_path.read_text())
        photos = card.get("verified_photos", [])
        assert len(photos) == entry["photo_count"] == gallery["entries"][sid]["count"]
        card_changed = False
        for photo in photos:
            src = photo["src"]
            assert src.startswith("media/" + sid + "/"), src
            assert Path(src).suffix.lower() in IMAGE_EXTENSIONS, src
            assert src not in all_sources, src
            all_sources.add(src)
            current_file = site / src
            assert current_file.is_file() and not current_file.is_symlink(), src
            current = current_file.read_bytes()
            total_before += len(current)
            archive_path = "site/" + src
            assert archive_path in archive, "Missing original in pinned archive: " + src
            if photo.get("display_sha256"):
                assert hashlib.sha256(current).hexdigest() == photo["display_sha256"], src
                total_after += len(current)
                untouched += 1
                continue
            original_blob = blob_sha(current)
            assert archive[archive_path] == original_blob, "Archive/original mismatch: " + src
            if photo.get("sha256"):
                assert hashlib.sha256(current).hexdigest() == photo["sha256"], src
            if len(current) <= MAX_DISPLAY_BYTES:
                total_after += len(current)
                untouched += 1
                continue
            optimized, original_dims, geometry = encode_display(current)
            assert optimized and len(optimized) < len(current), src
            assert len(optimized) <= MAX_DISPLAY_BYTES, "Individual JPEG exceeds display budget: " + src
            current_file.write_bytes(optimized)
            photo["display_sha256"] = hashlib.sha256(optimized).hexdigest()
            photo["display_blob_sha"] = blob_sha(optimized)
            photo["display_original_site_sha256"] = hashlib.sha256(current).hexdigest()
            photo["display_original_blob_sha"] = original_blob
            photo["display_original_archive_commit"] = args.archive_sha
            photo["display_modifications"] = "Resized and JPEG-compressed for web display; exact original preserved in archive branch."
            previous = photo.get("modified") or ""
            photo["modified"] = (previous.rstrip(". ") + "; " if previous else "") + "web copy resized and recompressed; archived original unchanged"
            photo["display_dimensions"] = [geometry[0], geometry[1]]
            photo["display_bytes"] = len(optimized)
            card_changed = True
            modified += 1
            total_after += len(optimized)
            rows.append({"src": src,
                         "original_bytes": len(current),
                         "web_bytes": len(optimized),
                         "original_sha256": photo["display_original_site_sha256"],
                         "display_sha256": photo["display_sha256"],
                         "original_dimensions": original_dims,
                         "display_dimensions": photo["display_dimensions"]})
        if card_changed:
            card_path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n")
    actual = {p.relative_to(site).as_posix() for p in (site / "media").rglob("*") if p.is_file()}
    assert actual == all_sources, "Orphan/unreferenced images in public site"
    assert total_after <= TARGET_SITE_BYTES, ("Optimized gallery still exceeds the target", total_after)
    record = {
        "schema_version": 1,
        "purpose": "Web-display derivatives; exact originals are preserved in a pinned Git commit",
        "original_archive_repository": "Crking92/Hays-Botany-Asteraceae",
        "original_archive_branch": args.archive_branch,
        "original_archive_commit": args.archive_sha,
        "display_image_count": len(all_sources),
        "optimized_image_count": modified,
        "untouched_image_count": untouched,
        "original_media_bytes": total_before,
        "optimized_media_bytes": total_after,
        "saved_media_bytes": total_before - total_after,
        "display_max_bytes_per_image": MAX_DISPLAY_BYTES,
        "site_media_target_bytes": TARGET_SITE_BYTES,
        "changes": rows,
    }
    (site / "data/web-display-optimization.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    print("ASTERACEAE_WEB_DISPLAY_OPTIMIZATION " + json.dumps({
        "photos": len(all_sources), "optimized": modified,
        "unchanged": untouched,
        "original_media_bytes": total_before,
        "new_media_bytes": total_after,
        "saved_bytes": total_before - total_after,
        "archive_commit": args.archive_sha,
    }), flush=True)

if __name__ == "__main__":
    main()
