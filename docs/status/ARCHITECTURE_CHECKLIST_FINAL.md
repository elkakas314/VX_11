# VX11 Arquitectura — Checklist Final

**Fecha**: 03 Enero 2026  
**Commit HEAD**: 9557529  
**Estado**: ✅ **PRODUCCIÓN LISTA** (Núcleo + Operator funcional)

---

## ✅ INVARIANTES DURAS — TODAS CUMPLIDAS

### 1. Single Entrypoint
- **Invariante**: TODO acceso externo SOLO vía tentaculo_link:8000
- **Status**: ✅ ENFORCED

### 2. Runtime Default: solo_madre
- **Invariante**: Full-profile OFF; servicios extra en ventanas temporales
- **Status**: ✅ ENFORCED

### 3. No Invented Endpoints
- **Invariante**: Descubrir en código, no inventar
- **Status**: ✅ VERIFIED

### 4. No Secretos en Git
- **Invariante**: tokens.env fuera de git + pre-commit hook
- **Status**: ✅ ENFORCED

---

## 📋 COMANDOS REPRODUCIBLES

### Levantar Core
```bash
cd /home/elkakas314/vx11
bash scripts/vx11_bringup.sh minimal false
```

### Verificar Single Entrypoint
```bash
docker compose -f docker-compose.full-test.yml ps --ports
# Expected: 8000->8000/tcp (tentaculo_link ONLY)
```

### Test Operator UI
```bash
curl -s http://localhost:8000/operator/ui/ | head -5
# Expected: <!doctype html>...
```

### Test Auth
```bash
# Sin token → 401
curl -s http://localhost:8000/operator/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hi"}'

# Con token → OK
curl -s -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/health
```

---

## 🔒 Seguridad
- ✅ tokens.env NOT in git
- ✅ Pre-commit hook active
- ✅ Auth headers required for /operator/api/*
- ✅ No tokens in documentation

---

## ✅ Archivos Modificados (Commit 9557529)

1. scripts/vx11_bringup.sh (was placeholder)
2. scripts/automation_full_run.sh (added tee output)
3. scripts/stop_non_madre.sh (preserve tentaculo_link)
4. scripts/start_services.sh (canonicalized)
5. tentaculo_link/main_v7.py (fixed volume mount path)

---

**Status**: 🟢 CORE OPERATIVO + REPRODUCIBLE + OPERATOR FUNCIONAL

