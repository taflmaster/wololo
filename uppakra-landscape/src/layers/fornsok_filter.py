"""Classify registered remains by dating and keep those relevant to 0-1000 AD.

Input: any point/polygon layer of registered remains with text attributes
(the K-samsök download, or a Fornsök GeoPackage export). All text columns are
searched for dating keywords from src/config.py.

Output (data/processed/):
  sites_all.gpkg        every remain, with a `period_class` column; used to
                        exclude already-registered areas from candidates
  sites_0_1000.gpkg     period_class in {core, broad}; training labels for
                        the settlement model and anchors for the route model

period_class:
  core      dating text names a sub-period inside 0-1000 AD
  broad     "järnålder" without sub-period (may include 500 BC-0)
  other     dated outside the period only
  undated   no dating keyword found

Usage:
    python -m src.layers.fornsok_filter [--input path ...]
"""
import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.config import CRS, DATING_KEYWORDS, PROCESSED, RAW


def classify_text(text):
    t = (text or "").lower()
    # strip excluded phrases first: "förromersk järnålder" contains both
    # "romersk järnålder" and "järnålder" but lies before the period
    stripped = t
    for k in sorted(DATING_KEYWORDS["exclude"], key=len, reverse=True):
        stripped = stripped.replace(k, " ")
    if any(k in stripped for k in DATING_KEYWORDS["core"]):
        return "core"
    if any(k in stripped for k in DATING_KEYWORDS["broad"]):
        return "broad"
    if any(k in t for k in DATING_KEYWORDS["exclude"]):
        return "other"
    return "undated"


def classify(gdf):
    text_cols = [c for c in gdf.columns
                 if c != "geometry" and pd.api.types.is_string_dtype(gdf[c])]
    joined = gdf[text_cols].fillna("").astype(str).agg(" | ".join, axis=1)
    out = gdf.copy()
    out["period_class"] = joined.map(classify_text)
    return out


def load_inputs(paths):
    frames = []
    for p in paths:
        g = gpd.read_file(p)
        g = g.to_crs(CRS) if g.crs else g.set_crs(CRS)
        g["source_file"] = Path(p).name
        frames.append(g)
    gdf = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=CRS)
    if "uri" in gdf.columns:
        gdf = gdf.drop_duplicates(subset="uri")
    return gdf


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--input", nargs="+",
                    default=[str(p) for p in sorted((RAW / "fornsok").glob("*.gpkg"))])
    args = ap.parse_args()
    if not args.input:
        raise SystemExit("no input; run python -m src.download.fornsok first")

    gdf = classify(load_inputs(args.input))
    PROCESSED.mkdir(parents=True, exist_ok=True)
    gdf.to_file(PROCESSED / "sites_all.gpkg", driver="GPKG")
    sel = gdf[gdf["period_class"].isin(["core", "broad"])]
    sel.to_file(PROCESSED / "sites_0_1000.gpkg", driver="GPKG")
    print(gdf["period_class"].value_counts().to_string())
    print(f"{len(sel)} sites kept for 0-1000 AD")


if __name__ == "__main__":
    main()
