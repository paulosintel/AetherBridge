---
name: omniroute-council
description: >-
  Sandwich Architecture & Multi-Model Council: Gemini acts as the orchestrator bread,
  intelligently delegating to the world's most powerful frontier models (Claude Opus,
  Claude Sonnet, DeepSeek R1, Groq LPU, Gemini 2.0 Pro) based on quality vs latency trade-offs.
---

# Gemini Sandwich Architecture & OmniRoute Multi-Model Council

This skill implements the **Sandwich Protocol**:
- **Top Bread (Gemini)**: Analyzes user intent, determines whether quality or latency is paramount, and selects the optimal specialist ingredient.
- **Middle Ingredient (OmniRoute 1000+ Models)**: Specialized frontier model executes computation at $0 cost.
- **Bottom Bread (Gemini)**: Validates correctness, refines implementation, and presents the final solution.

## Decision Matrix (Quality vs Latency)

| Tarea / Objetivo | Modelo Ingrediente Óptimo | Ventaja Clave |
| :--- | :--- | :--- |
| **Velocidad Extrema / Inferencia Inmediata** | Groq / Cerebras (`auto/fast`) | Sub-250ms con chips LPU dedicados (1000+ tok/s). |
| **Código Complejo, Refactor y Depuración** | Claude 3.7 / 3.5 Sonnet (`auto/claude-sonnet`) | Máxima puntuación en benchmarks de ingeniería de software. |
| **Razonamiento Matemático & Algorítmico** | DeepSeek R1 (`deepseek-r1` / `auto/best-reasoning`) | Cadena de pensamiento profunda sin restricciones. |
| **Arquitectura de Sistemas y Estrategia** | Claude Opus (`auto/claude-opus`) | Síntesis conceptual y visión global de sistemas. |
| **Ingesta de Documentos Masivos (1M tokens)** | Gemini 3.1 Flash Lite / 2.0 Pro (`gemini/gemini-3.1-flash-lite`) | Ventana de contexto colosal con coste cero. |
| **Código Local Privado (Apple Silicon M2)** | Ollama Local (`qwen2.5-coder:3b`) | 42 tok/s en local, especialista en código sin internet. |
| **Razonamiento Lógico Local (Apple Silicon M2)** | Ollama Local (`deepseek-r1:1.5b`) | 75 tok/s en local, cadena de pensamiento `<think>`. |
| **Sin Conexión a Internet / Respaldo General** | Ollama Local (`llama3.2:latest`) | 100% privado en hardware local. |

## Ejecución del Sándwich

Para ejecutar una consulta delegada con métricas de tiempo y selección automática:

```bash
python3 scripts/gemini_sandwich.py --mode auto "<prompt>"
```

O forzar un modo específico:
- `--mode speed`
- `--mode coding`
- `--mode reasoning`
- `--mode architecture`
- `--mode offline`

## Auto-Actualización
El catálogo se sincroniza automáticamente cada 6 horas con el demonio de macOS:
`~/Library/LaunchAgents/com.omniroute.autoupdate.plist`
