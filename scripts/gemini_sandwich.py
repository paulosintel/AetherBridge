#!/usr/bin/env python3
"""
AetherBridge: Gemini Sandwich Architecture Engine (Direct OmniRoute Cloud-First)
Orchestrates multi-model intelligence directly through OmniRoute - AetherBridge:
- Pan Superior (Gemini): Evaluates quality vs latency trade-off, detects explicit in-chat
  model mentions, or automatically selects the optimal specialist based on complexity.
- Ingredientes Centrales (Direct Cloud Providers at $0 Cost via OmniRoute):
  Gemini 3.5 Flash / 3.1 Flash Lite, NVIDIA NIM (Nemotron 3 Ultra 550B, Gemma 4 31B),
  OpenRouter (:free), and smart Claude combos (claude-opus-5-5, claude-sonnet-5-5, claude-haiku-5-5).
  Ollama local (:11434) is strictly optional and only used if active locally.
- Pan Inferior (Gemini): Validates, audits, and formats the response transparently.
"""

import json
import os
import re
import sys
import time
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

CLOUD_RESILIENCE_TAIL = [
    "claude-sonnet-5-5",
    "gemini/gemini-3.5-flash",
    "nvidia/google/gemma-4-31b-it",
    "gemini/gemini-3.1-flash-lite",
    "openrouter/auto",
]

