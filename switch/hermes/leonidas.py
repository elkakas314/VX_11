"""
Leonidas: rigorous permission enforcement for Hermes.
Allowlist, denylist, prefix rules, command sanitization.
"""

from typing import Tuple, List, Optional, Dict
import shlex
import logging
import time
from collections import defaultdict

from config.forensics import write_log

log = logging.getLogger("vx11.leonidas")

# Whitelist: explicit allow
SAFE_COMMANDS = {
    "echo", "date", "uptime", "whoami", "pwd", "ls", "cat",
    "git", "curl", "python", "node",
}

# Safe prefixes (always allowed with args)
SAFE_PREFIXES = (
    "echo ",
    "ls ",
    "cat ",
    "git ",
    "curl ",
)

# Dangerous commands (absolute deny)
DENY_LIST = {
    "rm", "rmrf", "dd", "mkfs", "shutdown", "halt", "reboot",
    "fdisk", "parted", "deluser", "passwd", "useradd",
    "chmod", "chown", "pkill", "killall", "systemctl",
    "iptables", "ip6tables", "ufw", "firewall",
}

# Dangerous args (always block)
DANGEROUS_ARGS = [
    "/etc/shadow", "/etc/passwd", "/root/.ssh", "/root/.bash_history",
    "/proc/", "/sys/", "/dev/", "&&", "||", ";", "|", ">", "<",
    "`", "${", "$(", "${IFS}", "\\x", "/bin/sh", "/bin/bash",
]


# Rate Limiter (Patch 3: Prevent brute force)
class RateLimiter:
    """Simple rate limiter per user."""
    
    def __init__(self, max_attempts: int = 10, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempt_history: Dict[str, List[float]] = defaultdict(list)
    
    def check(self, user: str) -> Tuple[bool, str]:
        """Check if user is rate limited."""
        now = time.time()
        attempts = self._attempt_history[user]
        recent = [t for t in attempts if now - t < self.window_seconds]
        
        if len(recent) >= self.max_attempts:
            return False, f"rate_limit_exceeded:{len(recent)}/{self.max_attempts}"
        
        self._attempt_history[user] = recent + [now]
        return True, "ok"


_RATE_LIMITER = RateLimiter(max_attempts=5, window_seconds=60)
_AUDIT_LOG: List[Dict] = []


def check_permission(command: str) -> Tuple[bool, str]:
    """Check if command is allowed. Returns (allowed, reason)."""
    cmd = command.strip()
    if not cmd:
        return False, "empty_command"
    
    parts = cmd.split()
    base_cmd = parts[0] if parts else ""
    
    # Check deny list first
    if base_cmd in DENY_LIST:
        write_log("leonidas", f"check:deny_list:{base_cmd}", level="WARN")
        return False, "deny_list"
    
    # Check exact whitelist
    if base_cmd in SAFE_COMMANDS:
        write_log("leonidas", f"check:allow_exact:{base_cmd}")
        return True, "allowed_exact"
    
    # Check prefixes
    for prefix in SAFE_PREFIXES:
        if cmd.startswith(prefix):
            write_log("leonidas", f"check:allow_prefix:{base_cmd}")
            return True, "allowed_prefix"
    
    write_log("leonidas", f"check:deny_default:{base_cmd}", level="WARN")
    return False, "not_whitelisted"


def sanitize_command(command: str, args: Optional[List[str]] = None) -> Optional[List[str]]:
    """Sanitize command and args. Returns safe [cmd, arg1, arg2, ...] or None if invalid."""
    cmd = command.strip()
    if not cmd:
        write_log("leonidas", "sanitize:empty_command", level="WARN")
        return None
    
    # Parse command
    try:
        parts = shlex.split(cmd)
    except ValueError:
        write_log("leonidas", f"sanitize:shlex_error:{cmd}", level="WARN")
        return None
    
    base_cmd = parts[0]
    cmd_args = parts[1:] if len(parts) > 1 else []
    
    # Add provided args
    if args:
        cmd_args.extend(args)
    
    # Check base command is safe
    allowed, reason = check_permission(base_cmd)
    if not allowed:
        write_log("leonidas", f"sanitize:cmd_not_allowed:{base_cmd}", level="WARN")
        return None
    
    # Check for dangerous args
    full_arg_str = " ".join(cmd_args)
    for danger in DANGEROUS_ARGS:
        if danger in full_arg_str:
            write_log("leonidas", f"sanitize:dangerous_arg:{base_cmd}:{danger}", level="WARN")
            return None
    
    result = [base_cmd] + cmd_args
    write_log("leonidas", f"sanitize:ok:{base_cmd}:args_count={len(cmd_args)}")
    return result


def audit_check(command: str, allowed: bool, reason: str, user: Optional[str] = None):
    """Audit log for command checks."""
    user_info = f"user={user}" if user else "user=unknown"
    status = "ALLOW" if allowed else "DENY"
    write_log("leonidas", f"audit:{status}:{command}:{reason}:{user_info}")
