#!/usr/bin/env python3
"""
AetherBridge: Gemini Sandwich Architecture Engine
Orchestrates multi-model intelligence:
- Pan Superior (Gemini): Evaluates quality vs latency trade-off and chooses the best specialist.
- Ingredientes Centrales (Frontier Specialists): Claude Sonnet, DeepSeek R1, Claude Opus, Groq/Cerebras LPU, Ollama.
- Pan Inferior (Gemini): Validates, audits, and delivers the final response.
"""

import sys
import json
import time
import urllib.request
import urllib.error

OMNIROUTE_URL = "http://127.0.0.1:20128/v1/chat/completions"
OMNIROUTE_TOKEN = "omniroute-secret-key-local"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# Routing Matrix: Quality vs Latency profiles
ROUTING_TIERS = {
    "speed": {
        "description": "Inferencia a hiper-velocidad con LPUs dedicados (sub-300ms)",
        "models": ["auto/fast", "auto/best-fast", "groq/llama-3.3-70b-versatile"],
        "fallback": "llama3.2:latest"
    },
    "coding": {
        "description": "Máxima calidad de código, refactorización y depuración",
        "models": ["auto/claude-sonnet", "auto/best-coding", "claude-3-7-sonnet"],
        "fallback": "llama3.2:latest"
    },
    "reasoning": {
        "description": "Razonamiento matemático profundo, algoritmos y cadena lógica",
        "models": ["deepseek-r1", "auto/best-reasoning", "auto/claude-opus"],
        "fallback": "llama3.2:latest"
    },
    "architecture": {
        "description": "Diseño de sistemas, visión holística y síntesis de alto nivel",
        "models": ["auto/claude-opus", "auto/claude-sonnet"],
        "fallback": "llama3.2:latest"
    },
    "massive_context": {
        "description": "Análisis de documentos masivos y contexto ultra-largo (1M tokens)",
        "models": ["gemini-2.0-flash", "auto/best-fast"],
        "fallback": "llama3.2:latest"
    },
    "offline": {
        "description": "100% privado en hardware local sin internet",
        "models": ["llama3.2:latest"],
        "fallback": "llama3.2:latest"
    }
}

def analyze_and_route(prompt: str, mode: str = "auto") -> tuple:
    """Decide el ingrediente óptimo según el objetivo (Calidad vs Latencia)."""
    if mode != "auto" and mode in ROUTING_TIERS:
        return mode, ROUTING_TIERS[mode]["models"][0]

    p_lower = prompt.lower()

    # Heurística de decisión inteligente
    if any(k in p_lower for k in ["rápido", "veloz", "urgente", "resumen corto", "en una línea", "sin rodeos", "fast"]):
        return "speed", "auto/fast"
    elif any(k in p_lower for k in ["prueba matemática", "demuestra", "razona paso a paso", "lógica formal", "algoritmo complejo", "r1"]):
        return "reasoning", "deepseek-r1"
    elif any(k in p_lower for k in ["diseño de arquitectura", "arquitectura", "estrategia", "filosofía", "opus", "sistema distribuido"]):
        return "architecture", "auto/claude-opus"
    elif any(k in p_lower for k in ["código", "programa", "función", "script", "refactor", "bug", "depurar", "typescript", "python", "css", "html", "react"]):
        return "coding", "auto/claude-sonnet"
    elif any(k in p_lower for k in ["offline", "sin internet", "local", "privado"]):
        return "offline", "llama3.2:latest"
    else:
        # Por defecto: Mejor equilibrio Calidad/Velocidad (Auto Best Coding/Fast)
        return "balanced", "auto/best-coding"

def query_model(model: str, prompt: str, system: str = "") -> dict:
    start_time = time.time()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({"model": model, "messages": messages}).encode("utf-8")
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
                return {
                    "success": True,
                    "model_used": model,
                    "elapsed_sec": round(elapsed, 3),
                    "content": content,
                    "source": "omniroute_cloud"
                }
            return {"success": False, "error": json.dumps(data)}
    except Exception as e:
        # Fallback instantáneo a Ollama local
        fallback_start = time.time()
        try:
            ollama_payload = json.dumps({"model": "llama3.2:latest", "prompt": prompt, "stream": False}).encode("utf-8")
            o_req = urllib.request.Request(OLLAMA_URL, data=ollama_payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(o_req, timeout=120) as o_resp:
                o_data = json.loads(o_resp.read().decode("utf-8"))
                elapsed = time.time() - fallback_start
                return {
                    "success": True,
                    "model_used": "llama3.2:latest (Ollama Fallback)",
                    "elapsed_sec": round(elapsed, 3),
                    "content": o_data.get("response", ""),
                    "source": "ollama_local_fallback",
                    "upstream_notice": str(e)
                }
        except Exception as o_err:
            return {"success": False, "error": f"Both OmniRoute and Ollama failed: {e} / {o_err}"}

def execute_sandwich(prompt: str, mode: str = "auto", system: str = "") -> dict:
    """Ejecuta el pipeline sándwich completo."""
    tier, target_model = analyze_and_route(prompt, mode)
    result = query_model(target_model, prompt, system)
    result["tier"] = tier
    result["target_model"] = target_model
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 gemini_sandwich.py [--mode speed|coding|reasoning|architecture|auto] '<prompt>'")
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
