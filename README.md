# Britain's earthquakes since 1382

Where do Britain's earthquakes happen, how big do they get, how often does a big one come, and what is the biggest earthquake ever recorded near your town? This study puts the British Geological Survey's historical catalogue (all known UK earthquakes before 1970) and its instrumental catalogue (1970 on) on one map, 1382 to 2024-09-02.

**Interactive version:** https://tristan-hotham.github.io/british-earthquakes/

This repository holds the interactive page, derived data and the analysis code for the data study *Britain's Earthquakes Since 1382: Clusters, Coalfields and How Often the Big Ones Come* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Paper and archived release: https://doi.org/10.5281/zenodo.23729643

## Headline results

- The two BGS catalogues hold 7,032 earthquakes (471 historical, 6,561 instrumental after removing 1,273 duplicate rows); 5,513 lie on land in Great Britain or within 20 km of its coast.
- The biggest is the Dogger Bank earthquake of 7 June 1931 (magnitude 6.1, offshore). On land the record is 5.3 (Caernarfon 1852, Hereford 1896, Derby 1957); the biggest instrumentally recorded are Market Rasen 2008 and Llŷn 1984 (5.2 in the catalogue).
- Gutenberg-Richter fit for magnitude 2.0+ in Britain, 1980 to 2024 (802 events): b = 0.92 (95% interval 0.86 to 0.99); a magnitude 4+ about every 3.9 years and a 5+ about every 32 years. Since 1750 the catalogues hold 91 magnitude 4+ (one every 3.0 years) and 15 magnitude 5+ (one every 18 years).
- 40% of onshore earthquakes recorded 1970 to 2014 lay within 5 km of a coal mine mapped in OpenStreetMap, against 10% of Britain's land; 15% since 2020. Near-mine earthquakes were shallower (median 1.7 km against 7.4 km) and fell less often at weekends (19% against 27%). The four busiest 20 km squares since 1970 are all coalfields.
- Detection bias: the share of recorded earthquakes below magnitude 2 rose from 69% in the 1970s to 87% in the 1990s, while the count of magnitude 3+ did not rise.
- 41% of the 1,426 OS cities and towns have had a magnitude 4+ within 25 km; 125 have had a magnitude 5+.
- The south and east of England (east of 1° W, south of 53° N) is 17% of Britain's land but has 3% of its recorded earthquakes.

## Files

