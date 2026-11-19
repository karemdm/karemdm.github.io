"""Record the PPE Streamlit app in use: sidebar choices, upload, live feed and the VLM report cards.

Playwright drives a headless Edge page and records the page itself (no screen capture, so the
desktop can be used meanwhile). A drawn cursor shows where the clicks happen. Prints time marks
(seconds from the start of the page video) for editing.
"""
import json
import shutil
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from screencast import Screencast  # noqa: E402

URL = "http://127.0.0.1:8501"
VIDEO = r"C:\Users\KAREMDAIANEMARCOMINI\Desktop\portfolio-demos\ppe-compliance-vlm\outputs\construction_12s.mp4"
OUT = Path(r"C:\Users\KAREMDAIANEMARCOMINI\Desktop\portfolio-demos\recordings\ppe-app-raw.mkv")
VW, VH = 1440, 900
KEEP = ("Hardhat", "Safety vest")
CURSOR_JS = """
window.addEventListener('DOMContentLoaded', () => {
  const c = document.createElement('div');
  c.id = '__cursor';
  c.style.cssText = 'position:fixed;left:0;top:0;width:22px;height:22px;z-index:2147483647;pointer-events:none;' +
    'transform:translate(-3px,-2px);transition:transform .05s;';
  c.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M3 2l7 19 2.6-7.4L20 11z" ' +
    'fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
  document.body.appendChild(c);
  document.addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
  document.addEventListener('mousedown', () => { c.style.transform = 'translate(-3px,-2px) scale(.8)'; }, true);
  document.addEventListener('mouseup', () => { c.style.transform = 'translate(-3px,-2px)'; }, true);
});
"""
marks, t0 = [], None


def mark(name):
    marks.append({"name": name, "t": round(time.time() - t0, 2)})
    print("mark", name, marks[-1]["t"], flush=True)


def glide(pg, locator, pause=0.35):
    """Moves the mouse smoothly to the center of ``locator`` and returns that point."""
    box = locator.bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    pg.mouse.move(x, y, steps=18)
    pg.wait_for_timeout(1000 * pause)
    return x, y


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context(viewport={"width": VW, "height": VH})
    ctx.add_init_script(CURSOR_JS)
    pg = ctx.new_page()
    pg.goto(URL)
    sc = Screencast(pg, OUT.parent / ("frames-" + OUT.stem))
    sc.start()
    t0 = time.time()
    pg.wait_for_selector("text=Upload a video", timeout=90000)
    pg.mouse.move(700, 450)
    pg.wait_for_timeout(1000 * 2.0)
    mark("ready")
    # keep only the hardhat and safety vest infractions
    while True:
        btns = [x for x in pg.locator('[data-testid=stSidebar] button[aria-label^="Remove "]').all()
                if not any(k in (x.get_attribute("aria-label") or "") for k in KEEP)]
        if not btns:
            break
        glide(pg, btns[0])
        pg.mouse.down(); pg.mouse.up()
        pg.wait_for_timeout(1000 * 1.0)
    mark("infractions")
    pg.wait_for_timeout(1000 * 1.0)
    glide(pg, pg.locator("[data-testid=stFileUploaderDropzone] button").first, 0.8)
    pg.mouse.down(); pg.mouse.up()
    pg.locator("input[type=file]").set_input_files(VIDEO)
    mark("uploaded")
    pg.mouse.move(VW - 60, VH - 60, steps=15)
    pg.wait_for_selector("text=Processing video", timeout=120000)
    mark("processing")
    deadline = time.time() + 1800
    while time.time() < deadline:
        txt = pg.inner_text("body")
        if "Video processed" in txt and not any(m["name"] == "processed" for m in marks):
            mark("processed")
        if "Reports ready for" in txt or "No significant infractions" in txt:
            break
        pg.wait_for_timeout(1000 * 0.5)
    mark("done")
    # Streamlit lazy-loads images below the fold: load every report crop before scrolling to them
    pg.evaluate("document.querySelectorAll('img').forEach(i => { i.loading = 'eager'; })")
    end = time.time() + 60
    while time.time() < end and not pg.evaluate(
            "[...document.querySelectorAll('img')].every(i => i.complete && i.naturalWidth > 0)"):
        pg.wait_for_timeout(1000 * 0.3)
    mark("images_loaded")
    pg.wait_for_timeout(1000 * 1.0)
    rep = pg.get_by_text("Report - person").first
    if rep.count():
        glide(pg, rep, 0.4)
    pg.mouse.move(VW - 24, VH / 2, steps=14)  # park the cursor on the empty margin: no hover toolbars
    for _ in range(10):
        pg.mouse.wheel(0, 90)
        pg.wait_for_timeout(1000 * 0.15)
    mark("scrolled")
    pg.wait_for_timeout(1000 * 5.0)
    for _ in range(12):
        pg.mouse.wheel(0, 90)
        pg.wait_for_timeout(1000 * 0.15)
    pg.wait_for_timeout(1000 * 4.0)
    mark("end")
    sc.stop()
    pg.screenshot(path=str(OUT.with_suffix(".final.png")), full_page=True)
    ctx.close()
    sc.to_video(OUT)
    b.close()
Path(str(OUT) + ".marks.json").write_text(json.dumps(marks, indent=1), encoding="utf-8")
print(json.dumps(marks))
