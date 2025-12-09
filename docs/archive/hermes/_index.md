# Hermes v6.3
- Rol: wrappers DSP ligeros y CLI seguros.
- Endpoints: `/waveform`, `/spectrogram`, `/normalize`, `/ingest`, `/control`.
- Sandbox: paths restringidos a `SANDBOX_PATH` (fallback `./sandbox`), límite 50MB, rechazo de symlinks fuera de base.
- BD: tabla `hermes_ingest` almacena ingestas con tamaño/duración.
