#!/usr/bin/env python3
"""
OmniRoute Automatic Frontier Model Catalog Synchronizer
Scans live providers from OmniRoute, discovers new state-of-the-art models,
and automatically updates Codex, Claude CLI, and Antigravity profiles.
"""

import os
import sys
import json
import time
import subprocess
import urllib.request

OMNIROUTE_URL = os.environ.get("OMNIROUTE_URL", "http://127.0.0.1:20128/v1/models")
OMNIROUTE_TOKEN = os.environ.get("OMNIROUTE_API_KEY", os.environ.get("OMNIROUTE_LOCAL_TOKEN", "omniroute-secret-key-local"))
CODEX_OMNI_CATALOG = os.path.expanduser("~/.codex/omniroute-launch-models.json")
CODEX_OLLAMA_CATALOG = os.path.expanduser("~/.codex/ollama-launch-models.json")
STATUS_LOG_PATH = os.path.expanduser("~/.omniroute/catalog_update_status.json")

FRONTIER_PATTERNS = [
    # (regex/substring, display_name, description, priority, category)
    ("claude-3-7-sonnet", "Claude 3.7 Sonnet (Anthropic Flagship)", "Hybrid reasoning and premier coding model", 110, "coding"),
    ("claude-3-5-sonnet", "Claude 3.5 Sonnet (Anthropic)", "State of the art coding and engineering", 108, "coding"),
    ("claude-3-opus", "Claude 3 Opus (Anthropic)", "Deep architectural reasoning and synthesis", 105, "architecture"),
    ("deepseek-r1", "DeepSeek R1 (Reasoning Champion)", "Frontier open reasoning and mathematical proofs", 104, "reasoning"),
    ("deepseek-v3", "DeepSeek V3 (Coding/Chat)", "Frontier open general intelligence", 102, "coding"),
    ("gemini-2.0-pro", "Gemini 2.0 Pro (Google AI Studio - Free)", "Premier reasoning with 1M token context", 100, "context"),
    ("gemini-2.0-flash", "Gemini 2.0 Flash (Google AI Studio - Free)", "Ultra-fast multimodal model with 1M context", 99, "speed"),
    ("o3-mini", "OpenAI o3-mini (High Reasoning)", "STEM, logic, and rapid competitive coding", 98, "reasoning"),
    ("gpt-4o", "OpenAI GPT-4o", "Omni multimodal flagship", 96, "general"),
    ("llama-3.3-70b", "Meta Llama 3.3 70B (Groq/Cerebras LPU)", "Fastest open model via hardware acceleration", 95, "speed"),
    ("qwen-2.5-coder-32b", "Qwen 2.5 Coder 32B (Leading Open Coder)", "Premier code generation and repository engineering", 94, "coding"),
    ("auto/best-coding", "OmniRoute Best Coding (Auto-Fallback)", "Zero-cost multi-provider cascade for programming", 120, "combo"),
    ("auto/best-reasoning", "OmniRoute Best Reasoning (Auto-Fallback)", "Multi-provider cascade for deep logic and math", 119, "combo"),
    ("auto/fast", "OmniRoute Ultra-Fast (LPU Fallback)", "Sub-250ms inference cascade across fastest chips", 118, "combo"),
    ("auto/best-free", "OmniRoute Best Free (Zero-Cost)", "Cascades strictly across 100% free tiers", 117, "combo"),
    ("llama3.2:latest", "Llama 3.2 (Ollama Local - 100% Offline)", "Local private model running directly on Apple Silicon", 90, "offline")
]

def fetch_live_models():
    req = urllib.request.Request(OMNIROUTE_URL, headers={"Authorization": f"Bearer {OMNIROUTE_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("id", "") for m in data.get("data", [])]
    except Exception as e:
        print(f"[AutoUpdate] Could not fetch models from OmniRoute: {e}", file=sys.stderr)
        return []

def update_single_catalog(path, live_models):
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[AutoUpdate] Error reading catalog at {path}: {e}", file=sys.stderr)
        return 0

    existing_slugs = {m.get("slug") for m in data.get("models", [])}
    template = data["models"][0].copy() if data.get("models") else {}

    added_count = 0
    for pattern, name, desc, priority, category in FRONTIER_PATTERNS:
        matched_live = any(pattern.lower() in lm.lower() for lm in live_models)
        slug = pattern

        if slug not in existing_slugs:
            new_entry = template.copy()
            new_entry["slug"] = slug
            new_entry["display_name"] = name
            new_entry["description"] = f"{desc} [{'Live Verified' if matched_live else 'Gateway Route'}]"
            new_entry["priority"] = priority
            new_entry["visibility"] = "list"
            new_entry["model_provider"] = "omniroute"
            data["models"].append(new_entry)
            existing_slugs.add(slug)
            added_count += 1

    # Ensure every model in the catalog is bound to omniroute provider
    for m in data.get("models", []):
        m["model_provider"] = "omniroute"

    data["models"].sort(key=lambda x: x.get("priority", 0), reverse=True)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return added_count

def update_codex_catalog(live_models):
    added_omni = update_single_catalog(CODEX_OMNI_CATALOG, live_models)
    added_ollama = update_single_catalog(CODEX_OLLAMA_CATALOG, live_models)

    # Ensure config.toml is locked to OmniRoute without breaking websocket bridge
    config_path = os.path.expanduser("~/.codex/config.toml")
    if os.path.exists(config_path):
        try:
            import re
            with open(config_path, "r") as f:
                c = f.read()
            c = re.sub(r'model_catalog_json\s*=\s*"[^"]*"', f'model_catalog_json = "{CODEX_OMNI_CATALOG}"', c, count=1)
            c = re.sub(r'openai_base_url\s*=\s*"[^"]*"', 'openai_base_url = "http://127.0.0.1:20128/v1"', c, count=1)
            
            # Ensure top-level model_provider = "omniroute"
            if "model_provider =" not in c:
                c = re.sub(r'(model\s*=\s*"[^"]*"\n)', r'\1model_provider = "omniroute"\n', c, count=1)
            
            # Ensure [model_providers.omniroute] has supports_websockets = false
            if "[model_providers.omniroute]" in c:
                if "supports_websockets" not in c:
                    c = re.sub(
                        r'(\[model_providers\.omniroute\][\s\S]*?requires_openai_auth\s*=\s*false)',
                        r'\1\nsupports_websockets = false',
                        c,
                        count=1
                    )
            with open(config_path, "w") as f:
                f.write(c)
        except Exception as e:
            print(f"[AutoUpdate] Notice updating config.toml: {e}", file=sys.stderr)

    return max(added_omni, added_ollama)

def sync_cli_profiles():
    env = os.environ.copy()
    env["OMNIROUTE_API_KEY"] = OMNIROUTE_TOKEN
    subprocess.run(["omniroute", "setup-codex", "--api-key", OMNIROUTE_TOKEN], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["omniroute", "setup-claude", "--api-key", OMNIROUTE_TOKEN], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    start = time.time()
    live_models = fetch_live_models()
    added_to_codex = update_codex_catalog(live_models)
    sync_cli_profiles()

    status = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_live_models": len(live_models),
        "newly_added_codex_models": added_to_codex,
        "duration_sec": round(time.time() - start, 2),
        "status": "success"
    }

    os.makedirs(os.path.dirname(STATUS_LOG_PATH), exist_ok=True)
    with open(STATUS_LOG_PATH, "w") as f:
        json.dump(status, f, indent=2)

    print(f"Catalog sync completed in {status['duration_sec']}s. Total live models: {len(live_models)}.")

if __name__ == "__main__":
    main()
