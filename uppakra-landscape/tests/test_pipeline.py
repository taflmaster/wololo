"""Checks on synthetic data; no downloads needed. Run: python -m pytest tests"""
import geopandas as gpd
import numpy as np
import rasterio
from shapely.geometry import LineString, Point, box

from src.download.fornsok import parse_coords
from src.layers import cost_surface, lidar_viz
from src.layers.fornsok_filter import classify, classify_text
from src.models import route

RES = 10.0


def profile_for(shape, x0=380000, y0=6176000, res=RES):
    return {"crs": "EPSG:3006", "transform": rasterio.transform.from_origin(x0, y0, res, res),
            "width": shape[1], "height": shape[0]}


# --- dating -----------------------------------------------------------------

def test_dating_classes():
    assert classify_text("Boplats, vikingatid") == "core"
    assert classify_text("Gravfält. Yngre romersk järnålder") == "core"
    assert classify_text("Härd, järnålder") == "broad"
    assert classify_text("Boplats, förromersk järnålder") == "other"
    assert classify_text("Hög, bronsålder") == "other"
    assert classify_text("Fossil åker") == "undated"
    # a site with both pre-Roman and Viking dating is still in the period
    assert classify_text("förromersk järnålder - vikingatid") == "core"


def test_classify_reads_all_text_columns():
    g = gpd.GeoDataFrame({"label": ["Boplats", "Hög"], "dating": [None, "Vendeltid"]},
                         geometry=[Point(0, 0), Point(1, 1)], crs="EPSG:3006")
    assert list(classify(g)["period_class"]) == ["undated", "core"]


def test_parse_coords_orders():
    assert parse_coords("13.168,55.664")[2] == 4326
    x, y, _ = parse_coords("55.664 13.168")  # lat lon -> swapped
    assert (x, y) == (13.168, 55.664)
    assert parse_coords("384760,6170206") == (384760.0, 6170206.0, 3006)


# --- lidar ------------------------------------------------------------------

def test_slope_aspect_east_rising_plane_faces_west():
    dem = np.tile(np.arange(50, dtype="float32"), (50, 1))  # +1 m per 1 m eastwards
    slope, aspect = lidar_viz.slope_aspect(dem, 1.0)
    assert np.allclose(slope[5:-5, 5:-5], 45, atol=0.1)
    assert np.allclose(aspect[5:-5, 5:-5], 270, atol=0.1)


def test_hillshade_lit_side():
    # plane facing north-west (falls towards NW) should be brighter than one facing SE
    yy, xx = np.mgrid[0:50, 0:50].astype("float32")
    faces_nw = xx - yy * -1.0  # rises to the east and to the south (rows go south)
    faces_se = -faces_nw
    assert lidar_viz.hillshade(faces_nw, 1.0).mean() > lidar_viz.hillshade(faces_se, 1.0).mean()


def test_svf_and_lrm_on_ditch_and_mound():
    dem = np.zeros((80, 80), dtype="float32")
    dem[:, 38:42] = -1.0        # N-S ditch (hollow way)
    dem[15:20, 15:20] = 1.0     # mound
    svf = lidar_viz.sky_view_factor(dem, 1.0, radius_m=10)
    lrm = lidar_viz.local_relief(dem, 1.0, kernel_m=21)
    assert svf[40, 40] < svf[40, 10]         # ditch sees less sky than flat ground
    assert np.isclose(svf[40, 10], 1.0)
    assert lrm[17, 17] > 0.5 and lrm[40, 40] < -0.5


def test_blocked_processing_matches_whole(tmp_path):
    rng = np.random.default_rng(0)
    dem = np.cumsum(rng.normal(size=(300, 300)), axis=1).astype("float32")
    prof = profile_for(dem.shape, res=1.0)
    src = tmp_path / "dem.tif"
    with rasterio.open(src, "w", driver="GTiff", count=1, dtype="float32", **prof) as dst:
        dst.write(dem, 1)
    out = tmp_path / "lrm.tif"
    lidar_viz.run_blocked(src, out, lidar_viz.PRODUCTS["lrm"], block=128)
    with rasterio.open(out) as r:
        blocked = r.read(1)
    whole = lidar_viz.local_relief(dem, 1.0)
    assert np.allclose(blocked, whole, atol=1e-4)


