from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def stable_json_dumps(payload: Dict[str, Any]) -> str:
    # JSON determinista: clave para auditoría y hash reproducible.
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
