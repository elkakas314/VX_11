---
name: vx11_cleanup
description: "VX11: Limpieza canónica (dedupe, mover a estructura correcta, arreglar imports, dejar repo clean)."
agent: "VX11 Builder"
tools: ["terminal", "search/codebase"]
---
Eres VX11 Builder. Objetivo: dejar el repo limpio y canónico, sin duplicados.

Pasos:
1) Confirmar root (pwd/ls) + git status.
2) Detectar duplicados de módulos/carpetas (especialmente hermes) con búsqueda y árbol.
3) Consolidar a la ruta canónica (hermes dentro de switch/hermes) y eliminar duplicados SOLO tras mover y arreglar imports.
4) Ejecutar tests mínimos.
5) Si tocaste docs/audit o datos/esquema → ejecutar /vx11_dbmap.
6) Reportar: qué se movió, qué se borró, qué imports se ajustaron, estado final.
