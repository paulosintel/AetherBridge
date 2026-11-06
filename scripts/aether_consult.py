#!/usr/bin/env python3
"""
AetherBridge Multi-Model Consultation CLI Tool
Dispatches prompts to Claude Opus, Claude Sonnet, DeepSeek V4/R2, GLM-5.3,
Kimi K3, Qwen 3.6 Coder, Gemini 2.5 Pro/Flash, Nemotron 3 Ultra, and local Ollama models on demand
with zero subscription fees.
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error

OMNIROUTE_URL = os.environ.get("OMNIROUTE_URL", "http://127.0.0.1:20128/v1/chat/completions")
OMNIROUTE_TOKEN = os.environ.get("OMNIROUTE_API_KEY", os.environ.get("OMNIROUTE_LOCAL_TOKEN", "omniroute-secret-key-local"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")

MODEL_SHORTCUTS = {
    # 1. DeepSeek V4 & R2 (Claude Opus / Sonnet Equiv)
    "v4": "deepseek-v4-pro",
    "deepseek-v4": "deepseek-v4-pro",
    "v4-pro": "deepseek-v4-pro",
    "deepseek-v4-pro": "deepseek-v4-pro",
    "v4-flash": "deepseek-v4-flash",
    "deepseek-v4-flash": "deepseek-v4-flash",
    "r2": "deepseek-r2",
    "deepseek-r2": "deepseek-r2",

    # 2. GLM Family (Claude Opus 4.6 Equiv)
    "glm": "glm-5.3-flash",
    "glm5": "glm-5.3-flash",
    "glm-5": "glm-5.2",
    "glm-5.1": "glm-5.1",
    "glm-5.2": "glm-5.2",
    "glm-5.3": "glm-5.3-flash",
    "glm-5.3-flash": "glm-5.3-flash",
    "glm-flash": "glm-5.3-flash",
    "zai": "glm-5.3-flash",
    "z.ai": "glm-5.3-flash",

    # 3. Kimi Moonshot AI (Claude Sonnet / Fable Equiv)
    "kimi": "kimi-k3",
    "kimi-k3": "kimi-k3",
    "k3": "kimi-k3",
    "kimi-k2.6": "kimi-k2.6",
    "k2.6": "kimi-k2.6",
    "moonshot": "kimi-k3",

    # 4. Qwen 3 / 3.6 MoE & Coder (Claude Sonnet Equiv)
    "qwen": "qwen-3.6-coder",
    "qwen3": "qwen-3.6-coder",
    "qwen-3": "qwen-3.6-coder",
    "qwen-3.6": "qwen-3.6-coder",
    "qwen-coder": "qwen-3.6-coder",
    "qwen-3.6-coder": "qwen-3.6-coder",
    "qwen-235b": "qwen-3-235b",

    # 5. Gemini 2.5 Pro / Flash (Claude Opus / Sonnet Equiv)
    "gemini-2.5": "gemini-2.5-pro",
    "gemini25": "gemini-2.5-pro",
    "gemini-2.5-pro": "gemini-2.5-pro",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini": "gemini/gemini-3.1-flash-lite",

    # 6. Nemotron 3 Ultra / gpt-oss-120b (Claude Sonnet Equiv)
    "nemotron": "nemotron-3-ultra",
    "nemotron-3": "nemotron-3-ultra",
    "nemotron-ultra": "nemotron-3-ultra",
    "nemotron-3-ultra": "nemotron-3-ultra",
    "gpt-oss": "gpt-oss-120b",
    "gpt-oss-120b": "gpt-oss-120b",

    # Existing Standard Models
    "opus": "auto/claude-opus",
    "sonnet": "claude-3-5-sonnet-latest",
    "haiku": "claude-3-5-haiku-20241022",
    "coding": "auto/best-coding",
    "reasoning": "auto/best-reasoning",
    "fast": "auto/best-fast",
    "free": "auto/best-fast",
    "r1": "deepseek-r1",
    "r1-local": "ollama-local/deepseek-r1:1.5b",
    "local-r1": "ollama-local/deepseek-r1:1.5b",
    "deepseek-local": "ollama-local/deepseek-r1:1.5b",
    "coder": "ollama-local/qwen2.5-coder:3b",
    "local-coder": "ollama-local/qwen2.5-coder:3b",
    "local": "llama3.2:latest",
    "offline": "llama3.2:latest"
}

FALLBACK_MAP = {
    "deepseek-v4-pro": ["deepseek-r1", "auto/claude-opus"],
    "deepseek-v4-flash": ["auto/claude-sonnet", "auto/fast"],
    "deepseek-r2": ["deepseek-r1", "auto/best-reasoning"],
    "glm-5.3-flash": ["auto/claude-opus", "gemini/gemini-3.1-flash-lite"],
    "glm-5.2": ["auto/claude-opus"],
    "glm-5.1": ["auto/claude-opus"],
    "kimi-k3": ["claude-3-5-sonnet-latest", "gemini/gemini-3.1-flash-lite"],
    "kimi-k2.6": ["claude-3-5-sonnet-latest", "gemini/gemini-3.1-flash-lite"],
    "qwen-3.6-coder": ["claude-3-5-sonnet-latest", "auto/best-coding"],
    "qwen-3-235b": ["claude-3-5-sonnet-latest", "auto/best-coding"],
    "gemini-2.5-pro": ["gemini/gemini-3.1-flash-lite", "auto/claude-opus"],
    "gemini-2.5-flash": ["gemini/gemini-3.1-flash-lite", "auto/fast"],
    "nemotron-3-ultra": ["claude-3-5-sonnet-latest", "auto/best-coding"],
    "gpt-oss-120b": ["auto/best-coding", "claude-3-5-sonnet-latest"]
}

def query_gateway(model: str, prompt: str, system: str = "") -> str:
    target_model = MODEL_SHORTCUTS.get(model.lower(), model)
    candidates = [target_model]
    if target_model in FALLBACK_MAP:
        candidates.extend(FALLBACK_MAP[target_model])

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
                "Authorization": f"Bearer {OMNIROUTE_TOKEN}"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
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

    # Automatic fallback to Ollama local
    local_target = "qwen2.5-coder:3b" if ("coder" in model or "code" in model) else "llama3.2:latest"
    print(f"[AetherBridge Notice]: OmniRoute Cloud unavailable ({last_error}). Falling back to local Ollama ({local_target})...", file=sys.stderr)
    return query_ollama(local_target, prompt)

def query_ollama(model: str, prompt: str) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("response", json.dumps(data))
    except Exception as e:
        return f"[AetherBridge Error connecting to local Ollama]: {e}"

def main():
    parser = argparse.ArgumentParser(description="AetherBridge: Query frontier cloud or local models with auto-fallback")
    parser.add_argument("-m", "--model", default="auto/best-coding",
                        help="Model shortcut (v4, r2, glm5, kimi, qwen3, gemini25, nemotron, opus, sonnet, r1, fast, local)")
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

    output = query_gateway(args.model, prompt, args.system)
    print(output)

if __name__ == "__main__":
    main()
