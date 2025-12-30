# VX11 Bootstrap

Este archivo documenta los invariantes, health detection, defaults DeepSeek R1, y reglas de auto-review para VX11.

## Invariantes
- Single entrypoint: solo tentaculo_link expone puertos al host
- Solo madre puede estar up por defecto (solo_madre policy)
- Todos los servicios deben pasar healthcheck y PRAGMA DB

## Health Detection
- /health endpoint en cada servicio
- docker-compose.full-test.yml debe levantar todos los servicios y pasar health

## DeepSeek R1 Defaults
- Modelo por defecto: deepseek-r1
- Temperatura: 0.7

## Auto-review rules
- No breaking changes en main
- Evidencia de auditoría en docs/audit/
- No duplicar scripts ni archivos de configuración