# Catálogo Maestro de Equivalencias Frontera (enrutado directo vía OmniRoute Cloud)
MODEL_EQUIVALENCE_CATALOG = {
    "deepseek-v4-pro": {
        "display_name": "DeepSeek V4 Pro / Nemotron 550B",
        "claude_equiv": "Claude Opus",
        "category": "reasoning_flagship",
        "description": "Razonamiento extremo, matemáticas avanzadas y programación de élite",
        "fallback_chain": [
            "cfp/deepseek-ai/deepseek-v4-pro-0813",
            "claude-opus-5-5",
            "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
            "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
            "auto/best-reasoning",
        ],
    },
    "deepseek-v4-flash": {
        "display_name": "DeepSeek V4 Flash",
        "claude_equiv": "Claude Sonnet",
        "category": "speed_coding",
        "description": "Inferencia de alta velocidad para código y depuración ágil",
        "fallback_chain": [
            "oc/deepseek-v4-flash-free",
            "cfp/deepseek-ai/deepseek-v4-flash-0731",
            "claude-sonnet-5-5",
            "gemini/gemini-3.5-flash",
        ],
    },
    "deepseek-r2": {
        "display_name": "DeepSeek R2 / Reasoning Flagship",
        "claude_equiv": "Claude Opus",
        "category": "deep_reasoning",
        "description": "Cadena de razonamiento lógico y matemático de próxima generación",
        "fallback_chain": [
            "claude-opus-5-5",
            "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
            "auto/best-reasoning",
            "gemini/gemini-3.5-flash",
        ],
    },
    "glm-5.3-flash": {
        "display_name": "GLM-5.3-Flash (Z.ai)",
        "claude_equiv": "Claude Opus 4.6",
        "category": "architecture_speed",
        "description": "Arquitectura de sistemas complejos, agentes autónomos y alta velocidad",
        "fallback_chain": [
            "nvidia/z-ai/glm-5.3-flash",
            "claude-opus-5-5",
            "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
            "gemini/gemini-3.5-flash",
        ],
    },
    "glm-5.2": {
        "display_name": "GLM-5.2 (Z.ai)",
        "claude_equiv": "Claude Opus 4.6",
        "category": "architecture",
        "description": "Macro-síntesis y razonamiento conceptual profundo",
        "fallback_chain": ["nvidia/z-ai/glm-5.3-flash", "claude-opus-5-5", "auto/best-reasoning"],
    },
    "glm-5.1": {
        "display_name": "GLM-5.1 (Z.ai)",
        "claude_equiv": "Claude Opus 4.6",
        "category": "architecture",
        "description": "Diseño estructural y análisis sistémico",
        "fallback_chain": ["claude-opus-5-5", "nvidia/google/gemma-4-31b-it"],
    },
    "kimi-k3": {
        "display_name": "Kimi K3 (Moonshot AI)",
        "claude_equiv": "Claude Sonnet / Fable",
        "category": "massive_context",
        "description": "Contexto ultra-largo, lectura de repositorios completos y fidelidad estricta",
        "fallback_chain": ["claude-sonnet-5-5", "gemini/gemini-3.5-flash", "gemini/gemini-3.1-flash-lite"],
    },
    "kimi-k2.6": {
        "display_name": "Kimi K2.6 (Moonshot AI)",
        "claude_equiv": "Claude Sonnet / Fable",
        "category": "massive_context",
        "description": "Ingesta masiva de código y documentos técnicos complejos",
        "fallback_chain": ["claude-sonnet-5-5", "gemini/gemini-3.5-flash", "gemini/gemini-3.1-flash-lite"],
    },
    "qwen-3.6-coder": {
        "display_name": "OmniRoute Elite Coding (Sonnet / Qwen / Gemma 4)",
        "claude_equiv": "Claude Sonnet",
        "category": "elite_coding",
        "description": "Programación masiva multi-archivo, refactorización y depuración profunda",
        "fallback_chain": [
            "claude-sonnet-5-5",
            "auto/best-coding",
            "nvidia/google/gemma-4-31b-it",
            "openrouter/cohere/north-mini-code:free",
        ],
    },
    "qwen-3-235b": {
        "display_name": "OmniRoute Coding & MoE",
        "claude_equiv": "Claude Sonnet",
        "category": "general_coding",
        "description": "Ingeniería multi-archivo y alta densidad de razonamiento",
        "fallback_chain": ["claude-sonnet-5-5", "auto/best-coding", "nvidia/google/gemma-4-31b-it"],
    },
    "gemini-2.5-pro": {
        "display_name": "Gemini 3.5 / 2.5 Pro",
        "claude_equiv": "Claude Opus / Sonnet",
        "category": "multimodal_reasoning",
        "description": "Multimodal nativo con 1M+ tokens de contexto y razonamiento analítico",
        "fallback_chain": ["gemini/gemini-3.5-flash", "gemini/gemini-3.1-flash-lite", "claude-opus-5-5"],
    },
    "gemini-2.5-flash": {
        "display_name": "Gemini 3.5 / 3.1 Flash",
        "claude_equiv": "Claude Haiku / Sonnet",
        "category": "speed_context",
        "description": "Hiper-velocidad multimodal con ventana de contexto masiva",
        "fallback_chain": ["gemini/gemini-3.1-flash-lite", "gemini/gemini-3.5-flash", "claude-haiku-5-5"],
    },
    "nemotron-3-ultra": {
        "display_name": "Nemotron 3 Ultra 550B (NVIDIA)",
        "claude_equiv": "Claude Opus / Sonnet",
        "category": "enterprise_engineering",
        "description": "Modelo flagship de 550B de NVIDIA vía NIM y OpenRouter",
        "fallback_chain": [
            "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
            "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
            "claude-opus-5-5",
        ],
    },
    "gpt-oss-120b": {
        "display_name": "gpt-oss-120b (Open Flagship)",
        "claude_equiv": "Claude Sonnet",
        "category": "open_flagship",
        "description": "Modelo abierto de 120B parámetros con alta competencia en programación",
        "fallback_chain": ["claude-sonnet-5-5", "nvidia/nvidia/nemotron-3-ultra-550b-a55b"],
    },
    "claude-opus-5-5": {
        "display_name": "OmniRoute Claude Opus (Nemotron 550B / Gemini)",
        "claude_equiv": "Claude Opus",
        "category": "architecture",
        "description": "Combo OmniRoute directo para arquitectura y razonamiento profundo",
        "fallback_chain": ["nvidia/nvidia/nemotron-3-ultra-550b-a55b", "gemini/gemini-3.5-flash", "openrouter/auto"],
    },
    "claude-sonnet-5-5": {
        "display_name": "OmniRoute Claude Sonnet (Gemini 3.5 / Gemma 4)",
        "claude_equiv": "Claude Sonnet",
        "category": "elite_coding",
        "description": "Combo OmniRoute directo para programación e ingeniería",
        "fallback_chain": ["gemini/gemini-3.5-flash", "nvidia/google/gemma-4-31b-it", "openrouter/auto"],
    },
    "claude-haiku-5-5": {
        "display_name": "OmniRoute Claude Haiku (Flash Lite / Lightning)",
        "claude_equiv": "Claude Haiku",
        "category": "speed",
        "description": "Combo OmniRoute directo para latencia mínima",
        "fallback_chain": ["gemini/gemini-3.1-flash-lite", "openrouter/cohere/north-mini-code:free"],
    },
}

