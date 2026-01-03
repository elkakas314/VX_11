# MONITORING & OBSERVABILITY GUIDE

**Date:** 2026-01-03  
**Component:** SSE Ephemeral Token System  
**Metrics TTL:** 60s (token lifetime)

---

## Prometheus Configuration

### File: `prometheus.yml` (add to scrape_configs)

```yaml
scrape_configs:
  - job_name: 'vx11-operator-backend'
    static_configs:
      - targets: ['localhost:8011']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
```

### Metrics to Track

**Ephemeral Token Lifecycle:**
```
# Counter: Total tokens issued
vx11_operator_ephemeral_tokens_issued_total{service="operator-backend"} 1250

# Gauge: Active tokens in cache
vx11_operator_ephemeral_tokens_active{service="operator-backend"} 45

# Counter: Expired tokens cleaned up
vx11_operator_ephemeral_tokens_expired_total{service="operator-backend"} 1205

# Counter: Token validation failures (invalid/expired)
vx11_operator_ephemeral_tokens_invalid_total{service="operator-backend"} 5

# Counter: SSE connections using ephemeral tokens
vx11_operator_sse_connections_ephemeral_total{service="operator-backend"} 1200

# Counter: SSE connections using principal tokens (fallback)
vx11_operator_sse_connections_principal_total{service="operator-backend"} 50
```

---

## Alerting Rules

### File: `prometheus-rules.yml`

```yaml
groups:
  - name: vx11_operator_ephemeral_tokens
    interval: 30s
    rules:
      # Alert: High token request rate
      - alert: HighEphemeralTokenRequestRate
        expr: rate(vx11_operator_ephemeral_tokens_issued_total[5m]) > 100
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High ephemeral token request rate ({{ $value }}/sec)"
          description: "Token issuance rate exceeded 100/sec for 2 minutes"
          runbook: "docs/runbooks/HIGH_TOKEN_REQUEST_RATE.md"

      # Alert: Cache size anomaly
      - alert: UnusuallyHighCacheSize
        expr: vx11_operator_ephemeral_tokens_active > 500
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Unusually high active ephemeral tokens ({{ $value }})"
          description: "Active token count > 500 (possible leak or bug)"
          runbook: "docs/runbooks/CACHE_SIZE_ANOMALY.md"

      # Alert: Validation failure rate
      - alert: HighTokenValidationFailureRate
        expr: rate(vx11_operator_ephemeral_tokens_invalid_total[5m]) > 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High token validation failure rate ({{ $value }}/sec)"
          description: "Token validation failures > 10/sec (possible attack or misconfiguration)"
          runbook: "docs/runbooks/TOKEN_VALIDATION_FAILURES.md"

      # Alert: Fallback usage (indicates client issues)
      - alert: HighPrincipalTokenUsageInSSE
        expr: rate(vx11_operator_sse_connections_principal_total[5m]) > rate(vx11_operator_sse_connections_ephemeral_total[5m]) * 0.1
        for: 5m
        labels:
          severity: info
        annotations:
          summary: "High principal token usage in SSE (fallback being used)"
          description: "Principal token SSE connections > 10% of ephemeral (clients not using new endpoint)"
          runbook: "docs/runbooks/PRINCIPAL_TOKEN_FALLBACK.md"
```

---

## Dashboard Queries (Grafana)

### Token Issuance Rate
```promql
rate(vx11_operator_ephemeral_tokens_issued_total[5m])
```

### Active Cache Size
```promql
vx11_operator_ephemeral_tokens_active
```

### Token Validity Rate (%)
```promql
100 * (1 - rate(vx11_operator_ephemeral_tokens_invalid_total[5m]) / rate(vx11_operator_ephemeral_tokens_issued_total[5m]))
```

### SSE Stream Success Rate
```promql
rate(vx11_operator_sse_connections_ephemeral_total[5m]) / (rate(vx11_operator_sse_connections_ephemeral_total[5m]) + rate(vx11_operator_sse_connections_principal_total[5m]))
```

---

## Logging Configuration

### Backend Log Level
```python
# In operator/backend/main.py
LOG_LEVEL = os.environ.get("VX11_OPERATOR_LOG_LEVEL", "INFO")
# Set to DEBUG for ephemeral token details

# Typical output:
# [SSE AUTH] Header: None, Query: bc3eceb7-..., Valid principal: {...}, Ephemeral cache size: 45
```

### Log Patterns to Search (ELK/Splunk/etc)

**Token issued:**
```
grep "ephemeral_token.*created_at"
```

**Token expired:**
```
grep "EPHEMERAL.*expired" | grep -v "info"
```

**Token validation failure:**
```
grep "\[SSE AUTH\] MISMATCH"
```

---

## Health Checks

### POST /operator/api/health

**Expected response:**
```json
{
  "status": "ok",
  "service": "operator_backend",
  "version": "7.0",
  "timestamp": "2026-01-03T20:00:00+00:00",
  "ephemeral_token_cache_size": 45
}
```

### Kubernetes/Docker Health Probe

```yaml
livenessProbe:
  httpGet:
    path: /operator/api/health
    port: 8011
  initialDelaySeconds: 10
  periodSeconds: 10
  
readinessProbe:
  httpGet:
    path: /operator/api/health
    port: 8011
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Performance SLOs

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Token issuance latency | < 50ms | > 100ms |
| Cache lookup latency | < 1ms | > 5ms |
| SSE stream establishment | < 500ms | > 1s |
| Token validation success rate | > 99% | < 98% |

---

## Incident Response

### If cache size grows abnormally

1. Check for token leaks (clients requesting tokens but not using them)
2. Verify TTL setting (should be 60s)
3. Check for authentication loop (clients failing, retrying)
4. Consider manual cache clear (restart backend)

### If validation failure rate spikes

1. Check frontend/client logs
2. Verify token endpoint responding (POST /operator/api/events/sse-token)
3. Verify gateway (tentaculo_link) proxy enabled
4. Check network connectivity between services

### If high principal token fallback usage

1. Check frontend code (should use ephemeral token endpoint)
2. Verify POST /operator/api/events/sse-token is accessible
3. Check browser console for errors
4. Monitor adoption rate (should be > 90% within 24h of deploy)

---

## Retention Policies

| Data | Retention | Storage |
|------|-----------|---------|
| Prometheus metrics | 15 days | Time-series DB |
| Application logs | 7 days | Centralized logging |
| Access logs | 30 days | Object storage |
| Audit logs | 1 year | Compliance storage |

---
