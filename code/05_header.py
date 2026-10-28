"""Step 5. Render ../header.png (1200x630 social card) with Playwright Chromium.

Fonts: pass a folder holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf and
IBMPlexMono-Medium.ttf as FONT_DIR (from github.com/google/fonts); otherwise system serif is used.
Coastline: Natural Earth 1:10m land for the British Isles, as extracted for the lighthouse project.
Run: FONT_DIR=/path/to/fonts python3 05_header.py
"""
import json, math, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
K = math.cos(math.radians(54.5))
X0, X1, Y0, Y1 = -8.2 * K, 2.2 * K, -59.2, -49.8
Hh = 620; Ww = Hh * (X1 - X0) / (Y1 - Y0)


def pr(lat, lon):
    return (lon * K - X0) / (Y1 - Y0) * Hh, (-lat - Y0) / (Y1 - Y0) * Hh


COAST = os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")
land = ""
for g in json.load(open(COAST)):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        land += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (pr(q[1], q[0]) for q in poly[0])) + "Z"
C = P["ecols"]; ev = [dict(zip(C, r)) for r in P["E"]]
dots = ""
for e in sorted(ev, key=lambda e: -(e["mag"] or 0)):
    if e["mag"] is None: continue
    x, y = pr(e["lat"], e["lon"])
    if not (0 <= x <= Ww and 0 <= y <= Hh): continue
    r = 0.8 + max(e["mag"] - 0.8, 0.2) ** 1.75 * 0.75
    c = "#B42A1F" if e["cat"] else "#9A6A33"
    dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}" fill-opacity="{0.5 if e["mag"] >= 4 else 0.3}" stroke="{c}" stroke-width=".6" stroke-opacity=".8"/>'
ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
    ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
    ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")]) if os.path.isdir(FD) else ""
g = R["gr"]
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(circle at 78% 50%,#FAF5EC 0%,#F3EBDD 55%,#E8DCC6 100%);color:#22201C;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:66px;top:62px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#6D6455;display:flex;gap:12px;align-items:center}}
.k b{{background:#B42A1F;color:#F5EFE4;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:60px;top:100px;margin:0;font:900 88px/.92 Fraunces,Georgia,serif;letter-spacing:-.02em;width:700px}}
h1 em{{font-style:normal;color:#B42A1F}}
p{{position:absolute;left:66px;top:400px;width:640px;margin:0;font-size:25px;line-height:1.36}}
p b{{color:#B42A1F}}
.f{{position:absolute;left:66px;bottom:40px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#6D6455}}
svg{{position:absolute;right:30px;top:5px}}
</style></head><body>
<div class="k"><b>Data study</b><span>BGS catalogues · 1382 to 2024</span></div>
<h1>Britain's <em>earthquakes</em> since 1382</h1>
<p><b>{R['counts']['total']:,}</b> recorded earthquakes. A magnitude 4 about every <b>{g['all4_ret']:.0f} years</b>, a magnitude 5 about every <b>{g['all5_ret']:.0f}</b>.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Ww:.0f}" height="{Hh}" viewBox="0 0 {Ww:.0f} {Hh}"><path d="{land}" fill="#E6DBC6" stroke="#CDBFA3" stroke-width="1"/>{dots}</svg>
</body></html>"""
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
