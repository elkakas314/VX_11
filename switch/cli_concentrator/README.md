# Switch CLI Concentrator (Phase 3)

## Overview

The CLI Concentrator is the brain of provider selection in Switch. It:
- Manages available CLI providers (Copilot CLI, shell, APIs, etc.)
- Scores them based on priority, availability, quotas, and FLUZO signals
- Executes selected CLI with timeouts and error handling
- Logs usage statistics and routing decisions to database

## Components

- **registry.py**: Loads providers from environment and database
- **scoring.py**: Scores providers using weighted factors
- **breaker.py**: Circuit breaker to prevent cascading failures
- **executor.py**: Executes CLI commands safely
- **schemas.py**: Pydantic models for contract
- **providers/**: Individual provider implementations (Copilot CLI, generic shell)

## Environment Variables

```bash
VX11_COPILOT_CLI_ENABLED=1          # Enable Copilot CLI (default: 1)
VX11_FLUZO_MODE=balanced            # low_power, balanced, performance
VX11_FLUZO_PERSIST=0                # Persist FLUZO signals to DB (default: 0)
VX11_CLI_TIMEOUT=30                 # CLI timeout in seconds (default: 30)
VX11_CLI_BREAKER_THRESHOLD=3        # Failures before opening breaker (default: 3)
VX11_CLI_BREAKER_RECOVERY_S=60      # Recovery timeout in seconds (default: 60)
```

## Usage

```python
from switch.cli_concentrator import (
    CLIRegistry,
    CLIScorer,
    CircuitBreaker,
    CLIExecutor,
    CLIRequest,
)

# Initialize components
registry = CLIRegistry(db_session)
breaker = CircuitBreaker()
scorer = CLIScorer(registry, breaker)
executor = CLIExecutor()

# Create request
request = CLIRequest(
    prompt="What is the weather?",
    intent="chat",
    task_type="short",
    metadata={"force_cli": True}
)

# Get FLUZO data (from switch/fluzo module)
fluzo_data = {"profile": "balanced", "cpu_load": 0.5, "memory_pct": 45}

# Select best provider
provider, scoring_debug = scorer.select_best_provider(request, fluzo_data)

if provider:
    # Execute CLI
    result = executor.execute(provider, request.prompt)
    breaker.record_success(provider.provider_id) if result["success"] else breaker.record_failure(provider.provider_id)
    
    # Log usage stats to DB
    # ... (handled by caller via routing_events and cli_usage_stats tables)
```

## Contract

### CLIRequest
- prompt: str
- intent: str (chat | code | reasoning | general)
- task_type: str (short | long)
- metadata: dict
- force_cli: bool
- provider_preference: optional str
- trace_id: optional str (correlation ID)

### CLIResponse
- reply: str (normalized response)
- provider_id: str
- model_hint: optional str
- latency_ms: int
- tokens_estimated: int
- cost_estimated: float
- success: bool
- error_class: optional str
- trace_id: str
- scoring_debug: optional dict

## Integration with Switch

In `/switch/chat` and `/switch/task`:

```python
# If metadata.force_cli or intent requires CLI:
concentrator = CLIConcentrator(registry, breaker, scorer, executor)
response = await concentrator.process(request, fluzo_data)
```

This ensures Copilot CLI is prioritized for conversational tasks while maintaining fallback options.
