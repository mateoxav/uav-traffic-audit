from __future__ import annotations

from typing import Dict

# COCO typical names: car, motorcycle, bus, truck, bicycle, ...
TYPOLOGY_MAP: Dict[str, str] = {
    "car": "tourism",
    "motorcycle": "moto",
    "bicycle": "moto",
    "bus": "heavy",
    "truck": "heavy",
}


def map_typology(cls_name: str) -> str:
    return TYPOLOGY_MAP.get(cls_name, "other")
