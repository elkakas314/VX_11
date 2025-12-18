# Postmortem summary

Timestamp: jue 18 dic 2025 02:26:55 UTC

## Puertos vivos (filtrados)

PIDs from ss and commands:
NO_PORT_PIDS
\n## Procesos con /home/elkakas314/vx11 en cmdline
    727       1 Ssl  /home/elkakas314/vx11/.venv/bin/python3 /home/elkakas314/vx11/.venv/bin/uvicorn hormiguero.main:app --host 0.0.0.0 --port 52114
    729       1 Ssl  /home/elkakas314/vx11/.venv/bin/python3 /home/elkakas314/vx11/.venv/bin/uvicorn madre.main:app --host 0.0.0.0 --port 52112
    730       1 Ssl  /home/elkakas314/vx11/.venv/bin/python3 /home/elkakas314/vx11/.venv/bin/uvicorn manifestator.main:app --host 0.0.0.0 --port 52115
    731       1 Ssl  /home/elkakas314/vx11/.venv/bin/python3 /home/elkakas314/vx11/.venv/bin/uvicorn mcp.main:app --host 0.0.0.0 --port 52116
    733       1 Ssl  /home/elkakas314/vx11/.venv/bin/python3 /home/elkakas314/vx11/.venv/bin/uvicorn shubniggurath.main:app --host 0.0.0.0 --port 52117
 803404  802648 Sl   /home/elkakas314/vx11/.venv/bin/python /home/elkakas314/.vscode/extensions/ms-python.black-formatter-2025.2.0/bundled/tool/lsp_server.py --stdio
 942848  874601 S+   grep --color=auto /home/elkakas314/vx11
\n## Zombies detectados (raw)
No zombies detected.
