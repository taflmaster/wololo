"""Mosaic Lantmäteriet elevation tiles and clip them to the pilot (plus margin).

Put the GeoTIFF tiles from the Geotorget order (Markhöjdmodell grid 1+, or a
DEM you built from Laserdata Skog) in data/raw/lidar/. Any CRS is accepted;
the output is EPSG:3006 at the requested resolution.

Usage:
    python -m src.layers.dem                    # 1 m DEM -> data/processed/dem_1m.tif
    python -m src.layers.dem --res 2            # coarser copy for cost surfaces
"""
import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.warp import Resampling, reproject

from src.common import expand_bbox, write_raster
from src.config import CRS, PILOT_BBOX, PROCESSED, RAW, ROUTE_MARGIN


def build_dem(tiles, bbox, res, resampling=Resampling.bilinear):
    srcs = [rasterio.open(t) for t in tiles]
    try:
        mosaic, transform = merge(srcs, nodata=np.nan, dtype="float32")
        src_crs = srcs[0].crs
    finally:
        for s in srcs:
            s.close()
    width = int(round((bbox[2] - bbox[0]) / res))
    height = int(round((bbox[3] - bbox[1]) / res))
    dst_transform = rasterio.transform.from_origin(bbox[0], bbox[3], res, res)
    dst = np.full((height, width), np.nan, dtype="float32")
    reproject(mosaic[0], dst, src_transform=transform, src_crs=src_crs, src_nodata=np.nan,
              dst_transform=dst_transform, dst_crs=CRS, dst_nodata=np.nan, resampling=resampling)
    profile = {"crs": CRS, "transform": dst_transform, "width": width, "height": height}
    return dst, profile


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tiles", default=str(RAW / "lidar"), help="folder with GeoTIFF tiles")
    ap.add_argument("--res", type=float, default=1.0)
    ap.add_argument("--margin", type=float, default=ROUTE_MARGIN)
    args = ap.parse_args()

    tiles = sorted(p for p in Path(args.tiles).rglob("*") if p.suffix.lower() in (".tif", ".tiff"))
    if not tiles:
        raise SystemExit(f"no GeoTIFF tiles in {args.tiles}; see docs/manual_steps.md")
    resampling = Resampling.bilinear if args.res <= 1 else Resampling.average
    dem, profile = build_dem(tiles, expand_bbox(PILOT_BBOX, args.margin), args.res, resampling)
    res_tag = f"{args.res:g}".replace(".", "p")
    out = write_raster(PROCESSED / f"dem_{res_tag}m.tif", dem, profile)
    print(f"{len(tiles)} tiles -> {out} ({dem.shape[1]} x {dem.shape[0]}, "
          f"{np.isnan(dem).mean():.1%} nodata)")


if __name__ == "__main__":
    main()
