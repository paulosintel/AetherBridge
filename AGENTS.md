# Reglas de Agente: AetherBridge & Arquitectura Sándwich

## 🌉 1. Ecosistema AetherBridge
AetherBridge democratiza el acceso a la IA conectando clientes de desarrollo (Claude Desktop, Claude CLI / Claude Code, Codex, Antigravity) directamente con:
- **Proveedores Directos Cloud (Primarios):** Vía el gateway local **OmniRoute - AetherBridge** en `localhost:20128` (Google Gemini, NVIDIA NIM, OpenRouter, Groq y cascadas inteligentes `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-haiku-5-5`, `auto/*`).
- **Nodos Locales Opcionales:** Vía Ollama en `localhost:11434` únicamente si está instalado y activo en el equipo.

---

## 🥪 2. El Paradigma del Sándwich de Inteligencia Artificial (Titanes de Frontera)
En este entorno, **Gemini actúa como las dos rebanadas de pan** que envuelven la ejecución:
- **Pan Superior (Evaluador & Enrutador Inteligente - Gemini):**
  Gemini analiza el objetivo del usuario con **doble modalidad de activación**:
  
  ### A. Activación por Mención Directa en Chat:
  Si el usuario escribe en su prompt el modelo o familia deseada, el sistema lo activa inmediatamente:
  - **`deepseek v4` / `v4 pro` / `v4 flash` / `deepseek r2`**: Enruta a la familia DeepSeek de última generación.
  - **`glm-5` / `glm 5.3 flash` / `z.ai`**: Enruta a GLM (Claude Opus 4.6 equiv).
  - **`kimi` / `kimi k3` / `kimi k2.6` / `moonshot`**: Enruta a Moonshot Kimi (Claude Sonnet / Fable equiv).
  - **`qwen 3` / `qwen 3.6 coder` / `qwen 235b`**: Enruta a Qwen MoE Coder (Claude Sonnet equiv).
  - **`gemini 2.5 pro` / `gemini 2.5 flash`**: Enruta a Gemini 2.5 multimodal masivo.
  - **`nemotron` / `nemotron 3 ultra` / `gpt-oss-120b`**: Enruta a Nemotron 3 Ultra (Claude Sonnet equiv).
  - Modelos clásicos: `opus`, `sonnet`, `deepseek r1`, `groq`, `ollama local`.

  ### B. Decisión Autónoma por Complejidad:
  Si el usuario no especifica modelo, Gemini calcula la complejidad multidimensional:
  - **Complejidad Arquitectónica & Macro-Diseño:** Delega a **GLM-5.3-Flash** (Claude Opus 4.6 equiv) o **Claude Opus**.
  - **Complejidad Lógica & Matemática Formal:** Delega a **DeepSeek R2** (Claude Opus/Sonnet equiv) o **DeepSeek V4 Pro**.
  - **Ingeniería de Software & Código Complejo:** Delega a **Qwen 3.6 Coder 235B MoE** (Claude Sonnet equiv) o **Nemotron 3 Ultra**.
  - **Contexto Masivo & Repositorios Extensos:** Delega a **Gemini 2.5 Pro** o **Kimi K3 (Moonshot)**.
  - **Velocidad Extrema / Sub-segundo:** Delega a **Gemini 3.1 Flash Lite** o `claude-haiku-5-5` / `auto/best-fast`.
  - **Respaldo Cloud Multi-Proveedor:** Cascada automática entre **Google Gemini**, **NVIDIA NIM** y **OpenRouter (:free)** (y nodo Ollama local únicamente si se encuentra instalado y activo).

- **Ingrediente Central (Especialista AetherBridge / OmniRoute):**
  Se ejecuta el modelo seleccionado a costo $0 mediante:
  ```bash
  python3 scripts/gemini_sandwich.py --mode [auto|v4|r2|glm|kimi|qwen|gemini25|nemotron|speed|coding|reasoning|architecture] "<prompt>"
  ```
  o mediante el CLI de consulta directa:
  ```bash
  python3 scripts/aether_consult.py -m [v4|r2|glm5|kimi|qwen3|gemini25|nemotron|opus|sonnet|r1|local] "<prompt>"
  ```
  o las herramientas MCP de OmniRoute (`sandwich_orchestration`, `ask_deepseek_v4_r2`, `ask_glm_family`, `ask_kimi_moonshot`, `ask_qwen_3_coder`, `ask_gemini_2_5`, `ask_nemotron_ultra`).

- **Pan Inferior (Validador & Sintetizador - Gemini):**
  Gemini audita el código o razonamiento devuelto por el ingrediente, verifica que cumpla con las restricciones del proyecto y añade el banner de transparencia correspondiente.

---

## 🔄 3. Auto-Actualización de Nuevos Modelos en Segundo Plano
- El demonio de macOS `com.omniroute.autoupdate` corre cada 6 horas ejecutando:
  ```bash
  python3 scripts/auto_update_catalog.py
  ```
- Detecta automáticamente nuevos lanzamientos mundiales (+1,000 modelos) e inyecta los nuevos campeones en el catálogo de Codex, Claude CLI y Antigravity sin intervención manual.

---

## ⚡ 4. Regla Inquebrantable de Sincronización Inmediata con GitHub
- Repositorio oficial público: `https://github.com/paulosintel/AetherBridge`
- **Mandato:** CUALQUIER mejora técnica, corrección de bug, nuevo script o actualización de documentación realizada en el entorno local **DEBE ser sincronizada y enviada a GitHub inmediatamente** en el mismo turno mediante:
  ```bash
  ./scripts/sync_github.sh "<mensaje descriptivo>"
  ```
- Queda terminantemente prohibida cualquier desincronización entre el código local y el repositorio público.
