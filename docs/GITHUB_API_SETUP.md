# GitHub API Configuration - VX11

## Status: ✅ CONFIGURED

**User**: elkakas314  
**Token Type**: Fine-grained PAT (stored securely in tokens.env)  
**API Access**: ✅ Ready (use environment variables only)

---

## ⚠️ Security First

**NEVER expose tokens in:**
- Documentation files
- Git commits or history
- Error messages or logs
- Chat, emails, or shared channels

**Tokens are stored in**: `tokens.env` (git-ignored, file mode 600)

---

## Environment Setup

### Load Tokens Safely

```bash
# Tokens are defined in tokens.env (NOT shown here)
source /home/elkakas314/vx11/tokens.env

# Verify token is loaded (DON'T echo the token!)
echo "Token loaded: ${GITHUB_FINEGRAND_PAT:0:20}..." # Shows only first 20 chars
```

### Token Rotation (if compromised)

1. **Revoke immediately** at https://github.com/settings/tokens
2. **Generate new tokens** with minimal scopes:
   - Repository access: `contents`, `pull_requests`, `issues`
   - No admin or workflow scopes unless required
3. **Update** `tokens.env` with new tokens
4. **Reload**: `source tokens.env`
5. **For team**: Distribute new token securely (1Password, GitLab Vault, etc.)

---

## REST API Usage (Modern Best Practices)

### Setup Headers (Reusable)

```bash
# Load token from environment (from tokens.env)
source tokens.env

# API constants
GH_API="https://api.github.com"
AUTH="Authorization: Bearer ${GITHUB_FINEGRAND_PAT}"
ACCEPT="Accept: application/vnd.github+json"
API_VER="X-GitHub-Api-Version: 2022-11-28"
```

### 1. Get Authenticated User

```bash
curl -sS \
  -H "$AUTH" \
  -H "$ACCEPT" \
  -H "$API_VER" \
  "$GH_API/user" | jq '{ login, id, type }'
```

### 2. List Your Repositories (Paginated)

```bash
curl -sS \
  -H "$AUTH" \
  -H "$ACCEPT" \
  -H "$API_VER" \
  "$GH_API/user/repos?per_page=100&page=1" | jq -r '.[].name'
```

**Or using `gh api` (better):**

```bash
gh api --paginate /user/repos --jq '.[] | .name'
```

### 3. Get Repository Info

```bash
curl -sS \
  -H "$AUTH" \
  -H "$ACCEPT" \
  -H "$API_VER" \
  "$GH_API/repos/elkakas314/VX_11" | jq '{ name, description, stargazers_count }'
```

### 4. List Issues (with pagination)

```bash
curl -sS \
  -H "$AUTH" \
  -H "$ACCEPT" \
  -H "$API_VER" \
  "$GH_API/repos/elkakas314/VX_11/issues?per_page=50&state=open" | jq '.[] | { number, title, state }'
```

### 5. Create Issue (Safe, No Shell Injection)

```bash
# Use jq to build JSON safely (NO shell escaping needed)
ISSUE_DATA=$(jq -n \
  --arg title "Fix: Documentation security" \
  --arg body "Remove exposed tokens and harden examples" \
  --argjson labels '["security","documentation"]' \
  '{ title: $title, body: $body, labels: $labels }')

curl -sS -X POST \
  -H "$AUTH" \
  -H "$ACCEPT" \
  -H "$API_VER" \
  -H "Content-Type: application/json" \
  -d "$ISSUE_DATA" \
  "$GH_API/repos/elkakas314/VX_11/issues" | jq '{ number, title, html_url }'
```

### 6. List Pull Requests

```bash
curl -sS \
  -H "$AUTH" \
  -H "$ACCEPT" \
  -H "$API_VER" \
  "$GH_API/repos/elkakas314/VX_11/pulls?per_page=50&state=open" | jq '.[] | { number, title, state }'
```

### 7. Create Pull Request

```bash
PR_DATA=$(jq -n \
  --arg title "feat: hardened GitHub API examples" \
  --arg head "github-api-hardening" \
  --arg base "main" \
  --arg body "Removed exposed tokens, modernized headers, added safe examples." \
  '{ title: $title, head: $head, base: $base, body: $body }')

curl -sS -X POST \
  -H "$AUTH" \
  -H "$ACCEPT" \
  -H "$API_VER" \
  -H "Content-Type: application/json" \
  -d "$PR_DATA" \
  "$GH_API/repos/elkakas314/VX_11/pulls" | jq '{ number, title, html_url }'
```

### 8. ETag Caching (Rate Limit Optimization)

```bash
# First request: save ETag
curl -sS -I \
  -H "$AUTH" \
  -H "$ACCEPT" \
  -H "$API_VER" \
  "$GH_API/repos/elkakas314/VX_11" | grep -i "etag"

# Subsequent requests: use If-None-Match (returns 304 if unchanged)
curl -sS \
  -H "$AUTH" \
  -H "$ACCEPT" \
  -H "$API_VER" \
  -H "If-None-Match: \"<ETag value>\"" \
  "$GH_API/repos/elkakas314/VX_11" | jq .
```

---

## Git Configuration (Safe Practices)

### ✅ RECOMMENDED: Use SSH Keys

