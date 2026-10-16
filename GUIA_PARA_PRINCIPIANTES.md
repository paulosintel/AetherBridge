# 🧙‍♂️ Guía Rápida: +300 Modelos de IA Gratis con AetherBridge
### (Edición para Principiantes: Sin saber programar ni configurar servidores)

> **Bienvenido a AetherBridge:**  
> Esta guía está diseñada para que cualquier persona pueda tener una supercomputadora de Inteligencia Artificial en su propia máquina sin pagar suscripciones mensuales de $20 o $40 dólares.  
> **Lo mejor de todo:** No tienes que pelear con comandos raros. Tu asistente de IA (**Antigravity**, **Codex** o **Claude Code**) hará de técnico informático e instalará todo por ti.

---

## 💡 ¿Qué obtienes con AetherBridge?

1. **Modelos Locales y 100% Privados (Ollama):**  
   Inteligencias artificiales que funcionan dentro de tu ordenador, incluso sin conexión a internet. Nadie lee tus conversaciones ni tus archivos.
2. **Acceso a los Mejores Modelos del Mundo sin Pagar (Cloud Free Tiers):**  
   Google Gemini 2.0 (con ventana gigante de 1 millón de tokens), Meta Llama 3.3 a velocidad luz (Groq/Cerebras), DeepSeek R1 y Claude.
3. **Claude CLI Desbloqueado:**  
   Usa la interfaz oficial de Claude Code en tu terminal conectada a cientos de modelos en lugar de estar atado a una sola empresa.
4. **Resiliencia Total (Si uno falla, salta a otro solo):**  
   Si una empresa de IA satura su servicio o te pone en espera, AetherBridge cambia de inmediato a la siguiente sin interrumpirte.

---

## 🛠️ Los 3 Únicos Pasos que Debes Seguir

### Paso 1: Conseguir tus "Llaves de Acceso" Gratuitas (5 a 10 minutos)
Las empresas de tecnología regalan acceso gratuito para desarrolladores mediante unas claves llamadas **API Keys** (códigos de texto largos).

Consigue al menos **1 o 2** de estas claves gratuitas (ninguna te pide tarjeta de crédito para empezar):

1. **Google AI Studio (Imprescindible):**  
   - Entra a: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)  
   - Inicia sesión con tu cuenta de Google / Gmail.  
   - Haz clic en **"Create API key"** y copia el código que te genere.
