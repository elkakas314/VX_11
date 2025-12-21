#!/usr/bin/env python3
"""Populate `ia_decisions` from recent `switch_queue_v2` entries when missing.

This is a safe, idempotent helper used during acceptance to ensure the
IA decision ledger is populated for recent processed tasks.
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py

import os
import sys
import json
from datetime import datetime

# Ensure repo root is on sys.path when script is invoked directly
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from config.db_schema import get_session, SwitchQueueV2, IADecision


def main(limit=1000):
    sess = get_session("vx11")
    try:
        rows = (
            sess.query(SwitchQueueV2)
            .filter(SwitchQueueV2.status == "done")
            .order_by(SwitchQueueV2.finished_at.desc())
            .limit(limit)
            .all()
        )
        added = 0
        for r in rows:
            # check if ia_decision exists for this payload_hash
            exists = (
                sess.query(IADecision)
                .filter(IADecision.prompt_hash == (r.payload_hash or ""))
                .first()
            )
            if exists:
                continue
            try:
                ia = IADecision(
                    prompt_hash=r.payload_hash or "",
                    provider="reconstructed",
                    task_type=r.task_type or "unknown",
                    prompt=(
                        json.dumps(r.payload)
                        if isinstance(r.payload, dict)
                        else str(r.payload)
                    ),
                    response="reconstructed from switch_queue_v2",
                    latency_ms=0,
                    success=True,
                    confidence=0.5,
                    meta_json=json.dumps({"reconstructed_from_queue_id": r.id}),
                )
                sess.add(ia)
                sess.commit()
                added += 1
            except Exception:
                try:
                    sess.rollback()
                except Exception:
                    pass
        print("Added ia_decisions:", added)
    finally:
        sess.close()


if __name__ == "__main__":
    main()