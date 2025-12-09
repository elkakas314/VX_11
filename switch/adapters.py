
from typing import Dict, Any
import time
import asyncio
import logging
import shutil
import subprocess
import shlex

from config import deepseek
from config.settings import settings
from config.forensics import write_log

log = logging.getLogger("vx11.switch.adapters")


async def local_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    await asyncio.sleep(0)
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    res = {"reply": prompt[::-1], "note": "local-stub-reversed"}
    write_log("switch.adapters", f"local_call:prompt_len={len(prompt)}")
    return {"ok": True, "engine": "local", "result": res, "latency_ms": int((time.time() - start) * 1000)}


async def deepseek_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    write_log("switch.adapters", f"deepseek_call:start:len={len(prompt)}")
    try:
        resp = await asyncio.to_thread(deepseek.call_deepseek, prompt, opts)
    except Exception as e:
        return {"ok": False, "engine": "deepseek", "error": str(e)}
    latency = int((time.time() - start) * 1000)
    if resp.get("ok"):
        write_log("switch.adapters", "deepseek_call:ok")
        return {"ok": True, "engine": "deepseek", "result": resp.get("result"), "latency_ms": latency}
    write_log("switch.adapters", f"deepseek_call:error:{resp.get('error')}")
    return {"ok": False, "engine": "deepseek", "error": resp.get("error"), "latency_ms": latency}


async def hermes_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    write_log("switch.adapters", f"hermes_call:start:{prompt[:80]}")
    hermes_url = getattr(settings, "hermes_url", None)
    if not hermes_url:
        write_log("switch.adapters", "hermes_unavailable")
        return {"ok": False, "engine": "hermes", "error": "hermes_unavailable"}
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{hermes_url}/hermes/execute", json={"command": "echo", "args": prompt})
            if resp.status_code == 200:
                data = resp.json()
                latency = int((time.time() - start) * 1000)
                out = {"engine": "cli", "ok": True, "output": data.get("output") or data.get("result") or ""}
                write_log("switch.adapters", f"hermes_call:ok")
                return {"ok": True, "engine": "hermes", "result": out, "latency_ms": latency}
            else:
                write_log("switch.adapters", f"hermes_call:http_{resp.status_code}")
                return {"ok": False, "engine": "hermes", "error": f"http_{resp.status_code}"}
    except Exception as e:
        write_log("switch.adapters", f"hermes_call:error:{str(e)}")
        return {"ok": False, "engine": "hermes", "error": str(e)}


async def openrouter_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    await asyncio.sleep(0)
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    write_log("switch.adapters", f"openrouter_call:{prompt[:80]}")
    return {"ok": True, "engine": "openrouter", "result": {"reply": prompt}, "latency_ms": int((time.time() - start) * 1000)}


async def llama_local_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    await asyncio.sleep(0)
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    write_log("switch.adapters", f"llama_local_call:len={len(prompt)}")
    return {"ok": True, "engine": "llama_local", "result": {"reply": prompt[:200]}, "latency_ms": int((time.time() - start) * 1000)}


async def codex_cli_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    await asyncio.sleep(0)
    write_log("switch.adapters", f"codex_cli_call:start")
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    binpath = shutil.which("gh")
    if not binpath:
        return {"ok": False, "engine": "codex_cli", "error": "binary_not_found"}
    cmd = f"{binpath} api -X POST /repos -f data='{prompt[:200]}'"
    try:
        parts = shlex.split(cmd)
        proc = subprocess.run(parts, capture_output=True, text=True, timeout=8)
        out = (proc.stdout or proc.stderr).strip()
        return {"ok": True, "engine": "codex_cli", "result": {"reply": out}, "latency_ms": int((time.time() - start) * 1000)}
    except Exception as e:
        write_log("switch.adapters", f"codex_cli_call:error:{str(e)}")
        return {"ok": False, "engine": "codex_cli", "error": str(e)}


