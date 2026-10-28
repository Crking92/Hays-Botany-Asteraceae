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
        summary=page.request.get("http://127.0.0.1:8767/data/preview-summary.json").json()
        assert summary["verified_photo_copies"]==358, summary
        assert summary["new_texas_cc_field_photo_copies"]==36, summary
        assert summary["new_texas_cc_field_species"]==26, summary
        assert summary["species_with_any_review_photos"]==175, summary
        page.locator("#detail h3",has_text="LOOK HERE FIRST").wait_for()
        page.locator(".gallery-photo img").first.wait_for()
        images=page.locator(".gallery-photo img")
        assert images.count()==2,f"Expected two verified yarrow photographs, found {images.count()}"
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
        page.goto("http://127.0.0.1:8767/?species=gymnosperma-glutinosum",wait_until="networkidle")
        page.locator(".gallery-photo img").first.wait_for()
        owner_text=page.locator("#detail").inner_text()
        assert "Calvin King" in owner_text
        assert "Used with Calvin King's permission" in owner_text
        assert page.locator(".photo-review").count()>=1
        assert page.locator(".gallery-photo img").first.evaluate("(e)=>e.complete && e.naturalWidth>0")
        page.screenshot(path=str(OUT/f"asteraceae-calvin-attribution-{label}.png"),full_page=True)
        page.goto("http://127.0.0.1:8767/?species=chloracantha-spinosa",wait_until="networkidle")
        page.locator(".gallery-photo img").first.wait_for()
        joey_text=page.locator("#detail").inner_text()
        assert "Joey Santore" in joey_text
        assert "CC BY-NC" in joey_text
        assert page.locator(".photo-nc").count()>=1
        assert page.locator(".gallery-photo img").first.evaluate("(e)=>e.complete && e.naturalWidth>0")
        page.goto("http://127.0.0.1:8767/?species=aphanostephus-riddellii",wait_until="networkidle")
        page.locator(".gallery-photo img").first.wait_for()
        gbif_text=page.locator("#detail").inner_text()
        assert "Eric Knight" in gbif_text and "Chet Burrier" in gbif_text
        assert page.locator(".gallery-photo img").count()>=2
        assert all(page.locator(".gallery-photo img").nth(i).evaluate("(e)=>e.complete && e.naturalWidth>0") for i in range(2))
        page.screenshot(path=str(OUT/f"asteraceae-new-gbif-photos-{label}.png"),full_page=True)
        page.goto("http://127.0.0.1:8767/?species=erigeron-geiseri",wait_until="networkidle")
        page.locator(".gallery-photo img").first.wait_for()
        nc_text=page.locator("#detail").inner_text()
        assert "Andy Newman" in nc_text
        assert "CC BY-NC" in nc_text
        assert page.locator(".photo-nc").count()>=1, "New live-verified NC84 photo has no noncommercial warning"
        assert page.locator(".gallery-photo img").first.evaluate("(e)=>e.complete && e.naturalWidth>0")
        page.screenshot(path=str(OUT/f"asteraceae-nc84-new-geiseri-{label}.png"),full_page=True)
        page.goto("http://127.0.0.1:8767/?species=heterotheca-subaxillaris",wait_until="networkidle")
        heads=page.locator(".gallery-photo img")
        heads.first.wait_for()
        assert heads.count()==2,"Camphorweed should show both recovered Commons photos"
        assert "MathKnight" in page.locator("#detail").inner_text()
        assert all(heads.nth(i).evaluate("(e)=>e.complete && e.naturalWidth>0") for i in range(heads.count()))
        page.screenshot(path=str(OUT/f"asteraceae-heterotheca-recovered-{label}.png"),full_page=True)
        page.goto("http://127.0.0.1:8767/?species=carthamus-tinctorius",wait_until="networkidle")
        head=page.locator(".gallery-photo img")
        head.first.wait_for()
        assert head.count()==1,"Safflower needs its original restored photo"
        txt=page.locator("#detail").inner_text()
        assert "Pseudoanas" in txt and "Public domain" in txt
        assert head.first.evaluate("(e)=>e.complete && e.naturalWidth>0")
        page.screenshot(path=str(OUT/f"asteraceae-carthamus-recovered-{label}.png"),full_page=True)
        for taxon_id,artist in [
            ("tetraneuris-linearifolia","Brooke Smith"),
            ("ratibida-columnifera",None),
            ("verbesina-encelioides",None),
            ("plectocephalus-americanus","Annika Lindqvist"),
            ("pyrrhopappus-grandiflorus","Chet Burrier")
        ]:
            page.goto("http://127.0.0.1:8767/?species="+taxon_id,wait_until="networkidle")
            photos=page.locator(".gallery-photo img")
            photos.first.wait_for()
            assert photos.count()==2,(taxon_id,photos.count())
            assert all(photos.nth(i).evaluate("(e)=>e.complete && e.naturalWidth>0") for i in range(2)),taxon_id
            txt=page.locator("#detail").inner_text()
            assert "Texas research-grade observation photograph" in txt,taxon_id
            if artist:assert artist in txt,(taxon_id,artist)
            assert page.locator(".gallery-photo a",has_text="Photo source").count()==2,taxon_id
            assert page.locator(".photo-nc").count()==0,"Public-safe Texas images must not use NC licenses"
        page.screenshot(path=str(OUT/f"asteraceae-new-texas-cc-photo-backfill-{label}.png"),full_page=True)
        assert not errors,errors
        print("ASTERS_REAL_PHOTO_BROWSER_PASS",label,"358 photographs across 175 species; 36 new Texas CC, yarrow, Calvin, Joey, new GBIF, NC and responsive search",flush=True)
        page.close()
    browser.close()
