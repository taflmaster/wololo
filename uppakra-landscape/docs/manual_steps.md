# Manual steps

These are the parts of the first milestone that a person has to do in a
browser or in QGIS. Everything after them is scripted.

## 1. Geotorget: lidar and historical orthophotos

1. Create a free account at <https://geotorget.lantmateriet.se>.
2. Order **Markhöjdmodell nedladdning, grid 1+** (open data, CC0) for the
   pilot. Pilot bounding box in SWEREF 99 TM (EPSG:3006), with the 2 km route
   margin included:
   - with margin: `377760, 6163206, 391760, 6177206`
   - pilot only:  `379760, 6165206, 389760, 6175206`
3. Order **Historiska ortofoton** for the same box. Request as many years as
   are offered (at least 1949-50s, 1960s, 1970s and 1990s); dry summers
   are the most useful for crop marks.
4. Optional, for valley edges and Romeleåsen later: **Laserdata Skog** point
   clouds (to build your own DEM with a ground filter).
5. Unpack the delivery:
   - elevation tiles (GeoTIFF) -> `data/raw/lidar/`
   - orthophotos, reprojected/clipped to EPSG:3006 -> `data/processed/ortho/`
     (one GeoTIFF per year, name it `ortho_<year>.tif`, e.g. with
     `gdalwarp -t_srs EPSG:3006 -te 377760 6163206 391760 6177206 in.tif ortho_1959.tif`)

Then run `python -m src.layers.dem`.

## 2. 1812-20 map (Skånska rekognosceringskartan)

Check first whether a georeferenced version already exists (see open
questions). If not:

1. Download the sheet(s) covering the pilot from Lantmäteriet's historical
   map search (Historiska kartor) or Krigsarkivet.
2. Georeference in QGIS (Layer > Georeferencer). Use churches, which mostly
   stand where they did in 1812, plus road junctions and stream confluences.
   Aim for 15+ points spread over the sheet, thin plate spline or polynomial
   2, target CRS EPSG:3006. Save as `data/processed/rekogn/rekogn_<sheet>.tif`
   and note the RMS error in the layer's metadata.
3. Digitize, inside the pilot square, into GeoPackages in `data/processed/`:

| File | Geometry | What | Suggested fields |
|---|---|---|---|
| `wetlands_1812.gpkg` | polygon | bogs, wet meadows (kärr, mosse, sank äng) | `type`, `certainty` (1-3) |
| `roads_1812.gpkg` | line | all mapped roads | `class` (main / village / track), `certainty` |
| `rivers.gpkg` | line | Höje å and tributaries as drawn in 1812 (meanders before straightening) | `name` |
| `fords.gpkg` | point | plausible crossings: where 1812 roads cross, narrow points, firm soil on both banks | `name`, `basis` |
| `water.gpkg` | polygon | sea, lakes, mill ponds | `type` |

Rivers and fords can also be seeded from modern hydrography
(Lantmäteriet Hydrografi or OSM) and corrected against the 1812 map.

Then run `python -m src.layers.cost_surface` and `python -m src.models.route`.

## 3. QGIS project

Run `qgis/build_project.py` (see the script's header). It adds every layer
that exists under `data/processed/` and `outputs/` and writes
`qgis/project.qgz` with relative paths.
