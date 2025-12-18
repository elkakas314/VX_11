# Power Saver Report

Resumen de acciones realizadas por el agente VX11 (modo cirujano):

- Precheck forense realizado y capturado en este OUT.
- Zombis detectados: ver `04_zombies.txt`.
- Acciones sobre zombis: ver `04_zombie_actions.txt`.
- Apagado HARD_OFF: docker compose down (si disponible), terminación de dev servers Node y procesos uvicorn/gunicorn vinculados al repo (si se encontraron).

Archivos generados en este OUT:

- 00_pwd.txt, 00_date_utc.txt, 00_git_status_sb.txt
- 01_uptime.txt, 01_free_h.txt, 01_ps_top_cpu.txt, 01_ps_top_mem.txt
- 02_db_file_ls.txt, 02_db_integrity.txt, 02_runtime_services_from_db.txt, 02_system_state.txt
- 03_ss_listen_all.txt, 03_ss_listen_filtered.txt, 03_docker_ps.txt, 03_docker_compose_ps.txt
- 03_node_processes.txt, 03_python_vx11_processes.txt
- 04_zombies.txt, 04_ps_full.txt, 04_zombie_ppids.txt, 04_zombie_parents.txt, 04_zombie_actions.txt
- 05_compose_down.txt or 05_compose_stop.txt, 05_node_candidates.txt, 05_node_actions.txt, 05_uvicorn_candidates.txt, 05_uvicorn_actions.txt
- 06_ss_listen_after.txt, 06_docker_ps_after.txt, 06_ps_top_after.txt, 06_free_after.txt

Comandos ejecutados (ejemplos resumidos):
- ss -ltnp
- docker compose down
- pgrep/kill TERM para procesos node/uvicorn detectados bajo /home/elkakas314/vx11

Recomendaciones:
- Revisar `04_zombie_parents.txt` y `04_zombie_actions.txt` para confirmar que reinicios/terminaciones fueron apropiadas.
- Si se desea un modo menos agresivo, ejecutar el flujo IDLE_MIN (mantener gateway/entrypoint).

