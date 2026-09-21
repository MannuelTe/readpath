"""Render index.html to an MP4 by stepping the scripted timeline frame by frame.
Usage: python3 render.py [A|B] [fps]   (needs playwright + Google Chrome + ffmpeg)"""
import sys, subprocess, tempfile, pathlib
from playwright.sync_api import sync_playwright

profile = sys.argv[1] if len(sys.argv) > 1 else "A"
fps = int(sys.argv[2]) if len(sys.argv) > 2 else 15
here = pathlib.Path(__file__).resolve().parent
out = here / f"interaction-{profile}.mp4"

with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 1280, "height": 720})
    pg.goto(f"file://{here}/index.html?capture=1&profile={profile}")
    dur = pg.evaluate("getDuration()")
    n = int(dur * fps)
    for i in range(n):
        pg.evaluate(f"setTime({i / fps})")
        pg.screenshot(path=f"{tmp}/f{i:05d}.png")
    b.close()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{tmp}/f%05d.png",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", str(out)], check=True)
print("wrote", out)
