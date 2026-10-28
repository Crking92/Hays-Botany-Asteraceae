#!/usr/bin/env python3
"""Headless visual and direct-link QA for 180-text-record staging preview."""
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT = Path("shell/qa-report/asteraceae-text-preview")
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    for label, size in [("desktop", {"width":1366,"height":850}), ("mobile",{"width":390,"height":844})]:
        page=browser.new_page(viewport=size,device_scale_factor=1)
        errors=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.goto("http://127.0.0.1:8767/?species=achillea-millefolium",wait_until="networkidle")
        assert page.locator("#species-count").inner_text()=="180"
        page.locator("#detail h3",has_text="LOOK HERE FIRST").wait_for()
        text=page.locator("#detail").inner_text()
        assert "Achillea millefolium" in text and "finely" in text.lower(), text[:400]
        assert "Photographs, verified arrows" in text
        assert not page.locator("#detail img").count(), "Rights-unreviewed images leaked into preview"
        page.locator('button[data-mode="field"]').click()
        assert page.locator('button[data-mode="field"]').get_attribute("aria-pressed")=="true"
        page.locator("#search").fill("acourtia")
        assert page.locator("#results button").count()>=1
        width=page.evaluate("document.body.scrollWidth")
        viewport=page.evaluate("document.documentElement.clientWidth")
        assert width<=viewport+1, f"{label}: horizontal overflow {width}/{viewport}"
        assert not errors, errors
        page.locator('button[data-mode="learner"]').click()
        page.locator("#search").fill("")
        page.screenshot(path=str(OUT/f"asteraceae-180-species-{label}.png"),full_page=True)
        print("PASS_ASTERS_TEXT_PREVIEW", label, "180 species, deep link, real anatomy lesson, Field ID, search, zero photos")
        page.close()
    browser.close()
