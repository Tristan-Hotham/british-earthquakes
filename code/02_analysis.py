"""Step 2. All statistics. Reads ../data/events.csv (step 1) and writes:
  ../data/results.json     every number used on the page, in the paper, blog and collage
  ../data/decades.csv      events per decade and magnitude band (detection over time)
  ../data/magfreq.csv      cumulative magnitude-frequency counts, 1980 to 2024, Britain and coastal waters
  ../data/hotspots.csv     20 km grid squares with the most recorded earthquakes since 1970
  ../data/towns.csv        every OS Open Names city and town with the biggest recorded earthquake within 25 km
  ../data/page_data.json   compact data for the page (events and searchable places)

"Britain" below means epicentres on land in Great Britain or within 20 km of its coast (step 1 zones).
Gutenberg-Richter: log10 N(>=M) = a - bM, b by Aki's maximum likelihood with Utsu's correction for
0.1-unit binning, b = log10(e) / (mean(M) - (Mc - 0.05)); 95% intervals by bootstrap (2,000 resamples).
Inputs read in place: ../../_data12/wd_osm_bundle12.json.gz (OpenStreetMap colliery features, ODbL),
../../osnames_gb.tsv (OS Open Names), Natural Earth land via ../work/gb_buffer.json.
Run: python3 02_analysis.py
"""
import gzip, io, json, os, re
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy.stats import binomtest
from shapely.geometry import shape, Point
from shapely.prepared import prep

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); HIST = os.path.join(ROOT, "..")
DATA = os.path.join(ROOT, "data")
E = pd.read_csv(os.path.join(DATA, "events.csv"), keep_default_na=False, na_values=[""])
PC = json.load(open(os.path.join(ROOT, "work", "prep_counts.json")))
R = {}
BRZ = ["Britain onshore", "Britain coast (within 20 km)"]
E["br"] = E.zone.isin(BRZ)
H = E[E.cat == "historical"]; M = E[E.cat == "modern"]
last = M.sort_values("date").iloc[-1]
first = H.sort_values(["year", "date"]).iloc[0]
yrs_modern_1980 = (pd.Timestamp(last.date) - pd.Timestamp("1980-01-01")).days / 365.25
R["counts"] = dict(
    historical=len(H), historical_br=int(H.br.sum()), historical_nomag=int(H.mag.isna().sum()),
    modern_raw=PC["modern_raw"], modern_dupes=PC["modern_raw"] - PC["modern_events"], modern=len(M), modern_br=int(M.br.sum()),
    total=len(E), total_br=int(E.br.sum()), onshore=int((E.zone == "Britain onshore").sum()), coast=int((E.zone == "Britain coast (within 20 km)").sum()),
    offshore=int((E.zone == "Offshore").sum()), ireland=int((E.zone == "Ireland").sum()),
    first_date=first.date, first_year=int(first.year), last_date=last.date, last_year=int(last.year),
    modern_min_mag=float(M.mag.min()), years_1980=round(yrs_modern_1980, 2),
    by_country={c: int(n) for c, n in E[E.br].country.value_counts().items()},
    last_date_text=pd.Timestamp(last.date).strftime("%-d %B %Y"),
    offshore_nns=int(((E.zone == "Offshore") & (E.lat > 58) & (E.lon > 0)).sum()))

# ---------- biggest ----------
def ev(r):
    r = r._asdict() if hasattr(r, "_asdict") else r.to_dict()
    g = lambda k: None if (r[k] is None or (isinstance(r[k], float) and np.isnan(r[k]))) else r[k]
    return dict(id=r["id"], date=r["date"], year=int(r["year"]), mag=None if g("mag") is None else float(r["mag"]), mag_type=r["mag_type"] if isinstance(r["mag_type"], str) else "",
                intensity=r["intensity"] if isinstance(r["intensity"], str) else "", depth=None if g("depth") is None else float(r["depth"]),
                locality=r["locality"] if isinstance(r["locality"], str) else "", zone=r["zone"], near_town=r["near_town"], near_town_km=float(r["near_town_km"]),
                near_place=r["near_place"], lat=float(r["lat"]), lon=float(r["lon"]), cat=r["cat"])


