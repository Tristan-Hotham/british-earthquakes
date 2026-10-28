"""Step 7. Build the paper PDF: fill paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_British_Earthquakes.tex and compile it with xelatex (figures from 06_figures.py).
Placeholders: {{path|fmt}} as in 04_build_site.py, with % escaped for LaTeX.
Run: python3 07_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_British_Earthquakes"
WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "words": return WORDS[int(v)] if int(v) < len(WORDS) else f"{int(v):,}"
    if f == "Words": w = fmt(v, "words"); return w[0].upper() + w[1:]
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("ŷ", "\\^{y}")
dep = lambda v, d=0: "" if v is None else f"{v:.{d}f}"
lab = {s["id"]: s["label"] for s in R["stories"].values()}
rows = ""
for e in R["biggest_br"]:
    name = lab.get(e["id"], f"{e['year']} {e['locality'] or e['near_town']}")
    rows += f"{tex(e['date'])} & {tex(name.split(' ', 1)[1])} & {e['mag']:.1f} & {tex(e['mag_type'])} & {tex(e['intensity'])} & {dep(e['depth'])} & {tex(e['near_town'])} ({e['near_town_km']:.0f}) & {'H' if e['cat'] == 'historical' else 'I'}\\\\\n"
TB = ("\\begin{table}[tbp]\\centering\\small\\caption{The fifteen largest earthquakes on land in Britain or within 20 km of its coast. Type: ML instrumental local magnitude, MGMC macroseismic magnitude. "
      "Int.: maximum intensity as given. Depth in km. Nearest OS town with distance in km. H: historical catalogue; I: instrumental.}\\label{tab:big}"
      "\\begin{tabular}{llrlllll}\\toprule Date & Event & Mag. & Type & Int. & Depth & Nearest town (km) & Cat.\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for h in R["hotspots"][:10]:
    rows += f"{tex(h['town'])} & {h['n']} & {h['first']} to {h['last']} & {h['max_mag']:.1f} & {dep(h['median_depth'], 1)} & {h['near_coal'] * 100:.0f}\\\\\n"
TH = ("\\begin{table}[tbp]\\centering\\small\\caption{The ten busiest 20 km squares in Britain, instrumental catalogue 1970 to " + str(R["counts"]["last_year"]) + ". "
      "Near coal: share of epicentres within 5 km of a mapped coal mine.}\\label{tab:hot}"
      "\\begin{tabular}{lrlrrr}\\toprule Square (nearest town) & Events & Years & Max. mag. & Median depth (km) & Near coal (\\%)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
g = R["gr"]
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Average years between earthquakes of magnitude 4 or more and 5 or more in Britain: Gutenberg-Richter fit and observed counts.}\\label{tab:rates}"
      "\\begin{tabular}{lrrrr}\\toprule Source & M4+ events & Years per M4+ & M5+ events & Years per M5+\\\\\\midrule\n"
      f"Fit, M{g['mc']:.1f}+ 1980 to {R['counts']['last_year']} (95\\% interval) & & {g['ret4']:.1f} ({g['ret4_ci'][0]:.1f} to {g['ret4_ci'][1]:.1f}) & & {g['ret5']:.0f} ({g['ret5_ci'][0]:.0f} to {g['ret5_ci'][1]:.0f})\\\\\n"
      f"Instrumental, 1980 to {R['counts']['last_year']} & {g['obs4']} & {g['obs4_ret']:.1f} & {g['obs5']} & {g['obs5_ret']:.1f}\\\\\n"
      f"Historical, 1750 to 1969 & {g['hist4_1750_1969']} & {g['hist4_ret']:.1f} & {g['hist5_1750_1969']} & {g['hist5_ret']:.1f}\\\\\n"
      f"Both catalogues, 1750 to {R['counts']['last_year']} & {g['all4_since1750']} & {g['all4_ret']:.1f} & {g['all5_since1750']} & {g['all5_ret']:.1f}\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
TS = "\n".join(f"{s['mc']:.1f} & {s['n']:,} & {s['b']:.2f}\\\\" for s in g["stability"])
s = open(os.path.join(HERE, "paper_template.tex")).read()
s = s.replace("{{TABLE_BIG}}", TB).replace("{{TABLE_HOT}}", TH).replace("{{TABLE_RATES}}", TR).replace("{{TABLE_STAB}}", TS)
s = re.sub(r"\{\{(.+?)\}\}", sub, s)
assert "{{" not in s
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(s)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
print(r.stdout[-600:])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
