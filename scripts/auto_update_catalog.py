#!/usr/bin/env python3
"""
OmniRoute Automatic Frontier Model Catalog Synchronizer (Direct Cloud-First)
Scans live providers from OmniRoute, discovers state-of-the-art cloud models,
and automatically updates Codex, Claude CLI, and Antigravity profiles.
Ollama local models are only registered if Ollama is active on localhost:11434.
"""

import json
import os
import re
import subprocess
import sys
import time
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


OMNIROUTE_URL = os.environ.get("OMNIROUTE_URL", "http://127.0.0.1:20128/v1/models")
OMNIROUTE_TOKEN = resolve_omniroute_token()
OLLAMA_TAGS_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/") + "/api/tags"
CODEX_OMNI_CATALOG = os.path.expanduser("~/.codex/omniroute-launch-models.json")
STATUS_LOG_PATH = os.path.expanduser("~/.omniroute/catalog_update_status.json")

CLOUD_PATTERNS = [
    ("auto/best-coding", "OmniRoute Best Coding (Auto-Fallback)", "Zero-cost multi-provider cascade for programming", 135, "combo"),
    ("auto/best-reasoning", "OmniRoute Best Reasoning (Auto-Fallback)", "Multi-provider cascade for deep logic and math", 134, "combo"),
    ("auto/best-fast", "OmniRoute Ultra-Fast (Cloud Cascade)", "Low-latency inference cascade across active cloud providers", 133, "combo"),
    ("claude-opus-5-5", "OmniRoute Claude Opus (Nemotron 550B / Gemini)", "Flagship architectural reasoning & synthesis combo", 132, "architecture"),
    ("claude-sonnet-5-5", "OmniRoute Claude Sonnet (Gemini 3.5 / Gemma 4)", "Primary software engineering & coding combo", 131, "coding"),
    ("claude-haiku-5-5", "OmniRoute Claude Haiku (Flash Lite / Lightning)", "Sub-second lightweight cloud combo", 130, "speed"),
    ("nvidia/nvidia/nemotron-3-ultra-550b-a55b", "Nemotron 3 Ultra 550B (NVIDIA NIM)", "NVIDIA 550B frontier reasoning and enterprise engineering", 125, "frontier"),
    ("openrouter/nvidia/nemotron-3-ultra-550b-a55b:free", "Nemotron 3 Ultra 550B (:free OpenRouter)", "Zero-cost 550B flagship via OpenRouter", 124, "frontier"),
    ("gemini/gemini-3.5-flash", "Gemini 3.5 Flash (Google AI Studio)", "High-speed 1M context coding & reasoning", 123, "coding"),
    ("gemini/gemini-3.1-flash-lite", "Gemini 3.1 Flash Lite (Google AI Studio)", "Instant low-latency multimodal intelligence", 122, "speed"),
    ("nvidia/google/gemma-4-31b-it", "Gemma 4 31B IT (NVIDIA NIM)", "Fast open-weights coding and reasoning model", 121, "coding"),
    ("openrouter/cohere/north-mini-code:free", "Cohere North Mini Code (:free)", "Agile coding assistant via OpenRouter free tier", 120, "coding"),
    ("openrouter/auto", "OpenRouter Auto Router", "Automatic cloud fallback across free and open endpoints", 118, "combo"),
]

OPTIONAL_OLLAMA_PATTERNS = [
    ("qwen2.5-coder:3b", "Qwen 2.5 Coder 3B (Ollama Local)", "Local coding model", 82, "offline"),
    ("deepseek-r1:1.5b", "DeepSeek R1 1.5B (Ollama Local)", "Local chain-of-thought reasoning engine", 81, "offline"),
    ("llama3.2:latest", "Llama 3.2 (Ollama Local - Offline)", "Local private model", 80, "offline"),
]


def is_ollama_active() -> bool:
    try:
        with urllib.request.urlopen(urllib.request.Request(OLLAMA_TAGS_URL), timeout=0.8) as resp:
            return resp.status == 200
    except Exception:
        return False


