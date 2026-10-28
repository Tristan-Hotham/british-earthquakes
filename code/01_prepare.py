"""Step 1. Build one clean table of British earthquakes from the two BGS catalogues.

Inputs (read in place, never copied):
  ../../_data12/bgs_quakes.json.gz  British Geological Survey UK earthquake catalogues, via the BGS ArcGIS
                                    REST services (map.bgs.ac.uk), retrieved 28 October 2026:
                                    historical (all known events before 1970) and modern (instrumentally
                                    recorded since 1970).
  ../../osnames_gb.tsv              OS Open Names (OGL v3), for the nearest town and place.
  ../../did-lighthouses-work/release/build/ne10m_land_british_isles.json   Natural Earth 1:10m land.

Steps:
  * Historical layer (onshore_historical; identical to the sdds_historical layer, checked): 471 rows.
    Magnitude = ML where the catalogue gives one (> 0), otherwise MGMC (the macroseismic magnitude);
    this matches the catalogue's own MAG column. Five rows have no magnitude.
  * Modern layer (onshore_modern; the offshore_modern layer is identical): rows with the same time,
    place and magnitude are dropped, then rows within 5 seconds and 0.1 degrees of each other are
    treated as one event, keeping the analyst-reviewed row (USER_ENTERED other than SYSTEM).
  * Each event is placed: on land in Great Britain (Natural Earth land, excluding Ireland and the
    continent), within 20 km of the British coast, in Ireland, on the continent, or further offshore;
    (Isle of Man and Channel Islands kept apart), and given the nearest OS Open Names city or town and the nearest populated place.
Outputs: ../data/events.csv (one row per event, derived fields), ../work/gb_buffer.json.
Run: python3 01_prepare.py
"""
import gzip, json, os
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import shape, Point, mapping
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely import transform as shp_transform

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); HIST = os.path.join(ROOT, "..")
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
B = json.load(gzip.open(os.path.join(HIST, "_data12", "bgs_quakes.json.gz")))
L = B["layers"]

# ---------- historical ----------
h = pd.DataFrame([f["attributes"] for f in L["onshore_historical"]["features"]])
s = pd.DataFrame([f["attributes"] for f in L["sdds_historical"]["features"]])
key = ["DY_MO_YEAR", "HRMN", "SECS", "LAT", "LON", "MAG", "LOCALITY"]
assert set(map(tuple, h[key].astype(str).values)) == set(map(tuple, s[key].astype(str).values)), "historical layers differ"


def hist_row(r):
    dd, mm, yy = [p.strip() for p in r.DY_MO_YEAR.split("/")]
    day = int(dd) if dd and dd != "0" else None
    mon = int(mm) if mm and mm != "0" else None
    hm = int(r.HRMN or 0)
    mag = r.ML if (r.ML or 0) > 0 else (r.MGMC if (r.MGMC or 0) > 0 else None)
    return dict(id=f"H{int(r.OBJECTID)}", cat="historical", year=int(yy), month=mon, day=day,
                time=(f"{hm // 100:02d}:{hm % 100:02d}" if (r.HRMN or 0) > 0 else ""),
                lat=float(r.LAT), lon=float(r.LON), depth=(float(r.DEP) if (r.DEP or 0) > 0 else None),
                mag=(round(float(mag), 1) if mag else None), mag_type=("ML" if (r.ML or 0) > 0 else ("MGMC" if mag else "")),
                intensity=(r.INT or "").strip(), locality=(r.LOCALITY or "").strip().title(), reviewed=1)


H = pd.DataFrame([hist_row(r) for r in h.itertuples()])
assert ((H.mag.fillna(0) - h.MAG.values).abs() < 1e-6).all(), "magnitude rule does not match catalogue MAG"

# ---------- modern ----------
m = pd.DataFrame([f["attributes"] for f in L["onshore_modern"]["features"]])
o = pd.DataFrame([f["attributes"] for f in L["offshore_modern"]["features"]])
assert set(m.EARTHQUAKE_EVENT_ID) == set(o.EARTHQUAKE_EVENT_ID)
n_raw = len(m)
m["rev"] = (m.USER_ENTERED != "SYSTEM").astype(int)
m = m.sort_values(["DATETIME", "rev"], ascending=[True, False])
m = m.drop_duplicates(["DATETIME", "LATITUDE", "LONGITUDE", "ML"]).reset_index(drop=True)
n_exact = len(m)
keep = np.ones(len(m), bool)
t = m.DATETIME.values; la = m.LATITUDE.values; lo = m.LONGITUDE.values; rv = m.rev.values
for i in range(len(m)):
    if not keep[i]: continue
    j = i + 1
    while j < len(m) and t[j] - t[i] <= 5000:
        if keep[j] and abs(la[j] - la[i]) <= 0.1 and abs(lo[j] - lo[i]) <= 0.1:
            if rv[j] > rv[i]:
                keep[i] = False; break
            keep[j] = False
        j += 1
m = m[keep].reset_index(drop=True)
dt = pd.to_datetime(m.DATETIME, unit="ms")
M = pd.DataFrame(dict(id=["M" + str(int(x)) for x in m.EARTHQUAKE_EVENT_ID], cat="modern", year=dt.dt.year, month=dt.dt.month, day=dt.dt.day,
                      time=dt.dt.strftime("%H:%M"), lat=m.LATITUDE.astype(float), lon=m.LONGITUDE.astype(float),
                      depth=m.DEPTH.where(m.DEPTH > 0), mag=m.ML.round(1), mag_type="ML",
                      intensity=m.INTENSITY.where(m.INTENSITY > 0).map(lambda v: "" if pd.isna(v) else str(int(v))),
                      locality="", reviewed=m.rev))
