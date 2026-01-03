# "Read-only in full mode" - Design Explanation

**Status:** ✅ By Design (Not a Bug)

---

## What You're Seeing

The UI shows:
- **Mode**: `window_active` (from `/operator/api/window/status`)
- **Policy**: `policy: SOLO_MADRE` (from `/vx11/status`)
- **Chat State**: Read-only (can't type messages)
- **Error on send**: "Error: Disabled by SOLO_MADRE policy"

---

## Why This Is Correct

### The SOLO_MADRE Policy

SOLO_MADRE is an **intentional operational mode** where:

1. **Madre is the only active service** running
2. **Operator can observe but not control** (read-only mode)
3. **Madre controls all operations** (windows, resource allocation, policy changes)
4. **Chat is blocked** (no send/command capability)

### Window Status vs Policy

- `window_status = "window_active"` means: A window **is open** (for observation)
- `policy = "SOLO_MADRE"` means: **The chat is blocked anyway**

These two states can coexist:
- You can see a window (observe)
- But you can't interact with it (policy blocks it)

---

## What Backend is Doing

### GET `/operator/api/window/status`
```json
{
  "mode": "window_active",
  "ttl_seconds": null,
  "window_id": null,
  "services": [...],
  "degraded": false,
  "reason": null
}
```

**Meaning**: Madre opened an observer window for Operator to watch.

### GET `/vx11/status`
```json
{
  "policy": "SOLO_MADRE",
  "degraded": false
}
```

**Meaning**: SOLO_MADRE policy is active (Madre has full control, Operator is read-only).

---

## How to Disable SOLO_MADRE

To switch from SOLO_MADRE (read-only) to full operative mode, you need to:

1. **Call Madre to change policy**:
   ```bash
   curl -X POST http://localhost:8001/power/policy/full/apply
   ```

2. **Or use the UI if available**:
   - Settings → Power → Change Policy → "full" or "operative"

3. **Or programmatically** (backend can request):
   ```bash
   curl -X POST http://localhost:8001/power/policy/change \
     -H "Content-Type: application/json" \
     -d '{"policy": "full"}'
   ```

---

## Operational States

| State | Policy | Window | Chat | Purpose |
|-------|--------|--------|------|---------|
| **Startup** | SOLO_MADRE | None | ❌ Blocked | Madre initializing |
| **Observer** | SOLO_MADRE | Open | ❌ Blocked | Watch Madre operations |
| **Operative** | full | Open | ✅ Enabled | Full control |
| **Low Power** | low_power | None | ❌ Blocked | Resource conservation |

---

## Frontend Responsibility

The UI should:

1. **Display the policy clearly**: "Mode: SOLO_MADRE (Read-Only)"
2. **Show when it's safe to interact**: Only enable chat when `policy != "SOLO_MADRE"`
3. **Provide policy change button**: Let users request policy changes (if authorized)
4. **Handle "Disabled by SOLO_MADRE policy" error gracefully**:
   ```typescript
   if (error.includes("SOLO_MADRE")) {
     showMessage("Chat is blocked in SOLO_MADRE mode. Waiting for Madre...");
   }
   ```

---

## Testing the Transition

Once you're ready to test interactive mode:

```bash
# 1. Check current policy
curl http://localhost:8001/vx11/status | jq '.policy'
# Output: "SOLO_MADRE"

# 2. Change to full policy
curl -X POST http://localhost:8001/power/policy/full/apply

# 3. Verify change
curl http://localhost:8001/vx11/status | jq '.policy'
# Output: "full"

# 4. Refresh UI (Ctrl+Shift+R)
# Chat should now be enabled
```

---

## Why This Design?

1. **Safety**: Madre can maintain full control during startup/shutdown
2. **Observability**: Operator can watch without interfering
3. **Flexible**: Easy to change modes programmatically
4. **Clear**: No ambiguity about who's in control

---

## Summary

✅ **Backend is working correctly**
- Token generation ✓
- Window status ✓
- SSE streaming ✓

⏳ **Frontend needs to**:
1. Display SOLO_MADRE state clearly
2. Disable chat UI when policy is SOLO_MADRE
3. Show helpful message: "Waiting for Madre to enable operative mode..."
4. Optionally show "Change Policy" button (if authorized)

❌ **This is NOT an authentication error** (tokens work fine)  
❌ **This is NOT an SSE error** (stream works fine)  
✅ **This IS the intended operational mode**

