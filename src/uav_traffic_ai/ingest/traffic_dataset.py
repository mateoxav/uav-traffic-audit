from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd


@dataclass(frozen=True)
class TrafficScene:
    scene_id: str
    scene_name: str
    lat: float
    lon: float
    folder: Path


def load_scenes(scenes_csv: Path, dataset_dir: Path) -> List[TrafficScene]:
    df = pd.read_csv(scenes_csv)
    scenes: List[TrafficScene] = []
    for _, row in df.iterrows():
        scene_id = str(row["Sequence"])
        folder = (dataset_dir / "dataset" / scene_id).resolve()
        scenes.append(
            TrafficScene(
                scene_id=scene_id,
                scene_name=str(row["Scene name"]),
                lat=float(row["lat"]),
                lon=float(row["long"]),
                folder=folder,
            )
        )
    return scenes


def list_scene_frames(scene_folder: Path) -> List[Path]:
    exts = {".png", ".jpg", ".jpeg"}
    frames = sorted([p for p in scene_folder.rglob("*") if p.is_file() and p.suffix.lower() in exts])
    if not frames:
        raise FileNotFoundError(f"No encuentro frames en {scene_folder}")
    return frames


def sample_frames(frames: List[Path], stride: int = 8, max_frames: int = 64) -> List[Path]:
    stride = max(1, int(stride))
    sampled = frames[::stride]
    return sampled[: max_frames]