E = pd.concat([H, M], ignore_index=True)

# ---------- geography ----------
tf = Transformer.from_crs(4326, 27700, always_xy=True); tfi = Transformer.from_crs(27700, 4326, always_xy=True)
E["x"], E["y"] = tf.transform(E.lon.values, E.lat.values)
polys = []
for g in json.load(open(os.path.join(HIST, "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    s_ = shape(g)
    polys += list(s_.geoms) if s_.geom_type == "MultiPolygon" else [s_]
polys.sort(key=lambda p: -p.area)
IRE, FRA = polys[1], polys[2]                     # Ireland and the continental fragment (checked by bounds)
assert IRE.bounds[0] < -10 and FRA.bounds[2] > 3
others = [p for p in polys if p is not IRE and p is not FRA]
# islands west of 5.4 W and south of 55.45 N with Irish longitudes belong to Ireland (none of size); keep the rest as Britain
ci = [p for p in others if p.bounds[3] < 49.8]                                   # Channel Islands
iom = [p for p in others if p.bounds[0] > -4.9 and p.bounds[2] < -4.25 and 54.0 < p.bounds[1] < 54.45]   # Isle of Man
gb_ll = unary_union([p for p in others if not (p.bounds[2] < -5.6 and p.bounds[3] < 55.45) and p not in ci and p not in iom])
proj = lambda geom: shp_transform(geom, lambda c: np.c_[tf.transform(c[:, 0], c[:, 1])])
gb = proj(gb_ll); gbp = prep(gb); cip = prep(proj(unary_union(ci))); iomp = prep(proj(unary_union(iom))); gb20 = prep(gb.buffer(20000)); ire = prep(proj(IRE)); fra = prep(proj(FRA))
json.dump(mapping(gb.buffer(20000).simplify(500)), open(os.path.join(ROOT, "work", "gb_buffer.json"), "w"))


def zone(x, y):
    p = Point(x, y)
    if gbp.contains(p): return "Britain onshore"
    if ire.contains(p): return "Ireland"
    if iomp.contains(p): return "Isle of Man"
    if cip.contains(p): return "Channel Islands"
    if fra.contains(p): return "Continent"
    if gb20.contains(p): return "Britain coast (within 20 km)"
    lon, lat = tfi.transform(x, y)
    if lat < 48.9 or (lon > 2.6 and lat < 51.6): return "Continent"   # Brittany, Belgium and inland France beyond the land outline
    return "Offshore"


E["zone"] = [zone(x, y) for x, y in zip(E.x, E.y)]

O = pd.read_csv(os.path.join(HIST, "osnames_gb.tsv"), sep="\t", usecols=["name1", "lang1", "name2", "lang2", "local_type", "lat", "lon", "x", "y", "district", "county", "country"], dtype=str)
for c in ("x", "y", "lat", "lon"): O[c] = O[c].astype(float)
# show the English form where OS gives a Welsh or Gaelic first name with an English alternative (Abertawe -> Swansea)
eng2 = O.lang1.isin(["cym", "gla"]) & (O.lang2 == "eng") & O.name2.notna()
O.loc[eng2, "name1"] = O.loc[eng2, "name2"]
O["county"] = O.county.str.split(" - ").str[0]
T = O[O.local_type.isin(["City", "Town"])].reset_index(drop=True)
P = O[O.local_type.isin(["City", "Town", "Village", "Hamlet", "Suburban Area", "Other Settlement"])].reset_index(drop=True)
kt = cKDTree(T[["x", "y"]].values); kp = cKDTree(P[["x", "y"]].values)
dtw, it = kt.query(E[["x", "y"]].values); dpl, ip = kp.query(E[["x", "y"]].values)
E["near_town"] = T.name1.values[it]; E["near_town_km"] = (dtw / 1000).round(1)
E["near_place"] = P.name1.values[ip]; E["near_place_km"] = (dpl / 1000).round(1)
E["county"] = [(P.county.values[i] if isinstance(P.county.values[i], str) else (P.district.values[i] if isinstance(P.district.values[i], str) else "")) for i in ip]
E["country"] = [P.country.values[i] if z in ("Britain onshore", "Britain coast (within 20 km)") else "" for i, z in zip(ip, E.zone)]
E.loc[E.zone == "Ireland", "country"] = "Ireland"
E["date"] = [f"{int(y):04d}-{int(mo):02d}-{int(d):02d}" if pd.notna(mo) and pd.notna(d) else (f"{int(y):04d}-{int(mo):02d}" if pd.notna(mo) else f"{int(y):04d}")
             for y, mo, d in zip(E.year, E.month, E.day)]
E = E.sort_values(["year", "month", "day", "time"], na_position="first").reset_index(drop=True)
cols = ["id", "cat", "date", "year", "time", "lat", "lon", "depth", "mag", "mag_type", "intensity", "locality", "zone", "country",
        "near_town", "near_town_km", "near_place", "near_place_km", "county", "reviewed", "x", "y"]
E["x"] = E.x.round().astype(int); E["y"] = E.y.round().astype(int); E["lat"] = E.lat.round(3); E["lon"] = E.lon.round(3)
E[cols].to_csv(os.path.join(ROOT, "data", "events.csv"), index=False)
json.dump(dict(modern_raw=n_raw, modern_after_exact=n_exact, modern_events=int((E.cat == "modern").sum()), historical_events=int((E.cat == "historical").sum())),
          open(os.path.join(ROOT, "work", "prep_counts.json"), "w"))
print(E.zone.value_counts(), E.groupby("cat").size(), n_raw, n_exact)
