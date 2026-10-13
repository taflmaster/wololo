# Iron Age SW Skåne: landscape discovery

Open-data pipeline for finding candidate settlements, roads and
marketplaces from 0-1000 AD around Uppåkra that are not in the national
register. The output is a ranked candidate table with evidence, for
archaeologists to check.

Questions:

1. **Settlements**: high-probability Iron Age settlement locations with no registered site.
2. **Roads**: routes between Uppåkra, Lund, Borgeby, Löddeköpinge and Trelleborgen, and where they crossed Höje å, Sege å and Kävlingeån.
3. **Marketplaces**: where routes meet river mouths or the coast, backed by place names or finds.

The work starts with a **10 x 10 km pilot square centred on Uppåkra**
(EPSG:3006 bbox `379760, 6165206, 389760, 6175206`). The rest of SW Skåne
comes only once the pilot works end to end. Uppåkra itself, fieldwork
and metal detecting are out of scope.

> Ancient remains are protected by law. No digging or detecting without a
> permit from Länsstyrelsen Skåne. Candidates go to Länsstyrelsen or Lund
> University Historical Museum.

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests        # synthetic-data checks, no downloads
```

Everything is in SWEREF 99 TM (EPSG:3006). Settings (pilot box, central
places, dating keywords) live in `src/config.py`. Raw and processed data
stay out of git.

## Pipeline: first milestone

| Step | Command | Output |
|---|---|---|
| Lidar and orthophotos (manual order) | see [docs/manual_steps.md](docs/manual_steps.md) | `data/raw/lidar/` |
| DEM mosaic | `python -m src.layers.dem` | `data/processed/dem_1m.tif` |
| Lidar visualizations | `python -m src.layers.lidar_viz` | hillshade, slope, SVF, LRM in `data/processed/lidar/` |
| Registered remains | `python -m src.download.fornsok` | `data/raw/fornsok/*.gpkg` |
| Filter to 0-1000 AD | `python -m src.layers.fornsok_filter` | `sites_all.gpkg`, `sites_0_1000.gpkg` |
| Soils | `python -m src.download.sgu_soils` | `data/processed/soils.gpkg` |
| Sentinel-2, summer 2018 | `python -m src.download.sentinel2 --year 2018` | per-date RGBN + NDVI, NDVI anomaly |
| 1812-20 map | georeference and digitize in QGIS, see [docs/manual_steps.md](docs/manual_steps.md) | `roads_1812`, `wetlands_1812`, `rivers`, `fords`, `water` |
| Cost surface | `python -m src.layers.cost_surface --res 10` | `data/processed/cost_10m.tif` |
| Uppåkra-Lund route | `python -m src.models.route --pairs Uppakra:Lund` | `outputs/routes/` with route, near-optimal corridor and comparison with the 1812 roads |
| QGIS project | `qgis/build_project.py` | `qgis/project.qgz` |
| Add a candidate | `python -m src.candidates add --kind settlement --x … --y … --evidence …` | `outputs/candidates/candidates.{gpkg,csv}` |

Milestone checklist:

- [ ] Geotorget account created; lidar and historical orthophotos ordered for the pilot square
- [x] Download scripts for Fornsök, SGU soils and Sentinel-2 (2018 summer), written but not yet run against the live services
- [x] Lidar visualizations: hillshade, sky-view factor, local relief model (code done, waiting for data)
- [ ] Fornsök sites 0-1000 AD filtered and mapped (filter done; needs a download)
- [ ] 1812-20 map georeferenced; wetlands and roads digitized for the pilot square
- [ ] One least-cost path, Uppåkra to Lund, compared with the 1812 road (model done; needs DEM and 1812 roads)
- [ ] QGIS project loading all of the above (builder script done)

## Method notes

**Dating filter.** All text attributes are searched for period words.
`core` means a sub-period inside 0-1000 AD (Roman Iron Age, Migration
period, Vendel, Viking). `broad` means plain "järnålder", which can include
the pre-Roman Iron Age and needs a manual look. "Förromersk järnålder" on
its own counts as outside the period.

**Lidar.** SVF uses a 10 m radius and 16 directions. LRM is the DEM minus a
20 m mean filter. Both are tuned for hollow ways and low mounds on a 1 m DEM.
Most of the pilot is ploughed, so expect lidar to help mainly on pasture,
valley edges and along Höje å.

**Sentinel-2.** Scenes come from the Earth Search STAC (the same ESA L2A
product as Copernicus Data Space, public COGs, no account). Only the pilot
window is read. Clouds and shadows are masked with SCL. The NDVI anomaly
is the summer mean minus a 500 m local median. Crop marks are 1-3 m
features, so 10 m pixels only catch large ones. Historical orthophotos
carry more weight for small features.

**Cost surface.** Tobler's hiking function on slope (isotropic). Soil
factors: peat and gyttja ×4, clay ×1.3. Wetlands from 1812 ×6. Rivers are
effectively barriers except within 60 m of a ford point. Without ford points
they get a ×8 penalty, so the model picks crossings itself. Sea and lakes
are impassable. The route model also writes a **corridor**: every cell on a
path within 5% of the optimal cost. Compare the corridor with the 1812 road
and lidar hollow ways, not just the single line.

**Pilot edge.** Lund sits about 0.5 km inside the pilot's northern edge,
so inputs are clipped with a 2 km margin. Borgeby, Löddeköpinge and
Trelleborgen fall outside the pilot. Those routes need the expanded area.

## Known pitfalls

- **Survey bias.** Known sites cluster along motorways, rail lines and
  1990s+ housing areas. The settlement model (next phase) must draw
  background points from surveyed areas, or model the excavation footprint
  as a control.
- **Undated features.** Crop marks and hollow ways can be Bronze Age or
  1800s, so they stay hypotheses.
- **Modern disturbance.** Drainage, removed field boundaries and pipelines
  make crop marks too. Cross-check against the 1812 map.

## Open questions

- Is the *Key to Uppåkra* database public, or does access go through the museum?
- Does Institutet för språk och folkminnen offer a bulk place-name export?
- Is there a georeferenced 1812-20 map already?
- Untested endpoints: this code was written without network access to
  kulturarvsdata.se, api.sgu.se and the STAC catalogue. On the first run,
  check the K-samsök CQL (`serviceOrganization=RAÄ`), the SGU collection id
  (`--list`) and the record counts against Fornsök's map.

## Layout

```
data/raw/            downloads (not in git)
data/processed/      reprojected, clipped layers (not in git)
src/download/        one script per source
src/layers/          DEM, lidar visualizations, dating filter, cost surface
src/models/          route model (settlement model: next phase)
src/candidates.py    candidate table and evidence tags
notebooks/           exploration
outputs/candidates/  candidate table and screenshots
qgis/                project builder (writes project.qgz)
docs/                manual steps
tests/               checks on synthetic data
```
