"""r/dataisbeautiful collage for Britain's earthquakes since 1382 (british-earthquakes). Run from this folder: python3 collage.py
Every number is read from ../data/results.json or ../data/page_data.json."""
import json, math, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon

F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(F, f))
DISP = fm.FontProperties(fname=os.path.join(F, "FrauncesVar.ttf"), weight=900)
SER = "Source Serif 4"; MONO = "IBM Plex Mono"
BG = "#F4ECDD"; FG = "#22201C"; MUT = "#6D6455"; LAND = "#E5D8BF"; EDGE = "#CDBB98"
RED = "#B42A1F"; SEP = "#9A6A33"; INK = "#1F3557"; COAL = "#3B3936"; INKL = "#9DB0CC"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
EV = [dict(zip(P["ecols"], r)) for r in P["E"]]
K = math.cos(math.radians(54.5))
LANDP = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LANDP.append(np.c_[a[:, 0] * K, a[:, 1]])
pct = lambda v: f"{v * 100:.0f}%"
g = R["gr"]; c = R["coal"]; t = R["towns"]

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.04, 0.968, "Britain doesn't have earthquakes?", fontproperties=DISP, fontsize=42, color=FG, va="top")
fig.text(0.04, 0.917, f"It has thousands. Every earthquake in the British Geological Survey catalogues, {R['counts']['first_year']} to {R['counts']['last_year']}:\n"
         f"{R['counts']['historical']} from felt reports before 1970 (sepia) and {R['counts']['modern']:,} recorded by seismometers since (red).",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.2)

# seismograph strip: every magnitude 4+ in Britain since 1750
sx = fig.add_axes([0.04, 0.79, 0.92, 0.055]); sx.axis("off")
y0, y1 = 1750, R["counts"]["last_year"] + 1
rng = np.random.default_rng(7); xs = np.linspace(y0, y1, 1400)
sx.plot(xs, rng.normal(0, .04, xs.size), color=MUT, lw=.5, alpha=.7)
m4 = [e for e in EV if e["zone"] <= 1 and e["mag"] is not None and e["mag"] >= 4 and int(e["date"][:4]) >= y0]
for e in m4:
    tt = int(e["date"][:4]) + (int(e["date"][5:7]) - 1) / 12 if len(e["date"]) >= 7 else int(e["date"][:4]) + .5
    a = (e["mag"] - 3.6) * .9; k = np.arange(8)
    sx.plot(tt + k * .45, a * np.exp(-k * .5) * np.where(k % 2, -1, 1), color=RED if e["cat"] else SEP, lw=1.1 if e["mag"] < 5 else 1.7, solid_joinstyle="round")
sx.set_xlim(y0, y1 + 3); sx.set_ylim(-1.5, 1.5)
for yy in (1750, 1800, 1850, 1900, 1950, 2000):
    sx.text(yy, -1.75, str(yy), family=MONO, fontsize=10, color=MUT, ha="center", va="top")
fig.text(0.04, 0.852, f"A SPIKE FOR EVERY MAGNITUDE 4+ EARTHQUAKE IN BRITAIN SINCE 1750 ({len(m4)})", family=MONO, fontsize=10.5, color=MUT)

# hero map
ax = fig.add_axes([0.0, 0.25, 0.6, 0.53])
for a in LANDP:
    ax.add_patch(Polygon(a, closed=True, fc=LAND, ec=EDGE, lw=.6, zorder=0))
ax.set_xlim(-7.6 * K, 2.6 * K); ax.set_ylim(49.85, 59.0); ax.set_aspect("equal"); ax.axis("off")
ev = sorted([e for e in EV if e["mag"] is not None], key=lambda e: -e["mag"])
for cat, col in ((0, SEP), (1, RED)):
    v = [e for e in ev if e["cat"] == cat]
    ax.scatter([e["lon"] * K for e in v], [e["lat"] for e in v], s=[(1.0 + max(e["mag"] - .8, .2) ** 1.75 * .95) ** 2 for e in v],
               fc=col, ec=col, alpha=.33 if cat else .45, lw=.4, zorder=2 + cat, rasterized=True)
lab = {"1931_Dogger_Bank": (-8, 16, "right"), "1580_Dover_Straits": (-10, -16, "right"), "2008_Market_Rasen": (10, 14, "left"),
       "1984_Llyn_Peninsula": (-8, -18, "right"), "1839_Comrie": (-14, 10, "right"), "1884_Colchester": (-8, 14, "right")}
