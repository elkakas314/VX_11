# VX11 Quick Status

Check system health in low-power mode (MAX 2 containers running).

## Quick Commands
```bash
# Check running containers
docker compose ps

# Health check all modules
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
  echo "Port $port:"
  curl -s http://127.0.0.1:$port/health | jq .
done

# Gateway status
curl -s http://127.0.0.1:8000/vx11/status | jq .
```

## Enforce MAX2 (if needed)
```bash
# Count running containers
RUNNING=$(docker compose ps --services --filter "status=running" | wc -l)
if [ $RUNNING -gt 2 ]; then
  echo "⚠️  $RUNNING containers running (MAX 2 allowed). Stopping excess..."
  docker compose stop $(docker compose ps --services --filter "status=running" | tail -n +3)
fi
```

## What to Look For
- **All /health endpoints:** should return `"status":"ok"`
- **Gateway /vx11/status:** should list all modules
- **No memory errors:** check `docker compose logs --tail=20`
- **Ports:** 8000–8008 should be listening

## Report Format (if generating audit)
- Timestamp (ISO 8601)
- Services status (table)
- Any errors detected
- Recommendation (e.g., "restart module X")