EXPLICIT_TRIGGERS = [
    (r"\b(deepseek[-\s]?v4[-\s]?pro|v4[-\s]?pro)\b", "deepseek-v4-pro"),
    (r"\b(deepseek[-\s]?v4[-\s]?flash|v4[-\s]?flash)\b", "deepseek-v4-flash"),
    (r"\b(deepseek[-\s]?v4|v4)\b", "deepseek-v4-pro"),
    (r"\b(deepseek[-\s]?r2|r2)\b", "deepseek-r2"),
    (r"\b(glm[-\s]?5\.3[-\s]?flash|glm[-\s]?flash)\b", "glm-5.3-flash"),
    (r"\b(glm[-\s]?5\.3)\b", "glm-5.3-flash"),
    (r"\b(glm[-\s]?5\.2)\b", "glm-5.2"),
    (r"\b(glm[-\s]?5\.1)\b", "glm-5.1"),
    (r"\b(glm[-\s]?5|z\.ai|zai|zhipu)\b", "glm-5.3-flash"),
    (r"\b(kimi[-\s]?k3|k3)\b", "kimi-k3"),
    (r"\b(kimi[-\s]?k2\.6|k2\.6)\b", "kimi-k2.6"),
    (r"\b(kimi|moonshot)\b", "kimi-k3"),
    (r"\b(qwen[-\s]?3\.6[-\s]?coder|qwen[-\s]?3\.6|qwen[-\s]?coder)\b", "qwen-3.6-coder"),
    (r"\b(qwen[-\s]?3[-\s]?235b|qwen[-\s]?235b|qwen[-\s]?3)\b", "qwen-3-235b"),
    (r"\b(gemini[-\s]?2\.5[-\s]?pro|gemini[-\s]?3\.5)\b", "gemini-2.5-pro"),
    (r"\b(gemini[-\s]?2\.5[-\s]?flash|gemini[-\s]?3\.1)\b", "gemini-2.5-flash"),
    (r"\b(gemini[-\s]?2\.5)\b", "gemini-2.5-pro"),
    (r"\b(nemotron[-\s]?3[-\s]?ultra|nemotron[-\s]?ultra|nemotron[-\s]?3)\b", "nemotron-3-ultra"),
    (r"\b(nemotron)\b", "nemotron-3-ultra"),
    (r"\b(gpt[-\s]?oss[-\s]?120b|gpt[-\s]?oss)\b", "gpt-oss-120b"),
    (r"\b(claude[-\s]?opus|opus)\b", "claude-opus-5-5"),
    (r"\b(claude[-\s]?sonnet|sonnet)\b", "claude-sonnet-5-5"),
    (r"\b(claude[-\s]?haiku|haiku)\b", "claude-haiku-5-5"),
    (r"\b(deepseek[-\s]?r1|r1)\b", "deepseek-r2"),
    (r"\b(groq|cerebras|fast|lpu)\b", "claude-haiku-5-5"),
    (r"\b(ollama|offline|local)\b", "offline"),
]


def is_ollama_available() -> bool:
    tags_url = OLLAMA_URL.rsplit("/api/", 1)[0] + "/api/tags"
    try:
        with urllib.request.urlopen(urllib.request.Request(tags_url), timeout=0.6) as resp:
            return resp.status == 200
    except Exception:
        return False


def detect_explicit_mention(prompt: str):
    p_lower = prompt.lower()
    for pattern, model_id in EXPLICIT_TRIGGERS:
        m = re.search(pattern, p_lower)
        if m:
            return model_id, f"Mención explícita detectada en chat: '{m.group(0)}'"
    return None, None


