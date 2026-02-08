from __future__ import annotations

import argparse
from pathlib import Path

from uav_traffic_ai.ingest.media import read_image_bgr
from uav_traffic_ai.schemas import SceneMeta
from uav_traffic_ai.settings import load_settings
from uav_traffic_ai.pipeline import (
    anchor_and_verify,
    persist_artifacts,
    run_analysis_on_image,
)
from uav_traffic_ai.vision.detector import YoloDetector


def main() -> None:
    s = load_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, required=True, help="Ruta a imagen (png/jpg).")
    parser.add_argument("--scene-id", type=str, default=None)
    parser.add_argument("--scene-name", type=str, default=None)
    parser.add_argument("--lat", type=float, default=None)
    parser.add_argument("--lon", type=float, default=None)
    parser.add_argument("--anchor", action="store_true", help="Anclar hash en BSV testnet.")
    args = parser.parse_args()

    img_path = Path(args.image).resolve()
    img_bgr = read_image_bgr(img_path)

    scene = SceneMeta(
        scene_id=args.scene_id,
        scene_name=args.scene_name,
        lat=args.lat,
        lon=args.lon,
    )

    detector = YoloDetector(
        weights=s.yolo_weights,
        conf=s.yolo_conf,
        iou=s.yolo_iou,
    )

    evidence, annotated_png = run_analysis_on_image(
        img_bgr=img_bgr,
        scene=scene,
        detector=detector,
        model_weights=s.yolo_weights,
    )

    prefix = img_path.stem
    paths = persist_artifacts(
        artifacts_base=s.artifacts_dir,
        evidence=evidence,
        annotated_png=annotated_png,
        prefix=prefix,
    )

    if args.anchor:
        evidence = anchor_and_verify(
            evidence=evidence,
            chain_name=s.bsv_chain,
            wif=s.bsv_wif_testnet,
            dust_sats=s.bsv_dust_sats,
            woc_base=s.woc_base,
        )
        # re-guardar JSON con txid/verified
        (paths["json"]).write_text(evidence.model_dump_json(indent=2), encoding="utf-8")

    print("✅ OK")
    print(f"JSON: {paths['json']}")
    print(f"PNG:  {paths['png']}")
    print(f"HASH: {paths['sha256']}")
    if evidence.txid:
        print(f"TXID: {evidence.txid} (verified={evidence.verified})")


if __name__ == "__main__":
    main()
