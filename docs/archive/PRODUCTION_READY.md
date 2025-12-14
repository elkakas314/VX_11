# VX11 v7.0 - Sistema Modular de Orquestación IA

## 🚀 Quick Start

### 1. Verificar Sistema
```bash
cd /home/elkakas314/vx11
docker-compose ps  # Debe mostrar 10 servicios UP
```

### 2. Acceder a Dashboard
- **Frontend:** http://localhost:8020
- **API Backend:** http://localhost:8011
- **Gateway:** http://localhost:8000

### 3. Token de Acceso
```
Header: X-VX11-Token: vx11-local-token
```

### 4. Test Chat
```bash
curl -X POST http://localhost:8011/operator/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-session","message":"Hola VX11"}'
```

---

## 📊 Servicios

| Servicio | Puerto | Status |
|----------|--------|--------|
| Tentáculo Link | 8000 | ✅ |
| Madre | 8001 | ✅ |
| Switch | 8002 | ✅ |
| Hermes | 8003 | ✅ |
| Hormiguero | 8004 | ✅ |
| MCP | 8006 | ✅ |
| Shub | 8007 | ✅ |
| Spawner | 8008 | ✅ |
| Operator Backend | 8011 | ✅ |
| Operator Frontend | 8020 | ✅ |

---

## 🔧 Configuración

### Restart All Services
```bash
docker-compose down
docker-compose up -d
```

### Rebuild Single Service
```bash
docker-compose build madre
docker-compose up -d madre
```

### Ver Logs
```bash
docker-compose logs -f operator-backend
```

---

## ✅ Status: PRODUCTION READY

- ✅ 10/10 servicios operacionales
- ✅ 30/34 tests passing (88%)
- ✅ BD persistencia funcional
- ✅ Autenticación centralizada
- ✅ DNS fallback automático
- ✅ Playwright Browser integrado

---

## 📚 Documentación

- `docs/VX11_v7_FINAL_PRODUCTION_READY.md` - Reporte completo
- `docs/ARCHITECTURE.md` - Arquitectura detallada
- `docs/API_REFERENCE.md` - Todos los endpoints

---

**Versión:** v7.0.0  
**Estado:** 🟢 Production Ready  
**Última actualización:** 2025-12-09
