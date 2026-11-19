"""Screen-record the line-counter desktop flow: launcher, file dialog, drawing two lines, processing, result.

Windows are moved onto a fixed stage that ffmpeg records; every keystroke and click first checks that the
expected window has the focus (it stops instead of typing elsewhere). Prints time marks for editing.
"""
import ctypes
import json
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

ctypes.windll.user32.SetProcessDPIAware()
import imageio_ffmpeg  # noqa: E402
import pyautogui  # noqa: E402
import pygetwindow as gw  # noqa: E402

user32 = ctypes.windll.user32
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND] + [ctypes.c_int] * 4 + [ctypes.c_uint]
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]

ROOT = Path(r"C:\Users\KAREMDAIANEMARCOMINI\Desktop\portfolio-demos")
REPO = ROOT / "directional-line-crossing-counter"
VIDEO = REPO / "samples" / "shinjuku_crossing_60s.mp4"
OUTDIR = REPO / "outputs"
OUT = ROOT / "recordings" / "line-counter-raw.mkv"
SX, SY, SW, SH = 240, 40, 1440, 1080           # recorded stage
MAIN = (0, 0, 1440, 840)                         # OpenCV windows
CONSOLE = (0, 840, 1440, 240)
# two lines in frame coordinates (1920x1080): big crosswalk (pedestrians) and the crossing lane (vehicles)
FRAME_W, FRAME_H = 1920, 1080
LINES = [((720, 730), (1850, 560)), ((1010, 190), (1010, 440))]
marks, t0 = [], None


def mark(name):
    marks.append({"name": name, "t": round(time.time() - t0, 2)})
    print("mark", name, marks[-1]["t"], flush=True)


def windows(pred):
    """Visible windows matching pred(title, w), ignoring windows that vanish while being inspected."""
    out = []
    for w in gw.getAllWindows():
        try:
            if w.visible and pred(w.title.strip(), w):
                out.append(w)
        except Exception:
            continue
    return out


def place(win, x, y, w, h):
    user32.SetWindowPos(win._hWnd, -1, SX + x, SY + y, w, h, 0x0040)
    raise_backdrop()


def find(title, timeout=120, exact=False):
    end = time.time() + timeout
    while time.time() < end:
        found = windows(lambda t, w: w.width > 100 and (t == title if exact else t.startswith(title)))
        if found:
            return found[0]
        time.sleep(0.2)
    raise TimeoutError(title)


def focus(win):
    for _ in range(6):
        pyautogui.press("alt")
        user32.SetForegroundWindow(win._hWnd)
        time.sleep(0.25)
        if user32.GetForegroundWindow() == win._hWnd:
            return
        pyautogui.click(win.left + win.width // 2, win.top + 12)
        time.sleep(0.3)
        if user32.GetForegroundWindow() == win._hWnd:
            return
    raise RuntimeError("no focus: " + win.title)


def keys(win, *seq):
    focus(win)
    for k in seq:
        pyautogui.press(k)
        time.sleep(0.35)


def type_in(win, text, enter=True, clear=False):
    focus(win)
    time.sleep(0.6)
    if clear:  # file dialogs: replace whatever the name field holds
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)
    pyautogui.write(text, interval=0.02)
    time.sleep(0.3)
    if enter:
        pyautogui.press("enter")


def client_point(win, fx, fy, fw=FRAME_W, fh=FRAME_H):
    rc = wintypes.RECT()
    user32.GetClientRect(win._hWnd, ctypes.byref(rc))
    pt = wintypes.POINT(0, 0)
    user32.ClientToScreen(win._hWnd, ctypes.byref(pt))
    return pt.x + fx * rc.right / fw, pt.y + fy * rc.bottom / fh


BUTTONS = {1: (215, 81), 2: (215, 152), 3: (215, 210)}  # launcher button centres in client pixels


def press_button(win, n):
    focus(win)
    pt = wintypes.POINT(*BUTTONS[n])
    user32.ClientToScreen(win._hWnd, ctypes.byref(pt))
    pyautogui.moveTo(pt.x, pt.y, duration=0.6)
    time.sleep(0.3)
    pyautogui.click()


