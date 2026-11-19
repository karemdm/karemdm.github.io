"""High-quality page recording through the Chrome DevTools screencast (JPEG frames + timestamps).

Usage inside a Playwright script (sync API):

    sc = Screencast(page, out_dir)
    sc.start()
    ... drive the page; use page.wait_for_timeout() instead of time.sleep() so frames keep flowing ...
    sc.stop()
    sc.to_video("demo.mkv")
"""
import base64
import subprocess
from pathlib import Path

import imageio_ffmpeg


class Screencast:
    def __init__(self, page, out_dir, quality=92):
        self.page = page
        self.dir = Path(out_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        for f in self.dir.glob("*.jpg"):
            f.unlink()
        self.quality = quality
        self.frames = []  # (path, timestamp)
        self.cdp = page.context.new_cdp_session(page)
        self.cdp.on("Page.screencastFrame", self._on_frame)

    def _on_frame(self, ev):
        path = self.dir / ("%06d.jpg" % len(self.frames))
        path.write_bytes(base64.b64decode(ev["data"]))
        self.frames.append((path, ev["metadata"]["timestamp"]))
        self.cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})

    def start(self):
        vp = self.page.viewport_size
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": self.quality,
                                               "maxWidth": vp["width"], "maxHeight": vp["height"], "everyNthFrame": 1})

    def stop(self):
        self.page.wait_for_timeout(300)
        self.cdp.send("Page.stopScreencast")

    @property
    def t0(self):
        return self.frames[0][1] if self.frames else 0.0

    def to_video(self, out, fps=25):
        """Write the frames with their real durations, resampled to a constant frame rate."""
        lst = self.dir / "frames.txt"
        lines = []
        for i, (p, t) in enumerate(self.frames):
            nxt = self.frames[i + 1][1] if i + 1 < len(self.frames) else t + 0.5
            lines.append("file '%s'\nduration %.4f" % (p.as_posix(), max(nxt - t, 0.001)))
        lines.append("file '%s'" % self.frames[-1][0].as_posix())
        lst.write_text("\n".join(lines), encoding="utf-8")
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                        "-i", str(lst), "-vf", "fps=%d,format=yuv420p" % fps, "-c:v", "libx264", "-crf", "14",
                        "-preset", "fast", str(out)], check=True)
