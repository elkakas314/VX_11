"""
INEE Extended: Builder, Colony, Rewards implementation.
All dormant (flag-gated), no direct execution.
"""

import os
import uuid
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    JSON,
    DateTime,
    Boolean,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


# ============ BUILDER ============


class BuilderService:
    """
    Generates patchsets and prompt packs.
    Does NOT execute; only creates INTENT and registers in DB.
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.enabled = os.getenv("HORMIGUERO_BUILDER_ENABLED", "0") == "1"

    async def create_patchset(
        self, spec_id: str, description: str, parameters: Dict
    ) -> Dict:
        """Generate patchset from spec (no execution)."""
        if not self.enabled:
            return {"status": "disabled", "message": "Builder not enabled"}

        patchset_id = f"patch-{uuid.uuid4().hex[:8]}"

        # Simulate patch generation
        changes = {
            "module": spec_id,
            "description": description,
            "parameters": parameters,
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Register in DB
        if self.db_session:
            # INSERT builder_patchsets (would use ORM)
            pass

        # Create INTENT for Spawner (but don't execute)
        intent_id = f"intent-builder-{patchset_id}"

        return {
            "status": "ok",
            "patchset_id": patchset_id,
            "intent_id": intent_id,
            "changes": changes,
            "message": "Patchset created. Submit to Spawner for execution.",
        }

    async def create_prompt_pack(self, patchset_id: str) -> Dict:
        """Generate prompt pack from patchset."""
        if not self.enabled:
            return {"status": "disabled"}

        pack_id = f"pack-{uuid.uuid4().hex[:8]}"
        prompts = [
            f"Review patchset {patchset_id}",
            "Verify compatibility",
            "Suggest improvements",
        ]

        return {"status": "ok", "pack_id": pack_id, "prompts": prompts}


# ============ COLONY ============


class ColonyEnvelopeManager:
    """
    Manages HMAC-signed envelopes for remote colony communication.
    Replay protection via nonce tracking.
    """

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv(
            "VX11_COLONY_SECRET_KEY", "default-secret"
        )
        self.seen_nonces = set()  # In-memory; prod would use DB

    def create_envelope(self, colony_id: str, payload: Dict) -> Dict:
        """Create HMAC-signed envelope."""
        nonce = f"nonce-{uuid.uuid4().hex}"
        envelope_id = f"env-{uuid.uuid4().hex[:8]}"

        # Create HMAC signature
        message = f"{colony_id}:{nonce}:{json.dumps(payload)}"
        signature = hmac.new(
            self.secret_key.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

        return {
            "envelope_id": envelope_id,
            "nonce": nonce,
            "hmac_signature": signature,
            "payload": payload,
            "created_at": datetime.utcnow().isoformat(),
        }

    def verify_envelope(
        self, colony_id: str, nonce: str, signature: str, payload: Dict
    ) -> bool:
        """Verify HMAC signature and check for replay."""
        # Replay check
        if nonce in self.seen_nonces:
            return False  # Rejected (replay)

        # Verify signature
        message = f"{colony_id}:{nonce}:{json.dumps(payload)}"
        expected_sig = hmac.new(
            self.secret_key.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

        if signature != expected_sig:
            return False

        # Mark nonce as seen
        self.seen_nonces.add(nonce)
        return True


class ColonyLifecycleManager:
    """
    Manages colony lifecycle: egg -> larva -> adult.
    Includes heartbeat and ACK/retry backoff.
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.remote_plane_enabled = (
            os.getenv("VX11_INEE_REMOTE_PLANE_ENABLED", "0") == "1"
        )

    async def register_colony(self, colony_id: str, remote_url: Optional[str]) -> Dict:
        """Register new colony (initial state: egg)."""
        if not self.remote_plane_enabled and remote_url:
            return {"status": "error", "message": "Remote plane not enabled"}

        return {
            "status": "ok",
            "colony_id": colony_id,
            "state": "egg",
            "message": "Colony registered",
        }

    async def advance_lifecycle(self, colony_id: str, new_state: str) -> Dict:
        """Advance colony state (egg -> larva -> adult)."""
        valid_states = ["egg", "larva", "adult"]
        if new_state not in valid_states:
            return {"status": "error", "message": f"Invalid state: {new_state}"}

        return {
            "status": "ok",
            "colony_id": colony_id,
            "new_state": new_state,
            "changed_at": datetime.utcnow().isoformat(),
        }

    async def heartbeat(self, colony_id: str) -> Dict:
        """Record colony heartbeat."""
        return {
            "status": "ok",
            "colony_id": colony_id,
            "heartbeat_at": datetime.utcnow().isoformat(),
        }


# ============ REWARDS ============


class RewardsEngine:
    """
    Internal economy: points/scoring for scheduling/priority.
    Used for agent/colony prioritization (NOT real money).
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.enabled = os.getenv("VX11_REWARDS_ENABLED", "0") == "1"

    async def get_account(self, account_id: str) -> Dict:
        """Get reward account balance."""
        if not self.enabled:
            return {"status": "disabled"}

        # Query DB (stub)
        return {
            "status": "ok",
            "account_id": account_id,
            "balance_points": 0,
            "rank": "novice",
        }

    async def add_transaction(self, account_id: str, amount: int, reason: str) -> Dict:
        """Record reward transaction."""
        if not self.enabled:
            return {"status": "disabled"}

        transaction_id = f"txn-{uuid.uuid4().hex[:8]}"

        return {
            "status": "ok",
            "transaction_id": transaction_id,
            "account_id": account_id,
            "amount_points": amount,
            "reason": reason,
            "created_at": datetime.utcnow().isoformat(),
        }

    async def calculate_score(
        self, account_id: str, complexity: int, success_rate: float, speed_mult: float
    ) -> Dict:
        """Calculate reward score (for scheduling priority)."""
        if not self.enabled:
            return {"status": "disabled"}

        # Simple formula: complexity * success_rate * speed_multiplier
        points = int(complexity * success_rate * speed_mult * 10)

        return {
            "status": "ok",
            "account_id": account_id,
            "points_earned": points,
            "calculation": {
                "complexity": complexity,
                "success_rate": success_rate,
                "speed_multiplier": speed_mult,
            },
        }


# ============ MANIFESTATOR EXTENDED ============


class ManifestatorExtension:
    """
    Extends manifestator: generate patch plans + prompt packs + diagram packs.
    Never docker build directly; always via INTENT to Spawner.
    """

    def __init__(self):
        self.enabled = os.getenv("MANIFESTATOR_INEE_ENABLED", "0") == "1"

    async def generate_patch_plan(self, modules: List[str], patch_type: str) -> Dict:
        """Generate patch plan (code/config/schema)."""
        if not self.enabled:
            return {"status": "disabled"}

        plan_id = f"plan-{uuid.uuid4().hex[:8]}"

        return {
            "status": "ok",
            "plan_id": plan_id,
            "patch_type": patch_type,
            "modules_affected": modules,
            "changes_summary": f"Generated plan for {patch_type} patches",
            "risk_level": "low",
            "estimated_impact": {
                "performance": "neutral",
                "compatibility": "compatible",
            },
        }

    async def generate_prompt_pack(self, context: Dict) -> Dict:
        """Generate prompt pack for LLM."""
        if not self.enabled:
            return {"status": "disabled"}

        pack_id = f"prompt-{uuid.uuid4().hex[:8]}"
        prompts = [
            "Analyze code quality",
            "Suggest optimizations",
            "Validate schema changes",
        ]

        return {
            "status": "ok",
            "pack_id": pack_id,
            "prompts": prompts,
            "context": context,
        }