```bash
# Generate SSH key (if not already done)
ssh-keygen -t ed25519 -C "elkakas314@github.com" -f ~/.ssh/github_rsa

# Add public key to https://github.com/settings/keys
cat ~/.ssh/github_rsa.pub

# Clone using SSH (NO credentials in URL)
git clone git@github.com:elkakas314/VX_11.git

# Configure SSH as default remote
git remote set-url vx_11_remote git@github.com:elkakas314/VX_11.git
```

### ✅ ALTERNATIVE: GitHub CLI (gh)

```bash
# Authenticate (stores token securely in ~/.config/gh)
gh auth login --with-token <<< "${GITHUB_FINEGRAND_PAT}"

# Clone using gh (token handled securely)
gh repo clone elkakas314/VX_11

# Git commands use gh for auth automatically
git push vx_11_remote main
```

### ❌ DO NOT USE: Token in URL (Deprecated & Insecure)

```bash
# DEPRECATED (GitHub disabled 2024-11)
# ❌ git clone https://<token>@github.com/...

# Reason: Tokens appear in:
# - Git config (git remote -v)
# - Shell history
# - Process output (ps aux)
# - Git logs
```

### Credentials Storage (Legacy)

If using HTTPS with git-credential-helper (not recommended):

```bash
# Use OAuth instead of Personal Access Tokens
git config --global credential.helper osxkeychain  # macOS
# OR
git config --global credential.helper pass         # Linux
```

---

## Advanced: GitHub Apps vs Personal Access Tokens

### When to Use GitHub Apps

- **Automated workflows** (CI/CD, background jobs)
- **Multiple repositories** (better scoping)
- **Long-lived operations** (apps don't expire like tokens)
- **Rate limits**: 15,000 requests/hour (vs 5,000 for PAT)

### When to Use Personal Access Tokens

- **Personal scripts** (interactive, ad-hoc)
- **Single repository** operations
- **Development workflows**

See: https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps

---

## Rate Limiting & Best Practices

### Check Rate Limit

```bash
gh api rate_limit --jq '.rate_limit | {limit, remaining, reset}'
```

### Reduce Rate Limit Usage

1. **Use conditional requests (ETags)**:
   ```bash
   # Save ETag from first request
   curl -sS -I "$GH_API/repos/elkakas314/VX_11" | grep -i "^etag"
   
   # Use If-None-Match (304 = not modified, no quota used)
   curl -H "If-None-Match: <ETag>" "$GH_API/repos/elkakas314/VX_11"
   ```

2. **Batch operations**:
   ```bash
   # Use GraphQL API instead of REST (more efficient)
   gh api graphql --paginate -f query='...'
   ```

3. **Pagination**:
   ```bash
   # Fetch only what you need
   gh api /repos/elkakas314/VX_11/issues?per_page=10 --jq '.[] | .number'
   ```

---

## Troubleshooting

### 401 Unauthorized

```bash
# Verify token is loaded and not empty
[ -z "$GITHUB_FINEGRAND_PAT" ] && echo "ERROR: Token not set" || echo "Token is set"

# Check token validity (without printing it)
gh auth status  # Should show: Logged in to github.com
```

### 403 Forbidden

```bash
# Check token scopes
gh api /user/repos --include "X-OAuth-Scopes:" -H "X-GitHub-Api-Version: 2022-11-28"
```

### Rate Limit Exceeded

```bash
# Check reset time
gh api rate_limit --jq '.rate_limit.reset | . as $reset | ($reset - now | floor) + " seconds"'
```

---

## Token Compromise Checklist

If you suspect your token has been leaked:

- [ ] **Immediate**: Go to https://github.com/settings/tokens → Revoke all PATs
- [ ] **Generate new token**: Create with minimal scopes
- [ ] **Update tokens.env**: Add new token value
- [ ] **Reload**: `source tokens.env`
- [ ] **Verify**: `gh auth status`
- [ ] **Check audit log**: https://github.com/settings/security-log
- [ ] **Team notification**: Inform team of rotation (if shared token)
- [ ] **For CI/CD**: Update secrets in GitHub Actions, GitLab, etc.

---

## Integration with Copilot Tools

VX11 provides built-in GitHub tools (activated in sandboxed environment):

- `activate_repository_management_tools` - Create repos, branches, PRs
- `activate_file_management_tools` - Create/delete files
- `activate_issue_and_commit_management_tools` - Issues, commits, tags
- `activate_release_management_tools` - Releases, versioning
- `activate_branch_and_commit_inspection_tools` - Browse branches
- `activate_code_and_repository_search_tools` - Search code
- `activate_pull_request_commenting_tools` - Review PRs

**Example**:
```bash
# These are Copilot MCP server functions, NOT shell commands
mcp_io_github_git_create_issue       # Create issue via Copilot
mcp_io_github_git_create_pull_request # Create PR via Copilot
mcp_io_github_git_list_issues        # Search issues via Copilot
```

---

## Last Updated

**Date**: 2026-01-03T02:15:00Z  
**Security Review**: ✅ COMPLETE - No tokens in documentation  
**User**: elkakas314  
**Repository**: VX_11 (https://github.com/elkakas314/VX_11.git)