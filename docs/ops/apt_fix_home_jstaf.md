# APT Repository `home:jstaf` Fix Guide

## Síntoma
```
E: Repository 'https://download.opensuse.org/repositories/home:/jstaf/xUbuntu_24.04 Release' does not have a Release file.
E: The repository may no longer be available or the URL may be incorrect.
E: Failed to fetch https://...EXPKEYSIG / signed by unknown key
```

**Causa**: El repositorio `home:jstaf` (OneDrive hybrid) está bloqueando `apt-get update` en sistemas sin la key correcta o repo deprecated.

---

## Solución: Deshabilitar SOLO el repo conflictivo

### Manual (rápido)
```bash
# Identificar el archivo
ls -la /etc/apt/sources.list.d/ | grep -i "onedriver\|jstaf"

# Deshabilitar (no eliminar)
sudo mv /etc/apt/sources.list.d/onedriver.list /etc/apt/sources.list.d/onedriver.list.disabled

# Reintentar update
sudo apt-get update
```

### Automatizado (ver script)
```bash
bash scripts/ops/apt_fix_home_jstaf.sh
```

---

## Cómo Revertir
```bash
# Si necesitas el repositorio de nuevo:
sudo mv /etc/apt/sources.list.d/onedriver.list.disabled /etc/apt/sources.list.d/onedriver.list
sudo apt-get update
```

---

## Impacto
- ✅ VX11 operativo sin cambios
- ✅ apt-get update funciona
- ❌ onedrive_hybrid_pipeline requiere activación manual (está fuera de este repo)

---

## OJO: No toques manualmente
- NO elimines `/etc/apt/sources.list.d/onedriver.list` (podría romperse future recovery)
- NO intentes `apt-key adv` sin supervisión (las keys del repo home:jstaf pueden estar expiradas)
- SOLO desactiva la lista (.disabled)