- `index.html`: the interactive page (Leaflet map with a year slider and "biggest earthquake near you" search, charts, sortable city table).
- `header.png`: social card.
- `data/events.csv`: one row per earthquake: id (H = historical catalogue OBJECTID, M = modern EARTHQUAKE_EVENT_ID), catalogue, date, year, time (UTC), latitude, longitude, depth (km), magnitude and its type (ML, or MGMC macroseismic), intensity as given, locality (historical), my zone (Britain onshore, within 20 km of the British coast, offshore, Ireland, continent, Channel Islands), country, nearest OS town and place with distances, whether analyst-reviewed, British National Grid x and y, distance to the nearest OpenStreetMap coal mine feature (km).
- `data/decades.csv`: events per decade (instrumental) and per 50 years (historical) by magnitude band.
- `data/magfreq.csv`: cumulative magnitude-frequency counts and the fitted rates, 1980 to 2024.
- `data/hotspots.csv`: 20 km National Grid squares with instrumentally recorded earthquakes since 1970.
- `data/coal_periods.csv`: share of onshore earthquakes within 5 km of a mapped coal mine, by five-year period.
- `data/towns.csv`: every OS Open Names city and town with the biggest earthquake within 25 km and counts within 10 and 25 km.
- `data/page_data.json`: compact data for the page. `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `code/`: Python scripts, run in order: `01_prepare.py` (merge, de-duplicate and place the catalogues), `02_analysis.py` (all statistics), `04_build_site.py` (page and README), `05_header.py` (social card), `06_figures.py` (paper and blog figures), `07_paper.py` (paper PDF via xelatex), `08_release.py` (blog post and Zenodo files).
- `release/`: paper PDF and LaTeX source, blog post and figures, Zenodo files. `reddit/`: collage and post text.

## Method in brief

**Catalogues.** BGS historical catalogue (all known UK earthquakes before 1970, compiled from felt reports; before 1700 only magnitude 4 or more) and modern catalogue (instrumentally recorded since 1970), from the BGS ArcGIS map services, retrieved 28 October 2026. Historical magnitude = ML where given, otherwise the macroseismic magnitude (MGMC), as in the catalogue's MAG column. The modern layer had 7,834 rows: exact duplicates and near-duplicates (within 5 seconds and 0.1 degrees, keeping the analyst-reviewed row) were removed, leaving 6,561 events. The layer as served starts at ML 1.0.

**Places.** Natural Earth 1:10m land decides onshore, coastal (within 20 km of Great Britain), Ireland, continent or offshore. Nearest OS Open Names city or town and populated place by straight-line distance.

**Statistics.** b-value by Aki's maximum likelihood with Utsu's binning correction, completeness magnitude 2.0 (where b stabilises), 95% intervals from 2,000 bootstrap resamples. Coal mines: 2,574 OpenStreetMap features named as collieries, coal mines or pits or tagged resource=coal; land share from a 2 km grid. Weekend share tested against 2/7 with a binomial test.

**Caveats.** Historical locations and magnitudes are estimates from felt effects. Detection improves over time, so counts of small earthquakes reflect the network. Induced earthquakes are not labelled in the catalogue; closeness to a mapped mine is an indicator only. The fracking-induced earthquakes near Blackpool (2011, 2019) are not in the layer used. Magnitudes can differ from those quoted elsewhere (Llŷn 1984 is 5.2 here, 5.4 in many accounts).

## How to rerun

Python 3 with pandas, numpy, scipy, shapely, pyproj and matplotlib (Playwright for the header, xelatex for the paper). From `code/`: `python3 01_prepare.py && python3 02_analysis.py && python3 04_build_site.py`. Inputs are read one folder up and are not included: `_data12/bgs_quakes.json.gz` (BGS catalogues as downloaded), `_data12/wd_osm_bundle12.json.gz` (OpenStreetMap features via QLever), `osnames_gb.tsv` (OS Open Names) and a Natural Earth land outline.

## Sources and licence

- Earthquakes: British Geological Survey, UK historical earthquake catalogue and UK modern recorded earthquake catalogue, via the BGS map services (map.bgs.ac.uk), retrieved 28 October 2026; dataset record http://data.bgs.ac.uk/id/dataHolding/13480080 for the historical catalogue. Contains British Geological Survey materials © UKRI 2026. Copyright in BGS materials is vested in UKRI (NERC); the BGS asks for an acknowledgement whenever any part is reproduced. This repository republishes derived and reformatted catalogue values (dates, positions, magnitudes, intensities, localities) with that acknowledgement.
- Places: OS Open Names, Ordnance Survey, Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2026.
- Coal mines: © OpenStreetMap contributors, Open Database Licence 1.0 (via QLever). The coal mine distance in `events.csv` is derived from it.
- Coastline: Natural Earth (public domain). Base map tiles on the page: Esri. Map library: Leaflet.
- Background: Wikipedia articles "List of earthquakes in the British Isles", "1382 Dover Straits earthquake", "1580 Dover Straits earthquake", "1884 Colchester earthquake", "1931 Dogger Bank earthquake", "1984 Llŷn Peninsula earthquake", "1990 Bishop's Castle earthquake", "2007 Kent earthquake", "2008 Market Rasen earthquake", "1906 Swansea earthquake", "1185 East Midlands earthquake", "1275 British earthquake", "Fracking in the United Kingdom", "Coal mining in the United Kingdom" (CC BY-SA 4.0); Undiscovered Scotland, Comrie Earthquake House.

My text, charts and derived tables are released under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), keeping the BGS acknowledgement above on any reuse; the coal mine distances are derived from OpenStreetMap (ODbL). Code is MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) *Britain's Earthquakes Since 1382: Clusters, Coalfields and How Often the Big Ones Come*. Zenodo. https://doi.org/10.5281/zenodo.23729643

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