big = E.dropna(subset=["mag"]).sort_values(["mag", "year"], ascending=[False, True])
R["biggest_all"] = [ev(r) for r in big.head(12).itertuples()]
R["biggest_br"] = [ev(r) for r in big[big.br].head(15).itertuples()]
R["biggest_onshore"] = [ev(r) for r in big[big.zone == "Britain onshore"].head(10).itertuples()]
R["biggest_modern_br"] = [ev(r) for r in big[big.br & (big.cat == "modern")].head(10).itertuples()]
R["n_br_ge5"] = int((E.br & (E.mag >= 5)).sum()); R["n_br_ge4"] = int((E.br & (E.mag >= 4)).sum())

# ---------- detection over time ----------
rows = []
for d0 in range(1970, 2030, 10):
    x = M[M.br & (M.year >= d0) & (M.year < d0 + 10)].mag
    rows.append(dict(decade=d0, n=len(x), lt2=int((x < 2).sum()), m2_3=int(((x >= 2) & (x < 3)).sum()), m3_4=int(((x >= 3) & (x < 4)).sum()),
                     ge4=int((x >= 4).sum()), share_lt2=round(float((x < 2).mean()), 3), median=float(x.median())))
dec = pd.DataFrame(rows)
hrows = []
for c in range(1350, 1970, 50):
    x = H[H.br & (H.year >= c) & (H.year < c + 50)].mag
    hrows.append(dict(period=f"{c} to {c + 49}", start=c, n=len(x), ge4=int((x >= 4).sum()), ge5=int((x >= 5).sum()), lt4=int((x < 4).sum())))
hdec = pd.DataFrame(hrows)
R["detection"] = dict(modern=rows, historical=hrows,
                      share_lt2_1970s=rows[0]["share_lt2"], share_lt2_1990s=rows[2]["share_lt2"], share_lt2_2010s=rows[4]["share_lt2"],
                      n_1970s=rows[0]["n"], n_1980s=rows[1]["n"], n_2010s=rows[4]["n"], lt2_ratio_80s_70s=round(rows[1]["lt2"] / rows[0]["lt2"], 2),
                      ge3_by_decade=[r["m3_4"] + r["ge4"] for r in rows],
                      lt2_1970s=rows[0]["lt2"], lt2_1980s=rows[1]["lt2"],
                      hist_before1700=int((H.br & (H.year < 1700)).sum()), hist_1800s=int((H.br & H.year.between(1800, 1899)).sum()))
pd.concat([dec.assign(catalogue="modern"), hdec.assign(catalogue="historical")]).to_csv(os.path.join(DATA, "decades.csv"), index=False)

# ---------- Gutenberg-Richter ----------
G = M[M.br & (M.year >= 1980)].mag.values
MC = 2.0; YR = yrs_modern_1980
rng = np.random.default_rng(1382)


def bval(m, mc):
    x = m[m >= mc - 1e-9]
    return np.log10(np.e) / (x.mean() - (mc - 0.05)), len(x)


b, n_mc = bval(G, MC)
rate_mc = n_mc / YR
ret = lambda bb, rr, mm: 1 / (rr * 10 ** (-bb * (mm - MC)))
boots = []
for _ in range(2000):
    s = rng.choice(G[G >= MC - 1e-9], n_mc, replace=True)
    bb = np.log10(np.e) / (s.mean() - (MC - 0.05))
    rr = rng.poisson(n_mc) / YR
    boots.append((bb, ret(bb, rr, 4), ret(bb, rr, 5)))
boots = np.array(boots)
q = lambda a: [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]
stab = []
for mc in np.arange(1.0, 3.01, 0.2):
    bb, nn = bval(G, mc); stab.append(dict(mc=round(float(mc), 1), n=int(nn), b=round(float(bb), 3)))
