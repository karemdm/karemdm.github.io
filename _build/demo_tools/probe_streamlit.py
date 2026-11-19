"""Open the Streamlit app in Edge (Playwright) and dump its widgets and a screenshot, to plan the recording."""
import sys
import time

from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
out = sys.argv[2] if len(sys.argv) > 2 else "probe.png"
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 840})
    pg.goto(url)
    pg.wait_for_selector("text=Upload a video", timeout=60000)
    time.sleep(2)
    for sel in ["[data-testid=stSidebar] label", "[data-testid=stFileUploaderDropzone]", "h1", "[data-testid=stSidebar] [data-baseweb=select]"]:
        for el in pg.query_selector_all(sel)[:12]:
            box = el.bounding_box()
            print(sel, "|", (el.inner_text() or "")[:70].replace("\n", " / "), "|", box and {k: round(v) for k, v in box.items()})
    pg.screenshot(path=out)
    b.close()
