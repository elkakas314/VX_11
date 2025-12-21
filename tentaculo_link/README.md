# Tentaculo Link v6.7

Gateway/bridge HTTP principal de VX11.

## Docker (compose)

- **Puerto:** 8000
- **Health:** `GET /health`
- **Volúmenes:** `./data/runtime` → `/app/data/runtime`, `./build/artifacts/logs` → `/app/logs`

## Rol

- Puente de entrada/salida entre módulos (Madre/Switch/etc.) y herramientas externas.
- Mantiene contratos simples y “plug-and-play” para el stack local.

