# 🤝 Contribuir a AetherBridge / Contributing to AetherBridge

¡Gracias por tu interés en contribuir a **AetherBridge**! Nuestro objetivo es democratizar el acceso a modelos de inteligencia artificial de frontera a costo $0 para desarrolladores de todo el mundo.

---

## 🌐 Filosofía del Proyecto

1. **Democratización Real:** Todas las herramientas y configuraciones deben priorizar proveedores con tiers gratuitos generosos y modelos locales offline.
2. **Cero Fricción:** El usuario debe poder levantar su entorno en minutos, idealmente automatizado mediante el [Prompt Maestro](PROMPT_MAESTRO.md).
3. **Resiliencia Absoluta:** Si un proveedor en la nube falla o impone rate-limits, el sistema debe cambiar automáticamente al siguiente o conmutar a Ollama local.
4. **Privacidad y Seguridad:** Ninguna clave API ni dato privado debe salir del entorno `localhost`.

---

## 🛠️ ¿Cómo contribuir?

### 1. Reportar Errores o Sugerir Proveedores
- Si encuentras un proveedor nuevo con tier gratuito (ej. nuevos LPUs o modelos abiertos de última generación), abre un **Issue** describiendo:
  - Nombre del proveedor y enlace a su consola de claves API.
  - Modelos disponibles y límites de cuota gratuita.
  - Compatibilidad con el protocolo OpenAI/Anthropic.

### 2. Proponer Cambios (Pull Requests)
1. Haz un Fork de este repositorio: `https://github.com/paulosintel/AetherBridge`.
2. Crea una rama descriptiva para tu cambio:
   ```bash
   git checkout -b feature/nuevo-proveedor-lpu
   ```
3. Realiza tus modificaciones respetando la estructura de `scripts/` y la documentación.
4. Asegúrate de probar el entorno ejecutando:
   ```bash
   ./scripts/verify_setup.sh
   ```
5. Realiza un commit claro y envía tu Pull Request hacia la rama `main`.

---

## 📋 Reglas de Código y Seguridad

- **NUNCA subas claves reales:** Asegúrate de que `api_keys.env` esté en `.gitignore` y que solo modifiques `api_keys.env.example`.
- **Compatibilidad Multiplataforma:** Verifica que los scripts de bash o python funcionen tanto en macOS (Apple Silicon/Intel) como en Linux y Windows (WSL2).

¡Tu aporte ayuda a miles de estudiantes y desarrolladores a programar con IAs de clase mundial sin barreras económicas! 🚀
