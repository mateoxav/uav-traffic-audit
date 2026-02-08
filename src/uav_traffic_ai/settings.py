from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
import os


ChainName = Literal["main", "test"]


@dataclass(frozen=True)
class AppSettings:
    app_name: str
    artifacts_dir: Path

    traffic_dataset_dir: Path
    traffic_scenes_csv: Path

    yolo_weights: str
    yolo_conf: float
    yolo_iou: float

    bsv_chain: ChainName
    bsv_wif_testnet: str
    bsv_dust_sats: int

    woc_base: str


def load_settings() -> AppSettings:
    load_dotenv()

    artifacts_dir = Path(os.getenv("ARTIFACTS_DIR", "artifacts")).resolve()

    traffic_dataset_dir = Path(os.getenv("TRAFFIC_DATASET_DIR", "data/raw/traffic")).resolve()
    traffic_scenes_csv = Path(os.getenv("TRAFFIC_SCENES_CSV", str(traffic_dataset_dir / "scenes.csv"))).resolve()

    yolo_weights = os.getenv("YOLO_WEIGHTS", "yolov8s.pt")
    yolo_conf = float(os.getenv("YOLO_CONF", "0.25"))
    yolo_iou = float(os.getenv("YOLO_IOU", "0.7"))

    bsv_chain = os.getenv("BSV_CHAIN", "test").strip().lower()
    if bsv_chain not in {"main", "test"}:
        bsv_chain = "test"

    bsv_wif_testnet = os.getenv("BSV_WIF_TESTNET", "").strip()
    bsv_dust_sats = int(os.getenv("BSV_DUST_SATS", "546"))

    woc_base = os.getenv("WOC_BASE", "https://api.whatsonchain.com").rstrip("/")

    return AppSettings(
        app_name=os.getenv("APP_NAME", "UAV Traffic AI"),
        artifacts_dir=artifacts_dir,
        traffic_dataset_dir=traffic_dataset_dir,
        traffic_scenes_csv=traffic_scenes_csv,
        yolo_weights=yolo_weights,
        yolo_conf=yolo_conf,
        yolo_iou=yolo_iou,
        bsv_chain=bsv_chain,  # type: ignore[assignment]
        bsv_wif_testnet=bsv_wif_testnet,
        bsv_dust_sats=bsv_dust_sats,
        woc_base=woc_base,
    )
