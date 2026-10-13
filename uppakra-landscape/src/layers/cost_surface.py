"""Travel cost surface for pre-modern movement on foot / with carts.

cost (hours per km) = slope term x soil factor x wetland factor x river factor

  slope     Tobler's hiking function, isotropic: 6 * exp(-3.5 * |tan(slope)|) km/h
  soil      SGU soil map; peat/gyttja are slow, clay a bit slow (matched on
            the soil name, see SOIL_FACTORS)
  wetlands  bogs/meadows digitized from the 1812-20 map (pre-drainage)
  rivers    river lines are near-impassable except within FORD_RADIUS of a
            ford point; without ford points rivers get a finite penalty so
            the model picks the cheapest crossing itself
  water     sea and lakes polygons are barriers

Optional inputs in data/processed/ are used when present:
  soils.gpkg, wetlands_1812.gpkg, rivers.gpkg, fords.gpkg, water.gpkg

Usage:
    python -m src.layers.cost_surface --res 10
"""
import argparse

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize

from src.common import expand_bbox, write_raster
from src.config import CRS, PILOT_BBOX, PROCESSED, ROUTE_MARGIN

# (substring in soil name, factor). First match wins, so order matters.
SOIL_FACTORS = [
    ("vatten", np.inf),
    ("torv", 4.0), ("gyttja", 4.0), ("kärr", 4.0), ("mosse", 4.0),
    ("svämsediment", 2.0), ("lera", 1.3), ("silt", 1.2),
    ("sand", 1.0), ("grus", 1.0), ("morän", 1.0), ("berg", 1.1),
    ("fyllning", 1.0),  # modern fill; true ground unknown
]
WETLAND_FACTOR = 6.0
RIVER_FACTOR = 1000.0       # away from a ford: effectively a barrier
RIVER_FACTOR_NO_FORDS = 8.0  # when no ford points exist
RIVER_WIDTH_M = 15.0
FORD_RADIUS_M = 60.0
FORD_FACTOR = 1.5


def tobler_cost(slope_deg):
    speed = 6.0 * np.exp(-3.5 * np.abs(np.tan(np.radians(slope_deg))))
    return 1.0 / speed  # hours per km


def soil_factor_raster(soils, shape, transform, column=None):
    if column is None:
        candidates = [c for c in soils.columns
                      if c != "geometry" and pd.api.types.is_string_dtype(soils[c])]
        # prefer a column whose values look like soil names
        column = max(candidates, key=lambda c: soils[c].astype(str).str.lower()
                     .str.contains("lera|sand|morän|torv").sum())
    names = soils[column].astype(str).str.lower()
    factors = np.ones(len(soils))
    for i, name in enumerate(names):
        for key, f in SOIL_FACTORS:
            if key in name:
                factors[i] = f
                break
    shapes = [(g, f if np.isfinite(f) else -1) for g, f in zip(soils.geometry, factors)]
    out = rasterize(shapes, out_shape=shape, transform=transform, fill=1.0, dtype="float32")
    out[out < 0] = np.inf
    return out, column


def read_dem(path, bbox, res):
    width = int(round((bbox[2] - bbox[0]) / res))
    height = int(round((bbox[3] - bbox[1]) / res))
    transform = rasterio.transform.from_origin(bbox[0], bbox[3], res, res)
    with rasterio.open(path) as src:
        win = rasterio.windows.from_bounds(*bbox, transform=src.transform)
        dem = src.read(1, window=win, out_shape=(height, width), boundless=True,
                       fill_value=np.nan, resampling=Resampling.average, masked=True)
    return dem.astype("float32").filled(np.nan), {
        "crs": CRS, "transform": transform, "width": width, "height": height}


def optional(name):
    p = PROCESSED / name
    if p.exists():
        g = gpd.read_file(p)
        return g.to_crs(CRS) if g.crs else g.set_crs(CRS)
    return None


def build_cost(dem, profile, soils=None, wetlands=None, rivers=None, fords=None, water=None,
               soil_column=None):
    from src.layers.lidar_viz import slope_aspect

    res = profile["transform"].a
    shape = dem.shape
    transform = profile["transform"]
    slope, _ = slope_aspect(dem, res)
    cost = tobler_cost(slope)
    notes = ["slope"]

    if soils is not None and len(soils):
        f, col = soil_factor_raster(soils, shape, transform, soil_column)
        cost = cost * f
        notes.append(f"soil({col})")
    if wetlands is not None and len(wetlands):
        m = rasterize(wetlands.geometry, out_shape=shape, transform=transform, fill=0, dtype="uint8")
        cost = np.where(m == 1, cost * WETLAND_FACTOR, cost)
        notes.append("wetlands")
    if rivers is not None and len(rivers):
        have_fords = fords is not None and len(fords)
        river_geom = rivers.geometry.buffer(max(RIVER_WIDTH_M / 2, res / 2))
        # all_touched so a diagonal step can't slip between river cells
        m = rasterize(river_geom, out_shape=shape, transform=transform, fill=0, dtype="uint8",
                      all_touched=True)
        factor = np.where(m == 1, RIVER_FACTOR if have_fords else RIVER_FACTOR_NO_FORDS, 1.0)
        if have_fords:
            fm = rasterize(fords.geometry.buffer(FORD_RADIUS_M), out_shape=shape,
                           transform=transform, fill=0, dtype="uint8")
            factor = np.where((m == 1) & (fm == 1), FORD_FACTOR, factor)
        cost = cost * factor
        notes.append("rivers+fords" if have_fords else "rivers")
    if water is not None and len(water):
        m = rasterize(water.geometry, out_shape=shape, transform=transform, fill=0, dtype="uint8")
        cost = np.where(m == 1, np.inf, cost)
        notes.append("water")

    cost = np.where(np.isnan(dem), np.inf, cost).astype("float32")
    return cost, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dem", default=str(PROCESSED / "dem_1m.tif"))
    ap.add_argument("--res", type=float, default=10.0)
    ap.add_argument("--margin", type=float, default=ROUTE_MARGIN)
    ap.add_argument("--soil-column", help="soil-name attribute (auto-detected if omitted)")
    args = ap.parse_args()

    bbox = expand_bbox(PILOT_BBOX, args.margin)
    dem, profile = read_dem(args.dem, bbox, args.res)
    cost, notes = build_cost(dem, profile, optional("soils.gpkg"), optional("wetlands_1812.gpkg"),
                             optional("rivers.gpkg"), optional("fords.gpkg"),
                             optional("water.gpkg"), args.soil_column)
    out = PROCESSED / f"cost_{args.res:g}m.tif"
    # GeoTIFF readers handle inf poorly; store barriers as nodata
    write_raster(out, np.where(np.isfinite(cost), cost, np.nan), profile)
    print(f"wrote {out} using: {', '.join(notes)}")


if __name__ == "__main__":
    main()
