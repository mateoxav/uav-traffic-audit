# UAV Traffic AI — NeuralHack Demo MVP (YOLO + Métricas + Evidencia en BSV Testnet)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![YOLOv8](https://img.shields.io/badge/AI-YOLOv8-green)
![BSV](https://img.shields.io/badge/Blockchain-BSV_Testnet-orange)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)

> **Team Singularity**
> *"La IA que todo lo ve, la Blockchain que nada olvida."*

Sistema **end-to-end** para análisis de tráfico rodado a partir de imágenes UAV:
**subes imagen/frames → detecta vehículos → calcula métricas → genera evidencia (JSON + hash) → ancla el hash en BSV testnet (OP_RETURN) → verifica con WhatsOnChain**.

Este repo está diseñado para ser **demo-first**: no necesitas entrenar modelos para probarlo (usa **YOLOv8 preentrenado**).

---

## ✅ Qué hace (alcance actual)

### 1) Visión artificial (YOLOv8)
- Detección automática de objetos en imágenes aéreas (UAV).
- Modos de entrada:
  - **Subir imagen** (png/jpg)
  - **Dataset Traffic (escena)** (selección de escena + stride + frame)

> Nota: usando pesos COCO (`yolov8s.pt` por defecto) detecta clases como `car`, `truck`, `bus`, `motorcycle`, etc.  
> No hay fine-tuning incluido (por decisión de tiempo, potencia para entrenamiento y sobre todo robustez para demo).

### 2) Métricas de movilidad (MVP)
A partir de las detecciones:
- Conteo por clase y tipología (mapping simple)
- Densidad aproximada (por megapíxel)
- Ocupación aproximada (ratio área bboxes / área imagen)

### 3) Evidencia auditable (artefactos)
Por cada análisis se generan:
- `artifacts/outputs/<prefix>.json` (evidencia completa)
- `artifacts/outputs/<prefix>_detections.csv`
- `artifacts/outputs/<prefix>.sha256`
- `artifacts/annotated/<prefix>.png` (imagen anotada)

### 4) Blockchain BSV (testnet) — anclaje + verificación
- Se calcula `sha256` determinista del JSON de evidencia.
- Se emite una transacción en **BSV testnet** con un **OP_RETURN** que incluye:
  - prefijo/version
  - scene_id
  - sha256
  - timestamp
  - modelo (weights)
- Se verifica automáticamente contra **WhatsOnChain** leyendo el OP_RETURN por `txid`.
- La UI muestra:
  - `TXID: ...`
  - `Verificado: True/False`

---

## 🎥 Demo (flujo recomendado)
1. Abrir la app Streamlit
2. Subir una imagen de tráfico (o elegir una escena del dataset)
3. Click **Analizar**
4. Marcar **Anclar en BSV testnet** (requiere WIF testnet + fondos)
5. Ver `TXID` y `Verificado: True`
6. Mostrar `artifacts/outputs/*.json` con `sha256`, `txid`, `verified`

---

## 🧱 Arquitectura (resumen)

- `src/uav_traffic_ai/pipeline.py`: orquestación (detect → métricas → evidencia → hash → persist → anchor/verify)
- `src/uav_traffic_ai/blockchain/bsv_anchor.py`: crea y emite TX con OP_RETURN (bsvlib)
- `src/uav_traffic_ai/blockchain/verify.py`: lee OP_RETURN por txid (WhatsOnChain) y valida el hash
- `app.py`: UI Streamlit (subir imagen / dataset / anclar / mostrar outputs)

Estructura (simplificada):

```text
uav_traffic_ai/
├── app.py
├── main.py
├── requirements.txt
├── .env.example
├── data/
│   └── raw/traffic/...
├── artifacts/
│   ├── outputs/
│   └── annotated/
└── src/uav_traffic_ai/
    ├── pipeline.py
    ├── vision/
    ├── metrics/
    ├── reporting/
    └── blockchain/
```

---

## 🚀 Instalación y ejecución (Windows / Linux / Mac)

> Recomendado: **Python 3.10+** (probado con 3.11)

### 1) Clonar
```bash
git clone https://github.com/mateoxav/uav-traffic-audit.git
cd uav_traffic_ai
```

### 2) Crear entorno e instalar dependencias

#### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
pip install -e .
```

#### Linux / Mac
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
pip install -e .
```

### 3) Ejecutar la app
```bash
streamlit run app.py
```

---

## 📦 Dataset (Traffic Images Captured from UAVs)

Para el modo **Dataset Traffic (escena)**, se espera una estructura como:

```text
data/raw/traffic/
├── scenes.csv
└── dataset/
    ├── sec1/...
    ├── sec2/...
    └── ...
```

### Descarga con Kaggle API (recomendada)
1. Descarga tu `kaggle.json` (Kaggle → Account → Create New API Token)
2. Colócalo en:
   - Windows: `%USERPROFILE%\.kaggle\kaggle.json`
   - Linux/Mac: `~/.kaggle/kaggle.json`
3. Descarga:
```bash
kaggle datasets download -d javiersanchezsoriano/traffic-images-captured-from-uavs -p data/raw/traffic --unzip
```

> Nota: el dataset completo normalmente ya incluye `scenes.csv`.  
> Si **copiaste manualmente solo una carpeta** (por ejemplo una secuencia en especifico `sec2/`) es posible que NO tengas `scenes.csv`. Abajo tienes cómo generarlo.

---

## 🧾 ¿Qué es `scenes.csv` y por qué a veces hay que generarlo?

`scenes.csv` es un fichero de **metadatos** que mapea:
- `Sequence` (id de escena, p.ej. `sec2`)
- `Scene name`
- `lat` / `long`

La app lo usa para poblar el selector “Dataset Traffic (escena)” y para guardar la evidencia con localización.

Ejemplo mínimo para la escena `sec2`:

```csv
Sequence,Scene name,lat,long
sec2,Roundabout (far),40.591583,-4.332734
```
---

## 🔐 Blockchain (BSV testnet): configuración y prueba end-to-end

### 1) Crear `.env`
Copia el ejemplo:
```bash
# Linux/Mac
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

Completa al menos:
- `BSV_CHAIN=test`
- `BSV_WIF_TESTNET=...`
- `BSV_DUST_SATS=546`
- `WOC_BASE=https://api.whatsonchain.com`

### 2) Generar WIF **testnet** (IMPORTANTE)
La WIF de testnet suele empezar por `c` o `9` (WIF nativa de testnet).  
Usa el script incluido en `scripts/gen_testnet_wallet.py`.

### 3) Conseguir fondos en testnet (faucet)
Envía testnet coins a la dirección generada (por ejemplo con WitnessOnChain Faucet).

### 4) Probar desde Streamlit
1. Ejecuta:
   ```bash
   streamlit run app.py
   ```
2. Sube una imagen (o selecciona escena si tienes dataset)
3. Marca **Anclar en BSV testnet**
4. Click **Analizar**
5. Debe aparecer:
   - `TXID: <...>`
   - `Verificado: True`
6. Se guardará el JSON ya con `txid` y `verified`.

### (Opcional) Comprobar OP_RETURN con curl
Con el `TXID`, puedes ver el OP_RETURN en testnet:
```bash
curl "https://api.whatsonchain.com/v1/bsv/test/tx/<TXID>/opreturn"
```

---

## 🧪 Smoke test (terminal)

### Ver UTXOs (testnet)
```bash
python -c "import os; from bsvlib import Wallet; from bsvlib.constants import Chain; w=Wallet([os.environ['BSV_WIF_TESTNET']], chain=Chain.TEST); print('BAL=', w.get_balance(refresh=True)); print('UTXOS=', len(w.get_unspents(refresh=True)))"
```

---

## ⚠️ Limitaciones actuales (honestas)

- **Modelo**: YOLO preentrenado COCO (sin fine-tuning).
- **Tipologías**: mapping simple (heurístico) desde clases COCO.
- **Sin tracking**: análisis de **frames individuales** (no seguimiento multi-frame).
- **Métricas**: densidad/ocupación aproximadas (bboxes), no geometría real-world.
- **Blockchain**: se ancla **solo el hash**, no el JSON completo.
- **Dependencias externas**: faucet + WhatsOnChain pueden introducir latencia.

---

## 🛣️ Roadmap (mejoras posibles / fase 2)

- Fine-tuning con datasets UAV (Traffic + Roundabout) para mejorar precisión y clases.
- Conversión Roundabout (VOC → YOLO) + entrenamiento multi-clase (`car/cycle/bus/truck`).
- Tracking (SORT/ByteTrack) para:
  - conteo por carril/flujo
  - velocidad aproximada
  - comparación temporal real
- Métricas avanzadas:
  - ocupación por ROI (zonas)
  - incidentes/riesgo (congestión, invasión de ROI, etc.)
- Evidencia más fuerte:
  - firma del JSON
  - verificación completa (hash canónico ↔ OP_RETURN)
- Frontend:
  - timeline de frames
  - comparativas entre escenas

---

## 🧯 Troubleshooting

### “No pude cargar dataset”
- Verifica que exista:
  - `data/raw/traffic/scenes.csv`
  - `data/raw/traffic/dataset/<secX>/...`
- Si solo copiaste una escena manualmente, genera un `scenes.csv`.

### “UTXOS: 0”
- Asegúrate de usar una **WIF testnet** y que tenga fondos.
- Reintenta: la red puede tardar en reflejar UTXOs/OP_RETURN.

---

## 📄 Licencia
MIT

---

## Créditos
- Ultralytics YOLOv8
- Datasets UAV (Javier Sanchez-Soriano)
- BSV testnet + WhatsOnChain API
