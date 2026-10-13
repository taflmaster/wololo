"""Shared helpers for downloads and raster I/O."""
import time

import numpy as np
import rasterio
import requests
from pyproj import Transformer

from src.config import CRS


def bbox_to_wgs84(bbox, crs=CRS):
    """Return (min_lon, min_lat, max_lon, max_lat) covering a projected bbox."""
    t = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    minx, miny, maxx, maxy = bbox
    xs, ys = t.transform([minx, minx, maxx, maxx], [miny, maxy, miny, maxy])
    return min(xs), min(ys), max(xs), max(ys)


def expand_bbox(bbox, margin):
    minx, miny, maxx, maxy = bbox
    return minx - margin, miny - margin, maxx + margin, maxy + margin


def http_get(url, params=None, headers=None, retries=4, timeout=60, stream=False):
    """GET with exponential backoff on network errors and 5xx responses."""
    delay = 2
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout, stream=stream)
            if r.status_code < 500:
                r.raise_for_status()
                return r
        except requests.ConnectionError:
            if attempt == retries:
                raise
        if attempt == retries:
            r.raise_for_status()
        time.sleep(delay)
        delay *= 2


def read_raster(path):
    with rasterio.open(path) as src:
        arr = src.read(1, masked=True).astype("float32")
        return arr.filled(np.nan), src.profile.copy()


def write_raster(path, arr, profile, nodata=np.nan, dtype="float32"):
    profile = profile.copy()
    profile.update(driver="GTiff", count=1, dtype=dtype, nodata=nodata,
                   compress="deflate", tiled=True, blockxsize=512, blockysize=512,
                   predictor=3 if dtype.startswith("float") else 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr.astype(dtype), 1)
    return path
