#!/usr/bin/env python3
"""
OmniRoute CLI Model Consultation Tool (Direct Cloud Gateway)
Allows Antigravity, terminal scripts, or users to invoke OmniRoute cloud combos
and frontier models on demand, with optional Ollama fallback only if active locally.
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
    "opus": "claude-opus-5-5",
    "sonnet": "claude-sonnet-5-5",
    "haiku": "claude-haiku-5-5",
    "coding": "auto/best-coding",
    "reasoning": "auto/best-reasoning",
    "fast": "auto/best-fast",
    "free": "openrouter/auto",
    "r1": "claude-opus-5-5",
    "nemotron": "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
    "gemini": "gemini/gemini-3.5-flash",
    "gemma": "nvidia/google/gemma-4-31b-it",
    "qwen": "auto/best-coding",
    "local": "ollama-local",
    "offline": "ollama-local",
}

CLOUD_FALLBACKS = ["claude-sonnet-5-5", "gemini/gemini-3.1-flash-lite", "openrouter/auto"]


def is_ollama_available() -> bool:
    tags_url = OLLAMA_URL.rsplit("/api/", 1)[0] + "/api/tags"
    try:
        with urllib.request.urlopen(urllib.request.Request(tags_url), timeout=0.6) as resp:
            return resp.status == 200
    except Exception:
        return False


def query_ollama(model: str, prompt: str) -> str:
    if not is_ollama_available():
        return "[OmniRoute] Ollama no está instalado ni activo localmente. Usa proveedores cloud vía OmniRoute (ej. -m sonnet, -m fast)."
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("response", json.dumps(data))
    except Exception as e:
        return f"[Error connecting to Ollama local]: {e}"


def query_omniroute(model: str, prompt: str, system: str = "") -> str:
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
            with urllib.request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                return json.dumps(data, indent=2)
        except urllib.error.HTTPError as e:
            last_error = f"{e.code} - {e.read().decode('utf-8', errors='ignore')}"
            continue
        except Exception as e:
            last_error = str(e)
            continue

    if is_ollama_available():
        print(f"[OmniRoute Notice]: {last_error}. Falling back to local Ollama...", file=sys.stderr)
        return query_ollama("llama3.2:latest", prompt)
    return f"[OmniRoute Error]: {last_error}"


def main():
    parser = argparse.ArgumentParser(description="Query OmniRoute direct cloud models")
    parser.add_argument("-m", "--model", default="claude-sonnet-5-5", help="Model name or shortcut (sonnet, opus, haiku, fast, coding, reasoning, nemotron, gemini, gemma)")
    parser.add_argument("-s", "--system", default="", help="Optional system instruction")
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

    print(query_omniroute(args.model, prompt, args.system))


if __name__ == "__main__":
    main()
