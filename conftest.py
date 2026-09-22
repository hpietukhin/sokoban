# conftest.py

from dataclasses import dataclass
from pathlib import Path

import pytest


BASE_DIR = Path(__file__).parent
MAPS_DIR = BASE_DIR / "maps"


@dataclass(frozen=True)
class MapCase:
    path: Path
    reference_plan: str | None

    @property
    def search_limit(self) -> int:
        return len(self.reference_plan) if self.reference_plan is not None else 30


REFERENCE_PLANS = {
    "map1.txt": "dURRRDDLLurUl",
    "map2.txt": "URddRRUllULdULddUULdddLDrr",
    "map3.txt": "DLLLULUURddLDrrrrURRDDLuuuDDLLLLUURRUURrLLDlDLLUUrrrrLLLdddLDrrrrrDRuuu",
    "map4.txt": "RRrrr",
    "map5.txt": "RrrDll",
    "map6.txt": "rdLDLu",
    "map7.txt": "DRRRRuRUllUlULddURRDl",
    "map8.txt": "DRRuRUl",
    "map9.txt": None,
    "map10.txt": "URRRd",
}

map_paths = sorted(MAPS_DIR.glob("map*.txt"))
if {path.name for path in map_paths} != set(REFERENCE_PLANS):
    raise RuntimeError("Every map must have an entry in REFERENCE_PLANS")

MAP_CASES = [
    MapCase(path, REFERENCE_PLANS[path.name])
    for path in map_paths
]


@pytest.fixture(params=MAP_CASES, ids=lambda case: case.path.stem)
def map_case(request: pytest.FixtureRequest) -> MapCase:
    return request.param
