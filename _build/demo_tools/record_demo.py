"""Record a scripted screen demo of a project running.

Opens a console on a fixed "stage" region of the screen, types commands into it,
moves the windows the program opens into place (kept on top), and records only
the stage region with ffmpeg gdigrab. Usage:

    python record_demo.py scenario.json
"""
import ctypes
import json
import subprocess
import sys
import time
from pathlib import Path

ctypes.windll.user32.SetProcessDPIAware()
import imageio_ffmpeg  # noqa: E402
import pyautogui  # noqa: E402
import pygetwindow as gw  # noqa: E402

user32 = ctypes.windll.user32
from ctypes import wintypes  # noqa: E402
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
HWND_TOPMOST = -1
SWP_SHOWWINDOW = 0x0040


def place(win, x, y, w, h, topmost=True):
    win.restore() if win.isMinimized else None
    user32.SetWindowPos(win._hWnd, HWND_TOPMOST if topmost else 0, x, y, w, h, SWP_SHOWWINDOW)


def find(title, timeout=120):
    end = time.time() + timeout
    while time.time() < end:
        ws = [w for w in gw.getAllWindows() if (w.title.strip() == title or w.title.startswith(title + " - "))
              and w.visible and w.width > 100]
        if ws:
            return ws[0]
        time.sleep(0.2)
    raise TimeoutError(title)


def focus(win):
    """Bring win to the foreground; refuse to continue if another window keeps the focus."""
    for _ in range(6):
        pyautogui.press("alt")  # lifts the foreground lock for this process
        user32.SetForegroundWindow(win._hWnd)
        time.sleep(0.25)
        if user32.GetForegroundWindow() == win._hWnd:
            return
        pyautogui.click(win.left + win.width // 2, win.top + 12)  # click the title bar
        time.sleep(0.3)
        if user32.GetForegroundWindow() == win._hWnd:
            return
    raise RuntimeError("console did not get the focus; not typing")


def main(cfg_path):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    sx, sy, sw, sh = cfg["stage"]
    out = Path(cfg["output"])
    out.parent.mkdir(parents=True, exist_ok=True)
    marks = []
    t0 = None

    def mark(name):
        marks.append({"name": name, "t": round(time.time() - t0, 2)})

    # backdrop window so nothing else shows inside the stage
    backdrop = subprocess.Popen([sys.executable, str(Path(__file__).with_name("backdrop.py")), str(sx), str(sy), str(sw), str(sh), cfg.get("backdrop", "#1b1c1e")])
    time.sleep(1.0)

    consoles = {}
    for c in cfg["consoles"]:
        subprocess.Popen(["cmd", "/k", "title %s& prompt %s$G$S& color %s& %scls" % (c["title"], c.get("prompt", c["title"]), c.get("color", "0F"), (c["init"] + "& ") if c.get("init") else "")],
                         cwd=c["cwd"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        win = find(c["title"], 20)
        x, y, w, h = c["rect"]
        place(win, sx + x, sy + y, w, h)
        consoles[c["title"]] = win
    time.sleep(1.0)

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    rec = subprocess.Popen([ffmpeg, "-y", "-loglevel", "error", "-f", "gdigrab", "-framerate", str(cfg.get("fps", 20)),
                            "-offset_x", str(sx), "-offset_y", str(sy), "-video_size", "%dx%d" % (sw, sh),
                            "-draw_mouse", str(cfg.get("draw_mouse", 0)), "-i", "desktop", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "16",
                            "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    t0 = time.time()
    time.sleep(1.0)

    try:
      for step in cfg["steps"]:
          kind = step["do"]
          if kind == "type":
              win = consoles[step["console"]]
              focus(win)
              mark("type:" + step.get("label", "")); print("step", step.get("label"), flush=True)
              pyautogui.write(step["text"], interval=step.get("interval", 0.035))
              if step.get("enter", True):
                  pyautogui.press("enter")
          elif kind == "window":
              win = find(step["title"], step.get("timeout", 300))
              mark("window:" + step["title"])
              x, y, w, h = step["rect"]
              place(win, sx + x, sy + y, w, h)
          elif kind == "wait_gone":
              end = time.time() + step.get("timeout", 900)
              while time.time() < end and gw.getWindowsWithTitle(step["title"]):
                  time.sleep(0.3)
              mark("gone:" + step["title"])
          elif kind == "sleep":
              time.sleep(step["s"])
          elif kind == "mark":
              mark(step["name"])
          elif kind == "click":
              pyautogui.click(sx + step["x"], sy + step["y"])
              mark("click:" + step.get("label", ""))

    except Exception as e:
        print("STEP FAILED:", repr(e), flush=True)
        mark("error")
    time.sleep(cfg.get("tail", 2.0))
    mark("end")
    rec.communicate(b"q", timeout=60)
    for win in consoles.values():
        try:
            win.close()
        except Exception:
            pass
    backdrop.terminate()
    Path(str(out) + ".marks.json").write_text(json.dumps(marks, indent=1), encoding="utf-8")
    print(json.dumps(marks))


if __name__ == "__main__":
    main(sys.argv[1])
