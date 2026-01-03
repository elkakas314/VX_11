#!/bin/bash
# Token Revocation & Rotation Guide for VX11
# USAGE: Read and execute sections manually (NOT a full auto-script for safety)

set -e

echo "==============================================="
echo "GitHub Token Security - Revocation & Rotation"
echo "==============================================="
echo ""
echo "⚠️  READ CAREFULLY - This guide requires manual steps"
echo "   to revoke and rotate GitHub tokens"
echo ""

# ============================================================
# STEP 1: VERIFY CURRENT TOKENS
# ============================================================

echo "[1/5] Verifying current token status..."
echo ""
echo "✓ Check if tokens are loaded in this session:"
echo "    [ -z \"\$GITHUB_FINEGRAND_PAT\" ] && echo \"Token NOT set\" || echo \"Token is set\""

[ -z "$GITHUB_FINEGRAND_PAT" ] && echo "❌ TOKEN NOT SET" || echo "✅ Token is loaded (first 20 chars: ${GITHUB_FINEGRAND_PAT:0:20}...)"
echo ""

# ============================================================
# STEP 2: REVOKE TOKENS (Manual)
# ============================================================

echo "[2/5] MANUAL: Revoke exposed tokens on GitHub"
echo ""
echo "  1. Go to: https://github.com/settings/tokens"
echo "  2. Look for tokens created on 2026-01-02 or earlier"
echo "  3. Click 'Delete' on:"
echo "     - Any fine-grained PAT (name with 'pat')"
echo "     - Any classic token (name with 'ghp_' or 'CLASSIC')"
echo ""
echo "  4. Verify in Security Log: https://github.com/settings/security-log"
echo "     Look for 'Token revoked' events"
echo ""
echo "⏳  Press ENTER when tokens are revoked on GitHub..."
read

# ============================================================
# STEP 3: GENERATE NEW TOKENS (Manual)
# ============================================================

echo ""
echo "[3/5] MANUAL: Generate new replacement tokens"
echo ""
echo "  1. Go to: https://github.com/settings/tokens/new"
echo "  2. Create NEW fine-grained PAT with:"
echo "     Name: vx11-automation-pat"
echo "     Scopes: contents, pull_requests, issues, metadata"
echo "     Expiration: 90 days (recommended)"
echo "     Repository access: Only VX_11 repository"
echo ""
echo "  3. Copy the new token value (starts with 'github_pat_')"
echo "  4. DO NOT SHARE OR PASTE HERE"
echo ""
echo "⏳  Press ENTER when new PAT is created..."
read

# ============================================================
# STEP 4: UPDATE ENVIRONMENT
# ============================================================

echo ""
echo "[4/5] Update tokens.env with new credentials"
echo ""
echo "  Edit: vim tokens.env"
echo ""
echo "  Find and update these lines:"
echo "    GITHUB_FINEGRAND_PAT=<paste-new-token-here>"
echo "    GITHUB_TOKEN=<same-as-GITHUB_FINEGRAND_PAT>"
echo ""
echo "  Then reload:"
echo "    source tokens.env"
echo ""

echo "Edit tokens.env now? (y/n): "
read -r edit_tokens

if [ "$edit_tokens" = "y" ]; then
    if command -v vim &> /dev/null; then
        vim tokens.env
        echo "Reloading environment..."
        source tokens.env
        echo "✅ Environment reloaded"
    else
        echo "❌ vim not found. Edit manually:"
        echo "   nano tokens.env"
    fi
fi

echo ""

# ============================================================
# STEP 5: VERIFY NEW TOKEN
# ============================================================

echo "[5/5] Verify new token works"
echo ""

if [ -z "$GITHUB_FINEGRAND_PAT" ]; then
    echo "❌ Token NOT set in environment"
    echo "   Run: source tokens.env"
    exit 1
fi

echo "Testing GitHub API access..."

RESPONSE=$(curl -sS \
    -H "Authorization: Bearer ${GITHUB_FINEGRAND_PAT}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    https://api.github.com/user)

if echo "$RESPONSE" | grep -q '"login"'; then
    USER_LOGIN=$(echo "$RESPONSE" | jq -r '.login' 2>/dev/null || echo "unknown")
    echo "✅ API access verified (user: $USER_LOGIN)"
else
    echo "❌ API access failed"
    echo "   Response: $RESPONSE"
    exit 1
fi

# ============================================================
# STEP 6: VERIFY NO SECRETS IN REPO
# ============================================================

echo ""
echo "[BONUS] Checking for leftover secrets in repo..."
echo ""

FOUND_PATTERNS=0

if git grep -n "github_pat_" 2>/dev/null | grep -v ".git/" | head -5; then
    echo "⚠️  WARNING: Found 'github_pat_' pattern in working tree"
    FOUND_PATTERNS=$((FOUND_PATTERNS + 1))
fi

if git grep -n "ghp_" 2>/dev/null | grep -v ".git/" | head -5; then
    echo "⚠️  WARNING: Found 'ghp_' pattern in working tree"
    FOUND_PATTERNS=$((FOUND_PATTERNS + 1))
fi

if [ $FOUND_PATTERNS -eq 0 ]; then
    echo "✅ No exposed token patterns found in current working tree"
else
    echo "⚠️  Found $FOUND_PATTERNS pattern(s) - review manually"
fi

# ============================================================
# SUMMARY
# ============================================================

echo ""
echo "==============================================="
echo "✅ Token rotation complete!"
echo "==============================================="
echo ""
echo "Summary:"
echo "  ✅ Old tokens revoked on GitHub"
echo "  ✅ New PAT generated"
echo "  ✅ tokens.env updated"
echo "  ✅ New token verified working"
echo ""
echo "Next steps:"
echo "  1. If token was used in CI/CD:"
echo "     - Update GitHub Actions secrets"
echo "     - Update other CI/CD platforms (GitLab, Vercel, etc.)"
echo "  2. Inform team of token rotation"
echo "  3. Delete old tokens.env backups (if any)"
echo ""
echo "References:"
echo "  https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens"
echo ""
