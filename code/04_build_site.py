"""Step 4. Build ../index.html and ../README.md from page_template.html and README_template.md.

Every number in the text is a placeholder like {{gr.b|f2}} filled from ../data/results.json.
The page data (every earthquake and the searchable OS Open Names places) are embedded as `const D = ...`.
Formats: int, pct0, pct1, f1, f2, words, Words, raw.
Run: python3 04_build_site.py
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "words": return WORDS[int(v)] if int(v) < len(WORDS) else f"{int(v):,}"
    if f == "Words": w = fmt(v, "words"); return w[0].upper() + w[1:]
    return str(v)


def sub(m_):
    path, _, f = m_.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


if __name__ == "__main__":
    # the page needs only the results it reads, but they are small enough to embed whole
    t = open(os.path.join(HERE, "page_template.html")).read()
    t = re.sub(r"\{\{(.+?)\}\}", sub, t)
    t = t.replace("/*DATA*/", "const D = " + json.dumps(dict(R=R, P=P), separators=(",", ":"), ensure_ascii=False) + ";")
    open(os.path.join(ROOT, "index.html"), "w").write(t)
    print("index.html", len(t.encode()) // 1024, "KB")
    md = re.sub(r"\{\{(.+?)\}\}", sub, open(os.path.join(HERE, "README_template.md")).read())
    open(os.path.join(ROOT, "README.md"), "w").write(md)
    print("README.md written")
