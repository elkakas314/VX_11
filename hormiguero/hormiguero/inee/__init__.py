"""
INEE (Independent NEuroBehavioral EnginE) - Optional submódulo de Hormiguero.

Integración opcional para coordinación con sistemas remotos INEE.
Activación: VX11_INEE_ENABLED=1 (OFF por defecto).
Flujo: remoto -> tentaculo_link -> madre (nunca directo a Hormiguero).

Tablas DB:
- inee_colonies, inee_agents, inee_intents, inee_pheromones, inee_audit_events (additive).
"""

__version__ = "1.0.0"
