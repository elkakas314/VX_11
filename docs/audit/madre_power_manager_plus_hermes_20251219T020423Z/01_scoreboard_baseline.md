# SCOREBOARD BASELINE

Global scores (weighted):
- Order/Structure %: 75.00
- Stability %: 100.00
- Functionality %: 68.33
- Automation %: 21.67
- Autonomy %: 63.33
- Global Overall %: 65.67

Resumen reducido:
- Orden/Estructura global: 75.00%
- Estabilidad global: 100.00%

Subsystems (avg of module overall):
- core_runtime: 70.00
- gateway_operator: 60.00
- ai_pipeline: 61.25

Per-module axes:
- tentaculo_link: order=75.00, stability=100.00, functionality=75.00, automation=25.00, autonomy=75.00
- madre: order=75.00, stability=100.00, functionality=75.00, automation=100.00, autonomy=100.00
- switch: order=75.00, stability=100.00, functionality=100.00, automation=50.00, autonomy=75.00
- hermes: order=75.00, stability=100.00, functionality=25.00, automation=0.00, autonomy=50.00
- hormiguero: order=75.00, stability=100.00, functionality=75.00, automation=0.00, autonomy=50.00
- manifestator: order=75.00, stability=100.00, functionality=75.00, automation=0.00, autonomy=50.00
- mcp: order=75.00, stability=100.00, functionality=75.00, automation=0.00, autonomy=75.00
- shubniggurath: order=75.00, stability=100.00, functionality=75.00, automation=0.00, autonomy=50.00
- spawner: order=75.00, stability=100.00, functionality=75.00, automation=0.00, autonomy=50.00
- operator-backend: order=75.00, stability=100.00, functionality=50.00, automation=0.00, autonomy=50.00
- operator-frontend: order=75.00, stability=100.00, functionality=50.00, automation=0.00, autonomy=50.00

Heuristics used (evidence files in OUT):
- compose services from `00_precheck/compose_services.txt` if available; else `01_module_status_rows.txt`; else VX11_CONTEXT list.
- /health detection from string scan in module directories (see `01_scan_health_hits.txt`).
- offline-friendly detection from string scan (see `01_scan_offline_hits.txt`).
- plan/apply detection from string scan (see `01_scan_plan_hits.txt`, `01_scan_apply_hits.txt`).
- forensic evidence detection from `docs/audit` string scan (see `01_scan_forensic_hits.txt`).
- rate limit/breaker detection from string scan (see `01_scan_rate_hits.txt`).
- db event tracking detection from string scan (see `01_scan_dbwrite_hits.txt`).
- runtime signal detection from string scan (see `01_scan_autonomy_hits.txt`).
- ttl/idle detection from string scan (see `01_scan_idle_hits.txt`).
- docker autostart detection from string scan (see `01_scan_docker_autostart_hits.txt`).