for k, (dx, dy, ha) in lab.items():
    s = R["stories"][k]
    ax.annotate(f"{s['label']}  {s['mag']:.1f}", (s["lon"] * K, s["lat"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                family=MONO, fontsize=10.5, color=FG, zorder=6, bbox=dict(fc=BG, ec="none", alpha=.85, pad=1.2), arrowprops=dict(arrowstyle="-", color=FG, lw=.7))
kx = fig.add_axes([0.6, 0.245, 0.37, 0.03]); kx.axis("off"); kx.set_xlim(0, 1); kx.set_ylim(-1, 1)
for i, m in enumerate((2, 4, 6)):
    r = (1.0 + max(m - .8, .2) ** 1.75 * .95)
    kx.scatter([0.02 + i * .33], [0], s=r ** 2, fc="none", ec=MUT, lw=.9)
    kx.text(0.07 + i * .33, 0, f"magnitude {m}", family=MONO, fontsize=10, color=FG, va="center")

# headline numbers
tx = fig.add_axes([0.6, 0.27, 0.37, 0.5]); tx.axis("off")
notes = [(f"every {g['all4_ret']:.0f} yrs", RED, f"a magnitude 4 or bigger shakes Britain:\n{g['all4_since1750']} of them since 1750. A magnitude\n5 comes about every {g['all5_ret']:.0f} years."),
         (f"{pct(c['share_to2014'])}", COAL, f"of onshore quakes 1970 to 2014 were within\n5 km of a mapped coal mine. Only {pct(c['land_share'])} of\nBritain's land is that close."),
         (f"{pct(c['weekend_near'])}", INK, f"of those near-mine quakes fell at weekends,\nagainst {pct(c['weekend_expected'])} by chance. A mining signature.\nSince 2020: {pct(c['share_2020on'])} near a mine."),
         (f"{pct(t['share_ge4_25'])}", SEP, f"of {t['n']:,} British towns and cities have had\na magnitude 4+ within 25 km. Biggest of all:\nDogger Bank 1931, magnitude {R['stories']['1931_Dogger_Bank']['mag']:.1f}.")]
for (big, col, small), y in zip(notes, [1.0, 0.75, 0.5, 0.25]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=36, color=col, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.088, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.15)

# small multiple 1: coal share
fig.text(0.04, 0.228, "ONSHORE QUAKES NEAR A COAL MINE (DASHED: SHARE OF LAND)", family=MONO, fontsize=10.5, color=MUT)
bx = fig.add_axes([0.06, 0.118, 0.42, 0.1], facecolor=BG)
V = c["periods"]; x = np.arange(len(V))
bx.bar(x, [d["share"] for d in V], color=[INKL if d["start"] >= 2015 else COAL for d in V], width=.72)
bx.axhline(c["land_share"], color=RED, ls="--", lw=1.3)
bx.set_xticks(x[::2]); bx.set_xticklabels([str(d["start"]) for d in V][::2], family=MONO, fontsize=9.5)
bx.set_ylim(0, .66); bx.set_yticks([0, .2, .4]); bx.set_yticklabels(["0%", "20%", "40%"], family=MONO, fontsize=9.5)
bx.text(8.35, .65, "last deep mines close, 2015", family=MONO, fontsize=9.5, ha="right", va="top", color=FG); bx.axvline(8.5, color=FG, ls=":", lw=1)
# small multiple 2: magnitude-frequency
fig.text(0.56, 0.228, "QUAKES PER YEAR AT OR ABOVE EACH SIZE (1980+)", family=MONO, fontsize=10.5, color=MUT)
cx = fig.add_axes([0.58, 0.118, 0.38, 0.1], facecolor=BG)
mf = [d for d in R["magfreq"] if d["n_ge"] > 0]
mm = np.array([d["mag"] for d in mf]); rr = np.array([d["per_year"] for d in mf])
cx.semilogy(mm, rr, "o", ms=3.5, color=RED)
xx = np.linspace(g["mc"], 6, 40); cx.semilogy(xx, 10 ** (g["a"] - g["b"] * xx), color=INK, lw=1.8)
cx.text(3.6, 4, f"b = {g['b']:.2f}", family=MONO, fontsize=10, color=INK)
cx.set_xlim(.9, 6.1); cx.set_ylim(1e-3, 200); cx.set_yticks([100, 1, .01]); cx.set_yticklabels(["100", "1", "0.01"], family=MONO, fontsize=9.5)
cx.set_xticks([1, 2, 3, 4, 5, 6]); cx.set_xticklabels(["M1", "2", "3", "4", "5", "6"], family=MONO, fontsize=9.5)
for a in (bx, cx):
    for sp in ("top", "right"): a.spines[sp].set_visible(False)
    a.spines["left"].set_color(MUT); a.spines["bottom"].set_color(MUT); a.tick_params(colors=FG)
    a.grid(axis="y", color="#DED2BE", lw=.7); a.set_axisbelow(True)

fig.text(0.04, 0.079, "Britain = on land in Great Britain or within 20 km of its coast. Historical magnitudes and places are estimates from felt reports; small quakes\n"
         "are recorded far more often now because the seismometer network grew. Closeness to a mapped mine is an indicator of induced quakes, not proof.",
         family=MONO, fontsize=9, color=MUT, linespacing=1.2, va="top")
fig.text(0.04, 0.012,
         "Data: British Geological Survey UK historical and modern earthquake catalogues (Contains British Geological Survey materials © UKRI 2026).\n"
         "OS Open Names (Contains OS data © Crown copyright and database right 2026, OGL v3). Coal mines © OpenStreetMap contributors (ODbL). Natural Earth.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib.  tristan-hotham.github.io/british-earthquakes",
         family=MONO, fontsize=8.8, color=MUT, linespacing=1.25)
fig.savefig(os.path.join(HERE, "britain_doesnt_have_earthquakes.png"), facecolor=BG, dpi=200)
print("ok")