async def gemini_cli_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    await asyncio.sleep(0)
    write_log("switch.adapters", "gemini_cli_call:start")
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    try:
        res = await asyncio.to_thread(deepseek.call_deepseek, prompt, {"purpose": "gemini_cli"})
        if res.get("ok"):
            return {"ok": True, "engine": "gemini_cli", "result": res.get("result"), "latency_ms": int((time.time() - start) * 1000)}
        return {"ok": False, "engine": "gemini_cli", "error": res.get("error")}
    except Exception as e:
        return {"ok": False, "engine": "gemini_cli", "error": str(e)}


async def llama_cpp_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    await asyncio.sleep(0)
    write_log("switch.adapters", "llama_cpp_call:start")
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    binpath = shutil.which("llama") or shutil.which("llama-cli") or shutil.which("llama_cpp")
    if not binpath:
        return {"ok": False, "engine": "llama_cpp", "error": "binary_not_found"}
    cmd = f"{binpath} --prompt " + shlex.quote(prompt[:1000])
    try:
        parts = shlex.split(cmd)
        proc = subprocess.run(parts, capture_output=True, text=True, timeout=10)
        out = (proc.stdout or proc.stderr).strip()
        return {"ok": True, "engine": "llama_cpp", "result": {"reply": out}, "latency_ms": int((time.time() - start) * 1000)}
    except Exception as e:
        write_log("switch.adapters", f"llama_cpp_call:error:{str(e)}")
        return {"ok": False, "engine": "llama_cpp", "error": str(e)}