obs4 = int((M.br & (M.year >= 1980) & (M.mag >= 4)).sum()); obs5 = int((M.br & (M.year >= 1980) & (M.mag >= 5)).sum())
h4 = int((H.br & (H.year >= 1750) & (H.mag >= 4)).sum()); h5 = int((H.br & (H.year >= 1750) & (H.mag >= 5)).sum())
m4_all = int((E.br & (E.year >= 1750) & (E.mag >= 4)).sum()); m5_all = int((E.br & (E.year >= 1750) & (E.mag >= 5)).sum())
yrs_1750 = (pd.Timestamp(last.date) - pd.Timestamp("1750-01-01")).days / 365.25
a_val = np.log10(rate_mc) + b * MC
R["gr"] = dict(mc=MC, start="1980-01-01", end=last.date, years=round(YR, 2), n=int(n_mc), b=round(float(b), 3), b_ci=[round(v, 2) for v in q(boots[:, 0])],
               b_se=round(float(b / np.sqrt(n_mc)), 3), a=round(float(a_val), 3),
               rate_ge2=round(rate_mc, 2), rate_ge3=round(float(rate_mc * 10 ** (-b * 1)), 2), rate_ge4=round(float(rate_mc * 10 ** (-b * 2)), 3),
               ret4=round(float(ret(b, rate_mc, 4)), 1), ret4_ci=[round(v, 1) for v in q(boots[:, 1])],
               ret5=round(float(ret(b, rate_mc, 5)), 0), ret5_ci=[round(v, 0) for v in q(boots[:, 2])],
               ret6=round(float(ret(b, rate_mc, 6)), 0),
               obs3=int((M.br & (M.year >= 1980) & (M.mag >= 3)).sum()), obs4=obs4, obs5=obs5,
               obs3_rate=round(float((M.br & (M.year >= 1980) & (M.mag >= 3)).sum() / YR), 2),
               obs4_ret=round(YR / obs4, 1), obs5_ret=round(YR / obs5, 1) if obs5 else None,
               hist4_1750_1969=h4, hist5_1750_1969=h5, hist4_ret=round(220 / h4, 1), hist5_ret=round(220 / h5, 1),
               all4_since1750=m4_all, all5_since1750=m5_all, years_since1750=round(yrs_1750, 1),
               all4_ret=round(yrs_1750 / m4_all, 1), all5_ret=round(yrs_1750 / m5_all, 1), stability=stab)
mf = []
for mm in np.round(np.arange(1.0, 5.31, 0.1), 1):
    mf.append(dict(mag=float(mm), n_ge=int((G >= mm - 1e-9).sum()), per_year=round(float((G >= mm - 1e-9).sum() / YR), 4),
                   n_eq=int((np.abs(G - mm) < 0.05).sum()), fit_per_year=round(float(10 ** (a_val - b * mm)), 4)))
pd.DataFrame(mf).to_csv(os.path.join(DATA, "magfreq.csv"), index=False)
R["magfreq"] = mf

