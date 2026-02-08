from __future__ import annotations

from pathlib import Path
from typing import Tuple

import cv2
import numpy as np


def read_image_bgr(image_path: Path) -> np.ndarray:
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"No se pudo leer la imagen: {image_path}")
    return img


def image_size(img_bgr: np.ndarray) -> Tuple[int, int]:
    h, w = img_bgr.shape[:2]
    return w, h


def encode_png_bytes(img_bgr: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", img_bgr)
    if not ok:
        raise ValueError("No se pudo codificar PNG")
    return bytes(buf)
