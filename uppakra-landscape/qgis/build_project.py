"""Build qgis/project.qgz with every layer that exists so far.

Run inside QGIS (Plugins > Python Console > Show Editor > open this file > Run),
or headless with QGIS's Python:
    qgis --nologo --code qgis/build_project.py
    # or: python3 qgis/build_project.py   (with QGIS's python on PYTHONPATH)

Layers are added with relative paths, so the project works on any clone.
Re-run after new data arrives; the project is overwritten.
"""
import os
import sys
from pathlib import Path

from qgis.core import (QgsApplication, QgsCoordinateReferenceSystem, QgsLayerTreeGroup,
                       QgsProject, QgsRasterLayer, QgsVectorLayer)

try:
    ROOT = Path(__file__).resolve().parents[1]
except NameError:  # QGIS console run via exec() has no __file__
    ROOT = Path(os.getcwd())
    if not (ROOT / "data").exists():
        ROOT = ROOT.parent

P = ROOT / "data" / "processed"
O = ROOT / "outputs"

# (group, label, glob relative to ROOT, kind). Top of list draws on top.
LAYERS = [
    ("Candidates", "Candidates", "outputs/candidates/candidates.gpkg", "vector"),
    ("Routes", "Central places", "outputs/routes/central_places.gpkg", "vector"),
    ("Routes", "Least-cost routes", "outputs/routes/routes.gpkg", "vector"),
    ("Routes", "Corridor {stem}", "outputs/routes/corridor_*.tif", "raster"),
    ("Known sites", "Sites 0-1000 AD", "data/processed/sites_0_1000.gpkg", "vector"),
    ("Known sites", "All registered remains", "data/processed/sites_all.gpkg", "vector"),
    ("1812-20 map", "Roads 1812", "data/processed/roads_1812.gpkg", "vector"),
    ("1812-20 map", "Wetlands 1812", "data/processed/wetlands_1812.gpkg", "vector"),
    ("1812-20 map", "Fords", "data/processed/fords.gpkg", "vector"),
    ("1812-20 map", "Rekognosceringskartan (georef.)", "data/processed/rekogn/*.tif", "raster"),
    ("Hydrology", "Rivers", "data/processed/rivers.gpkg", "vector"),
    ("Hydrology", "Water", "data/processed/water.gpkg", "vector"),
    ("Soils", "SGU soils", "data/processed/soils.gpkg", "vector"),
    ("Lidar", "{stem}", "data/processed/lidar/*_lrm.tif", "raster"),
    ("Lidar", "{stem}", "data/processed/lidar/*_svf.tif", "raster"),
    ("Lidar", "{stem}", "data/processed/lidar/*_hillshade.tif", "raster"),
    ("Lidar", "{stem}", "data/processed/lidar/*_slope.tif", "raster"),
    ("Sentinel-2", "NDVI anomaly {stem}", "data/processed/sentinel2/ndvi_anomaly_*.tif", "raster"),
    ("Sentinel-2", "S2 {parent}", "data/processed/sentinel2/*/rgbn.tif", "raster"),
    ("Orthophotos", "{stem}", "data/processed/ortho/*.tif", "raster"),
    ("Cost", "Cost surface {stem}", "data/processed/cost_*.tif", "raster"),
    ("Base", "DEM {stem}", "data/processed/dem_*.tif", "raster"),
]


def build():
    project = QgsProject.instance()
    project.clear()
    project.setCrs(QgsCoordinateReferenceSystem("EPSG:3006"))
    project.setFileName(str(ROOT / "qgis" / "project.qgz"))
    project.writeEntryBool("Paths", "/Absolute", False)
    root = project.layerTreeRoot()
    groups, added = {}, 0
    for group, label, pattern, kind in LAYERS:
        for path in sorted(ROOT.glob(pattern)):
            name = label.format(stem=path.stem, parent=path.parent.name)
            layer = QgsVectorLayer(str(path), name, "ogr") if kind == "vector" \
                else QgsRasterLayer(str(path), name)
            if not layer.isValid():
                print(f"invalid layer skipped: {path}")
                continue
            project.addMapLayer(layer, False)
            if group not in groups:
                groups[group] = root.addGroup(group)
            node = groups[group].addLayer(layer)
            # only the first layer in each group starts visible to keep the map readable
            node.setItemVisibilityChecked(len(groups[group].children()) == 1)
            added += 1
    for g in groups.values():
        if isinstance(g, QgsLayerTreeGroup) and g.name() in ("Sentinel-2", "Orthophotos", "Cost"):
            g.setExpanded(False)
    project.write()
    print(f"{added} layers written to {project.fileName()}")


if __name__ in ("__main__", "__console__"):
    if QgsApplication.instance() is None:
        app = QgsApplication([], False)
        app.initQgis()
        build()
        app.exitQgis()
        sys.exit(0)
    build()
