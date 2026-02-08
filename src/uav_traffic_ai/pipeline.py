from __future__ import annotations

import time  # Añadido para el sleep del retry
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from uav_traffic_ai.schemas import Evidence, SceneMeta
from uav_traffic_ai.ingest.media import encode_png_bytes, image_size
from uav_traffic_ai.metrics.traffic_metrics import compute_metrics
from uav_traffic_ai.reporting.exporter import ensure_dirs, save_detections_csv, save_json
from uav_traffic_ai.reporting.hashing import sha256_hex, stable_json_dumps
from uav_traffic_ai.vision.detector import YoloDetector
from uav_traffic_ai.blockchain.bsv_anchor import anchor_sha256_opreturn
from uav_traffic_ai.blockchain.verify import verify_sha256_in_tx_opreturn


def _evidence_payload_for_hash(e: Evidence) -> Dict[str, Any]:
    # mode="json" convierte datetime/UUID/etc a tipos JSON-compatibles
    d = e.model_dump(mode="json")
    d.pop("txid", None)
    d.pop("verified", None)
    return d


def run_analysis_on_image(
    *,
    img_bgr,
    scene: SceneMeta,
    detector: YoloDetector,
    model_weights: str,
) -> Tuple[Evidence, bytes]:
    det_res = detector.detect_image(img_bgr)
    w, h = image_size(img_bgr)
    metrics = compute_metrics(det_res.detections, w, h)

    created_at = datetime.now(timezone.utc)
    evidence = Evidence(
        created_at_utc=created_at,
        model_weights=model_weights,
        scene=scene,
        image_width=w,
        image_height=h,
        detections=det_res.detections,
        metrics=metrics,
        sha256="",  # se rellena tras calcular hash
        bsv_chain="test",
    )

    payload = _evidence_payload_for_hash(evidence)
    evidence.sha256 = sha256_hex(stable_json_dumps(payload))

    annotated_png = encode_png_bytes(det_res.annotated_bgr)
    return evidence, annotated_png


def persist_artifacts(
    *,
    artifacts_base: Path,
    evidence: Evidence,
    annotated_png: bytes,
    prefix: str,
) -> Dict[str, Path]:
    dirs = ensure_dirs(artifacts_base)

    json_path = dirs["outputs"] / f"{prefix}.json"
    csv_path = dirs["outputs"] / f"{prefix}_detections.csv"
    img_path = dirs["annotated"] / f"{prefix}.png"
    hash_path = dirs["outputs"] / f"{prefix}.sha256"

    # JSON + CSV
    save_json(json_path, evidence.model_dump(mode="json"))
    save_detections_csv(
        csv_path,
        [
            {
                "cls_name": d.cls_name,
                "typology": d.typology,
                "confidence": d.confidence,
                "x1": d.bbox.x1,
                "y1": d.bbox.y1,
                "x2": d.bbox.x2,
                "y2": d.bbox.y2,
            }
            for d in evidence.detections
        ],
    )

    # Image
    img_path.write_bytes(annotated_png)
    hash_path.write_text(evidence.sha256 + "\n", encoding="utf-8")

    return {"json": json_path, "csv": csv_path, "png": img_path, "sha256": hash_path}


def anchor_and_verify(
    *,
    evidence: Evidence,
    chain_name: str,
    wif: str,
    dust_sats: int,
    woc_base: str,
) -> Evidence:
    scene_id = evidence.scene.scene_id or "unknown_scene"
    r = anchor_sha256_opreturn(
        chain_name=chain_name,
        wif=wif,
        dust_sats=dust_sats,
        scene_id=scene_id,
        sha256_hex=evidence.sha256,
        model=evidence.model_weights,
        created_at_utc=evidence.created_at_utc,
    )
    evidence.txid = r.txid
    evidence.bsv_chain = chain_name

    # WhatsOnChain puede tardar un momento en reflejar el OP_RETURN en mempool.
    # Intentamos verificar hasta 6 veces con pausas de 1s.
    ok = False
    for _ in range(6):  # ~6s total
        v = verify_sha256_in_tx_opreturn(
            woc_base=woc_base,
            chain_name=chain_name,
            txid=evidence.txid,
            expected_sha256_hex=evidence.sha256,
        )
        if v.ok:
            ok = True
            break
        time.sleep(1.0)
    
    evidence.verified = ok
    return evidence