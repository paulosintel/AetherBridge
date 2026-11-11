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
    ("auto/best-free", "OmniRoute Best Free (Cloud Cascade)", "Best free-tier multi-provider cascade", 132, "combo"),
    ("claude-opus-5-5", "OmniRoute Claude Opus (Nemotron 550B / Gemini)", "Flagship architectural reasoning & synthesis combo", 131, "architecture"),
    ("claude-sonnet-5-5", "OmniRoute Claude Sonnet (Gemini 3.8 / Gemma 4)", "Primary software engineering & coding combo", 130, "coding"),
    ("claude-haiku-5-5", "OmniRoute Claude Haiku (Flash Lite / Lightning)", "Sub-second lightweight cloud combo", 129, "speed"),
    ("gemini/gemini-3.8-flash", "Gemini 3.8 Flash (Google AI Studio)", "High-speed frontier coding & multimodal reasoning", 126, "coding"),
    ("gemini/gemini-3.1-pro-preview", "Gemini 3.1 Pro Preview (Google AI Studio)", "Massive context reasoning and architecture analysis", 125, "architecture"),
    ("gemini/gemini-3.1-flash-lite", "Gemini 3.1 Flash Lite (Google AI Studio)", "Instant low-latency multimodal intelligence", 124, "speed"),
    ("nvidia/nvidia/nemotron-3-ultra-550b-a55b", "Nemotron 3 Ultra 550B (NVIDIA NIM)", "NVIDIA 550B frontier reasoning and enterprise engineering", 123, "frontier"),
    ("openrouter/nvidia/nemotron-3-ultra-550b-a55b:free", "Nemotron 3 Ultra 550B (:free OpenRouter)", "Zero-cost 550B flagship via OpenRouter", 122, "frontier"),
    ("nvidia/deepseek-ai/deepseek-v4-pro-0813", "DeepSeek V4 Pro (NVIDIA NIM)", "DeepSeek V4 Pro engineering & formal reasoning", 121, "reasoning"),
    ("nvidia/moonshotai/kimi-k3", "Kimi K3 (NVIDIA NIM)", "Moonshot Kimi K3 long-context synthesis", 120, "architecture"),
    ("nvidia/google/gemma-4-31b-it", "Gemma 4 31B IT (NVIDIA NIM)", "Fast open-weights coding and reasoning model", 119, "coding"),
    ("groq/qwen/qwen3.8-27b", "Qwen 3.8 27B (Groq LPU)", "Ultra-fast Qwen 3.8 inference on Groq LPU", 118, "coding"),
    ("openrouter/cohere/north-mini-code:free", "Cohere North Mini Code (:free)", "Agile coding assistant via OpenRouter free tier", 117, "coding"),
    ("openrouter/auto", "OpenRouter Auto Router", "Automatic cloud fallback across free and open endpoints", 116, "combo"),
]

OPTIONAL_OLLAMA_PATTERNS = [
    ("qwen2.5-coder:3b", "Qwen 2.5 Coder 3B (Ollama Local)", "Local coding model", 82, "offline"),
    ("deepseek-r1:1.5b", "DeepSeek R1 1.5B (Ollama Local)", "Local chain-of-thought reasoning engine", 81, "offline"),
    ("llama3.2:latest", "Llama 3.2 (Ollama Local - Offline)", "Local private model", 80, "offline"),
]

LEGACY_OLLAMA_PREFIXES = ("ollama", "qwen2.5-coder:3b", "deepseek-r1:1.5b", "llama3.2")


def _default_codex_model_entry() -> dict:
    """Return canonical Codex ModelInfo defaults expected by model_catalog_json."""
    return {
        "additional_speed_tiers": [],
        "apply_patch_tool_type": None,
        "auto_compact_token_limit": None,
        "availability_nux": None,
        "base_instructions": (
            "You are Codex, a coding agent. You and the user share the same workspace "
            "and collaborate to achieve the user's goals."
        ),
        "context_window": 1048576,
        "default_reasoning_level": "max",
        "default_reasoning_summary": "auto",
        "default_service_tier": None,
        "default_verbosity": None,
        "description": "",
        "display_name": "",
        "effective_context_window_percent": 95,
        "experimental_supported_tools": [],
        "include_apps_usage_instructions": True,
        "include_plugin_usage_instructions": True,
        "include_skills_usage_instructions": True,
        "input_modalities": ["text", "image"],
        "max_context_window": 1048576,
        "model_messages": None,
        "model_provider": "omniroute",
        "priority": 100,
        "service_tiers": [],
        "shell_type": "unified_exec",
        "slug": "",
        "support_verbosity": False,
        "supported_in_api": True,
        "supported_reasoning_levels": [
            {"description": "Turn thinking off", "effort": "none"},
            {"description": "Fast responses with lighter thinking", "effort": "low"},
            {"description": "Greater thinking depth for complex tasks", "effort": "high"},
            {"description": "Maximum thinking depth for the hardest tasks", "effort": "max"},
        ],
        "supports_image_detail_original": False,
        "supports_parallel_tool_calls": True,
        "supports_reasoning_summaries": False,
        "supports_reasoning_summary_parameter": False,
        "supports_search_tool": True,
        "truncation_policy": {"limit": 10000, "mode": "tokens"},
        "upgrade": None,
        "visibility": "list",
        "web_search_tool_type": "text",
    }


