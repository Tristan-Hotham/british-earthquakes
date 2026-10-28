"""Step 6. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png, 1520 px wide).
Maps are drawn from coordinates over the Natural Earth 1:10m land outline (no web tiles).
Every number comes from ../data/results.json or ../data/page_data.json.
Run: python3 06_figures.py
"""
import json, math, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    if os.path.exists(os.path.join(FD, f)): fm.fontManager.addfont(os.path.join(FD, f))
BG = "#F5EFE4"; FG = "#22201C"; MUT = "#6D6455"; RULE = "#DED2BE"; LAND = "#E6DBC6"
RED = "#B42A1F"; REDL = "#E5A196"; SEP = "#9A6A33"; SEPL = "#D9BF96"; INK = "#1F3557"; INKL = "#9DB0CC"; COAL = "#3B3936"
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": "Source Serif 4", "font.size": 13, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG, "axes.facecolor": BG, "figure.facecolor": BG})
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
EV = [dict(zip(P["ecols"], r)) for r in P["E"]]
PO = os.path.join(ROOT, "release", "paper"); BO = os.path.join(ROOT, "release", "blog")
os.makedirs(PO, exist_ok=True); os.makedirs(BO, exist_ok=True)
K = math.cos(math.radians(54.5))
LAND_POLYS = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LAND_POLYS.append(np.c_[a[:, 0] * K, a[:, 1]])
pct = lambda v: f"{v * 100:.0f}%"
rad = lambda m: (1.3 + max(m - 0.8, 0.2) ** 1.75 * 1.05)


def save(fig, name, blog):
    out = os.path.join(BO if blog else PO, name)
    fig.savefig(out, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=.2 if blog else .15)
    plt.close(fig)
    if blog:
        from PIL import Image
        im = Image.open(out)
        if im.size[0] != 1520:
            im = im.resize((1520, round(im.size[1] * 1520 / im.size[0])), Image.LANCZOS)
        im.save(out, optimize=True)


