"""Maintainer script: builds the key frames and the overview GIF from index.html.
Not needed to read the example. Needs playwright, Google Chrome and ffmpeg.
Usage: python3 make_media.py"""
import subprocess, tempfile, pathlib, json
from playwright.sync_api import sync_playwright

here = pathlib.Path(__file__).resolve().parent
out = here.parent
GIF_FPS = 4

with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 1280, "height": 720})
    pg.goto(f"file://{here}/index.html?capture=1&profile=A")
    dur = pg.evaluate("getDuration()")
    m = pg.evaluate("""() => ({
      shelf: M.shelf.map(s => s.t),
      warn: M.feed.find(x => x.kind === 'warn').t,
      name: M.feed.find(x => x.text.startsWith('web_search("Nordwerk')).t,
      flag: M.feed.find(x => x.kind === 'flag').t,
      reveal: M.tReveal })""")
    sh = m["shelf"]
    keys = {  # name -> time in seconds
        "01-gate": 6.0, "02-results": 13.2, "03-honest-probes": 17.6,
        "04-connect": m["warn"] + 1.2, "05-search": sh[0] + 0.6, "06-ask-leaks-intent": sh[1] + 0.6,
        "07-licence": sh[2] + 0.6, "08-register-page": sh[3] + 0.6, "09-reconcile": sh[4] + 0.6,
        "10-honest-search": m["name"] + 2.4, "11-reviews": sh[5] + 0.6,
        "12-answer": m["flag"] + 0.6, "13-what-happened": m["reveal"] + 2.5}
    for name, t in keys.items():
        pg.evaluate(f"setTime({t})"); pg.screenshot(path=str(out / "frames" / f"{name}.png"))
    json.dump(keys, open(out / "frames" / "times.json", "w"), indent=1)
    n = int(dur * GIF_FPS)
    for i in range(n):
        pg.evaluate(f"setTime({i / GIF_FPS})"); pg.screenshot(path=f"{tmp}/f{i:05d}.png")
    b.close()
    vf = f"fps={GIF_FPS},scale=960:-1:flags=lanczos"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(GIF_FPS), "-i", f"{tmp}/f%05d.png",
                    "-vf", f"{vf},split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=none",
                    str(out / "overview.gif")], check=True)
print("done")
