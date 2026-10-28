"""Step 8. Blog post (release/blog/post.html from blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader.
Run: python3 08_release.py
"""
import json, os, re, shutil, zipfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = open(os.path.join(HERE, "blog_template.html")).read()
# fill numbers everywhere, including inside image alt text and captions
t = re.sub(r"\{\{(?!IMG\|)([^{}|]+(?:\|[a-zA-Z0-9]+)?)\}\}", b.sub, t)
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m
g = R["gr"]
TITLE = "Britain's Earthquakes Since 1382: Clusters, Coalfields and How Often the Big Ones Come"
meta = dict(
    title="Britain's earthquakes since 1382: the big ones, the coalfield quakes and the biggest near you",
    slug="british-earthquakes",
    excerpt=(f"I mapped all {R['counts']['total']:,} earthquakes in the British Geological Survey's catalogues since {R['counts']['first_year']}. Britain has a magnitude 4 "
             f"about every {g['all4_ret']:.0f} years, and its busiest modern earthquake zones were coalfields."),
    seo_description=f"{R['counts']['total']:,} British earthquakes since 1382 mapped: how often a magnitude 4 or 5 comes, the coalfield quakes, and the biggest near you.",
    tags=["earthquakes", "geology", "seismology", "coal mining", "maps", "data", "history", "Britain"],
    header_alt=("Title card reading 'Britain's earthquakes since 1382' on a pale sandstone background, beside a map of Britain covered in sepia and red circles for "
                f"historical and instrumentally recorded earthquakes. Text: {R['counts']['total']:,} recorded earthquakes; a magnitude 4 about every {g['all4_ret']:.0f} years, "
                f"a magnitude 5 about every {g['all5_ret']:.0f}."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

pt = open(os.path.join(ROOT, "release", "paper", "Hotham_British_Earthquakes.tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("$<$", "<")
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title=TITLE,
    description_html=f"<p>{ab}</p><p>Earthquake data derived from the British Geological Survey UK historical and modern earthquake catalogues. Contains British Geological Survey materials © UKRI 2026.</p>"
                     f"<p>Interactive version: https://tristan-hotham.github.io/british-earthquakes/. Data and code: https://github.com/Tristan-Hotham/british-earthquakes. Blog post: to follow.</p>",
    keywords=["earthquakes", "seismicity", "Great Britain", "historical seismology", "Gutenberg-Richter", "b-value", "induced seismicity", "coal mining", "detection bias", "open data"],
    licence="cc-by-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/british-earthquakes", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/british-earthquakes/", relation="issupplementedby", resource_type="other"),
        dict(identifier="http://data.bgs.ac.uk/id/dataHolding/13480080", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://map.bgs.ac.uk", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.openstreetmap.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.naturalearthdata.com", relation="isderivedfrom", resource_type="dataset"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", "Hotham_British_Earthquakes.pdf"), Z)
for f in ["events.csv", "towns.csv", "hotspots.csv", "decades.csv", "magfreq.csv", "coal_periods.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "british-earthquakes_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"british-earthquakes/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"british-earthquakes/{f}")
print("release files written; post words:", len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t, flags=re.S)).split()))