def raise_backdrop():
    """Put the backdrop above normal windows (but below the demo's topmost windows)."""
    for w in windows(lambda t, w: t == "tk" and w.width >= SW - 2):
            user32.SetWindowPos(w._hWnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)  # HWND_NOTOPMOST, keep size/pos
            user32.SetWindowPos(w._hWnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)   # HWND_TOP in the normal band


def close_dialog(title):
    """Close a Tk message box (WM_CLOSE on the visible window with that title); fall back to Enter."""
    for w in windows(lambda t, w: t == title):
            try:
                w.close()
                return
            except Exception:
                pass
    pyautogui.press("enter")
    time.sleep(0.4)
    raise_backdrop()


def gone(title, timeout):
    end = time.time() + timeout
    while time.time() < end:
        if not windows(lambda t, w: t.startswith(title)):
            return
        time.sleep(0.4)
    raise TimeoutError("still open: " + title)


def main():
    global t0
    OUTDIR.mkdir(exist_ok=True)
    backdrop = subprocess.Popen([sys.executable, str(Path(__file__).with_name("backdrop.py")), str(SX), str(SY), str(SW), str(SH), "#1b1c1e"])
    time.sleep(1.0)
    subprocess.Popen(["cmd", "/k", r"title line-counter& prompt directional-line-crossing-counter$G$S& color 0F& "
                      r"call ..\.venv-video\Scripts\activate.bat& cls"], cwd=str(REPO), creationflags=subprocess.CREATE_NEW_CONSOLE)
    con = find("line-counter", 20)
    place(con, *CONSOLE)
    time.sleep(1.0)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    rec = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "gdigrab", "-framerate", "20", "-offset_x", str(SX), "-offset_y", str(SY),
                            "-video_size", "%dx%d" % (SW, SH), "-draw_mouse", "1", "-i", "desktop", "-c:v", "libx264",
                            "-preset", "ultrafast", "-crf", "16", "-pix_fmt", "yuv420p", str(OUT)], stdin=subprocess.PIPE)
    t0 = time.time()
    try:
        time.sleep(1.0)
        type_in(con, "line-counter --gui --imgsz 960 --conf 0.2")
        app = find("Directional Line Crossing Counter", 90, exact=True)
        place(app, 495, 240, 450, 300)
        mark("launcher")
        time.sleep(1.5)
        press_button(app, 1)                            # 1. Select Input Video
        dlg = find("Select Video File", 30)
        place(dlg, 220, 120, 1000, 600)
        time.sleep(0.8)
        type_in(dlg, str(VIDEO), clear=True)
        mark("video_selected")
        time.sleep(1.5)
        press_button(app, 2)                            # 2. Draw Lines on Frame
        ed = find("Draw Lines", 30)
        place(ed, *MAIN)
        time.sleep(1.5)
        mark("editor")
        for p1, p2 in LINES:
            for fx, fy in (p1, p2):
                x, y = client_point(ed, fx, fy)
                pyautogui.moveTo(x, y, duration=0.7)
                time.sleep(0.25)
                pyautogui.click()
                time.sleep(0.6)
        time.sleep(1.0)
        keys(ed, "enter")
        mark("lines")
        ok = find("Success", 15)
        time.sleep(1.6)
        close_dialog("Success")
        time.sleep(1.0)
        press_button(app, 3)                            # 3. Process and Save Video
        dd = find("Select Output Directory", 30)
        place(dd, 220, 120, 1000, 600)
        time.sleep(0.8)
        type_in(dd, str(OUTDIR), clear=True)
        time.sleep(1.0)
        if windows(lambda t, w: t.startswith("Select Output Directory")):
            keys(dd, "enter")
        prev = find("Processing", 120)
        place(prev, *MAIN)
        mark("processing")
        gone("Processing", 1500)
        mark("processed")
        fin = find("Finished", 60)
        time.sleep(2.5)
        close_dialog("Finished")
        time.sleep(1.0)
        mark("end")
    except Exception as e:
        print("FAILED:", repr(e), flush=True)
        mark("error")
    finally:
        rec.communicate(b"q", timeout=60)
        for w in windows(lambda t, w: t in ("line-counter", "Directional Line Crossing Counter") or t.startswith("line-counter")):
            try:
                w.close()
            except Exception:
                pass
        backdrop.terminate()
        Path(str(OUT) + ".marks.json").write_text(json.dumps(marks, indent=1), encoding="utf-8")
        print(json.dumps(marks))


if __name__ == "__main__":
    main()
