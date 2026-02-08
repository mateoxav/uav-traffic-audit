from __future__ import annotations

from collections import Counter
from typing import List

from uav_traffic_ai.schemas import Detection, Metrics


def _bbox_area(d: Detection) -> float:
    w = max(0.0, d.bbox.x2 - d.bbox.x1)
    h = max(0.0, d.bbox.y2 - d.bbox.y1)
    return w * h


def compute_metrics(detections: List[Detection], image_w: int, image_h: int) -> Metrics:
    class_counts = Counter([d.cls_name for d in detections])
    typology_counts = Counter([d.typology for d in detections])

    img_area = float(max(1, image_w * image_h))
    occ = sum(_bbox_area(d) for d in detections) / img_area

    megapixels = img_area / 1_000_000.0
    density = (len(detections) / megapixels) if megapixels > 0 else 0.0

    return Metrics(
        counts_by_typology=dict(typology_counts),
        counts_by_class=dict(class_counts),
        density_per_megapixel=float(density),
        occupancy_ratio=float(occ),
    )
