#!/usr/bin/env python3
"""
AetherBridge Multi-Model Consultation CLI Tool
Dispatches prompts to Claude Opus, Claude Sonnet, DeepSeek R1 reasoning,
Gemini 2.0 Pro/Flash, and local Ollama models on demand with zero subscription fees.
"""

import sys
import json
import argparse
import urllib.request
import urllib.error

OMNIROUTE_URL = "http://127.0.0.1:20128/v1/chat/completions"
OMNIROUTE_TOKEN = "omniroute-secret-key-local"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

MODEL_SHORTCUTS = {
    "opus": "auto/claude-opus",
    "sonnet": "auto/claude-sonnet",
    "haiku": "auto/claude-haiku",
    "coding": "auto/best-coding",
    "reasoning": "auto/best-reasoning",
    "fast": "auto/fast",
    "free": "auto/best-free",
    "r1": "deepseek-r1",
    "deepseek": "deepseek-v3",
    "gemini": "gemini-2.0-flash",
    "llama": "llama-3.3-70b-instruct",
    "local": "llama3.2:latest",
    "offline": "llama3.2:latest"
}

def query_gateway(model: str, prompt: str, system: str = "") -> str:
    target_model = MODEL_SHORTCUTS.get(model.lower(), model)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({"model": target_model, "messages": messages}).encode("utf-8")
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
        err_body = e.read().decode("utf-8")
        # Automatic fallback to Ollama local
        print(f"[AetherBridge Notice]: HTTP {e.code} - {err_body}\nFalling back to local Ollama (llama3.2:latest)...", file=sys.stderr)
        return query_ollama("llama3.2:latest", prompt)
    except Exception as e:
        print(f"[AetherBridge Notice]: {e}. Falling back to local Ollama (llama3.2:latest)...", file=sys.stderr)
        return query_ollama("llama3.2:latest", prompt)

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
    parser.add_argument("-m", "--model", default="auto/best-coding", help="Model shortcut (opus, sonnet, r1, gemini, coding, fast, local)")
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
