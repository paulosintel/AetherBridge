---
name: omniroute-council
description: >-
  Sandwich Architecture & Multi-Model Council: Gemini acts as the orchestrator bread,
  intelligently delegating to the world's most powerful frontier models (DeepSeek V4/R2,
  GLM-5.3, Kimi K3, Qwen 3.6 Coder, Gemini 2.5 Pro/Flash, Nemotron 3 Ultra, Claude Opus/Sonnet, Groq LPU)
  either via explicit in-chat model mention or dynamic complexity assessment.
---

# Gemini Sandwich Architecture & OmniRoute Multi-Model Council

This skill implements the **Sandwich Protocol** across **Codex, Antigravity IDE, and Claude CLI**:
- **Pan Superior (Gemini)**: Analiza el prompt y objetivo del usuario con doble método de activación:
  1. **Mención Explícita en el Chat**: Si el usuario menciona el modelo deseado en su consulta (ej. *"usa kimi k3"*, *"con deepseek v4"*, *"glm 5.3 flash"*, *"qwen 3.6 coder"*, *"gemini 2.5 pro"*, *"nemotron ultra"*), el sistema lo activa inmediatamente.
  2. **Decisión Autónoma por Complejidad**: Si no se especifica, Gemini evalúa la complejidad multidimensional (arquitectura, lógica matemática, ingeniería de software, tamaño de contexto, velocidad) y asigna el especialista de mayor rendimiento.
- **Ingrediente Central (Modelos Titanes a Costo $0)**: Ejecuta la computación en el modelo seleccionado vía OmniRoute o nodo local Ollama.
- **Pan Inferior (Gemini)**: Valida la corrección, audita restricciones del proyecto y entrega el resultado con el banner de transparencia obligatorio.

---

## 🏛️ Matriz Maestra de Modelos y Equivalencias Claude

| Modelo Titán | Equivalencia en Claude | Especialidad Técnica Primaria | Activador en Chat |
| :--- | :--- | :--- | :--- |
| **DeepSeek V4 (Pro / Flash) y R2** | **Claude Opus / Sonnet** | Razonamiento matemático extremo, lógica formal profunda y coding de élite | `"deepseek v4"`, `"v4 pro"`, `"v4 flash"`, `"deepseek r2"`, `"r2"` |
| **GLM-5.1 / 5.2 / 5.3-Flash (Z.ai)** | **Claude Opus 4.6** | Macro-arquitectura de sistemas complejos, agentes autónomos y síntesis | `"glm 5"`, `"glm 5.1"`, `"glm 5.2"`, `"glm 5.3 flash"`, `"z.ai"` |
| **Kimi K3 / K2.6 (Moonshot AI)** | **Claude Sonnet / Fable** | Contexto ultra-largo, razonamiento de repositorios completos y comprensión técnica | `"kimi"`, `"kimi k3"`, `"kimi k2.6"`, `"moonshot"` |
| **Qwen 3 / 3.6 (235B MoE y Coder)** | **Claude Sonnet** | Programación masiva multi-archivo, refactorización y depuración profunda | `"qwen 3"`, `"qwen 3.6"`, `"qwen coder"`, `"qwen 235b"` |
| **Gemini 2.5 Pro / Flash** | **Claude Opus / Sonnet** | Multimodal nativo con 2M+ tokens de contexto y latencia sub-segundo | `"gemini 2.5"`, `"gemini 2.5 pro"`, `"gemini 2.5 flash"` |
| **Nemotron 3 Ultra / gpt-oss-120b** | **Claude Sonnet** | Rendimiento ultra-optimizado de NVIDIA y alineación de código empresarial | `"nemotron 3"`, `"nemotron ultra"`, `"gpt-oss-120b"` |
| **Claude 3.7 / 3.5 Sonnet** | **Claude Sonnet (Nativo)** | Ingeniería de software y refactorización de código de máxima precisión | `"sonnet"`, `"claude sonnet"` |
| **Claude 3 Opus** | **Claude Opus (Nativo)** | Filosofía de diseño, arquitectura conceptual y síntesis holística | `"opus"`, `"claude opus"` |
| **Groq / Cerebras LPU** | **Ultra-Fast Engine** | Inferencia sub-250ms a +1,000 tokens/segundo | `"fast"`, `"groq"`, `"lpu"` |
| **Ollama Local (M2)** | **Local Private Engine** | `qwen2.5-coder:3b` (42 tok/s) y `deepseek-r1:1.5b` (75 tok/s con `<think>`) | `"local"`, `"offline"`, `"coder local"` |

