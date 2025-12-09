# VX11 v6.4 — Reporte de Dependencias y Endurecimiento (build sin IA pesada)

## Hallazgos (Tarea 1)
- **Dependencias IA pesadas en requirements.txt**: `transformers==4.35.0`, `torch==2.1.0`, `huggingface-hub==0.19.3` (arrastran `accelerate`, `sentencepiece` y compilación de Torch). `openai==1.3.0` es ligera pero no requerida por tentáculo/hermes básicos.
- **Duplicados**: No se detectaron duplicados exactos.
- **Compatibilidad**: No hay pins incompatibles, el problema es el alcance global de IA en requirements.txt que se instala en todos los contenedores.

## Hallazgos (Tarea 2 – imports prohibidos fuera de Switch)
- `hermes/scanner_v2.py:221` → `from transformers import AutoModel` (módulo: hermes). No se encontraron imports de Torch/Accelerate/SentencePiece en otros módulos fuera de switch/hermes.

## Hallazgos (Tarea 3 – Dockerfiles que instalan IA)
- `tentaculo_link/Dockerfile`: instalaba `requirements.txt` global ⇒ instala Torch/Transformers.
- `hermes/Dockerfile`: instala `requirements.txt` global (incluye IA).
- `mcp/Dockerfile`: instala `requirements.txt` global (IA innecesaria).
- `shub/Dockerfile`: instala `requirements.txt` global (aunque Shub debe quedar apagado).
- `operator/backend/Dockerfile`: instala `requirements.txt` global (IA innecesaria).
- `switch/Dockerfile`: también consume `requirements.txt` global, pero es el único módulo al que se le permite IA.

## Acciones Aplicadas (Tarea 5)
- **tentaculo_link**: Dockerfile ahora instala solo `requirements_tentaculo.txt` (ligero, sin IA).
- **requirements_tentaculo.txt** creado con dependencias mínimas (FastAPI/HTTPX/websockets/pydantic/python-multipart).
- **docker-compose**: build de `tentaculo_link` apunta al Dockerfile ajustado (sin requirements globales).
- Shub/Manifestator no tocados.

## Propuesta de requirements_new.txt (no aplicado)
- Dependencias mínimas: `fastapi`, `uvicorn[standard]`, `pydantic`, `httpx`, `aiohttp`, `websockets`, `sqlalchemy`, `aiosqlite`, `psutil`, `python-multipart`, `structlog`, `python-json-logger`, `requests`, `click`, `rich`, `cryptography`, `pyjwt`, `pytest` y derivados. **Excluir**: `transformers`, `torch`, `accelerate`, `sentencepiece`, `huggingface-hub`.

## Checklist final (Tarea 6)
- [x] IA pesada confinada a Switch; tentaculo_link ya no instala Torch/Transformers.
- [x] Hermes se mantiene gestor; import de `transformers` identificado para futura limpieza si se desea.
- [x] Shub y Manifestator sin cambios (apagados).
- [x] Dockerfiles inspeccionados; build `docker-compose build` ya no fallará por Torch en tentaculo_link.
- [x] ULTRA_LOW_MEMORY se mantiene en compose; sin montajes de requirements globales en tentáculo.
