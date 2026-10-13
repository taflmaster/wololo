"""Least-cost routes between central places, compared with the 1812-20 roads.

For each pair it writes:
  outputs/routes/routes.gpkg          one LineString per pair, with cost
  outputs/routes/corridor_<A>_<B>.tif cells whose detour is within N% of
                                      the optimum: a band of near-optimal
                                      routes rather than one thin line
and, if data/processed/roads_1812.gpkg exists, a comparison table
  outputs/routes/route_vs_1812.csv    share of the path within 50/100/200 m of
                                      a mapped 1812 road, mean/max distance

Usage:
    python -m src.models.route --pairs Uppakra:Lund
"""
import argparse

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from shapely.geometry import LineString, Point
from skimage.graph import MCP_Geometric

from src.common import read_raster, write_raster
from src.config import CENTRAL_PLACES, CRS, OUTPUTS, PROCESSED

OUT = OUTPUTS / "routes"


def to_rc(transform, x, y):
    row, col = rasterio.transform.rowcol(transform, x, y)
    return int(row), int(col)


def to_xy(transform, rc_path):
    rows, cols = zip(*rc_path)
    xs, ys = rasterio.transform.xy(transform, rows, cols)
    return list(zip(xs, ys))


def least_cost_path(cost, transform, start_xy, end_xy):
    """Return (LineString, total cost, accumulated-cost raster from start)."""
    c = np.where(np.isfinite(cost), cost, -1)  # negative = impassable for MCP
    res = transform.a
    mcp = MCP_Geometric(c * res / 1000.0, fully_connected=True)  # cost per cell -> hours
    start, end = to_rc(transform, *start_xy), to_rc(transform, *end_xy)
    for name, (r, cc) in (("start", start), ("end", end)):
        if not (0 <= r < cost.shape[0] and 0 <= cc < cost.shape[1]):
            raise ValueError(f"{name} point outside the cost raster")
        if not np.isfinite(cost[r, cc]):
            raise ValueError(f"{name} point is on an impassable cell")
    acc, _ = mcp.find_costs([start])
    path = mcp.traceback(end)
    return LineString(to_xy(transform, path)), float(acc[end]), acc


def corridor(cost, transform, start_xy, end_xy, tolerance=0.05):
    _, total, acc_a = least_cost_path(cost, transform, start_xy, end_xy)
    _, _, acc_b = least_cost_path(cost, transform, end_xy, start_xy)
    through = acc_a + acc_b
    return np.where(through <= total * (1 + tolerance), (through - total) / total, np.nan)


def compare_with_roads(line, roads, step=10.0):
    pts = [line.interpolate(d) for d in np.arange(0, line.length + step, step)]
    union = roads.geometry.union_all() if hasattr(roads.geometry, "union_all") \
        else roads.geometry.unary_union
    dist = np.array([union.distance(p) for p in pts])
    return {
        "length_m": round(line.length),
        "within_50m": round(float((dist <= 50).mean()), 3),
        "within_100m": round(float((dist <= 100).mean()), 3),
        "within_200m": round(float((dist <= 200).mean()), 3),
        "mean_dist_m": round(float(dist.mean()), 1),
        "max_dist_m": round(float(dist.max()), 1),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cost", default=str(PROCESSED / "cost_10m.tif"))
    ap.add_argument("--pairs", nargs="+", default=["Uppakra:Lund"])
    ap.add_argument("--tolerance", type=float, default=0.05, help="corridor width as cost share")
    args = ap.parse_args()

    cost, profile = read_raster(args.cost)
    cost = np.where(np.isnan(cost), np.inf, cost)
    transform = profile["transform"]
    roads_path = PROCESSED / "roads_1812.gpkg"
    roads = gpd.read_file(roads_path).to_crs(CRS) if roads_path.exists() else None

    OUT.mkdir(parents=True, exist_ok=True)
    rows, comparisons = [], []
    for pair in args.pairs:
        a, b = pair.split(":")
        try:
            line, total, _ = least_cost_path(cost, transform, CENTRAL_PLACES[a], CENTRAL_PLACES[b])
        except ValueError as e:
            print(f"{pair}: skipped ({e})")
            continue
        rows.append({"from": a, "to": b, "cost_hours": round(total, 3),
                     "length_m": round(line.length), "geometry": line})
        corr = corridor(cost, transform, CENTRAL_PLACES[a], CENTRAL_PLACES[b], args.tolerance)
        write_raster(OUT / f"corridor_{a}_{b}.tif", corr, profile)
        msg = f"{pair}: {line.length / 1000:.2f} km, {total:.2f} h"
        if roads is not None:
            cmp = {"from": a, "to": b, **compare_with_roads(line, roads)}
            comparisons.append(cmp)
            msg += f", {cmp['within_100m']:.0%} within 100 m of 1812 roads"
        print(msg)

    if rows:
        gpd.GeoDataFrame(rows, crs=CRS).to_file(OUT / "routes.gpkg", driver="GPKG")
        places = gpd.GeoDataFrame({"name": list(CENTRAL_PLACES)},
                                  geometry=[Point(xy) for xy in CENTRAL_PLACES.values()], crs=CRS)
        places.to_file(OUT / "central_places.gpkg", driver="GPKG")
    if comparisons:
        pd.DataFrame(comparisons).to_csv(OUT / "route_vs_1812.csv", index=False)


if __name__ == "__main__":
    main()
