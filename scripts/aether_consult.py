#!/usr/bin/env python3
"""
AetherBridge Multi-Model Consultation CLI Tool (Direct OmniRoute Cloud-First)
Dispatches prompts directly through OmniRoute - AetherBridge to Gemini, NVIDIA NIM,
OpenRouter (:free), Groq, and smart Claude combos, with optional Ollama fallback only if active.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _read_env_value(filepath: str, keys: tuple) -> str:
    if not os.path.isfile(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() in keys:
                    val = v.strip().strip('"').strip("'")
                    if val:
                        return val
    except Exception:
        pass
    return ""


def resolve_omniroute_token() -> str:
    for env_key in ("OMNIROUTE_API_KEY", "OMNIROUTE_TOKEN", "OMNIROUTE_LOCAL_TOKEN"):
        val = os.environ.get(env_key, "").strip()
        if val:
            return val
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for candidate in (
        os.path.expanduser("~/.omniroute/.env"),
        os.path.join(repo_root, "api_keys.env"),
        os.path.join(os.getcwd(), "api_keys.env"),
    ):
        val = _read_env_value(candidate, ("OMNIROUTE_API_KEY", "OMNIROUTE_LOCAL_TOKEN"))
        if val:
            return val
    return "omniroute-secret-key-local"


OMNIROUTE_URL = os.environ.get("OMNIROUTE_URL", "http://127.0.0.1:20128/v1/chat/completions")
OMNIROUTE_TOKEN = resolve_omniroute_token()
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")

MODEL_SHORTCUTS = {
    "v4": "cfp/deepseek-ai/deepseek-v4-pro-0813",
    "deepseek-v4": "cfp/deepseek-ai/deepseek-v4-pro-0813",
    "v4-pro": "cfp/deepseek-ai/deepseek-v4-pro-0813",
    "deepseek-v4-pro": "cfp/deepseek-ai/deepseek-v4-pro-0813",
    "v4-flash": "oc/deepseek-v4-flash-free",
    "deepseek-v4-flash": "oc/deepseek-v4-flash-free",
    "r2": "claude-opus-5-5",
    "deepseek-r2": "claude-opus-5-5",
    "glm": "nvidia/z-ai/glm-5.3-flash",
    "glm5": "nvidia/z-ai/glm-5.3-flash",
    "glm-5": "nvidia/z-ai/glm-5.3-flash",
    "glm-5.3": "nvidia/z-ai/glm-5.3-flash",
    "glm-5.3-flash": "nvidia/z-ai/glm-5.3-flash",
    "zai": "nvidia/z-ai/glm-5.3-flash",
    "kimi": "claude-sonnet-5-5",
    "kimi-k3": "claude-sonnet-5-5",
    "k3": "claude-sonnet-5-5",
    "moonshot": "claude-sonnet-5-5",
    "qwen": "auto/best-coding",
    "qwen3": "auto/best-coding",
    "qwen-3.6-coder": "auto/best-coding",
    "gemini-2.5": "gemini/gemini-3.5-flash",
    "gemini25": "gemini/gemini-3.5-flash",
    "gemini-2.5-pro": "gemini/gemini-3.5-flash",
    "gemini-2.5-flash": "gemini/gemini-3.1-flash-lite",
    "gemini": "gemini/gemini-3.5-flash",
    "gemma": "nvidia/google/gemma-4-31b-it",
    "nemotron": "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
    "nemotron-3": "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
    "nemotron-ultra": "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
    "nemotron-3-ultra": "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
    "opus": "claude-opus-5-5",
    "sonnet": "claude-sonnet-5-5",
    "haiku": "claude-haiku-5-5",
    "coding": "auto/best-coding",
    "reasoning": "auto/best-reasoning",
    "fast": "auto/best-fast",
    "free": "openrouter/auto",
    "r1": "claude-opus-5-5",
    "local": "ollama-local",
    "offline": "ollama-local",
}

CLOUD_FALLBACKS = [
    "claude-sonnet-5-5",
    "gemini/gemini-3.5-flash",
    "nvidia/google/gemma-4-31b-it",
    "gemini/gemini-3.1-flash-lite",
    "openrouter/auto",
]


def is_ollama_available() -> bool:
    tags_url = OLLAMA_URL.rsplit("/api/", 1)[0] + "/api/tags"
    try:
        with urllib.request.urlopen(urllib.request.Request(tags_url), timeout=0.6) as resp:
            return resp.status == 200
    except Exception:
        return False


def query_ollama(model: str, prompt: str) -> str:
    if not is_ollama_available():
        return "[AetherBridge] Ollama no está instalado ni activo en este equipo. Usa un proveedor cloud directo vía OmniRoute (ej. -m sonnet, -m fast, -m nemotron)."
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("response", json.dumps(data))
    except Exception as e:
        return f"[AetherBridge Error connecting to local Ollama]: {e}"


def query_gateway(model: str, prompt: str, system: str = "") -> str:
    target_model = MODEL_SHORTCUTS.get(model.lower(), model)
    if target_model == "ollama-local":
        return query_ollama("llama3.2:latest", prompt)

    candidates = [target_model] + [m for m in CLOUD_FALLBACKS if m != target_model]
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_error = None
    for cand in candidates:
        payload = json.dumps({"model": cand, "messages": messages}).encode("utf-8")
        req = urllib.request.Request(
            OMNIROUTE_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OMNIROUTE_TOKEN}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                return json.dumps(data, indent=2)
        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}"
            continue
        except Exception as e:
            last_error = str(e)
            continue

    if is_ollama_available():
        local_target = "qwen2.5-coder:3b" if ("coder" in model or "code" in model) else "llama3.2:latest"
        print(f"[AetherBridge Notice]: OmniRoute Cloud unavailable ({last_error}). Falling back to local Ollama ({local_target})...", file=sys.stderr)
        return query_ollama(local_target, prompt)

    return f"[AetherBridge Error]: OmniRoute Cloud no pudo responder ({last_error})."


def main():
    parser = argparse.ArgumentParser(description="AetherBridge: Direct OmniRoute Multi-Model CLI")
    parser.add_argument(
        "-m",
        "--model",
        default="claude-sonnet-5-5",
        help="Model shortcut (sonnet, opus, haiku, fast, coding, reasoning, nemotron, gemini, gemma, free)",
    )
    parser.add_argument("-s", "--system", default="", help="Optional system instruction / persona")
    parser.add_argument("prompt", nargs="*", help="Prompt to evaluate")
    args = parser.parse_args()

    if not args.prompt:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
        else:
            parser.print_help()
            sys.exit(1)
    else:
        prompt = " ".join(args.prompt)

    print(query_gateway(args.model, prompt, args.system))


if __name__ == "__main__":
    main()
