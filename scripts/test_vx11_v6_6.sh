#!/usr/bin/env bash
# Ajuste VX11 v6.6 – pruebas rápidas (2025-12-05)
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo ">> Auditoría de orden (drift)"
python3 scripts/auditor_orden_vx11.py

echo ">> Smoke test Operator ↔ Switch/Hermes"
pytest tests/test_operator_switch_hermes_flow.py

echo ">> Suite completa (puede tardar)"
pytest