def fig_map(blog):
    fig, ax = plt.subplots(figsize=(8.6, 8.6) if blog else (6.4, 6.4))
    for a in LAND_POLYS:
        ax.add_patch(Polygon(a, closed=True, fc=LAND, ec="#CDBFA3", lw=.5, zorder=0))
    ax.set_xlim(-11.0 * K, 3.6 * K); ax.set_ylim(49.8, 59.4); ax.set_aspect("equal"); ax.axis("off")
    ev = sorted([e for e in EV if e["mag"] is not None], key=lambda e: -e["mag"])
    for cat, c in ((0, SEP), (1, RED)):
        v = [e for e in ev if e["cat"] == cat]
        ax.scatter([e["lon"] * K for e in v], [e["lat"] for e in v], s=[rad(e["mag"]) ** 2 * (1.1 if blog else .8) for e in v],
                   fc=c, ec=c, alpha=.35 if cat else .45, lw=.4, zorder=2 + cat, rasterized=True)
    for k, (dx, dy, ha) in {"1931_Dogger_Bank": (-6, 14, "right"), "1580_Dover_Straits": (-10, -14, "right"), "1884_Colchester": (-10, 10, "right"),
                            "2008_Market_Rasen": (12, 6, "left"), "1984_Llyn_Peninsula": (-12, -10, "right"), "1839_Comrie": (-12, 8, "right"),
                            "1990_Bishops_Castle": (-14, -6, "right"), "1957_Derby": (14, -10, "left")}.items():
        s = R["stories"][k]
        ax.annotate(f"{s['label']} ({s['mag']:.1f})", (s["lon"] * K, s["lat"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                    family=MONO, fontsize=9.5 if blog else 8, color=FG, zorder=6, bbox=dict(fc=BG, ec="none", alpha=.85, pad=1.2),
                    arrowprops=dict(arrowstyle="-", color=FG, lw=.6))
    hs = [Line2D([], [], marker="o", ls="", ms=7, mfc=SEP, mec=SEP, alpha=.7, label=f"Historical, {R['counts']['first_year']} to 1969 ({R['counts']['historical']:,})"),
          Line2D([], [], marker="o", ls="", ms=7, mfc=RED, mec=RED, alpha=.7, label=f"Instrumental, 1970 to {R['counts']['last_year']} ({R['counts']['modern']:,})")]
    hs += [Line2D([], [], marker="o", ls="", ms=rad(m) * (1.05 if blog else .9), mfc="none", mec=MUT, label=f"magnitude {m}") for m in (2, 4, 6)]
    ax.legend(handles=hs, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, frameon=False, prop=dict(family=MONO, size=9.5 if blog else 7.5), columnspacing=1.2, handletextpad=.3)
    save(fig, ("b_" if blog else "f_") + "map.png", blog)


def fig_big(blog):
    V = R["biggest_br"]; lab = {s["id"]: s["label"] for s in R["stories"].values()}
    fig, ax = plt.subplots(figsize=(7.6, 5.6) if blog else (6.4, 4.8))
    y = np.arange(len(V))[::-1]
    for yy, e in zip(y, V):
        c = SEP if e["cat"] == "historical" else RED
        ax.plot([4, e["mag"]], [yy, yy], color=c, lw=2); ax.plot(e["mag"], yy, "o", color=c, ms=8)
        ax.text(e["mag"] + .04, yy, f"{e['mag']:.1f}", va="center", family=MONO, fontsize=10.5 if blog else 9)
    ax.set_yticks(y); ax.set_yticklabels([lab.get(e["id"], f"{e['year']} {e['locality'] or e['near_town']}") for e in V], family=MONO, fontsize=10.5 if blog else 9)
    ax.set_xlim(4, 6.05); ax.set_xlabel("Magnitude"); ax.grid(axis="x", color=RULE); ax.set_axisbelow(True); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    ax.legend(handles=[Line2D([], [], marker="o", color=SEP, label="Historical (felt reports)"), Line2D([], [], marker="o", color=RED, label="Instrumental")],
              loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, prop=dict(family=MONO, size=10 if blog else 8.5))
    save(fig, ("b_" if blog else "f_") + "biggest.png", blog)


def fig_gr(blog):
    g = R["gr"]; V = [d for d in R["magfreq"] if d["n_ge"] > 0]
    fig, ax = plt.subplots(figsize=(7.6, 5.0) if blog else (6.4, 4.2))
    m = np.array([d["mag"] for d in V]); r = np.array([d["per_year"] for d in V])
    ax.semilogy(m[m < g["mc"] - 1e-6], r[m < g["mc"] - 1e-6], "o", color=REDL, ms=5, label=f"below M{g['mc']:.1f} (incomplete)")
    ax.semilogy(m[m >= g["mc"] - 1e-6], r[m >= g["mc"] - 1e-6], "o", color=RED, ms=5, label="observed, 1980 to 2024")
    x = np.linspace(g["mc"], 6.2, 50); ax.semilogy(x, 10 ** (g["a"] - g["b"] * x), color=INK, lw=2, label=f"Gutenberg-Richter fit, b = {g['b']:.2f}")
    for mm, ret in ((4, g["ret4"]), (5, g["ret5"])):
        ax.axvline(mm, color=MUT, ls="--", lw=.8)
        ax.text(mm - .06, 0.0016 if mm == 4 else 0.006, f"M{mm}+: one every\n{ret:.1f} years" if mm == 4 else f"M{mm}+: one every\n{ret:.0f} years", ha="right", va="bottom", family=MONO, fontsize=10 if blog else 8.5)
    ax.set_xlabel("Magnitude"); ax.set_ylabel("Earthquakes per year at or above magnitude"); ax.set_xlim(.9, 6.2); ax.set_ylim(1e-3, 200)
    ax.grid(color=RULE, which="major"); ax.set_axisbelow(True)
    ax.legend(frameon=False, prop=dict(family=MONO, size=10 if blog else 8.5), loc="upper right")
    save(fig, ("b_" if blog else "f_") + "magfreq.png", blog)


def fig_coal(blog):
    V = R["coal"]["periods"]; c = R["coal"]
    fig, ax = plt.subplots(figsize=(7.6, 4.4) if blog else (6.4, 3.6))
    x = np.arange(len(V))
    ax.bar(x, [d["share"] for d in V], color=[INKL if d["start"] >= 2015 else COAL for d in V], width=.7)
    ax.axhline(c["land_share"], color=RED, ls="--", lw=1.5)
    ax.plot([-.45, -.05], [.555, .555], color=RED, ls="--", lw=1.5)
    ax.text(.05, .555, f"{pct(c['land_share'])} of Britain's land is within 5 km of a mapped coal mine", family=MONO, fontsize=10 if blog else 8.5, color=RED, va="center")
    ax.axvline(8.5, color=FG, ls=":", lw=1); ax.text(8.45, .5, "2015: last deep\nmines close", ha="right", va="top", family=MONO, fontsize=10 if blog else 8.5)
    ax.set_xticks(x); ax.set_xticklabels([str(d["start"]) for d in V], family=MONO, fontsize=9.5 if blog else 8); ax.set_xlabel("Five-year periods starting")
    ax.set_ylim(0, .6); ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.set_ylabel("Share of onshore earthquakes"); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
    save(fig, ("b_" if blog else "f_") + "coal.png", blog)


def fig_det(blog):
    H = [d for d in R["detection"]["historical"] if d["start"] >= 1500]; M_ = R["detection"]["modern"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 4.2) if blog else (6.4, 3.4), gridspec_kw=dict(width_ratios=[1.1, 1]))
    x = np.arange(len(H)); g5 = np.array([d["ge5"] for d in H]); g4 = np.array([d["ge4"] for d in H]) - g5; l4 = np.array([d["n"] for d in H]) - g4 - g5
    a1.bar(x, g5, color=SEP, label="5+"); a1.bar(x, g4, bottom=g5, color="#C09A6A", label="4 to 4.9"); a1.bar(x, l4, bottom=g5 + g4, color=SEPL, label="below 4")
    a1.set_xticks(x[::2]); a1.set_xticklabels([str(d["start"]) for d in H][::2], family=MONO, fontsize=9 if blog else 7.5)
    a1.set_title("Historical, per 50 years", family=MONO, fontsize=10.5 if blog else 9, loc="left"); a1.legend(frameon=False, prop=dict(family=MONO, size=9 if blog else 7.5), loc="upper left")
    x = np.arange(len(M_)); b = np.zeros(len(M_))
    for k, c, l in (("ge4", RED, "4+"), ("m3_4", "#CB6A5F", "3 to 3.9"), ("m2_3", "#DB8E83", "2 to 2.9"), ("lt2", "#EDC4BC", "below 2")):
        v = np.array([d[k] for d in M_]); a2.bar(x, v, bottom=b, color=c, label=l); b += v
    a2.set_xticks(x); a2.set_xticklabels([f"{d['decade']}s" for d in M_], family=MONO, fontsize=9 if blog else 7.5)
    a2.set_title("Instrumental, per decade", family=MONO, fontsize=10.5 if blog else 9, loc="left"); a2.legend(frameon=False, prop=dict(family=MONO, size=9 if blog else 7.5), loc="upper right")
    a2.set_ylim(0, 1550); a1.set_ylim(0, 175)
    for a in (a1, a2): a.grid(axis="y", color=RULE); a.set_axisbelow(True)
    a1.set_ylabel("Recorded earthquakes in Britain")
    fig.tight_layout()
    save(fig, ("b_" if blog else "f_") + "detection.png", blog)


def fig_hot(blog):
    V = R["hotspots"][:12]
    fig, ax = plt.subplots(figsize=(7.6, 4.8) if blog else (6.4, 4.0))
    y = np.arange(len(V))[::-1]
    ax.barh(y, [h["n"] for h in V], color=[COAL if h["near_coal"] >= .5 else RED for h in V], height=.7)
    for yy, h in zip(y, V):
        ax.text(h["n"] + 3, yy, f"{h['n']}  (biggest {h['max_mag']:.1f})", va="center", family=MONO, fontsize=9.5 if blog else 8)
    ax.set_yticks(y); ax.set_yticklabels([f"near {h['town']}" for h in V], family=MONO, fontsize=10 if blog else 8.5)
    ax.set_xlabel("Earthquakes recorded since 1970 in the 20 km square"); ax.set_xlim(0, 300); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=COAL, label="most epicentres within 5 km of a mapped coal mine"), plt.Rectangle((0, 0), 1, 1, color=RED, label="other")],
              frameon=False, prop=dict(family=MONO, size=9 if blog else 7.5), loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
    save(fig, ("b_" if blog else "f_") + "hotspots.png", blog)


import matplotlib.ticker
for blog in (True, False):
    for f in (fig_map, fig_big, fig_gr, fig_coal, fig_det, fig_hot):
        f(blog)
print("figures written")