# ---------- coal mines ----------
B = json.load(gzip.open(os.path.join(HIST, "_data12", "wd_osm_bundle12.json.gz")))
t = pd.read_csv(io.StringIO(B["results"]["osm_collieries"]["tsv"]), sep="\t").drop_duplicates("?osm")
nm = t["?name"].fillna("")
coal = t[nm.str.contains(r"colliery|coal|\bpit\b", case=False, regex=True) | t["?resource"].fillna("").str.contains("coal")]
cxy = np.array([np.array(re.findall(r"(-?\d+\.\d+) (-?\d+\.\d+)", w), float).mean(0) for w in coal["?wkt"]])
tf = Transformer.from_crs(4326, 27700, always_xy=True); tfi = Transformer.from_crs(27700, 4326, always_xy=True)
CX, CY = tf.transform(cxy[:, 0], cxy[:, 1])
kc = cKDTree(np.c_[CX, CY])
E["coal_km"] = (kc.query(E[["x", "y"]].values)[0] / 1000).round(1)
on = E[(E.cat == "modern") & (E.zone == "Britain onshore")].copy()
on["near"] = on.coal_km <= 5
# land baseline: share of points on British land within 5 km of a colliery feature
gbuf = shape(json.load(open(os.path.join(ROOT, "work", "gb_buffer.json"))))
from shapely.geometry import shape as _s
land = []
for g in json.load(open(os.path.join(HIST, "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    land.append(_s(g))
from shapely.ops import unary_union
from shapely import transform as shp_transform
L_ = unary_union(land)
gbland = prep(shp_transform(L_, lambda c: np.c_[tf.transform(c[:, 0], c[:, 1])]).intersection(gbuf))
gx = np.arange(0, 700000, 2000); gy = np.arange(0, 1250000, 2000); GX, GY = np.meshgrid(gx, gy)
pts = np.c_[GX.ravel(), GY.ravel()]
inl = np.array([gbland.contains(Point(p)) for p in pts[::1]])
lp = pts[inl]
# keep land in Great Britain only (exclude Ireland and France by longitude/latitude screen)
llon, llat = tfi.transform(lp[:, 0], lp[:, 1])
gbmask = (llat > 49.85) & ~((llon < -5.45) & (llat < 55.4))
lp = lp[gbmask]
land_share = float((kc.query(lp)[0] <= 5000).mean())
per = []
for p0 in range(1970, 2025, 5):
    x = on[(on.year >= p0) & (on.year < p0 + 5)]
    per.append(dict(start=p0, label=f"{p0} to {min(p0 + 4, 2024)}", n=len(x), near=int(x.near.sum()), share=round(float(x.near.mean()), 3)))
on["dow"] = pd.to_datetime(on.date).dt.dayofweek
nr = on[on.near & (on.year <= 2014)]; fr = on[~on.near]
wk_near = float((nr.dow >= 5).mean()); wk_far = float((fr.dow >= 5).mean())
bt = binomtest(int((nr.dow >= 5).sum()), len(nr), 2 / 7)
R["coal"] = dict(features=int(len(coal)), land_share=round(land_share, 3), periods=per,
                 share_to2014=round(float(on[on.year <= 2014].near.mean()), 3), n_to2014=int((on.year <= 2014).sum()), near_to2014=int(on[on.year <= 2014].near.sum()),
                 share_2015on=round(float(on[on.year >= 2015].near.mean()), 3), n_2015on=int((on.year >= 2015).sum()), near_2015on=int(on[on.year >= 2015].near.sum()),
                 share_2020on=round(float(on[on.year >= 2020].near.mean()), 3),
                 depth_near_median=float(on[on.near].depth.median()), depth_far_median=float(on[~on.near].depth.median()),
                 weekend_near=round(wk_near, 3), weekend_far=round(wk_far, 3), weekend_expected=round(2 / 7, 3), weekend_near_n=len(nr),
                 weekend_p=float(bt.pvalue))
pd.DataFrame(per).to_csv(os.path.join(DATA, "coal_periods.csv"), index=False)
# south-east and east of England: share of British epicentres and of British land east of 1 W and south of 53 N
plon, plat = tfi.transform(lp[:, 0], lp[:, 1])
br_ = E[E.br]
R["southeast"] = dict(events=int(((br_.lon > -1) & (br_.lat < 53)).sum()), share_events=round(float(((br_.lon > -1) & (br_.lat < 53)).mean()), 3),
                      share_land=round(float(((plon > -1) & (plat < 53)).mean()), 3),
                      events_modern=int(((br_.lon > -1) & (br_.lat < 53) & (br_.cat == "modern")).sum()),
                      share_events_modern=round(float(((br_.lon > -1) & (br_.lat < 53))[br_.cat == "modern"].mean()), 3))
on_after = E[(E.zone == "Britain onshore") & (E.date > "2008-02-27")]
R["onshore_since_2008_max"] = float(on_after.mag.max())

# ---------- hotspots (20 km squares, modern, Britain) ----------
mb = E[(E.cat == "modern") & E.br].copy()
mb["cx"] = (mb.x // 20000).astype(int); mb["cy"] = (mb.y // 20000).astype(int)
hs = mb.groupby(["cx", "cy"]).agg(n=("id", "size"), max_mag=("mag", "max"), first=("year", "min"), last=("year", "max"), median_year=("year", "median"),
                                  median_depth=("depth", "median"), near_coal=("coal_km", lambda s: float((s <= 5).mean())),
                                  town=("near_town", lambda s: s.value_counts().index[0])).reset_index().sort_values("n", ascending=False)
hs["x"] = hs.cx * 20000 + 10000; hs["y"] = hs.cy * 20000 + 10000
# label each square by the OS town nearest to the mean epicentre of its earthquakes
Tt = pd.read_csv(os.path.join(HIST, "osnames_gb.tsv"), sep="\t", usecols=["name1", "lang1", "name2", "lang2", "local_type", "x", "y"], dtype=str)
Tt = Tt[Tt.local_type.isin(["City", "Town"])].reset_index(drop=True)
e2 = Tt.lang1.isin(["cym", "gla"]) & (Tt.lang2 == "eng") & Tt.name2.notna(); Tt.loc[e2, "name1"] = Tt.loc[e2, "name2"]
kt_ = cKDTree(Tt[["x", "y"]].astype(float).values)
mxy = mb.groupby(["cx", "cy"])[["x", "y"]].mean()
hs["town"] = [Tt.name1.values[kt_.query(mxy.loc[(a_, b_)].values)[1]] for a_, b_ in zip(hs.cx, hs.cy)]
hs["lon"], hs["lat"] = tfi.transform(hs.x.values, hs.y.values)
hs["lon"] = hs.lon.round(3); hs["lat"] = hs.lat.round(3); hs["near_coal"] = hs.near_coal.round(2)
hs.drop(columns=["cx", "cy"]).to_csv(os.path.join(DATA, "hotspots.csv"), index=False)
R["hotspots"] = hs.head(15).drop(columns=["cx", "cy", "x", "y"]).to_dict("records")
R["hotspot_cells"] = int(len(hs)); R["hotspot_top10_share"] = round(float(hs.n.head(10).sum() / hs.n.sum()), 3)
R["hist_localities"] = [dict(locality=k, n=int(v)) for k, v in H[H.br].locality.value_counts().head(12).items()]

# named areas (circles around OS Open Names places)
O = pd.read_csv(os.path.join(HIST, "osnames_gb.tsv"), sep="\t", usecols=["name1", "lang1", "name2", "lang2", "local_type", "lat", "lon", "x", "y", "district", "county", "country"], dtype=str)
for c in ("x", "y", "lat", "lon"): O[c] = O[c].astype(float)
eng2 = O.lang1.isin(["cym", "gla"]) & (O.lang2 == "eng") & O.name2.notna()
O["alt"] = np.where(eng2, O.name1, np.where(O.name2.notna(), O.name2, ""))
O.loc[eng2, "name1"] = O.loc[eng2, "name2"]
O["county"] = O.county.str.split(" - ").str[0]


def place(name, county=None):
    q = O[(O.name1 == name) & O.local_type.isin(["City", "Town", "Village", "Hamlet"])]
    if county: q = q[q.county == county]
    return q.iloc[0]


AREAS = [("Comrie", "Comrie", "Perth and Kinross", 10), ("Kidsgrove and Stoke", "Kidsgrove", "Staffordshire", 10), ("Ollerton and Mansfield coalfield", "Ollerton", "Nottinghamshire", 12),
         ("Midlothian coalfield", "Bonnyrigg", None, 10), ("Llŷn and Caernarfon", "Pwllheli", "Gwynedd", 20), ("Inverness and the Great Glen", "Inverness", None, 20)]
R["areas"] = []
for lab, nmn, cty, rad in AREAS:
    p = place(nmn, cty); d = np.hypot(E.x - p.x, E.y - p.y) / 1000; s = E[d <= rad]
    R["areas"].append(dict(area=lab, centre=nmn, radius_km=rad, n=len(s), n_hist=int((s.cat == "historical").sum()), n_modern=int((s.cat == "modern").sum()),
                           max_mag=float(s.mag.max()), max_date=s.loc[s.mag.idxmax(), "date"], first=int(s.year.min()), last=int(s.year.max()),
                           modern_median_year=float(s[s.cat == "modern"].year.median()) if (s.cat == "modern").any() else None))
AR = {a["centre"]: a for a in R["areas"]}
cm = AR["Comrie"]
c_place = place("Comrie", "Perth and Kinross"); dC = np.hypot(E.x - c_place.x, E.y - c_place.y) / 1000
R["comrie"] = dict(hist=int(((dC <= 10) & (E.cat == "historical")).sum()), hist_1839_1846=int(((dC <= 10) & E.year.between(1839, 1846)).sum()),
                   modern=int(((dC <= 10) & (E.cat == "modern")).sum()), max_mag=cm["max_mag"])

# fracking: events in the catalogue near Little Plumpton (Preston New Road) and Weeton (Preese Hall)
fr_ = []
for nmn in ("Little Plumpton", "Weeton"):
    p = place(nmn, "Lancashire"); d = np.hypot(E.x - p.x, E.y - p.y) / 1000
    fr_.append(dict(place=nmn, n_5km=int((d <= 5).sum()), years=sorted(set(int(y) for y in E[d <= 5].year))))
R["fracking"] = dict(near=fr_, n_2011=int(((np.hypot(E.x - place("Weeton", "Lancashire").x, E.y - place("Weeton", "Lancashire").y) <= 10000) & (E.year == 2011)).sum()),
                     n_2018_2019=int(((np.hypot(E.x - place("Little Plumpton", "Lancashire").x, E.y - place("Little Plumpton", "Lancashire").y) <= 10000) & E.year.between(2018, 2019)).sum()))

# ---------- stories (matched to catalogue rows) ----------
STORIES = [("1382 Dover Straits", "1382-05-21", None), ("1580 Dover Straits", "1580-04-06", None), ("1801 Comrie", "1801-09-07", None),
           ("1839 Comrie", "1839-10-23", None), ("1852 Caernarfon", "1852-11-09", None), ("1884 Colchester", "1884-04-22", None),
           ("1896 Hereford", "1896-12-17", None), ("1906 Swansea", "1906-06-27", None), ("1931 Dogger Bank", "1931-06-07", None),
           ("1957 Derby", "1957-02-11", None), ("1979 Longtown", "1979-12-26", None), ("1984 Llŷn Peninsula", "1984-07-19", None),
           ("1990 Bishop's Castle", "1990-04-02", None), ("2002 Dudley", "2002-09-22", None), ("2007 Folkestone", "2007-04-28", None),
           ("2008 Market Rasen", "2008-02-27", None), ("2018 Swansea Valley", "2018-02-17", None)]
R["stories"] = {}
for lab, d, _ in STORIES:
    s = E[E.date == d].sort_values("mag", ascending=False)
    assert len(s), lab
    R["stories"][lab.split(" ")[0] + "_" + "_".join(lab.split(" ")[1:]).replace("'", "").replace("ŷ", "y")] = dict(label=lab, **ev(s.iloc[0]))
# aftershocks of 1984 Llyn within 30 km in the following year
p0 = R["stories"]["1984_Llyn_Peninsula"]
d = np.hypot((E.lat - p0["lat"]) * 111, (E.lon - p0["lon"]) * 111 * np.cos(np.radians(53)))
R["llyn_aftershocks"] = int(((d <= 30) & (E.date > "1984-07-19") & (E.date <= "1985-07-19")).sum())
p0 = R["stories"]["1580_Dover_Straits"]
R["dover_1580_rows"] = int((E.year == 1580).sum())

y50 = E[E.year == 1750]
R["y1750"] = dict(n=len(y50), london=int((y50.locality == "London").sum()), london_max=float(y50[y50.locality == "London"].mag.max()))
R["pre1700_br"] = int((H.br & (H.year < 1700)).sum())

# ---------- towns ----------
T = O[O.local_type.isin(["City", "Town"])].copy().reset_index(drop=True)
ke = cKDTree(E[["x", "y"]].values)
mags = E.mag.fillna(-1).values
out = []
for r in T.itertuples():
    ii = ke.query_ball_point([r.x, r.y], 25000)
    ii10 = ke.query_ball_point([r.x, r.y], 10000)
    if ii:
        j = max(ii, key=lambda k: (mags[k], -E.year.values[k]))
        bigm = mags[j]
    else:
        j = None; bigm = None
    out.append(dict(name=r.name1, type=r.local_type, county=r.county if isinstance(r.county, str) else (r.district if isinstance(r.district, str) else ""),
                    country=r.country, lat=round(r.lat, 4), lon=round(r.lon, 4), n_25km=len(ii), n_10km=len(ii10),
                    biggest_mag=None if j is None or bigm < 0 else float(bigm), biggest_date=None if j is None else E.date.values[j],
                    biggest_km=None if j is None else round(float(np.hypot(E.x.values[j] - r.x, E.y.values[j] - r.y) / 1000), 1),
                    biggest_id=None if j is None else E.id.values[j]))
TW = pd.DataFrame(out)
TW.to_csv(os.path.join(DATA, "towns.csv"), index=False)
bm = TW.biggest_mag
R["towns"] = dict(n=len(TW), n_city=int((TW.type == "City").sum()), none_25=int(TW.n_25km.eq(0).sum()), share_none_25=round(float(TW.n_25km.eq(0).mean()), 3),
                  ge4_25=int((bm >= 4).sum()), share_ge4_25=round(float((bm >= 4).mean()), 3), ge5_25=int((bm >= 5).sum()), share_ge5_25=round(float((bm >= 5).mean()), 3),
                  ge3_25=int((bm >= 3).sum()), share_ge3_25=round(float((bm >= 3).mean()), 3),
                  most_10km=TW.sort_values("n_10km", ascending=False).head(10)[["name", "county", "n_10km", "n_25km", "biggest_mag"]].to_dict("records"),
                  ge5_list=TW[bm >= 5].sort_values("biggest_mag", ascending=False)[["name", "county", "biggest_mag", "biggest_date", "biggest_km"]].to_dict("records"))
C = TW[TW.type == "City"].sort_values("biggest_mag", ascending=False)
R["cities"] = C[["name", "county", "country", "biggest_mag", "biggest_date", "biggest_km", "n_25km"]].to_dict("records")
R["city_named"] = {r["name"]: r for r in R["cities"]}

# ---------- page data ----------
ZC = {"Britain onshore": 0, "Britain coast (within 20 km)": 1, "Offshore": 2, "Ireland": 3, "Continent": 4, "Channel Islands": 5, "Isle of Man": 6}
ev_rows = []
for r in E.itertuples():
    lab = r.locality if isinstance(r.locality, str) and r.locality else ""
    ev_rows.append([round(r.lat, 3), round(r.lon, 3), r.date, None if pd.isna(r.mag) else float(r.mag), None if pd.isna(r.depth) else round(float(r.depth), 1),
                    r.intensity if isinstance(r.intensity, str) else "", ZC[r.zone], 0 if r.cat == "historical" else 1, lab, r.near_place, round(float(r.near_place_km), 1),
                    1 if r.coal_km <= 5 else 0])
PL = O[O.local_type.isin(["City", "Town", "Village"])].copy()
PL["cty"] = PL.county.fillna(PL.district).fillna("")
PL = PL.drop_duplicates(["name1", "cty"]).sort_values(["local_type", "name1"])
PLR = [[r.name1, r.cty, round(r.lat, 3), round(r.lon, 3), {"City": 0, "Town": 1, "Village": 2}[r.local_type], r.alt] for r in PL.itertuples()]
STR = {k: dict(label=v["label"], id=v["id"]) for k, v in R["stories"].items()}
json.dump(dict(ids=list(E.id), ecols=["lat", "lon", "date", "mag", "depth", "int", "zone", "cat", "loc", "near", "near_km", "coal"], E=ev_rows, P=PLR,
               coal=[[round(float(a), 3), round(float(b), 3)] for a, b in cxy[::1]][:0], stories=STR),
          open(os.path.join(DATA, "page_data.json"), "w"), separators=(",", ":"), ensure_ascii=False)
E.drop(columns=["br"]).to_csv(os.path.join(DATA, "events.csv"), index=False)


def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating, float)): return None if np.isnan(o) else float(o)
    return o


json.dump(clean(R), open(os.path.join(DATA, "results.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: R[k] for k in ("counts", "gr", "coal", "towns", "fracking", "comrie")}, indent=1, default=str)[:6000])
