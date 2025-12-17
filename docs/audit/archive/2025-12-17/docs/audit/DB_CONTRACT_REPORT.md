DB Contract Validation Report - 2025-12-15T19:12:45.102139Z


Table: cli_registry
 - MISSING column: provider_id ; adding with spec: TEXT UNIQUE
   -> failed to add provider_id: Cannot add a UNIQUE column
 - OK column: vendor
 - OK column: category
 - OK column: adapter_type
 - OK column: auth_status
 - OK column: last_validated_at
 - OK column: quota_remaining
 - OK column: quota_reset_at
 - OK column: rate_limit_rpm
 - OK column: cost_hint
 - OK column: latency_avg_ms
 - OK column: enabled
 - OK column: degraded
 - OK column: domains_supported

Table: model_registry
 - MISSING column: model_id ; adding with spec: TEXT UNIQUE
   -> failed to add model_id: Cannot add a UNIQUE column
 - OK column: type
 - OK column: domain
 - OK column: capabilities
 - OK column: size_mb
 - OK column: max_ram_mb
 - OK column: cpu_cost_hint
 - OK column: warmup_ms_hint
 - OK column: local_path
 - OK column: runner_type
 - OK column: format
 - OK column: rotatable
 - OK column: offline_ok
 - OK column: last_used_at
 - OK column: use_count
 - OK column: health_score

Table: ia_decisions
 - OK column: request_id
 - OK column: chosen_resource
 - OK column: score
 - OK column: reasons
 - OK column: alternatives
 - OK column: latency_ms
 - OK column: success
 - OK column: error_class
 - OK column: tokens_est
 - OK column: fluzo_mode

Switch queue size (rows): 315368