# --- cost surface and route -------------------------------------------------

def test_tobler_flat_is_fastest():
    c = cost_surface.tobler_cost(np.array([0.0, 5.0, 20.0]))
    assert np.isclose(1 / c[0], 6.0)
    assert c[0] < c[1] < c[2]


def _flat_world(n=200):
    dem = np.zeros((n, n), dtype="float32")
    return dem, profile_for(dem.shape)


def test_route_uses_ford_and_avoids_wetland():
    dem, prof = _flat_world()
    t = prof["transform"]
    x0, y0 = t.c, t.f
    # river running west-east across the middle, ford near the east side
    river = gpd.GeoDataFrame(geometry=[LineString([(x0, y0 - 1000), (x0 + 2000, y0 - 1000)])],
                             crs="EPSG:3006")
    ford = gpd.GeoDataFrame(geometry=[Point(x0 + 1600, y0 - 1000)], crs="EPSG:3006")
    wet = gpd.GeoDataFrame(geometry=[box(x0 + 300, y0 - 600, x0 + 700, y0 - 300)], crs="EPSG:3006")
    soils = gpd.GeoDataFrame({"jordart": ["Lera", "Torv"]},
                             geometry=[box(x0, y0 - 2000, x0 + 2000, y0), box(x0, y0 - 2000, x0 + 100, y0)],
                             crs="EPSG:3006")
    cost, notes = cost_surface.build_cost(dem, prof, soils=soils, wetlands=wet, rivers=river, fords=ford)
    assert {"rivers+fords", "wetlands"} <= set(notes) and any(n.startswith("soil") for n in notes)

    start, end = (x0 + 500, y0 - 200), (x0 + 500, y0 - 1800)
    line, total, _ = route.least_cost_path(cost, t, start, end)
    crossing = line.intersection(river.geometry[0])
    assert crossing.distance(ford.geometry[0]) < 80   # crosses at the ford
    assert line.intersection(wet.geometry[0]).length < 50  # skirts the wetland

    corr = route.corridor(cost, t, start, end, tolerance=0.05)
    assert np.nanmin(corr) >= -1e-6 and np.isfinite(corr).sum() > 0


def test_impassable_water_and_comparison():
    dem, prof = _flat_world(100)
    t = prof["transform"]
    x0, y0 = t.c, t.f
    water = gpd.GeoDataFrame(geometry=[box(x0 + 400, y0 - 800, x0 + 600, y0)], crs="EPSG:3006")
    cost, _ = cost_surface.build_cost(dem, prof, water=water)
    line, _, _ = route.least_cost_path(cost, t, (x0 + 100, y0 - 100), (x0 + 900, y0 - 100))
    assert not line.intersects(water.geometry[0].buffer(-RES))
    road = gpd.GeoDataFrame(geometry=[line], crs="EPSG:3006")
    cmp = route.compare_with_roads(line, road)
    assert cmp["within_50m"] == 1.0 and cmp["max_dist_m"] < 1


def test_candidates_add(tmp_path, monkeypatch):
    from src import candidates
    monkeypatch.setattr(candidates, "CANDIDATES", tmp_path)
    monkeypatch.setattr(candidates, "GPKG", tmp_path / "candidates.gpkg")
    monkeypatch.setattr(candidates, "PROCESSED", tmp_path)
    a = candidates.add("settlement", 385000, 6169000, ["model_high_prob", "cropmark_s2_2018"])
    b = candidates.add("settlement", 385500, 6169500, ["model_high_prob"])
    c = candidates.add("market", 376000, 6181000, ["coast_or_mouth"])
    assert (a, b, c) == ("S-001", "S-002", "M-001")
    assert (tmp_path / "candidates.csv").exists()
