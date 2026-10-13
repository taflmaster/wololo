"""The candidate table: one row per candidate, shared by all three questions.

Columns
  id            S-001 (settlement), R-001 (road segment / ford), M-001 (market)
  kind          settlement | road | ford | market
  x, y          EPSG:3006 centre point
  evidence      semicolon-separated tags from EVIDENCE_TAGS
  score         0-1, how strongly the evidence agrees (see each model)
  nearest_site  distance (m) to the nearest registered remain of any period
  notes         free text for the archaeologist
  screenshot    relative path under outputs/candidates/screenshots/

Stored as outputs/candidates/candidates.gpkg (for QGIS) and .csv (for email).

Usage (to add a candidate by hand while inspecting in QGIS):
    python -m src.candidates add --kind settlement --x 385100 --y 6168900 \
        --evidence cropmark_s2_2018 --notes "circular ring ditch, ~15 m"
"""
import argparse

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from src.config import CANDIDATES, CRS, PROCESSED

EVIDENCE_TAGS = {
    "model_high_prob": "settlement model probability in top decile",
    "cropmark_s2_2018": "crop mark in Sentinel-2, summer 2018",
    "cropmark_ortho": "crop mark in a historical orthophoto (give year in notes)",
    "lidar_hollow_way": "hollow way(s) in LRM/SVF",
    "lidar_mound": "mound or bank in LRM/SVF",
    "map_1812_road": "on or next to a road on the 1812-20 map",
    "map_1812_village": "village/toft location on 1812-20 or enclosure map",
    "lcp_route": "on a modelled least-cost route or corridor",
    "river_crossing": "modelled route crosses a river here",
    "coast_or_mouth": "at the coast or a river mouth",
    "placename_old": "old place-name type (-löv/-lev, -inge, -hem/-um)",
    "placename_koping": "köping / market place name",
    "finds_soch": "museum finds nearby (K-samsök)",
    "dk_parallel": "comparable Danish site (Fund og Fortidsminder)",
}
COLUMNS = ["id", "kind", "x", "y", "evidence", "score", "nearest_site", "notes", "screenshot"]
PREFIX = {"settlement": "S", "road": "R", "ford": "R", "market": "M"}
GPKG = CANDIDATES / "candidates.gpkg"


def load():
    if GPKG.exists():
        return gpd.read_file(GPKG)
    return gpd.GeoDataFrame(columns=COLUMNS + ["geometry"], geometry="geometry", crs=CRS)


def save(gdf):
    CANDIDATES.mkdir(parents=True, exist_ok=True)
    gdf = gdf.sort_values(["kind", "score"], ascending=[True, False])
    gdf.to_file(GPKG, driver="GPKG")
    pd.DataFrame(gdf.drop(columns="geometry")).to_csv(CANDIDATES / "candidates.csv", index=False)


def nearest_site_distance(x, y):
    p = PROCESSED / "sites_all.gpkg"
    if not p.exists():
        return None
    sites = gpd.read_file(p).to_crs(CRS)
    return round(float(sites.distance(Point(x, y)).min()), 1) if len(sites) else None


def add(kind, x, y, evidence, score=None, notes="", screenshot=""):
    unknown = set(evidence) - set(EVIDENCE_TAGS)
    if unknown:
        raise ValueError(f"unknown evidence tags {unknown}; known: {list(EVIDENCE_TAGS)}")
    gdf = load()
    n = int((gdf["id"].astype(str).str[0] == PREFIX[kind]).sum()) + 1 if len(gdf) else 1
    row = {"id": f"{PREFIX[kind]}-{n:03d}", "kind": kind, "x": x, "y": y,
           "evidence": ";".join(evidence),
           "score": score if score is not None else round(min(1.0, len(evidence) / 4), 2),
           "nearest_site": nearest_site_distance(x, y), "notes": notes, "screenshot": screenshot}
    new = gpd.GeoDataFrame([row], geometry=[Point(x, y)], crs=CRS)
    save(pd.concat([gdf, new], ignore_index=True) if len(gdf) else new)
    return row["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--kind", required=True, choices=list(PREFIX))
    a.add_argument("--x", type=float, required=True)
    a.add_argument("--y", type=float, required=True)
    a.add_argument("--evidence", nargs="+", required=True)
    a.add_argument("--score", type=float)
    a.add_argument("--notes", default="")
    a.add_argument("--screenshot", default="")
    sub.add_parser("tags")
    args = ap.parse_args()
    if args.cmd == "tags":
        for k, v in EVIDENCE_TAGS.items():
            print(f"{k:20s} {v}")
    else:
        print(add(args.kind, args.x, args.y, args.evidence, args.score, args.notes, args.screenshot))


if __name__ == "__main__":
    main()