def fetch_live_models() -> list:
    req = urllib.request.Request(OMNIROUTE_URL, headers={"Authorization": f"Bearer {OMNIROUTE_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("id", "") for m in data.get("data", [])]
    except Exception as e:
        print(f"[AutoUpdate] Could not fetch models from OmniRoute: {e}", file=sys.stderr)
        return []


def update_single_catalog(path: str, live_models: list, ollama_active: bool) -> int:
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[AutoUpdate] Error reading catalog at {path}: {e}", file=sys.stderr)
        return 0

    models_list = data.get("models", [])
    if not ollama_active:
        models_list = [
            m for m in models_list
            if not str(m.get("slug", "")).startswith(("ollama", "qwen2.5-coder:3b", "deepseek-r1:1.5b", "llama3.2"))
        ]
        data["models"] = models_list

    existing_slugs = {m.get("slug") for m in models_list}
    template = models_list[0].copy() if models_list else {}

    patterns = list(CLOUD_PATTERNS)
    if ollama_active:
        patterns.extend(OPTIONAL_OLLAMA_PATTERNS)

    added_count = 0
    for pattern, name, desc, priority, _category in patterns:
        matched_live = any(pattern.lower() in lm.lower() for lm in live_models)
        if pattern not in existing_slugs:
            new_entry = template.copy()
            new_entry["slug"] = pattern
            new_entry["display_name"] = name
            new_entry["description"] = f"{desc} [{'Live Verified' if matched_live else 'Gateway Route'}]"
            new_entry["priority"] = priority
            new_entry["visibility"] = "list"
            new_entry["model_provider"] = "omniroute"
            models_list.append(new_entry)
            existing_slugs.add(pattern)
            added_count += 1

    for m in models_list:
        m["model_provider"] = "omniroute"

    models_list.sort(key=lambda x: x.get("priority", 0), reverse=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return added_count


def update_codex_catalog(live_models: list, ollama_active: bool) -> int:
    added_omni = update_single_catalog(CODEX_OMNI_CATALOG, live_models, ollama_active)
    config_path = os.path.expanduser("~/.codex/config.toml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                c = f.read()
            c = re.sub(r'model_catalog_json\s*=\s*"[^"]*"', f'model_catalog_json = "{CODEX_OMNI_CATALOG}"', c, count=1)
            c = re.sub(r'openai_base_url\s*=\s*"[^"]*"', 'openai_base_url = "http://127.0.0.1:20128/v1"', c, count=1)
            if "model_provider =" not in c:
                c = re.sub(r'(model\s*=\s*"[^"]*"\n)', r'\1model_provider = "omniroute"\n', c, count=1)
            if "[model_providers.omniroute]" in c and "supports_websockets" not in c:
                c = re.sub(
                    r'(\[model_providers\.omniroute\][\s\S]*?requires_openai_auth\s*=\s*false)',
                    r'\1\nsupports_websockets = false',
                    c,
                    count=1,
                )
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(c)
        except Exception as e:
            print(f"[AutoUpdate] Notice updating config.toml: {e}", file=sys.stderr)
    return added_omni


def sync_cli_profiles():
    env = os.environ.copy()
    env["OMNIROUTE_API_KEY"] = OMNIROUTE_TOKEN
    env["PATH"] = f"/usr/local/bin:/opt/homebrew/bin:{env.get('PATH', '')}"
    omni_bin = "/usr/local/bin/omniroute" if os.path.exists("/usr/local/bin/omniroute") else "omniroute"
    try:
        subprocess.run([omni_bin, "setup-codex", "--api-key", OMNIROUTE_TOKEN], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([omni_bin, "setup-claude", "--api-key", OMNIROUTE_TOKEN], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[AutoUpdate] Notice syncing CLI profiles: {e}", file=sys.stderr)


def main():
    start = time.time()
    ollama_active = is_ollama_active()
    live_models = fetch_live_models()
    added_to_codex = update_codex_catalog(live_models, ollama_active) if live_models else 0
    if live_models:
        sync_cli_profiles()

    status = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_live_models": len(live_models),
        "newly_added_codex_models": added_to_codex,
        "ollama_active": ollama_active,
        "duration_sec": round(time.time() - start, 2),
        "status": "success" if live_models else "gateway_unreachable",
    }

    try:
        os.makedirs(os.path.dirname(STATUS_LOG_PATH), exist_ok=True)
        with open(STATUS_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
    except Exception:
        pass

    print(f"[AutoUpdate] Catalog sync: {len(live_models)} live models scanned, {added_to_codex} new models registered (ollama_active={ollama_active}).")


if __name__ == "__main__":
    main()
