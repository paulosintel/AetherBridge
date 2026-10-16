# Reglas de Agente: AetherBridge & Arquitectura Sándwich

## 🌉 1. Ecosistema AetherBridge
AetherBridge democratiza el acceso a la IA conectando clientes de desarrollo (Claude CLI / Claude Code, Codex, Antigravity) con:
- **Proveedores Cloud Gratuitos:** Vía el gateway local OmniRoute en `localhost:20128`.
- **Nodos Locales Privados:** Vía Ollama en `localhost:11434`.

---

## 🥪 2. El Paradigma del Sándwich de Inteligencia Artificial
En este entorno, **Gemini actúa como las dos rebanadas de pan** que envuelven la ejecución:
- **Pan Superior (Evaluador & Enrutador Inteligente - Gemini):**
  Gemini analiza el objetivo del usuario evaluando la tensión entre **Calidad de Respuesta** y **Tiempo de Ejecución**:
  - **Prioridad Latencia / Respuestas Instantáneas:** Delega a chips LPU en la nube (**Groq / Cerebras** vía `auto/fast`).
  - **Prioridad Código & Refactorización:** Delega a **Claude 3.7 / 3.5 Sonnet** (`auto/claude-sonnet` / `auto/best-coding`).
  - **Prioridad Razonamiento Lógico / Matemático:** Delega a **DeepSeek R1** (`deepseek-r1` / `auto/best-reasoning`).
  - **Prioridad Arquitectura de Sistemas:** Delega a **Claude Opus** (`auto/claude-opus`).
  - **Prioridad Contexto Masivo (1M tokens):** Delega a **Gemini 3.1 Flash Lite / 2.0 Pro**.
  - **Código Local Privado (Apple Silicon M2):** Delega a **Ollama Local** (`qwen2.5-coder:3b` a 42 tok/s).
  - **Razonamiento Lógico Local (Apple Silicon M2):** Delega a **Ollama Local** (`deepseek-r1:1.5b` a 75 tok/s con `<think>`).
  - **Respaldo Offline General:** Delega a **Ollama Local** (`llama3.2:latest`).

- **Ingrediente Central (Especialista AetherBridge / OmniRoute):**
  Se ejecuta el modelo seleccionado a costo $0 mediante:
  ```bash
  python3 scripts/gemini_sandwich.py --mode [auto|speed|coding|reasoning|architecture] "<prompt>"
  ```
  o mediante el CLI de consulta directa:
  ```bash
  python3 scripts/aether_consult.py -m [opus|sonnet|r1|gemini|coding|local] "<prompt>"
  ```
  o la herramienta MCP `sandwich_orchestration`.

- **Pan Inferior (Validador & Sintetizador - Gemini):**
  Gemini audita el código o razonamiento devuelto por el ingrediente, verifica que cumpla con las restricciones del proyecto y lo entrega formateado con elegancia al usuario.

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

