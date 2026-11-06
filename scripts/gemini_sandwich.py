#!/usr/bin/env python3
"""
AetherBridge: Gemini Sandwich Architecture Engine (Next-Gen Multi-Model Council)
Orchestrates multi-model intelligence:
- Pan Superior (Gemini): Evaluates quality vs latency trade-off, detects explicit in-chat model mentions,
  or automatically selects the optimal specialist based on task complexity.
- Ingredientes Centrales (Frontier Titans at $0 Cost):
  1. DeepSeek V4 (Pro / Flash) & R2 -> Equivalencia: Claude Opus / Sonnet
  2. GLM-5.1 / 5.2 / 5.3-Flash (Z.ai) -> Equivalencia: Claude Opus 4.6
  3. Kimi K3 / K2.6 (Moonshot AI) -> Equivalencia: Claude Sonnet / Fable
  4. Qwen 3 / 3.6 (235B MoE & Coder) -> Equivalencia: Claude Sonnet
  5. Gemini 2.5 Pro / Flash -> Equivalencia: Claude Opus / Sonnet
  6. Nemotron 3 Ultra / gpt-oss-120b -> Equivalencia: Claude Sonnet
  Plus: Claude 3.7 / 3.5 Sonnet, Claude Opus, Groq LPU, and Ollama Local (M2).
- Pan Inferior (Gemini): Validates, audits, and formats the response transparently.
"""

import sys
import json
import time
import re
import urllib.request
import os
import urllib.error

