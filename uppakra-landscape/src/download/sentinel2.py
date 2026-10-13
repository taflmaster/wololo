"""Download Sentinel-2 L2A scenes over the pilot for a dry summer (default 2018).

Uses the public Earth Search STAC catalogue (Element 84), which serves the
same ESA L2A product as Copernicus Data Space as cloud-optimised GeoTIFFs on
AWS, with no account. Only the pilot window is read from each COG, so a scene
costs a few MB rather than ~1 GB.

For each scene with little cloud over the pilot it writes, in
data/processed/sentinel2/<date>/:
    rgbn.tif   B02, B03, B04, B08 (10 m, reflectance x 10000), EPSG:3006
    ndvi.tif   NDVI with clouds/shadows (SCL) masked
and a per-summer ndvi_anomaly_<year>.tif: each pixel's mean NDVI minus a
local (500 m) median, which highlights crop marks against field-level trends.

Usage:
    python -m src.download.sentinel2 --year 2018 --months 6 7 8 --max-cloud 20
"""
import argparse

import numpy as np
import rasterio
import requests
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.windows import from_bounds
from scipy import ndimage

from src.common import bbox_to_wgs84, write_raster
from src.config import CRS, PILOT_BBOX, PROCESSED

STAC = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-l2a"
BANDS = {"B02": "blue", "B03": "green", "B04": "red", "B08": "nir"}
# SCL classes to drop: no data, saturated, cloud shadow, cloud med/high, cirrus, snow
SCL_BAD = {0, 1, 3, 8, 9, 10, 11}
RES = 10


def search(year, months, max_cloud):
    bbox = bbox_to_wgs84(PILOT_BBOX)
    start = f"{year}-{min(months):02d}-01T00:00:00Z"
    end_month = max(months)
    end = f"{year}-{end_month + 1:02d}-01T00:00:00Z" if end_month < 12 else f"{year + 1}-01-01T00:00:00Z"
    body = {"collections": [COLLECTION], "bbox": list(bbox), "datetime": f"{start}/{end}",
            "query": {"eo:cloud_cover": {"lt": max_cloud}}, "limit": 100}
    items, url = [], f"{STAC}/search"
    while url:
        r = requests.post(url, json=body, timeout=60)
        r.raise_for_status()
        page = r.json()
        items += page["features"]
        nxt = next((ln for ln in page.get("links", []) if ln.get("rel") == "next"), None)
        url, body = (nxt["href"], nxt.get("body", body)) if nxt else (None, None)
    return sorted(items, key=lambda it: it["properties"]["datetime"])


def asset_href(item, band):
    # Earth Search v1 names assets by colour; older versions by band code
    assets = item["assets"]
    for key in (BANDS.get(band), band, band.lower()):
        if key and key in assets:
            return assets[key]["href"]
    if band == "SCL":
        return assets["scl"]["href"]
    raise KeyError(f"{band} not in {list(assets)}")


def read_window(href, bbox, resampling=Resampling.bilinear):
    width = int((bbox[2] - bbox[0]) / RES)
    height = int((bbox[3] - bbox[1]) / RES)
    transform = rasterio.transform.from_bounds(*bbox, width, height)
    with rasterio.open(href) as src, WarpedVRT(src, crs=CRS, transform=transform, width=width,
                                               height=height, resampling=resampling) as vrt:
        arr = vrt.read(1, window=from_bounds(*bbox, transform)).astype("float32")
        return arr, {"crs": CRS, "transform": transform, "width": width, "height": height}


def ndvi_anomaly(ndvi_stack, radius_m=500):
    mean = np.nanmean(ndvi_stack, axis=0)
    size = int(2 * radius_m / RES) + 1
    filled = np.where(np.isnan(mean), np.nanmedian(mean), mean)
    local = ndimage.median_filter(filled, size=size)
    return np.where(np.isnan(mean), np.nan, mean - local)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--year", type=int, default=2018)
    ap.add_argument("--months", type=int, nargs="+", default=[6, 7, 8])
    ap.add_argument("--max-cloud", type=float, default=20, help="scene-level cloud %%")
    ap.add_argument("--max-masked", type=float, default=0.1,
                    help="skip scenes where more than this share of the pilot is cloud/shadow")
    args = ap.parse_args()

    items = search(args.year, args.months, args.max_cloud)
    print(f"{len(items)} scenes found")
    out_root = PROCESSED / "sentinel2"
    seen, ndvis, profile = set(), [], None
    for it in items:
        date = it["properties"]["datetime"][:10]
        if date in seen:  # same day from an adjacent tile/orbit
            continue
        scl, prof = read_window(asset_href(it, "SCL"), PILOT_BBOX, Resampling.nearest)
        bad = np.isin(scl, list(SCL_BAD))
        if bad.mean() > args.max_masked:
            print(f"{date}: {bad.mean():.0%} masked, skipped")
            continue
        seen.add(date)
        bands = [read_window(asset_href(it, b), PILOT_BBOX)[0] for b in BANDS]
        blue, green, red, nir = bands
        profile = {"crs": prof["crs"], "transform": prof["transform"],
                   "width": prof["width"], "height": prof["height"]}
        out = out_root / date
        out.mkdir(parents=True, exist_ok=True)
        with rasterio.open(out / "rgbn.tif", "w", driver="GTiff", count=4, dtype="uint16",
                           compress="deflate", **profile) as dst:
            for i, arr in enumerate(bands, 1):
                dst.write(np.clip(arr, 0, 65535).astype("uint16"), i)
            dst.descriptions = tuple(BANDS)
        with np.errstate(invalid="ignore", divide="ignore"):
            ndvi = (nir - red) / (nir + red)
        ndvi[bad] = np.nan
        write_raster(out / "ndvi.tif", ndvi, profile)
        ndvis.append(ndvi)
        print(f"{date}: written ({bad.mean():.0%} masked)")

    if ndvis:
        anom = ndvi_anomaly(np.stack(ndvis))
        write_raster(out_root / f"ndvi_anomaly_{args.year}.tif", anom, profile)
        print(f"NDVI anomaly from {len(ndvis)} scenes written")


if __name__ == "__main__":
    main()