def evaluate_complexity(prompt: str) -> dict:
    p_lower = prompt.lower()
    word_count = len(prompt.split())

    arch_keywords = [
        "arquitectura", "sistema distribuido", "microservicios", "escalabilidad", "alta disponibilidad",
        "concurrencia", "diseño de sistema", "patrones de diseño", "domain driven", "event driven",
        "tolerancia a fallos", "consensus", "raft", "paxos", "infraestructura", "macro", "filosofía de diseño",
        "monolito", "kubernetes", "cloud native", "diagrama de arquitectura", "auditoría estructural",
    ]
    arch_score = sum(1 for kw in arch_keywords if kw in p_lower) * 20
    if word_count > 150:
        arch_score += 15

    reasoning_keywords = [
        "prueba matemática", "demuestra", "teorema", "algoritmo complejo", "programación dinámica",
        "np-hard", "grafo", "árbol", "complejidad temporal", "complejidad espacial", "o(n", "lógica formal",
        "inducción", "paso a paso", "cadena lógica", "deducción", "ecuación diferencial", "optimización combinatoria",
        "backtracking", "criptografía", "cálculo", "análisis formal",
    ]
    reasoning_score = sum(1 for kw in reasoning_keywords if kw in p_lower) * 22

    coding_keywords = [
        "código", "función", "script", "refactor", "refactoriza", "bug", "depurar", "typescript",
        "python", "javascript", "react", "golang", "rust", "c++", "dockerfile", "api rest", "endpoint",
        "sql", "postgresql", "migration", "test unitario", "jest", "pytest", "full-stack", "backend", "frontend",
        "pull request", "lint", "asyncio", "memory leak", "stack trace",
    ]
    coding_score = sum(1 for kw in coding_keywords if kw in p_lower) * 18

    context_keywords = [
        "repositorio completo", "todos los archivos", "código base entero", "documento largo",
        "pdf masivo", "1m tokens", "2m tokens", "contexto masivo", "análisis de repositorio",
        "ingesta completa", "historial de logs", "múltiples carpetas", "auditoría del repo",
    ]
    context_score = sum(1 for kw in context_keywords if kw in p_lower) * 30

    speed_keywords = [
        "rápido", "veloz", "urgente", "resumen corto", "en una línea", "sin rodeos", "fast",
        "breve", "ultra rápido", "flash", "instantáneo", "sub-segundo", "una sola frase",
    ]
    speed_score = sum(1 for kw in speed_keywords if kw in p_lower) * 25

    scores = {
        "architecture": min(arch_score, 100),
        "reasoning": min(reasoning_score, 100),
        "coding": min(coding_score, 100),
        "context": min(context_score, 100),
        "speed": min(speed_score, 100),
    }

    max_cat = max(scores, key=scores.get)
    max_val = scores[max_cat]

    return {
        "scores": scores,
        "dominant_category": max_cat if max_val > 0 else "balanced_coding",
        "intensity": max_val,
    }


def analyze_and_route(prompt: str, mode: str = "auto") -> tuple:
    if mode != "auto":
        if mode in MODEL_EQUIVALENCE_CATALOG:
            return mode, mode, f"Modo forzado por flag: {mode}"
        alias_map = {
            "v4": "deepseek-v4-pro",
            "r2": "deepseek-r2",
            "glm5": "glm-5.3-flash",
            "glm": "glm-5.3-flash",
            "kimi": "kimi-k3",
            "qwen": "qwen-3.6-coder",
            "gemini25": "gemini-2.5-pro",
            "nemotron": "nemotron-3-ultra",
            "opus": "claude-opus-5-5",
            "sonnet": "claude-sonnet-5-5",
            "haiku": "claude-haiku-5-5",
            "speed": "claude-haiku-5-5",
            "coding": "claude-sonnet-5-5",
            "reasoning": "claude-opus-5-5",
            "architecture": "claude-opus-5-5",
            "offline": "offline",
        }
        target = alias_map.get(mode, mode)
        return mode, target, f"Modo forzado por alias: {mode} -> {target}"

    explicit_model, explicit_reason = detect_explicit_mention(prompt)
    if explicit_model:
        return "explicit_chat_mention", explicit_model, explicit_reason

    eval_res = evaluate_complexity(prompt)
    dom = eval_res["dominant_category"]

    if dom == "speed":
        return "speed", "claude-haiku-5-5", "Evaluación de Sándwich: Latencia Mínima vía OmniRoute (Flash Lite / Lightning)"
    if dom == "context":
        return "massive_context", "gemini-2.5-pro", "Evaluación de Sándwich: Contexto masivo vía Gemini / OmniRoute"
    if dom == "reasoning":
        return "deep_reasoning", "claude-opus-5-5", "Evaluación de Sándwich: Alta complejidad lógica (Nemotron 550B / Opus)"
    if dom == "architecture":
        return "architecture", "claude-opus-5-5", "Evaluación de Sándwich: Arquitectura sistémica (Nemotron 550B / Opus)"
    if dom == "coding":
        return "coding", "claude-sonnet-5-5", "Evaluación de Sándwich: Ingeniería de software (Gemini 3.5 / Gemma 4)"
    return "balanced_flagship", "claude-sonnet-5-5", "Evaluación de Sándwich: Tarea general balanceada vía OmniRoute"


