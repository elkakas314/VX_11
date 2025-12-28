#!/bin/bash
# P1 TEST: DB Schema validation for INEE extended
# Verifies: inee_*, colony_*, builder_*, reward_* tables exist

set -e

DB_PATH="${1:-.}/data/runtime/vx11.db"
TEST_RESULTS=()
PASS=0
FAIL=0

if [[ ! -f "$DB_PATH" ]]; then
    echo "ERROR: DB file not found at $DB_PATH"
    exit 1
fi

log_test() {
    local name="$1"
    local status="$2"
    echo "[$(date +'%H:%M:%S')] $status: $name"
    TEST_RESULTS+=("$status: $name")
    if [[ "$status" == "PASS" ]]; then
        ((PASS++))
    else
        ((FAIL++))
    fi
}

echo "=== INEE Schema DB Validation ==="
echo "DB: $DB_PATH"

# ============ TEST 1: inee_colonies table ============
echo ""
echo "=== TEST 1: inee_colonies table ==="
if sqlite3 "$DB_PATH" ".schema inee_colonies" 2>/dev/null | grep -q "CREATE TABLE"; then
    log_test "inee_colonies table exists" "PASS"
else
    log_test "inee_colonies table exists" "FAIL"
fi

# ============ TEST 2: inee_intents table ============
echo ""
echo "=== TEST 2: inee_intents table ==="
if sqlite3 "$DB_PATH" ".schema inee_intents" 2>/dev/null | grep -q "CREATE TABLE"; then
    log_test "inee_intents table exists" "PASS"
else
    log_test "inee_intents table exists" "FAIL"
fi

# ============ TEST 3: colony_lifecycle table ============
echo ""
echo "=== TEST 3: colony_lifecycle table ==="
if sqlite3 "$DB_PATH" ".schema colony_lifecycle" 2>/dev/null | grep -q "CREATE TABLE"; then
    log_test "colony_lifecycle table exists" "PASS"
else
    log_test "colony_lifecycle table exists" "FAIL"
fi

# ============ TEST 4: colony_envelopes table ============
echo ""
echo "=== TEST 4: colony_envelopes table ==="
if sqlite3 "$DB_PATH" ".schema colony_envelopes" 2>/dev/null | grep -q "CREATE TABLE"; then
    log_test "colony_envelopes table exists" "PASS"
else
    log_test "colony_envelopes table exists" "FAIL"
fi

# ============ TEST 5: builder_patchsets table ============
echo ""
echo "=== TEST 5: builder_patchsets table ==="
if sqlite3 "$DB_PATH" ".schema builder_patchsets" 2>/dev/null | grep -q "CREATE TABLE"; then
    log_test "builder_patchsets table exists" "PASS"
else
    log_test "builder_patchsets table exists" "FAIL"
fi

# ============ TEST 6: reward_accounts table ============
echo ""
echo "=== TEST 6: reward_accounts table ==="
if sqlite3 "$DB_PATH" ".schema reward_accounts" 2>/dev/null | grep -q "CREATE TABLE"; then
    log_test "reward_accounts table exists" "PASS"
else
    log_test "reward_accounts table exists" "FAIL"
fi

# ============ TEST 7: DB integrity ============
echo ""
echo "=== TEST 7: DB Integrity Check ==="
INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>/dev/null || echo "FAILED")
if [[ "$INTEGRITY" == "ok" ]]; then
    log_test "DB integrity check OK" "PASS"
else
    log_test "DB integrity check OK" "FAIL"
    echo "  Result: $INTEGRITY"
fi

# ============ TEST 8: Foreign key check ============
echo ""
echo "=== TEST 8: FK Constraints Check ==="
FK_CHECK=$(sqlite3 "$DB_PATH" "PRAGMA foreign_key_check;" 2>/dev/null || echo "")
if [[ -z "$FK_CHECK" ]]; then
    log_test "Foreign key constraints satisfied" "PASS"
else
    log_test "Foreign key constraints satisfied" "FAIL"
    echo "  Issues: $FK_CHECK"
fi

# ============ TEST 9: Table count ============
echo ""
echo "=== TEST 9: INEE-related Table Count ==="
INEE_TABLES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'inee_%' OR name LIKE 'colony_%' OR name LIKE 'builder_%' OR name LIKE 'reward_%';" 2>/dev/null || echo "0")
if [[ "$INEE_TABLES" -gt 0 ]]; then
    log_test "Found $INEE_TABLES INEE/colony/builder/reward tables" "PASS"
else
    log_test "INEE extended tables found" "FAIL"
    echo "  Count: $INEE_TABLES"
fi

# ============ TEST 10: Indices created ============
echo ""
echo "=== TEST 10: Performance Indices ==="
INDICES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND (name LIKE 'idx_inee_%' OR name LIKE 'idx_colony_%' OR name LIKE 'idx_builder_%' OR name LIKE 'idx_reward_%');" 2>/dev/null || echo "0")
if [[ "$INDICES" -gt 0 ]]; then
    log_test "Found $INDICES performance indices" "PASS"
else
    log_test "Performance indices created" "FAIL"
    echo "  Count: $INDICES"
fi

# ============ SUMMARY ============
echo ""
echo "========================================"
echo "RESULTS: $PASS PASS, $FAIL FAIL"
echo "========================================"

for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
done

if [[ $FAIL -eq 0 ]]; then
    echo "✓ All DB schema tests passed"
    exit 0
else
    echo "✗ Some DB tests failed"
    exit 1
fi
