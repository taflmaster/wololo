"""Lidar visualizations for spotting hollow ways, mounds and old watercourses.

Implemented in numpy so the pipeline runs without RVT; rvt-py can be used to
cross-check (the formulas follow Zakšek et al. 2011 and Hesse 2010).

  hillshade      multi-directional hillshade (no single-light-direction bias)
  slope          degrees
  svf            sky-view factor: share of visible sky, low in hollows/ditches
  lrm            local relief model: DEM minus smoothed DEM, shows small
                 positive (mounds, banks) and negative (hollow ways) features

Large rasters are processed in overlapping blocks.

Usage:
    python -m src.layers.lidar_viz --dem data/processed/dem_1m.tif
"""
import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window
from scipy import ndimage

from src.config import PROCESSED


def _pad(dem):
    """Fill NaN with nearest valid value so filters don't spread holes."""
    mask = np.isnan(dem)
    if not mask.any():
        return dem
    idx = ndimage.distance_transform_edt(mask, return_distances=False, return_indices=True)
    return dem[tuple(idx)]


def slope_aspect(dem, res):
    z = _pad(dem)
    dzdy, dzdx = np.gradient(z, res)
    # rows run north -> south, so the northward gradient is -dzdy; aspect is
    # the compass direction of the downhill slope (0 = facing north)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    aspect = (np.degrees(np.arctan2(-dzdx, dzdy)) + 360) % 360
    return slope, aspect


def hillshade(dem, res, azimuth=315.0, altitude=45.0):
    z = _pad(dem)
    dzdy, dzdx = np.gradient(z, res)
    slope = np.arctan(np.hypot(dzdx, dzdy))
    aspect = np.arctan2(-dzdy, -dzdx)  # ESRI convention with rows running south
    az = np.radians(360.0 - azimuth + 90.0)
    alt = np.radians(altitude)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    return np.clip(hs, 0, 1)


def multi_hillshade(dem, res, n_dirs=6, altitude=35.0):
    azimuths = np.arange(n_dirs) * 360.0 / n_dirs
    return np.mean([hillshade(dem, res, a, altitude) for a in azimuths], axis=0)


def sky_view_factor(dem, res, radius_m=10.0, n_dirs=16):
    """SVF = 1 - mean over directions of sin(max horizon angle)."""
    z = _pad(dem)
    steps = max(1, int(round(radius_m / res)))
    h, w = z.shape
    padded = np.pad(z, steps, mode="edge")
    total = np.zeros_like(z, dtype="float64")
    for k in range(n_dirs):
        theta = 2 * np.pi * k / n_dirs
        dx, dy = np.cos(theta), np.sin(theta)
        max_tan = np.zeros_like(z, dtype="float64")
        for s in range(1, steps + 1):
            ox, oy = int(round(dx * s)), int(round(dy * s))
            if ox == 0 and oy == 0:
                continue
            dist = np.hypot(ox, oy) * res
            shifted = padded[steps + oy: steps + oy + h, steps + ox: steps + ox + w]
            np.maximum(max_tan, (shifted - z) / dist, out=max_tan)
        total += np.sin(np.arctan(max_tan))
    svf = 1 - total / n_dirs
    return np.where(np.isnan(dem), np.nan, svf).astype("float32")


def local_relief(dem, res, kernel_m=20.0):
    z = _pad(dem)
    size = max(3, int(round(kernel_m / res)) | 1)
    smooth = ndimage.uniform_filter(z, size=size, mode="nearest")
    return np.where(np.isnan(dem), np.nan, z - smooth).astype("float32")


PRODUCTS = {
    "hillshade": lambda d, r: multi_hillshade(d, r),
    "slope": lambda d, r: slope_aspect(d, r)[0],
    "svf": lambda d, r: sky_view_factor(d, r),
    "lrm": lambda d, r: local_relief(d, r),
}
OVERLAP_M = 40  # larger than any kernel/radius above


def run_blocked(dem_path, out_path, func, block=2048):
    with rasterio.open(dem_path) as src:
        res = src.res[0]
        ov = int(np.ceil(OVERLAP_M / res))
        profile = src.profile.copy()
        profile.update(dtype="float32", nodata=np.nan, compress="deflate", tiled=True,
                       blockxsize=512, blockysize=512, predictor=3, count=1, driver="GTiff")
        with rasterio.open(out_path, "w", **profile) as dst:
            for row in range(0, src.height, block):
                for col in range(0, src.width, block):
                    r0, c0 = max(0, row - ov), max(0, col - ov)
                    r1 = min(src.height, row + block + ov)
                    c1 = min(src.width, col + block + ov)
                    win = Window(c0, r0, c1 - c0, r1 - r0)
                    arr = src.read(1, window=win, masked=True).astype("float32").filled(np.nan)
                    if np.isnan(arr).all():
                        continue
                    res_arr = func(arr, res)
                    ir, ic = row - r0, col - c0
                    h = min(block, src.height - row)
                    w = min(block, src.width - col)
                    dst.write(res_arr[ir:ir + h, ic:ic + w].astype("float32"), 1,
                              window=Window(col, row, w, h))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dem", default=str(PROCESSED / "dem_1m.tif"))
    ap.add_argument("--products", nargs="+", default=list(PRODUCTS), choices=list(PRODUCTS))
    args = ap.parse_args()

    dem = Path(args.dem)
    out_dir = PROCESSED / "lidar"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in args.products:
        out = out_dir / f"{dem.stem}_{name}.tif"
        run_blocked(dem, out, PRODUCTS[name])
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
