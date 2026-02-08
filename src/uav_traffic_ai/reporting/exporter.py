from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd

from uav_traffic_ai.reporting.hashing import stable_json_dumps


def ensure_dirs(base: Path) -> Dict[str, Path]:
    outs = {
        "outputs": base / "outputs",
        "annotated": base / "annotated",
        "logs": base / "logs",
    }
    for p in outs.values():
        p.mkdir(parents=True, exist_ok=True)
    return outs


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    text = stable_json_dumps(payload)
    path.write_text(text, encoding="utf-8")


def save_detections_csv(path: Path, detections_rows: list[dict]) -> None:
    df = pd.DataFrame(detections_rows)
    df.to_csv(path, index=False)
