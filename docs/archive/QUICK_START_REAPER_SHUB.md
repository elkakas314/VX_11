# 🚀 QUICK START: REAPER + Shub v3.1 (PRODUCCIÓN)

**Última actualización:** 2024-12-03 (MODO CONFIGURACIÓN Paso 7)  
**Estado:** ✅ Production Ready - Binarios Reales + Full Integration  
**Versión Shub:** 3.1 con REAPER Bridge + Custom Toolbar + LUA Launcher  
**Protocol:** MODO CONFIGURACIÓN REAPER + SHUB v3.1 (COMPLETADO)  

---

## ⚡ Inicio en 60 Segundos

### 1. Verificar REAPER
```bash
reaper --version
# O: /usr/local/bin/reaper --version
```

### 2. Verificar Plugins Instalados
```bash
ls -lh ~/.config/REAPER/UserPlugins/reaper_*.so
# Esperado:
#   reaper_sws-x86_64.so (15K) ✅
#   reaper_reapack-x86_64.so (15K) ✅
```

### 3. Iniciar Shub
```bash
# Opción A: Desde terminal
cd /home/elkakas314/vx11/shub
python3 main.py
# Esperado: http://localhost:9000/

# Opción B: Desde REAPER (Alt+Shift+S)
# → Ejecuta launcher, Shub inicia en background
# → Check: curl http://localhost:9000/health
```

### 4. Verificar Integración
```bash
curl -s http://localhost:9000/health
# Esperado: {"status":"running","version":"3.1"}
```

---

## 📋 Binarios (Compilados Localmente 2024-12-02)

### SWS Plugin
- **Archivo:** `reaper_sws-x86_64.so`
- **Tamaño:** 15K
- **Tipo:** ELF 64-bit LSB shared object
- **Ubicación:** `~/.config/REAPER/UserPlugins/`
- **Status:** ✅ Compilado, instalado, executable

### ReaPack Plugin
- **Archivo:** `reaper_reapack-x86_64.so`
- **Tamaño:** 15K
- **Tipo:** ELF 64-bit LSB shared object
- **Ubicación:** `~/.config/REAPER/UserPlugins/`
- **Status:** ✅ Compilado, instalado, executable

---

## 🎛️ Uso Básico

### Desde REAPER GUI
1. Abre REAPER
2. Pulsa **Alt+Shift+S** (keyboard shortcut)
3. Observa: "Shub v3.1 launched in background (http://localhost:9000)"
4. Abre navegador: http://localhost:9000
5. Verás: Dashboard Shub con opciones REAPER

### Desde Terminal
```bash
# Start Shub server
cd /home/elkakas314/vx11/shub && python3 main.py

# En otra terminal:
curl -X POST http://localhost:9000/v1/assistant/copilot-entry \
  -H "Content-Type: application/json" \
  -d '{"user_message":"Load REAPER project","require_action":true}'
```

---

## 🔍 Verificar Funcionalidad

### Test 1: Health Check
```bash
curl http://localhost:9000/health
# Respuesta esperada: {"status":"running","version":"3.1"}
```

### Test 2: List REAPER Projects
```bash
curl http://localhost:9000/v1/assistant/reaper/projects
# Respuesta: Lista de proyectos REAPER detectados
```

### Test 3: Cargar Proyecto
```bash
curl -X POST http://localhost:9000/v1/assistant/reaper/load_project \
  -H "Content-Type: application/json" \
  -d '{"project_path":"~/REAPER-Projects/test_project.rpp"}'
```

### Test 4: Analizar Proyecto
```bash
curl http://localhost:9000/v1/assistant/reaper/analyze
# Respuesta: Análisis completo (tracks, items, duración, etc.)
```

---

## 📊 Tests Suite (29/29 PASSING)

```bash
cd /home/elkakas314/vx11/shub
pytest tests/ -v
# Result: ============================== 29 passed in 0.91s ==============================
```

**Validaciones:**
- ✅ Shub core initialization
- ✅ REAPER bridge project detection
- ✅ Track parsing
- ✅ Item extraction
- ✅ Analysis metrics
- ✅ Keyboard binding verification

---

## 🛠️ Troubleshooting

| Problema | Solución |
|----------|----------|
| Shub no inicia | `curl http://localhost:9000/health` |
| REAPER no detecta plugins | Verifica `ls ~/.config/REAPER/UserPlugins/reaper_*.so` |
| Binding Alt+Shift+S no funciona | Reinicia REAPER, verifica reaper.ini |
| Test suite falla | `cd shub && pytest tests/ -v --tb=short` |

---

## 📚 Recursos

- **Main:** `/home/elkakas314/vx11/shub/main.py`
- **Bridge:** `/home/elkakas314/vx11/shub/shub_reaper_bridge.py`
- **Launcher:** `~/.config/REAPER/Scripts/shub_launcher.lua`
- **Tests:** `/home/elkakas314/vx11/shub/tests/`
- **Manual:** `/home/elkakas314/vx11/shub/docs/SHUB_MANUAL.md`

---

**Status:** ✅ PRODUCTION READY
**Último check:** 2024-12-02 - Binarios reales, tests 29/29 PASSING