2. **Groq Cloud (Velocidad ultra rápida):**  
   - Entra a: [https://console.groq.com/keys](https://console.groq.com/keys)  
   - Crea tu cuenta y genera tu clave con **"Create API Key"**.
3. **OpenRouter (Catálogo masivo con cientos de modelos):**  
   - Entra a: [https://openrouter.ai/keys](https://openrouter.ai/keys)  
   - Crea tu cuenta y genera tu clave.

👉 **¿Dónde las guardas?**  
En esta carpeta encontrarás un archivo llamado `api_keys.env.example`. Haz una copia llamada `api_keys.env` y pega tus claves entre las comillas (o simplemente anótalas para dárselas a tu asistente).

---

### Paso 2: Dejar que tu Asistente haga Toda la Instalación

**No tienes que instalar programas manualmente:**  
Tu asistente de IA (**Antigravity**, **Codex** o **Claude Code**) tiene permisos para configurar el sistema por ti.

1. Abre tu herramienta (**Antigravity** o **Codex**).
2. Abre esta carpeta en el programa.
3. Abre el archivo **[`PROMPT_MAESTRO.md`](PROMPT_MAESTRO.md)** que te dejamos preparado.
4. Copia el texto y pégalo en el chat con tu asistente de IA.

Tu asistente:
- Instalará Ollama y el motor de AetherBridge.
- Descargará un modelo para cuando estés sin internet (ej. `llama3.2`).
- Conectará tus claves de Google, Groq u OpenRouter.
- Dejará todo encendido y listo.

---

### Paso 3: ¿Cómo Empezar a Usarlo en tu Día a Día?

Una vez que tu asistente termine de instalar todo:

#### 1. Para usar Claude en tu consola (Claude CLI):
1. Abre tu terminal (en Windows: Terminal o PowerShell; en Mac/Linux: Terminal).
2. Escribe:
   ```bash
   claude
   ```
3. ¡Listo! Todo lo que le pidas a Claude viajará a través de **AetherBridge**, aprovechando los modelos gratuitos y conmutando automáticamente si alguno se satura.

#### 2. Para usar Codex o Antigravity:
Apunta el modelo personalizado a la dirección local que tu asistente dejó configurada: `http://localhost:20128/v1` con la clave `sk-aetherbridge`.

#### 3. Para consultar cualquier modelo desde la terminal:
Hemos incluido un comando súper simple. Solo escribe:
- **En Windows:**
  ```powershell
  python scripts\aether_consult.py -m fast "¿Cuál es la capital de Francia?"
  python scripts\aether_consult.py -m r1 "Resuelve este problema matemático paso a paso"
  python scripts\aether_consult.py -m local "Explícame este concepto sin conexión a internet"
  ```
- **En macOS / Linux:**
  ```bash
  python3 scripts/aether_consult.py -m fast "¿Cuál es la capital de Francia?"
  python3 scripts/aether_consult.py -m r1 "Resuelve este problema matemático paso a paso"
  python3 scripts/aether_consult.py -m local "Explícame este concepto sin conexión a internet"
  ```

---

## 💻 Guía Rápida para Usuarios de Windows (Huawei, Lenovo, HP, Dell, etc.)

> **¡Buenas noticias!** No necesitas instalar Linux, ni máquinas virtuales, ni configurar WSL2. AetherBridge corre **100% de forma nativa en Windows 10 y Windows 11**.

### Los 3 pasos en Windows:
1. **Instala Ollama para Windows:**  
   Descarga el instalador oficial desde [ollama.com/download/windows](https://ollama.com/download/windows) y dale a Siguiente, Siguiente. (O abre PowerShell y escribe `winget install Ollama.Ollama`).
2. **Instala Node.js (si no lo tienes):**  
   Descárgalo desde [nodejs.org](https://nodejs.org/) versión LTS (o escribe `winget install OpenJS.NodeJS`).
3. **Pega el Prompt Maestro en tu asistente:**  
   Abre esta carpeta en tu editor (**Antigravity**, **Codex**, etc.), abre [`PROMPT_MAESTRO.md`](PROMPT_MAESTRO.md), cópialo y pégalo en el chat.  
   Tu asistente detectará Windows y configurará todo de manera transparente.
4. **Comprobación con un solo clic:**  
   En Windows puedes simplemente hacer doble clic sobre el archivo [`scripts/verify_setup.bat`](scripts/verify_setup.bat) o ejecutar en PowerShell:
   ```powershell
   python scripts\verify_setup.py
   ```

---

## ❓ Preguntas Frecuentes

- **¿Esto me cobrará algo en el futuro?**  
  No. Solo utilizas los tiers gratuitos oficiales que no requieren tarjeta de crédito y modelos locales que corren en tu propio disco duro.
- **¿Qué pasa si me quedo sin internet?**  
  AetherBridge detecta la desconexión automáticamente y enruta tus peticiones al modelo local de Ollama para que sigas trabajando.
- **En Windows me sale error diciendo que 'python3' no se reconoce:**  
  En Windows el comando oficial suele ser `python` (sin el 3) o `py`. Por ejemplo: `python scripts\verify_setup.py`.
- **¿Qué hago si algo falla?**  
  Solo copia el mensaje que te salga, pégalo en tu asistente y dile: *"Oye, ocurrió esto, por favor arréglalo"*.

¡Bienvenido al futuro de la inteligencia artificial abierta y sin ataduras con AetherBridge! 🚀