def _ensure_omniroute_provider_block(config_text: str, token: str) -> str:
    """Ensure [model_providers.omniroute] exists with Desktop-compatible settings."""
    header = "[model_providers.omniroute]"
    default_block = (
        f"{header}\n"
        'name = "OmniRoute - AetherBridge"\n'
        'base_url = "http://127.0.0.1:20128/v1"\n'
        'wire_api = "responses"\n'
        "requires_openai_auth = false\n"
        "supports_websockets = false\n"
        f'experimental_bearer_token = "{token}"\n'
    )
    if header not in config_text:
        separator = "\n\n" if config_text and not config_text.endswith("\n\n") else ""
        if config_text.endswith("\n") and not config_text.endswith("\n\n"):
            separator = "\n"
        return f"{config_text}{separator}{default_block}"

    # Patch missing keys only inside [model_providers.omniroute] section boundaries.
    match = re.search(r"(\[model_providers\.omniroute\][\s\S]*?)(?=\n\[|\Z)", config_text)
    if not match:
        return config_text
    section = match.group(1)
    required_settings = [
        ("base_url", 'base_url = "http://127.0.0.1:20128/v1"'),
        ("wire_api", 'wire_api = "responses"'),
        ("requires_openai_auth", "requires_openai_auth = false"),
        ("supports_websockets", "supports_websockets = false"),
        ("experimental_bearer_token", f'experimental_bearer_token = "{token}"'),
    ]
    for key, line in required_settings:
        if not re.search(rf"^\s*{re.escape(key)}\s*=", section, flags=re.MULTILINE):
            section = f"{section.rstrip()}\n{line}"
    return config_text[: match.start(1)] + section + config_text[match.end(1) :]


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
    data = {"models": []}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[AutoUpdate] Error reading catalog at {path}: {e}", file=sys.stderr)
            return 0
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)

    live_set = {lm.lower() for lm in live_models}
    models_list = data.get("models", [])
    if not ollama_active:
        models_list = [
            m
            for m in models_list
            if not (
                str(m.get("slug", "")).startswith(LEGACY_OLLAMA_PREFIXES)
                or (str(m.get("slug", "")).endswith(":cloud") and str(m.get("slug", "")).lower() not in live_set)
            )
        ]
    data["models"] = models_list

    existing_slugs = {m.get("slug") for m in models_list}

    patterns = list(CLOUD_PATTERNS)
    if ollama_active:
        patterns.extend(OPTIONAL_OLLAMA_PATTERNS)

    added_count = 0
    for pattern, name, desc, priority, _category in patterns:
        matched_live = any(pattern.lower() == lm.lower() or pattern.lower() in lm.lower() for lm in live_models)
        if pattern not in existing_slugs:
            new_entry = _default_codex_model_entry()
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
            if not re.search(r"^\s*model_provider\s*=", c, flags=re.MULTILINE):
                c = re.sub(r'(model\s*=\s*"[^"]*"\n)', r'\1model_provider = "omniroute"\n', c, count=1)
            if re.search(r"^\s*model_catalog_json\s*=", c, flags=re.MULTILINE):
                c = re.sub(r'model_catalog_json\s*=\s*"[^"]*"', f'model_catalog_json = "{CODEX_OMNI_CATALOG}"', c, count=1)
            else:
                c = re.sub(r'(model_provider\s*=\s*"[^"]*"\n)', rf'\1model_catalog_json = "{CODEX_OMNI_CATALOG}"\n', c, count=1)
            c = re.sub(r'openai_base_url\s*=\s*"[^"]*"', 'openai_base_url = "http://127.0.0.1:20128/v1"', c, count=1)
            c = _ensure_omniroute_provider_block(c, OMNIROUTE_TOKEN)
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(c)
        except Exception as e:
            print(f"[AutoUpdate] Notice updating config.toml: {e}", file=sys.stderr)
    return added_omni


def sync_cli_profiles(codex_only: bool = False):
    env = os.environ.copy()
    env["OMNIROUTE_API_KEY"] = OMNIROUTE_TOKEN
    env["PATH"] = f"/usr/local/bin:/opt/homebrew/bin:{env.get('PATH', '')}"
    omni_bin = "/usr/local/bin/omniroute" if os.path.exists("/usr/local/bin/omniroute") else "omniroute"
    try:
        subprocess.run([omni_bin, "setup-codex", "--api-key", OMNIROUTE_TOKEN], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not codex_only:
            subprocess.run([omni_bin, "setup-claude", "--api-key", OMNIROUTE_TOKEN], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[AutoUpdate] Notice syncing CLI profiles: {e}", file=sys.stderr)


def main():
    start = time.time()
    codex_only = "--codex-only" in sys.argv[1:]
    ollama_active = is_ollama_active()
    live_models = fetch_live_models()
    added_to_codex = update_codex_catalog(live_models, ollama_active) if live_models else 0
    if live_models:
        sync_cli_profiles(codex_only=codex_only)

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
