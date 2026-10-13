"""Project-wide settings: CRS, study area, paths and reference places.

Everything is in SWEREF 99 TM (EPSG:3006). Coordinates for central places are
approximate (church / site centre) and should be checked before reporting.
"""
from pathlib import Path

CRS = "EPSG:3006"

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
CANDIDATES = OUTPUTS / "candidates"

# Pilot: 10 x 10 km square centred on Uppåkra (55.664 N, 13.168 E).
PILOT_CENTRE = (384760, 6170206)
PILOT_HALF_SIZE = 5000
PILOT_BBOX = (
    PILOT_CENTRE[0] - PILOT_HALF_SIZE,
    PILOT_CENTRE[1] - PILOT_HALF_SIZE,
    PILOT_CENTRE[0] + PILOT_HALF_SIZE,
    PILOT_CENTRE[1] + PILOT_HALF_SIZE,
)  # (minx, miny, maxx, maxy)

# Extra margin used when clipping inputs for cost surfaces, so least-cost
# paths near the pilot edge are not forced along the boundary.
ROUTE_MARGIN = 2000

# Central places (EPSG:3006, approximate). Lund is ~0.5 km inside the pilot's
# northern edge; the others lie outside and are used when the area expands.
CENTRAL_PLACES = {
    "Uppakra": (384760, 6170206),
    "Lund": (386482, 6174693),  # medieval core, Lund cathedral area
    "Borgeby": (377081, 6180238),
    "Loddekopinge": (375571, 6181895),
    "Trelleborgen": (382754, 6138136),  # ring fortress in Trelleborg town
}

RIVERS = ["Höje å", "Sege å", "Kävlingeån"]

# Period of interest
PERIOD = (0, 1000)

# Keywords (lower case) used to classify Fornsök/K-samsök dating text.
# "core" = clearly within 0-1000 AD; "broad" = Iron Age without sub-period,
# which may include pre-Roman Iron Age (500 BC-0) and needs a manual look.
DATING_KEYWORDS = {
    "core": [
        "romersk järnålder", "äldre romersk", "yngre romersk",
        "folkvandringstid", "vendeltid", "vikingatid",
        "yngre järnålder", "roman iron age", "migration period",
        "vendel period", "viking age", "late iron age",
    ],
    "broad": ["järnålder", "iron age", "äldre järnålder", "early iron age"],
    "exclude": ["förromersk järnålder", "pre-roman iron age", "förromersk", "pre-roman", "bronsålder", "stenålder", "neolitikum",
                "medeltid", "efterreformatorisk", "historisk tid"],
}


def ensure_dirs():
    for d in (RAW, PROCESSED, CANDIDATES):
        d.mkdir(parents=True, exist_ok=True)