async def local_llm_fallback(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    await asyncio.sleep(0)
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    write_log("switch.adapters", "local_llm_fallback:start")
    return {"ok": True, "engine": "local_llm_fallback", "result": {"reply": prompt[:256]}, "latency_ms": int((time.time() - start) * 1000)}


async def gh_cli_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    await asyncio.sleep(0)
    write_log("switch.adapters", "gh_cli_call:start")
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    binpath = shutil.which("gh")
    if not binpath:
        return {"ok": False, "engine": "gh_cli", "error": "binary_not_found"}
    cmd = f"{binpath} api --raw /"
    try:
        parts = shlex.split(cmd)
        proc = subprocess.run(parts, capture_output=True, text=True, timeout=8)
        out = (proc.stdout or proc.stderr).strip()
        return {"ok": True, "engine": "gh_cli", "result": {"reply": out}, "latency_ms": int((time.time() - start) * 1000)}
    except Exception as e:
        write_log("switch.adapters", f"gh_cli_call:error:{str(e)}")
        return {"ok": False, "engine": "gh_cli", "error": str(e)}


async def docker_cli_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    await asyncio.sleep(0)
    write_log("switch.adapters", "docker_cli_call:start")
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    binpath = shutil.which("docker")
    if not binpath:
        return {"ok": False, "engine": "docker_cli", "error": "binary_not_found"}
    cmd = f"{binpath} ps --no-trunc"
    try:
        parts = shlex.split(cmd)
        proc = subprocess.run(parts, capture_output=True, text=True, timeout=8)
        out = (proc.stdout or proc.stderr).strip()
        return {"ok": True, "engine": "docker_cli", "result": {"reply": out}, "latency_ms": int((time.time() - start) * 1000)}
    except Exception as e:
        write_log("switch.adapters", f"docker_cli_call:error:{str(e)}")
        return {"ok": False, "engine": "docker_cli", "error": str(e)}


async def kubectl_cli_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    start = time.time()
    await asyncio.sleep(0)
    write_log("switch.adapters", "kubectl_cli_call:start")
    prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
    binpath = shutil.which("kubectl")
    if not binpath:
        return {"ok": False, "engine": "kubectl_cli", "error": "binary_not_found"}
    cmd = f"{binpath} get pods --no-headers"
    try:
        parts = shlex.split(cmd)
        proc = subprocess.run(parts, capture_output=True, text=True, timeout=8)
        out = (proc.stdout or proc.stderr).strip()
        return {"ok": True, "engine": "kubectl_cli", "result": {"reply": out}, "latency_ms": int((time.time() - start) * 1000)}
    except Exception as e:
        write_log("switch.adapters", f"kubectl_cli_call:error:{str(e)}")
        return {"ok": False, "engine": "kubectl_cli", "error": str(e)}


PROVIDER_MAP = {
    "local": local_call,
    "deepseek": deepseek_call,
    "hermes": hermes_call,
    "openrouter": openrouter_call,
    "llama_local": llama_local_call,
    "codex_cli": codex_cli_call,
    "gemini_cli": gemini_cli_call,
    "llama_cpp": llama_cpp_call,
    "local_llm_fallback": local_llm_fallback,
    "gh_cli": gh_cli_call,
    "docker_cli": docker_cli_call,
    "kubectl_cli": kubectl_cli_call,
}


registry = PROVIDER_MAP


async def call_provider(name: str, payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
    fn = PROVIDER_MAP.get(name)
    if not fn:
        write_log("switch.adapters", f"call_provider:unknown:{name}")
        return {"ok": False, "error": "provider_unknown", "engine": name}
    try:
        write_log("switch.adapters", f"call_provider:invoke:{name}")
        return await fn(payload, context or {}, **opts)
    except Exception as e:
        write_log("switch.adapters", f"call_provider:error:{name}:{str(e)}")
        return {"ok": False, "engine": name, "error": str(e)}


async def select_provider(prompt: str, providers: list | None = None, context: Dict[str, Any] | None = None) -> str:
    # prefer explicit list
    if providers:
        for p in providers:
            if p in PROVIDER_MAP:
                return p

    # Check Hermes for available CLIs and prefer CLI providers when prompt hints at them
    hermes_url = getattr(settings, "hermes_url", None)
    try:
        if hermes_url:
            import httpx
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{hermes_url}/hermes/available")
                if resp.status_code == 200:
                    info = resp.json()
                    bins = info.get("binaries", {})
                    low = prompt.lower()
                    if "docker" in low and bins.get("docker"):
                        return "docker_cli"
                    if ("kubectl" in low or "k8s" in low or "pod" in low) and bins.get("kubectl"):
                        return "kubectl_cli"
                    if any(x in low for x in ("repo", "github", "commit", "pull request", "pr")) and bins.get("gh"):
                        return "gh_cli"
    except Exception:
        pass

    ds_key = getattr(settings, "deepseek_api_key", None)
    if ds_key:
        try:
            res = await asyncio.to_thread(deepseek.call_deepseek, f"Choose best provider for: {prompt}", {"purpose": "switch_select"}, 10.0)
            if res.get("ok"):
                r = res.get("result")
                if isinstance(r, str):
                    return r
                if isinstance(r, dict):
                    return r.get("provider") or r.get("choice") or r.get("name") or "local"
        except Exception as e:
            write_log("switch.adapters", f"select_provider:deepseek_err:{str(e)}")

    # fallback heuristic
    if len(prompt) < 80:
        return "local"
    return "deepseek"


    async def docker_cli_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
        start = time.time()
        await _wrap_sleep()
        write_log("switch.adapters", "docker_cli_call:start")
        prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
        binpath = shutil.which("docker")
        if not binpath:
            return {"ok": False, "engine": "docker_cli", "error": "binary_not_found"}
        # be conservative: only allow 'docker ps' style queries unless explicit
        cmd = f"{binpath} ps --no-trunc"
        try:
            parts = shlex.split(cmd)
            proc = subprocess.run(parts, capture_output=True, text=True, timeout=8)
            out = (proc.stdout or proc.stderr).strip()
            return {"ok": True, "engine": "docker_cli", "result": {"reply": out}, "latency_ms": int((time.time() - start) * 1000)}
        except Exception as e:
            write_log("switch.adapters", f"docker_cli_call:error:{str(e)}")
            return {"ok": False, "engine": "docker_cli", "error": str(e)}


    async def kubectl_cli_call(payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
        start = time.time()
        await _wrap_sleep()
        write_log("switch.adapters", "kubectl_cli_call:start")
        prompt = payload if isinstance(payload, str) else payload.get("prompt") if isinstance(payload, dict) else str(payload)
        binpath = shutil.which("kubectl")
        if not binpath:
            return {"ok": False, "engine": "kubectl_cli", "error": "binary_not_found"}
        cmd = f"{binpath} get pods --no-headers"
        try:
            parts = shlex.split(cmd)
            proc = subprocess.run(parts, capture_output=True, text=True, timeout=8)
            out = (proc.stdout or proc.stderr).strip()
            return {"ok": True, "engine": "kubectl_cli", "result": {"reply": out}, "latency_ms": int((time.time() - start) * 1000)}
        except Exception as e:
            write_log("switch.adapters", f"kubectl_cli_call:error:{str(e)}")
            return {"ok": False, "engine": "kubectl_cli", "error": str(e)}


    PROVIDER_MAP = {
        "local": local_call,
        "deepseek": deepseek_call,
        "hermes": hermes_call,
        "openrouter": openrouter_call,
        "llama_local": llama_local_call,
        "codex_cli": codex_cli_call,
        "gemini_cli": gemini_cli_call,
        "llama_cpp": llama_cpp_call,
        "local_llm_fallback": local_llm_fallback,
        "gh_cli": gh_cli_call,
        "docker_cli": docker_cli_call,
        "kubectl_cli": kubectl_cli_call,
    }


    registry = PROVIDER_MAP


    async def call_provider(name: str, payload: Any, context: Dict[str, Any] | None = None, **opts) -> Dict[str, Any]:
        fn = PROVIDER_MAP.get(name)
        if not fn:
            write_log("switch.adapters", f"call_provider:unknown:{name}")
            return {"ok": False, "error": "provider_unknown", "engine": name}
        try:
            write_log("switch.adapters", f"call_provider:invoke:{name}")
            return await fn(payload, context or {}, **opts)
        except Exception as e:
            write_log("switch.adapters", f"call_provider:error:{name}:{str(e)}")
            return {"ok": False, "engine": name, "error": str(e)}


    async def select_provider(prompt: str, providers: list | None = None, context: Dict[str, Any] | None = None) -> str:
        # First, prefer explicit list
        if providers:
            # choose highest priority available (simple heuristic: first available in providers that exist in registry)
            for p in providers:
                if p in PROVIDER_MAP:
                    return p
        # Check Hermes for available CLIs and prefer CLI providers when prompt hints at them
        hermes_url = getattr(settings, "hermes_url", None)
        try:
            if hermes_url:
                import httpx
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get(f"{hermes_url}/hermes/available")
                    if resp.status_code == 200:
                        info = resp.json()
                        bins = info.get("binaries", {})
                        low = prompt.lower()
                        if "docker" in low and bins.get("docker"):
                            return "docker_cli"
                        if "kubectl" in low or "k8s" in low or "pod" in low and bins.get("kubectl"):
                            return "kubectl_cli"
                        if any(x in low for x in ("repo", "github", "commit", "pull request", "pr")) and bins.get("gh"):
                            return "gh_cli"
        except Exception:
            pass

        ds_key = getattr(settings, "deepseek_api_key", None)
        # If deepseek available, ask it for reasoning
        if ds_key:
            try:
                res = await asyncio.to_thread(deepseek.call_deepseek, f"Choose best provider for: {prompt}", {"purpose": "switch_select"}, 10.0)
                if res.get("ok"):
                    r = res.get("result")
                    if isinstance(r, str):
                        return r
                    if isinstance(r, dict):
                        return r.get("provider") or r.get("choice") or r.get("name") or "local"
            except Exception as e:
                write_log("switch.adapters", f"select_provider:deepseek_err:{str(e)}")
        # fallback heuristic
        if len(prompt) < 80:
            return "local"
        return "deepseek"
