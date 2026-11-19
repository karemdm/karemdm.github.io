"""Record the NutriLabel web interface in use (Playwright page video, headless, drawn cursor).

Flow: open six real photos with rapidocr, browse results and views, switch to doctr and run it,
compare, export CSV. Prints time marks for editing.
"""
import glob
import json
import sys
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from screencast import Screencast  # noqa: E402

URL = "http://127.0.0.1:9000"
PHOTOS = sorted(glob.glob(r"C:\Users\KAREMDAIANEMARCOMINI\Desktop\portfolio-demos\nutrilabel-photos\*.jpg"))
OUT = Path(r"C:\Users\KAREMDAIANEMARCOMINI\Desktop\portfolio-demos\recordings\nutrilabel-ui-raw.mkv")
VW, VH = 1440, 900
CURSOR_JS = Path(__file__).with_name("cursor.js").read_text(encoding="utf-8")
marks, t0 = [], None


def mark(name):
    marks.append({"name": name, "t": round(time.time() - t0, 2)})
    print("mark", name, marks[-1]["t"], flush=True)


def glide(pg, locator, pause=0.4):
    box = locator.bounding_box()
    pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=18)
    pg.wait_for_timeout(1000 * pause)


def click(pg, locator, pause=0.4):
    glide(pg, locator, pause)
    pg.mouse.down(); pg.mouse.up()


def wait_done(pg, engine, n, timeout=900):
    end = time.time() + timeout
    while time.time() < end:
        if pg.inner_text("#files-title").startswith("%d / %d images read with %s" % (n, n, engine)):
            return
        pg.wait_for_timeout(1000 * 0.5)
    raise TimeoutError(engine)


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context(viewport={"width": VW, "height": VH}, accept_downloads=True)
    ctx.add_init_script(CURSOR_JS)
    pg = ctx.new_page()
    pg.goto(URL)
    sc = Screencast(pg, OUT.parent / ("frames-" + OUT.stem))
    sc.start()
    t0 = time.time()
    pg.wait_for_selector("#engine option", state="attached", timeout=60000)
    pg.mouse.move(VW / 2, VH / 2)
    pg.wait_for_timeout(1000 * 2)
    mark("ready")
    glide(pg, pg.locator("label[for=pick-files]"), 0.8)
    pg.mouse.down(); pg.mouse.up()
    pg.locator("#pick-files").set_input_files(PHOTOS)
    mark("opened")
    pg.wait_for_selector("#file-list .item", timeout=30000)
    # open the first image as soon as it is read
    end = time.time() + 300
    while time.time() < end and "done" not in (pg.locator("#file-list .item").first.inner_text() + pg.inner_text("#files-title")):
        if pg.inner_text("#files-title").startswith("1 /"):
            break
        pg.wait_for_timeout(1000 * 0.5)
    click(pg, pg.locator("#file-list .item").first)
    wait_done(pg, "rapidocr", len(PHOTOS))
    mark("rapidocr_done")
    for i in (1, 3, 5):
        click(pg, pg.locator("#file-list .item").nth(i), 0.3)
        pg.wait_for_timeout(1000 * 2.2)
    for view in ("original", "annotated", "both"):
        click(pg, pg.locator('button[data-view="%s"]' % view), 0.3)
        pg.wait_for_timeout(1000 * 1.8)
    mark("views")
    glide(pg, pg.locator("#engine"), 0.5)
    pg.select_option("#engine", "doctr")
    pg.wait_for_timeout(1000 * 1.2)
    click(pg, pg.locator("#run-btn"), 0.6)
    mark("doctr_run")
    wait_done(pg, "doctr", len(PHOTOS))
    mark("doctr_done")
    for i in (5, 1):
        click(pg, pg.locator("#file-list .item").nth(i), 0.3)
        pg.wait_for_timeout(1000 * 2.5)
    other = pg.locator("#d-other")
    if other.count() and other.is_visible():
        glide(pg, other, 0.4)
        pg.wait_for_timeout(1000 * 1.5)
    with pg.expect_download():
        click(pg, pg.locator("#export-csv"), 0.5)
    mark("exported")
    pg.wait_for_timeout(1000 * 2.5)
    mark("end")
    sc.stop()
    pg.screenshot(path=str(OUT.with_suffix(".final.png")))
    ctx.close()
    sc.to_video(OUT)
    b.close()
Path(str(OUT) + ".marks.json").write_text(json.dumps(marks, indent=1), encoding="utf-8")
print(json.dumps(marks))
