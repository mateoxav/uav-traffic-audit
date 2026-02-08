from __future__ import annotations

from pathlib import Path
import tempfile

import streamlit as st

from uav_traffic_ai.ingest.media import read_image_bgr
from uav_traffic_ai.ingest.traffic_dataset import load_scenes, list_scene_frames, sample_frames
from uav_traffic_ai.schemas import SceneMeta
from uav_traffic_ai.settings import load_settings
from uav_traffic_ai.pipeline import anchor_and_verify, persist_artifacts, run_analysis_on_image
from uav_traffic_ai.vision.detector import YoloDetector


def main() -> None:
    s = load_settings()
    st.set_page_config(page_title=s.app_name, layout="wide")
    st.title("UAV Traffic AI — Demo MVP")

    detector = YoloDetector(weights=s.yolo_weights, conf=s.yolo_conf, iou=s.yolo_iou)

    st.sidebar.header("Entrada")
    mode = st.sidebar.radio("Modo", ["Subir imagen", "Dataset Traffic (escena)"])

    img_path: Path | None = None
    scene_meta = SceneMeta()
    
    # Variable para guardar el nombre original del archivo subido (para el prefix)
    upload_orig_name: str | None = None

    if mode == "Subir imagen":
        up = st.sidebar.file_uploader("Imagen (png/jpg)", type=["png", "jpg", "jpeg"])
        if up is not None:
            upload_orig_name = up.name
            # Guardamos en temp para que OpenCV lo pueda leer por path
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{up.name}") as tmp:
                tmp.write(up.getbuffer())
                img_path = Path(tmp.name)
            scene_meta = SceneMeta(scene_id="upload", scene_name="User Upload")
    else:
        try:
            scenes = load_scenes(s.traffic_scenes_csv, s.traffic_dataset_dir)
            scene_labels = [f"{x.scene_id} — {x.scene_name}" for x in scenes]
            choice = st.sidebar.selectbox("Escena", scene_labels)
            stride = st.sidebar.slider("Stride (1 = todos, 8 = 1/8)", 1, 30, 8)
            max_frames = st.sidebar.slider("Máx frames", 1, 200, 64)

            scene = scenes[scene_labels.index(choice)]
            frames = list_scene_frames(scene.folder)
            sampled = sample_frames(frames, stride=stride, max_frames=max_frames)

            frame_idx = st.sidebar.slider("Frame index", 0, len(sampled) - 1, 0)
            img_path = sampled[frame_idx]

            scene_meta = SceneMeta(
                scene_id=scene.scene_id,
                scene_name=scene.scene_name,
                lat=scene.lat,
                lon=scene.lon,
            )
            st.sidebar.caption(f"Archivo: {img_path.name}")
        except Exception as e:
            st.sidebar.error(f"No pude cargar dataset: {e}")

    st.sidebar.header("Blockchain")
    do_anchor = st.sidebar.checkbox("Anclar en BSV testnet", value=False)

    run = st.button("Analizar", type="primary", disabled=(img_path is None))

    if run and img_path is not None:
        img_bgr = read_image_bgr(img_path)

        # 1. Ejecutar análisis (CV + Métricas + Hash inicial)
        evidence, annotated_png = run_analysis_on_image(
            img_bgr=img_bgr,
            scene=scene_meta,
            detector=detector,
            model_weights=s.yolo_weights,
        )

        # 2. (OPCIONAL) Anclar antes de persistir
        # Así el JSON guardado y mostrado ya incluye el TXID.
        if do_anchor:
            with st.spinner("Anclando en Blockchain (BSV Testnet)..."):
                try:
                    evidence = anchor_and_verify(
                        evidence=evidence,
                        chain_name=s.bsv_chain,
                        wif=s.bsv_wif_testnet,
                        dust_sats=s.bsv_dust_sats,
                        woc_base=s.woc_base,
                    )
                    st.toast(f"Anclado correctamente! TXID: {evidence.txid[:8]}...", icon="🔗")
                except Exception as e:
                    st.error(f"Error en Blockchain: {e}")
                    # No detenemos la ejecución, guardamos la evidencia aunque falle el anclaje

        # 3. Definir nombre limpio para los archivos (Prefix)
        if mode == "Subir imagen" and upload_orig_name:
            # Usamos el nombre original del archivo subido
            clean_stem = Path(upload_orig_name).stem
            prefix = f"upload_{clean_stem}"
        else:
            # Usamos ID escena + nombre frame original
            prefix = f"{scene_meta.scene_id}_{img_path.stem}"

        # 4. Persistir (Guardar JSON, CSV, PNG, SHA256)
        paths = persist_artifacts(
            artifacts_base=s.artifacts_dir,
            evidence=evidence,
            annotated_png=annotated_png,
            prefix=prefix,
        )

        # 5. Visualizar resultados finales
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Imagen anotada")
            st.image(annotated_png, use_container_width=True)
            st.success(f"Archivos guardados en: {paths['json'].parent}")

        with col2:
            st.subheader("Métricas")
            st.json(evidence.metrics.model_dump())

            st.subheader("Evidencia Digital (JSON)")
            # Ahora este JSON ya tiene el TXID si se activó el checkbox
            st.code(evidence.model_dump_json(indent=2), language="json")
            
            if do_anchor and evidence.verified:
                st.info(f"✅ **Verificado en Blockchain**\n\nTXID: `{evidence.txid}`")
            elif do_anchor and not evidence.verified:
                st.warning("⚠️ Transacción enviada pero no verificada aún (timeout en propagación).")

if __name__ == "__main__":
    main()