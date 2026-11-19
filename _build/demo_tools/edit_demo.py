"""Cut a raw screen recording into speed-adjusted segments and export a light web MP4 + poster.

    python edit_demo.py raw.mkv out_basename "0-6.6:1" "6.6-11.6:4" ... [--width 1280] [--poster 12.0]

Each segment is "start-end:speed" in seconds of the raw file.
"""
import argparse
import subprocess

import imageio_ffmpeg

ap = argparse.ArgumentParser()
ap.add_argument("raw")
ap.add_argument("out")
ap.add_argument("segments", nargs="+")
ap.add_argument("--width", type=int, default=0, help="output width; 0 keeps the native size")
ap.add_argument("--fps", type=int, default=20)
ap.add_argument("--crf", type=int, default=20)
ap.add_argument("--poster", type=float, default=None, help="time in the OUTPUT video for the poster frame")
a = ap.parse_args()

parts, labels = [], []
for i, seg in enumerate(a.segments):
    rng, speed = seg.split(":")
    s, e = (float(x) for x in rng.split("-"))
    sp = float(speed)
    parts.append("[0:v]trim=start=%.3f:end=%.3f,setpts=(PTS-STARTPTS)/%.4f,fps=%d[v%d]" % (s, e, sp, a.fps, i))
    labels.append("[v%d]" % i)
scale = ",scale=%d:-2:flags=lanczos" % a.width if a.width else ""
graph = ";".join(parts) + ";" + "".join(labels) + "concat=n=%d:v=1:a=0%s[out]" % (len(labels), scale)
ff = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff, "-loglevel", "error", "-y", "-i", a.raw, "-filter_complex", graph, "-map", "[out]",
                "-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", a.out + ".mp4"], check=True)
if a.poster is not None:
    subprocess.run([ff, "-loglevel", "error", "-y", "-ss", str(a.poster), "-i", a.out + ".mp4", "-frames:v", "1",
                    "-q:v", "4", a.out + ".jpg"], check=True)
print("done", a.out)
