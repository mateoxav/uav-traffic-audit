from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from ultralytics import YOLO

from uav_traffic_ai.schemas import BBox, Detection
from uav_traffic_ai.vision.postprocess import map_typology


@dataclass(frozen=True)
class DetectionResult:
    detections: List[Detection]
    annotated_bgr: np.ndarray  # imagen con boxes dibujados


class YoloDetector:
    def __init__(self, weights: str, conf: float, iou: float) -> None:
        self.weights = weights
        self.conf = conf
        self.iou = iou
        self.model = YOLO(weights)

    def detect_image(self, img_bgr: np.ndarray) -> DetectionResult:
        # Ultralytics: results = model.predict(...)
        # result.plot() devuelve imagen anotada. :contentReference[oaicite:1]{index=1}
        results = self.model.predict(img_bgr, conf=self.conf, iou=self.iou, verbose=False)
        r0 = results[0]
        names = r0.names  # id -> name

        dets: List[Detection] = []
        if r0.boxes is not None and len(r0.boxes) > 0:
            xyxy = r0.boxes.xyxy.cpu().numpy()
            confs = r0.boxes.conf.cpu().numpy()
            clss = r0.boxes.cls.cpu().numpy().astype(int)

            for i in range(len(xyxy)):
                cls_name = str(names.get(int(clss[i]), "unknown"))
                dets.append(
                    Detection(
                        cls_name=cls_name,
                        confidence=float(confs[i]),
                        bbox=BBox(
                            x1=float(xyxy[i][0]),
                            y1=float(xyxy[i][1]),
                            x2=float(xyxy[i][2]),
                            y2=float(xyxy[i][3]),
                        ),
                        typology=map_typology(cls_name),
                    )
                )

        annotated = r0.plot()
        return DetectionResult(detections=dets, annotated_bgr=annotated)