def query_model(model: str, prompt: str, system: str = "") -> dict:
    start_time = time.time()

    if model == "offline" and is_ollama_available():
        candidates = []
    elif model == "offline":
        candidates = list(CLOUD_RESILIENCE_TAIL)
    elif model in MODEL_EQUIVALENCE_CATALOG:
        # Si es un combo real o modelo directo, primero su cadena y luego resiliencia cloud
        base = [model] if (model.startswith("claude-") or "/" in model) else []
        candidates = base + MODEL_EQUIVALENCE_CATALOG[model]["fallback_chain"] + CLOUD_RESILIENCE_TAIL
    else:
        candidates = [model] + CLOUD_RESILIENCE_TAIL

    # Deduplicar preservando orden
    seen = set()
    ordered_candidates = [c for c in candidates if not (c in seen or seen.add(c))]

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_error = None
    for cand in ordered_candidates:
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
                elapsed = time.time() - start_time
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    equiv_info = MODEL_EQUIVALENCE_CATALOG.get(model, {}).get(
                        "claude_equiv", "OmniRoute Direct Cloud"
                    )
                    return {
                        "success": True,
                        "model_requested": model,
                        "model_used": cand,
                        "claude_equivalence": equiv_info,
                        "elapsed_sec": round(elapsed, 3),
                        "content": content,
                        "source": "omniroute_cloud",
                    }
        except Exception as e:
            last_error = str(e)
            continue

    # Respaldo opcional a Ollama solo si está instalado y respondiendo localmente
    if is_ollama_available():
        fallback_start = time.time()
        local_model = "qwen2.5-coder:3b" if "code" in model or "coding" in model else "llama3.2:latest"
        try:
            ollama_payload = json.dumps({"model": local_model, "prompt": prompt, "stream": False}).encode("utf-8")
            o_req = urllib.request.Request(OLLAMA_URL, data=ollama_payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(o_req, timeout=120) as o_resp:
                o_data = json.loads(o_resp.read().decode("utf-8"))
                elapsed = time.time() - fallback_start
                return {
                    "success": True,
                    "model_requested": model,
                    "model_used": f"{local_model} (Ollama Local Fallback)",
                    "claude_equivalence": "Local Private Engine",
                    "elapsed_sec": round(elapsed, 3),
                    "content": o_data.get("response", ""),
                    "source": "ollama_local_fallback",
                    "upstream_notice": f"OmniRoute Cloud unavailable: {last_error}",
                }
        except Exception as o_err:
            return {
                "success": False,
                "error": f"OmniRoute falló ({last_error}) y Ollama local falló ({o_err}).",
            }

    return {
        "success": False,
        "error": f"OmniRoute no pudo responder ({last_error}). Verifica que el gateway esté activo en {OMNIROUTE_URL}.",
    }


def execute_sandwich(prompt: str, mode: str = "auto", system: str = "") -> dict:
    tier, target_model, reason = analyze_and_route(prompt, mode)
    result = query_model(target_model, prompt, system)
    result["tier"] = tier
    result["target_model"] = target_model
    result["routing_decision_reason"] = reason

    equiv = result.get("claude_equivalence", "OmniRoute Cloud")
    used = result.get("model_used", target_model)
    time_str = f"{result.get('elapsed_sec', 0)}s"
    result["transparency_banner"] = (
        f"> 🥪 **[Gemini Sandwich]** Modelo Activo: **{used}** "
        f"(Equivalencia: *{equiv}*) | Selección: *{reason}* ({time_str})"
    )
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 gemini_sandwich.py [--mode <modelo|auto|speed|coding|reasoning|architecture>] '<prompt>'")
        sys.exit(1)

    mode = "auto"
    prompt_parts = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--mode" and i + 1 < len(sys.argv):
            mode = sys.argv[i + 1]
            i += 2
        else:
            prompt_parts.append(sys.argv[i])
            i += 1

    res = execute_sandwich(" ".join(prompt_parts), mode)
    print(json.dumps(res, indent=2, ensure_ascii=False))
