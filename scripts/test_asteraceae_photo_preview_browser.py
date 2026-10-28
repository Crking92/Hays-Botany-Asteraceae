#!/usr/bin/env python3
"""Real-photo desktop/mobile regression; fails if images don't load or rights credits absent."""
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path("shell/qa-report/photo-site");OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    for label,viewport in [("desktop",{"width":1366,"height":850}),("mobile",{"width":390,"height":844})]:
        page=browser.new_page(viewport=viewport,device_scale_factor=1)
        errors=[];page.on("pageerror",lambda error:errors.append(str(error)))
        response=page.goto("http://127.0.0.1:8767/?species=achillea-millefolium",wait_until="networkidle")
        assert response.status==200
        assert page.locator("#species-count").inner_text()=="180"
        page.locator("#detail h3",has_text="LOOK HERE FIRST").wait_for()
        page.locator(".gallery-photo img").first.wait_for()
        images=page.locator(".gallery-photo img")
        assert images.count()>=2,f"Only {images.count()} first pilot yarrow photographs visible"
        for i in range(images.count()):
            assert images.nth(i).evaluate("(e)=>e.complete && e.naturalWidth>0")
        assert page.locator(".gallery-photo a",has_text="Photo source").count()>=1
        assert page.locator(".gallery-photo a",has_text="License").count()>=1
        assert "Jane S. Richardson" in page.locator("#detail").inner_text()
        assert "Fritzflohrreynolds" in page.locator("#detail").inner_text()
        assert page.locator("meta[name=robots]").get_attribute("content")=="noindex,nofollow"
        page.locator('button[data-mode="field"]').click()
        assert page.locator('button[data-mode="field"]').get_attribute("aria-pressed")=="true"
        page.locator("#search").fill("acourtia")
        assert page.locator("#results button").count()>=1
        page.locator("#search").fill("")
        page.locator('button[data-mode="learner"]').click()
        assert page.evaluate("document.body.scrollWidth")<=page.evaluate("document.documentElement.clientWidth")+1
        assert not errors,errors
        page.screenshot(path=str(OUT/f"asteraceae-real-photos-{label}.png"),full_page=True)
        print("ASTERS_REAL_PHOTO_BROWSER_PASS",label,"180 searchable, two yarrow CC photos load, credits, links, Field ID, no overflow",flush=True)
        page.close()
    browser.close()
