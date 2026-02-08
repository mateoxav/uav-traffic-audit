from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    cls_name: str
    confidence: float
    bbox: BBox
    typology: str  # tourism/moto/heavy/other


class SceneMeta(BaseModel):
    scene_id: Optional[str] = None
    scene_name: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class Metrics(BaseModel):
    counts_by_typology: Dict[str, int] = Field(default_factory=dict)
    counts_by_class: Dict[str, int] = Field(default_factory=dict)
    density_per_megapixel: float = 0.0
    occupancy_ratio: float = 0.0  # sum bbox areas / image area


class Evidence(BaseModel):
    schema_version: str = "uav_traffic_ai_evidence_v1"

    created_at_utc: datetime
    model_weights: str

    scene: SceneMeta
    image_width: int
    image_height: int

    detections: List[Detection]
    metrics: Metrics

    sha256: str  # sha256 del JSON determinista

    # Blockchain
    bsv_chain: str = "test"
    txid: Optional[str] = None
    verified: Optional[bool] = None
