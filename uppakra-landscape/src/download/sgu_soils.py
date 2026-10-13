"""Download the SGU soil map (jordarter 1:25 000-1:100 000) for the pilot.

Two routes:
  1. OGC API Features (default). SGU publishes open data at api.sgu.se; the
     collection id can change between versions, so it is a flag. List the
     collections with --list.
  2. --from-file PATH: clip an already downloaded GeoPackage/shapefile
     (e.g. the county file for Skåne from sgu.se's open data page).

Output: data/processed/soils.gpkg in EPSG:3006 with the original attributes.

Usage:
    python -m src.download.sgu_soils --list
    python -m src.download.sgu_soils --collection <id>
    python -m src.download.sgu_soils --from-file data/raw/sgu/jordarter_skane.gpkg
"""
import argparse

import geopandas as gpd
from shapely.geometry import box

from src.common import expand_bbox, http_get
from src.config import CRS, PILOT_BBOX, PROCESSED, RAW, ROUTE_MARGIN

API = "https://api.sgu.se/oppnadata/jordarter25-100/ogc/features/v1"
CRS_URI = "http://www.opengis.net/def/crs/EPSG/0/3006"


def list_collections(api):
    r = http_get(f"{api}/collections", params={"f": "json"})
    for c in r.json().get("collections", []):
        print(f"{c['id']:40s} {c.get('title', '')}")


def fetch_features(api, collection, bbox, limit=1000):
    url = f"{api}/collections/{collection}/items"
    params = {"bbox": ",".join(str(v) for v in bbox), "bbox-crs": CRS_URI, "crs": CRS_URI,
              "limit": limit, "f": "json"}
    features = []
    while url:
        r = http_get(url, params=params)
        page = r.json()
        features += page.get("features", [])
        url = next((ln["href"] for ln in page.get("links", []) if ln.get("rel") == "next"), None)
        params = None  # the next link already carries the query
        print(f"  {len(features)} features")
    gdf = gpd.GeoDataFrame.from_features(features)
    # Servers that ignore the crs parameter return CRS84
    if len(gdf) and gdf.total_bounds[0] < 180:
        return gdf.set_crs(4326).to_crs(CRS)
    return gdf.set_crs(CRS, allow_override=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=API)
    ap.add_argument("--collection", default="jordarter-25-100")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--from-file")
    ap.add_argument("--margin", type=float, default=ROUTE_MARGIN)
    args = ap.parse_args()

    if args.list:
        list_collections(args.api)
        return

    bbox = expand_bbox(PILOT_BBOX, args.margin)
    if args.from_file:
        gdf = gpd.read_file(args.from_file, bbox=bbox)
        gdf = gdf.to_crs(CRS) if gdf.crs else gdf.set_crs(CRS)
    else:
        gdf = fetch_features(args.api, args.collection, bbox)
        raw = RAW / "sgu" / "soils_pilot_raw.gpkg"
        raw.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(raw, driver="GPKG")

    gdf = gpd.clip(gdf, box(*bbox))
    out = PROCESSED / "soils.gpkg"
    out.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out, driver="GPKG")
    print(f"wrote {len(gdf)} polygons to {out}; columns: {list(gdf.columns)}")


if __name__ == "__main__":
    main()
