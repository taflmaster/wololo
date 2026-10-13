"""Download registered remains (Fornsök / KMR) for the pilot via K-samsök.

K-samsök (SOCH) aggregates Riksantikvarieämbetet's register together with
museum objects. We query by bounding box, ask for the "presentation" record
schema (flat XML), and keep label, type, description, dating text and point
geometry.

Usage:
    python -m src.download.fornsok                 # RAÄ register records
    python -m src.download.fornsok --all-orgs      # also museum finds (SOCH)

Alternative: export a selection from https://app.raa.se/open/fornsok/ as
GeoPackage and put it in data/raw/fornsok/. The filter step accepts either.

Note: the CQL fields below follow the K-samsök documentation; endpoints were
not reachable from the environment this was written in, so check the first
run's record count against Fornsök's map.
"""
import argparse
import re
import xml.etree.ElementTree as ET

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import Point

from src.common import bbox_to_wgs84, expand_bbox, http_get
from src.config import CRS, PILOT_BBOX, RAW, ROUTE_MARGIN

API = "https://kulturarvsdata.se/ksamsok/api"
PAGE = 500


def local(tag):
    return tag.rsplit("}", 1)[-1]


def find_all(elem, name):
    return [e for e in elem.iter() if local(e.tag) == name]


def first_text(elem, *names):
    for name in names:
        for e in find_all(elem, name):
            if e.text and e.text.strip():
                return e.text.strip()
    return None


def parse_coords(text):
    """Return (x, y, epsg) from a GML/georss coordinate string."""
    nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", text)]
    if len(nums) < 2:
        return None
    x, y = nums[0], nums[1]
    if abs(x) <= 180 and abs(y) <= 90:
        # lon,lat order in GML; swap if it looks like lat,lon for Sweden
        if x > 50 and y < 30:
            x, y = y, x
        return x, y, 4326
    return x, y, 3006


def parse_record(rec):
    coords = None
    for e in find_all(rec, "coordinates") + find_all(rec, "pos") + find_all(rec, "point"):
        if e.text:
            coords = parse_coords(e.text)
            if coords:
                break
    if not coords:
        return None
    times = [e.text.strip() for e in find_all(rec, "timeLabel") if e.text]
    times += [f"{a.text}..{b.text}" for a, b in zip(find_all(rec, "fromTime"), find_all(rec, "toTime"))
              if a.text and b.text]
    return {
        "uri": first_text(rec, "entityUri", "idLabel", "id"),
        "label": first_text(rec, "itemLabel", "label"),
        "type": first_text(rec, "type", "itemType"),
        "organization": first_text(rec, "organization", "serviceOrganization"),
        "description": " | ".join(e.text.strip() for e in find_all(rec, "description") if e.text)[:2000],
        "dating": " | ".join(times)[:500],
        "x": coords[0], "y": coords[1], "epsg": coords[2],
    }


def build_query(bbox_wgs84, all_orgs):
    q = 'boundingBox=/WGS84 "{:.5f} {:.5f} {:.5f} {:.5f}"'.format(*bbox_wgs84)
    if not all_orgs:
        q += " AND serviceOrganization=RAÄ"
    return q


def fetch(bbox, all_orgs=False, max_records=50000):
    query = build_query(bbox_to_wgs84(bbox), all_orgs)
    rows, start, total = [], 1, None
    while total is None or start <= min(total, max_records):
        r = http_get(API, params={
            "method": "search", "query": query, "hitsPerPage": PAGE,
            "startRecord": start, "recordSchema": "presentation",
        })
        root = ET.fromstring(r.content)
        if total is None:
            total = int(first_text(root, "totalHits") or 0)
            print(f"{total} hits for {query}")
        records = find_all(root, "record")
        if not records:
            break
        rows += [p for p in (parse_record(rec) for rec in records) if p]
        start += PAGE
    return rows


def to_gdf(rows):
    geoms = []
    to_sweref = Transformer.from_crs(4326, 3006, always_xy=True)
    for r in rows:
        x, y = (to_sweref.transform(r["x"], r["y"]) if r["epsg"] == 4326 else (r["x"], r["y"]))
        geoms.append(Point(x, y))
    cols = [{k: v for k, v in r.items() if k not in ("x", "y", "epsg")} for r in rows]
    return gpd.GeoDataFrame(cols, geometry=geoms, crs=CRS)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--all-orgs", action="store_true", help="include museum finds, not only RAÄ")
    ap.add_argument("--margin", type=float, default=ROUTE_MARGIN)
    args = ap.parse_args()

    bbox = expand_bbox(PILOT_BBOX, args.margin)
    gdf = to_gdf(fetch(bbox, args.all_orgs))
    gdf = gdf.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
    out = RAW / "fornsok" / ("ksamsok_all_pilot.gpkg" if args.all_orgs else "ksamsok_raa_pilot.gpkg")
    out.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out, driver="GPKG")
    print(f"wrote {len(gdf)} records to {out}")


if __name__ == "__main__":
    main()