OMNIROUTE_URL = os.environ.get("OMNIROUTE_URL", "http://127.0.0.1:20128/v1/chat/completions")
OMNIROUTE_TOKEN = os.environ.get("OMNIROUTE_API_KEY", os.environ.get("OMNIROUTE_LOCAL_TOKEN", "omniroute-secret-key-local"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")

# Catálogo Maestro de Equivalencias Frontera
MODEL_EQUIVALENCE_CATALOG = {
    # 1. DeepSeek V4 & R2
    "deepseek-v4-pro": {
        "display_name": "DeepSeek V4 Pro",
        "claude_equiv": "Claude Opus / Sonnet",
        "category": "reasoning_flagship",
        "description": "Razonamiento extremo, matemáticas avanzadas y programación de élite",
        "fallback_chain": ["deepseek-v4", "deepseek-r2", "deepseek-r1", "auto/claude-opus", "auto/best-reasoning"]
    },
    "deepseek-v4-flash": {
        "display_name": "DeepSeek V4 Flash",
        "claude_equiv": "Claude Sonnet",
        "category": "speed_coding",
        "description": "Inferencia de alta velocidad para código y depuración ágil",
        "fallback_chain": ["deepseek-v4", "auto/claude-sonnet", "auto/fast", "auto/best-coding"]
    },
    "deepseek-r2": {
        "display_name": "DeepSeek R2",
        "claude_equiv": "Claude Opus / Sonnet",
        "category": "deep_reasoning",
        "description": "Cadena de razonamiento lógico y matemático de próxima generación",
        "fallback_chain": ["deepseek-r1", "auto/best-reasoning", "auto/claude-opus"]
    },

    # 2. GLM Family (Z.ai / Zhipu AI)
    "glm-5.3-flash": {
        "display_name": "GLM-5.3-Flash (Z.ai)",
        "claude_equiv": "Claude Opus 4.6",
        "category": "architecture_speed",
        "description": "Arquitectura de sistemas complejos, agentes autónomos y alta velocidad",
        "fallback_chain": ["glm-5.2", "glm-5.1", "auto/claude-opus", "gemini/gemini-3.1-flash-lite"]
    },
    "glm-5.2": {
        "display_name": "GLM-5.2 (Z.ai)",
        "claude_equiv": "Claude Opus 4.6",
        "category": "architecture",
        "description": "Macro-síntesis y razonamiento conceptual profundo",
        "fallback_chain": ["glm-5.3-flash", "auto/claude-opus", "auto/best-reasoning"]
    },
    "glm-5.1": {
        "display_name": "GLM-5.1 (Z.ai)",
        "claude_equiv": "Claude Opus 4.6",
        "category": "architecture",
        "description": "Diseño estructural y análisis sistémico",
        "fallback_chain": ["glm-5.2", "auto/claude-opus"]
    },

    # 3. Kimi Moonshot AI
    "kimi-k3": {
        "display_name": "Kimi K3 (Moonshot AI)",
        "claude_equiv": "Claude Sonnet / Fable",
        "category": "massive_context",
        "description": "Contexto ultra-largo, lectura de repositorios completos y fidelidad estricta",
        "fallback_chain": ["kimi-k2.6", "claude-3-5-sonnet-latest", "gemini/gemini-3.1-flash-lite"]
    },
    "kimi-k2.6": {
        "display_name": "Kimi K2.6 (Moonshot AI)",
        "claude_equiv": "Claude Sonnet / Fable",
        "category": "massive_context",
        "description": "Ingesta masiva de código y documentos técnicos complejos",
        "fallback_chain": ["kimi-k3", "claude-3-5-sonnet-latest", "gemini/gemini-3.1-flash-lite"]
    },

    # 4. Qwen 3 / 3.6 MoE & Coder
    "qwen-3.6-coder": {
        "display_name": "Qwen 3.6 Coder (235B MoE)",
        "claude_equiv": "Claude Sonnet",
        "category": "elite_coding",
        "description": "Programación masiva multi-archivo, refactorización y depuración profunda",
        "fallback_chain": ["qwen-3-235b", "qwen-2.5-coder-32b", "claude-3-5-sonnet-latest", "auto/best-coding"]
    },
    "qwen-3-235b": {
        "display_name": "Qwen 3 (235B MoE)",
        "claude_equiv": "Claude Sonnet",
        "category": "general_coding",
        "description": "Modelo MoE general de 235B parámetros con alta densidad de razonamiento",
        "fallback_chain": ["qwen-3.6-coder", "claude-3-5-sonnet-latest", "auto/best-coding"]
    },

    # 5. Gemini 2.5 Pro / Flash
    "gemini-2.5-pro": {
        "display_name": "Gemini 2.5 Pro",
        "claude_equiv": "Claude Opus / Sonnet",
        "category": "multimodal_reasoning",
        "description": "Multimodal nativo con más de 2M tokens de contexto y razonamiento analítico",
        "fallback_chain": ["gemini-2.0-pro", "gemini/gemini-3.1-flash-lite", "auto/claude-opus"]
    },
    "gemini-2.5-flash": {
        "display_name": "Gemini 2.5 Flash",
        "claude_equiv": "Claude Sonnet",
        "category": "speed_context",
        "description": "Hiper-velocidad multimodal, latencia sub-segundo con ventana masiva",
        "fallback_chain": ["gemini-2.0-flash", "gemini/gemini-3.1-flash-lite", "auto/fast"]
    },

    # 6. Nemotron 3 Ultra / gpt-oss-120b
    "nemotron-3-ultra": {
        "display_name": "Nemotron 3 Ultra (NVIDIA AI)",
        "claude_equiv": "Claude Sonnet",
        "category": "enterprise_engineering",
        "description": "Alineación de código empresarial y rendimiento ultra-optimizado",
        "fallback_chain": ["gpt-oss-120b", "claude-3-5-sonnet-latest", "auto/best-coding"]
    },
    "gpt-oss-120b": {
        "display_name": "gpt-oss-120b (Open Flagship)",
        "claude_equiv": "Claude Sonnet",
        "category": "open_flagship",
        "description": "Modelo abierto de 120B parámetros con alta competencia en programación",
        "fallback_chain": ["nemotron-3-ultra", "auto/best-coding", "claude-3-5-sonnet-latest"]
    }
}

# Explicit Chat Mention Regex Patterns
EXPLICIT_TRIGGERS = [
    # DeepSeek V4 Pro / Flash / R2
    (r"\b(deepseek[-\s]?v4[-\s]?pro|v4[-\s]?pro)\b", "deepseek-v4-pro"),
    (r"\b(deepseek[-\s]?v4[-\s]?flash|v4[-\s]?flash)\b", "deepseek-v4-flash"),
    (r"\b(deepseek[-\s]?v4|v4)\b", "deepseek-v4-pro"),
    (r"\b(deepseek[-\s]?r2|r2)\b", "deepseek-r2"),

    # GLM 5.1 / 5.2 / 5.3-Flash (Z.ai)
    (r"\b(glm[-\s]?5\.3[-\s]?flash|glm[-\s]?flash)\b", "glm-5.3-flash"),
    (r"\b(glm[-\s]?5\.3)\b", "glm-5.3-flash"),
    (r"\b(glm[-\s]?5\.2)\b", "glm-5.2"),
    (r"\b(glm[-\s]?5\.1)\b", "glm-5.1"),
    (r"\b(glm[-\s]?5|z\.ai|zai|zhipu)\b", "glm-5.3-flash"),

    # Kimi Moonshot AI
    (r"\b(kimi[-\s]?k3|k3)\b", "kimi-k3"),
    (r"\b(kimi[-\s]?k2\.6|k2\.6)\b", "kimi-k2.6"),
    (r"\b(kimi|moonshot)\b", "kimi-k3"),

    # Qwen 3 / 3.6 MoE & Coder
    (r"\b(qwen[-\s]?3\.6[-\s]?coder|qwen[-\s]?3\.6|qwen[-\s]?coder)\b", "qwen-3.6-coder"),
    (r"\b(qwen[-\s]?3[-\s]?235b|qwen[-\s]?235b|qwen[-\s]?3)\b", "qwen-3-235b"),

    # Gemini 2.5 Pro / Flash
    (r"\b(gemini[-\s]?2\.5[-\s]?pro)\b", "gemini-2.5-pro"),
    (r"\b(gemini[-\s]?2\.5[-\s]?flash)\b", "gemini-2.5-flash"),
    (r"\b(gemini[-\s]?2\.5)\b", "gemini-2.5-pro"),

    # Nemotron 3 Ultra / gpt-oss-120b
    (r"\b(nemotron[-\s]?3[-\s]?ultra|nemotron[-\s]?ultra|nemotron[-\s]?3)\b", "nemotron-3-ultra"),
    (r"\b(nemotron)\b", "nemotron-3-ultra"),
    (r"\b(gpt[-\s]?oss[-\s]?120b|gpt[-\s]?oss)\b", "gpt-oss-120b"),

    # Classical Mentions
    (r"\b(claude[-\s]?opus|opus)\b", "auto/claude-opus"),
    (r"\b(claude[-\s]?sonnet|sonnet)\b", "claude-3-5-sonnet-latest"),
    (r"\b(deepseek[-\s]?r1|r1)\b", "deepseek-r1"),
    (r"\b(groq|cerebras|fast|lpu)\b", "auto/fast"),
    (r"\b(ollama|offline|local)\b", "llama3.2:latest")
]

def detect_explicit_mention(prompt: str):
    """Detecta si el usuario solicitó explícitamente un modelo en el chat."""
    p_lower = prompt.lower()
    for pattern, model_id in EXPLICIT_TRIGGERS:
        m = re.search(pattern, p_lower)
        if m:
            matched_text = m.group(0)
            return model_id, f"Mención explícita detectada en chat: '{matched_text}'"
    return None, None

def evaluate_complexity(prompt: str) -> dict:
    """
    Evalúa la complejidad semántica y técnica del prompt en 5 dimensiones.
    Retorna métricas y el nivel de complejidad dominante.
    """
    p_lower = prompt.lower()
    word_count = len(prompt.split())

    # 1. Dimensión Arquitectura de Sistemas & Macro-Síntesis (Claude Opus 4.6 / GLM-5.3 / DeepSeek V4)
    arch_keywords = [
        "arquitectura", "sistema distribuido", "microservicios", "escalabilidad", "alta disponibilidad",
        "concurrencia", "diseño de sistema", "patrones de diseño", "domain driven", "event driven",
        "tolerancia a fallos", "consensus", "raft", "paxos", "infraestructura", "macro", "filosofía de diseño",
        "monolito", "kubernetes", "cloud native", "diagrama de arquitectura", "auditoría estructural"
    ]
    arch_score = sum(1 for kw in arch_keywords if kw in p_lower) * 20
    if word_count > 150:
        arch_score += 15

    # 2. Dimensión Razonamiento Lógico Profundo & Matemáticas (DeepSeek R2 / DeepSeek V4 Pro)
    reasoning_keywords = [
        "prueba matemática", "demuestra", "teorema", "algoritmo complejo", "programación dinámica",
        "np-hard", "grafo", "árbol", "complejidad temporal", "complejidad espacial", "o(n", "lógica formal",
        "inducción", "paso a paso", "cadena lógica", "deducción", "ecuación diferencial", "optimización combinatoria",
        "backtracking", "criptografía", "cálculo", "análisis formal"
    ]
    reasoning_score = sum(1 for kw in reasoning_keywords if kw in p_lower) * 22

    # 3. Dimensión Ingeniería de Software & Código Completo (Qwen 3.6 Coder / Nemotron 3 Ultra / Sonnet)
    coding_keywords = [
        "código", "función", "script", "refactor", "refactoriza", "bug", "depurar", "typescript",
        "python", "javascript", "react", "golang", "rust", "c++", "dockerfile", "api rest", "endpoint",
        "sql", "postgresql", "migration", "test unitario", "jest", "pytest", "full-stack", "backend", "frontend",
        "pull request", "lint", "asyncio", "memory leak", "stack trace"
    ]
    coding_score = sum(1 for kw in coding_keywords if kw in p_lower) * 18

    # 4. Dimensión Contexto Masivo & Repositorios (Gemini 2.5 Pro / Kimi K3)
    context_keywords = [
        "repositorio completo", "todos los archivos", "código base entero", "documento largo",
        "pdf masivo", "1m tokens", "2m tokens", "contexto masivo", "análisis de repositorio",
        "ingesta completa", "historial de logs", "múltiples carpetas", "auditoría del repo"
    ]
    context_score = sum(1 for kw in context_keywords if kw in p_lower) * 30

    # 5. Dimensión Velocidad & Inferencia Flash (Gemini 2.5 Flash / GLM-5.3-Flash / Groq)
    speed_keywords = [
        "rápido", "veloz", "urgente", "resumen corto", "en una línea", "sin rodeos", "fast",
        "breve", "ultra rápido", "flash", "instantáneo", "sub-segundo", "una sola frase"
    ]
    speed_score = sum(1 for kw in speed_keywords if kw in p_lower) * 25

    # 6. Offline / Privacidad
    offline_keywords = ["offline", "sin internet", "local", "privado", "m2", "apple silicon"]
    offline_score = sum(1 for kw in offline_keywords if kw in p_lower) * 35

    scores = {
        "architecture": min(arch_score, 100),
        "reasoning": min(reasoning_score, 100),
        "coding": min(coding_score, 100),
        "context": min(context_score, 100),
        "speed": min(speed_score, 100),
        "offline": min(offline_score, 100)
    }

    # Determinar ganador por complejidad
    max_cat = max(scores, key=scores.get)
    max_val = scores[max_cat]

    return {
        "scores": scores,
        "dominant_category": max_cat if max_val > 0 else "balanced_coding",
        "intensity": max_val
    }

def analyze_and_route(prompt: str, mode: str = "auto") -> tuple:
    """
    Decide el ingrediente óptimo del Sándwich:
    1. Si mode != 'auto', respeta el modo forzado.
    2. Si el usuario menciona explícitamente un modelo en el chat, lo activa de inmediato.
    3. Si no, evalúa la complejidad multidimensional y asigna el campeón correspondiente.
    """
    # 1. Modo Forzado
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
            "speed": "gemini-2.5-flash",
            "coding": "qwen-3.6-coder",
            "reasoning": "deepseek-r2",
            "architecture": "glm-5.3-flash",
            "offline": "llama3.2:latest"
        }
        target = alias_map.get(mode, mode)
        return mode, target, f"Modo forzado por alias: {mode} -> {target}"

    # 2. Detección de Mención Explícita en el Chat
    explicit_model, explicit_reason = detect_explicit_mention(prompt)
    if explicit_model:
        return "explicit_chat_mention", explicit_model, explicit_reason

    # 3. Decisión Autónoma por Complejidad (Sándwich Gemini)
    eval_res = evaluate_complexity(prompt)
    dom = eval_res["dominant_category"]

    if dom == "offline":
        return "offline", "llama3.2:latest", "Evaluación de Sándwich: Solicitud de ejecución offline/privada"
    elif dom == "speed":
        return "speed", "gemini-2.5-flash", "Evaluación de Sándwich: Prioridad Latencia Mínima / Respuesta Instantánea"
    elif dom == "context":
        return "massive_context", "gemini-2.5-pro", "Evaluación de Sándwich: Ingesta de contexto masivo / repositorio"
    elif dom == "reasoning":
        return "deep_reasoning", "deepseek-r2", "Evaluación de Sándwich: Alta complejidad lógica y matemática (DeepSeek R2)"
    elif dom == "architecture":
        return "architecture", "glm-5.3-flash", "Evaluación de Sándwich: Alta complejidad de arquitectura sistémica (GLM-5.3 / Opus 4.6)"
    elif dom == "coding":
        return "coding", "qwen-3.6-coder", "Evaluación de Sándwich: Ingeniería de software y código complejo (Qwen 3.6 Coder 235B)"
    else:
        # Por defecto balanceado: Código de élite con Claude Sonnet / Qwen Coder
        return "balanced_flagship", "qwen-3.6-coder", "Evaluación de Sándwich: Tarea general balanceada de alto nivel"

def query_model(model: str, prompt: str, system: str = "") -> dict:
    """Envía la consulta a OmniRoute con tolerancia a fallos y fallback en cascada."""
    start_time = time.time()
    
    # Preparar lista de candidatos (modelo primario + fallbacks)
    candidates = [model]
    if model in MODEL_EQUIVALENCE_CATALOG:
        candidates.extend(MODEL_EQUIVALENCE_CATALOG[model]["fallback_chain"])
    else:
        candidates.extend(["claude-3-5-sonnet-latest", "gemini/gemini-3.1-flash-lite", "auto/best-coding"])

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
            with urllib.request.urlopen(req, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
                elapsed = time.time() - start_time
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    equiv_info = MODEL_EQUIVALENCE_CATALOG.get(cand, {}).get("claude_equiv", "Frontier Standard")
                    return {
                        "success": True,
                        "model_requested": model,
                        "model_used": cand,
                        "claude_equivalence": equiv_info,
                        "elapsed_sec": round(elapsed, 3),
                        "content": content,
                        "source": "omniroute_cloud"
                    }
        except Exception as e:
            last_error = str(e)
            continue

    # Fallback final a Ollama local
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
                "upstream_notice": f"OmniRoute Cloud unavailable: {last_error}"
            }
    except Exception as o_err:
        return {
            "success": False,
            "error": f"Ambos OmniRoute y Ollama fallaron. Nube: {last_error} / Local: {o_err}"
        }

def execute_sandwich(prompt: str, mode: str = "auto", system: str = "") -> dict:
    """Ejecuta el pipeline sándwich de 3 etapas con auditoría de Gemini."""
    tier, target_model, reason = analyze_and_route(prompt, mode)
    result = query_model(target_model, prompt, system)
    result["tier"] = tier
    result["target_model"] = target_model
    result["routing_decision_reason"] = reason

    # Banner descriptivo de transparencia AetherBridge
    equiv = result.get("claude_equivalence", "Claude Frontier")
    used = result.get("model_used", target_model)
    time_str = f"{result.get('elapsed_sec', 0)}s"
    banner = f"> 🥪 **[Gemini Sandwich]** Modelo Activo: **{used}** (Equivalencia: *{equiv}*) | Selección: *{reason}* ({time_str})"
    result["transparency_banner"] = banner
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

    prompt = " ".join(prompt_parts)
    res = execute_sandwich(prompt, mode)
    print(json.dumps(res, indent=2, ensure_ascii=False))
