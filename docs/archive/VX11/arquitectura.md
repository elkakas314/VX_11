# Arquitectura VX11 v6.3
- Servicios: gateway(8000), madre(8001), switch(8002), hermes(8003), hormiguero(8004), manifestator(8005), mcp(8006), shub(8007), spawner(8008), operator(8011).
- Auth: header `X-VX11-TOKEN` obligatorio salvo bypass en pruebas.
- Health: cada módulo expone `/health`; gateway/operator agregan.
- BD unificada: `data/vx11.db` compartida por todos.
- Red interna Docker bridge `vx11-network`.
- Operator frontend se sirve aparte (Vite), consume backend 8011 con el mismo token.
