#!/usr/bin/env python3
"""Browser smoke test for the nonpublishing Hays Botany collection shell."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qa-report" / "website-prototype"
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for label, viewport in [
        ("desktop", {"width": 1366, "height": 850}),
        ("mobile", {"width": 390, "height": 844}),
    ]:
        page = browser.new_page(viewport=viewport, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        response = page.goto("http://127.0.0.1:8767/", wait_until="networkidle")
        assert response.status == 200, response.status
        assert page.locator("#collection-title").inner_text() == "Asteraceae Visual Learner"
        assert "0" == page.locator("#species-count").inner_text()
        assert "No species imported yet" in page.locator("#results").inner_text()
        assert page.locator('meta[name="robots"]').get_attribute("content") == "noindex,nofollow"
        page.locator('button[data-mode="field"]').click()
        assert page.locator('button[data-mode="field"]').get_attribute("aria-pressed") == "true"
        assert page.locator('a[href="https://crking92.github.io/Hays-County-Botany/"]').count() >= 1
        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = page.evaluate("document.documentElement.clientWidth")
        assert body_width <= viewport_width + 1, f"{label}: horizontal overflow {body_width}/{viewport_width}"
        assert not errors, errors
        page.locator('button[data-mode="learner"]').click()
        page.screenshot(path=str(OUT / f"asteraceae-{label}.png"), full_page=True)
        print(f"BROWSER_PASS {label}: 0 exceptions; search shell; learner/field mode; no overflow")
        page.close()
    browser.close()