---

## 🎯 Doble Modo de Activación en Chat

### 1. Activación por Mención Directa
Escribe naturalmente en cualquier chat de Antigravity, Claude CLI o Codex:
- *"Usa **Kimi K3** para leer todo este repositorio y mapear dependencias."*
- *"Resuelve este algoritmo NP-Hard paso a paso con **DeepSeek R2**."*
- *"Diseña la arquitectura de microservicios distribuida con **GLM 5.3 Flash**."*
- *"Refactoriza estos controladores de NestJS con **Qwen 3.6 Coder**."*
- *"Analiza este documento extenso multimodal con **Gemini 2.5 Pro**."*
- *"Optimiza este pipeline concurrente en Go usando **Nemotron 3 Ultra**."*

### 2. Activación Automática por Complejidad (Sándwich Gemini)
Cuando el usuario envía una tarea sin mencionar modelo, el motor `gemini_sandwich.py` evalúa:
1. **Complejidad Arquitectónica & Macro:** Enruta a **GLM-5.3-Flash (Claude Opus 4.6 equiv)** o **DeepSeek V4 Pro**.
2. **Complejidad Lógica & Matemática Pura:** Enruta a **DeepSeek R2 (Claude Opus equiv)** o **DeepSeek R1**.
3. **Ingeniería de Software & Código Complejo:** Enruta a **Qwen 3.6 Coder 235B MoE (Claude Sonnet equiv)** o **Nemotron 3 Ultra**.
4. **Contexto Masivo & Repositorios Grandes:** Enruta a **Gemini 2.5 Pro** o **Kimi K3**.
5. **Velocidad Extrema & Tareas Breves:** Enruta a **Gemini 2.5 Flash** o **Groq LPU**.
6. **Privacidad / Sin Conexión:** Enruta a **Ollama Local**.

---

## 💻 Consumo en Clientes de Desarrollo

### En Antigravity IDE:
- Vía herramientas MCP: `sandwich_orchestration`, `ask_deepseek_v4_r2`, `ask_glm_family`, `ask_kimi_moonshot`, `ask_qwen_3_coder`, `ask_gemini_2_5`, `ask_nemotron_ultra`.
- Vía terminal / scripts:
  ```bash
  python3 scripts/gemini_sandwich.py --mode auto "<tu prompt>"
  python3 scripts/aether_consult.py -m v4 "<tu prompt>"
  python3 scripts/aether_consult.py -m kimi "<tu prompt>"
  python3 scripts/aether_consult.py -m glm5 "<tu prompt>"
  python3 scripts/aether_consult.py -m qwen3 "<tu prompt>"
  python3 scripts/aether_consult.py -m gemini25 "<tu prompt>"
  python3 scripts/aether_consult.py -m nemotron "<tu prompt>"
  ```

### En Codex CLI / IDE:
- Los modelos quedan automáticamente indexados en `~/.codex/omniroute-launch-models.json`.
- Seleccionables con `--model deepseek-v4-pro`, `--model glm-5.3-flash`, `--model kimi-k3`, etc.
- O escribiendo la mención del modelo en el prompt interactivo.

### En Claude CLI (Claude Code):
- Con `ANTHROPIC_BASE_URL="http://localhost:20128"`, Claude CLI enruta a través de OmniRoute.
- Reconoce las menciones directas en el chat o el sándwich autónomo.
