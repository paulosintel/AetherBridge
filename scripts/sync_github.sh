#!/usr/bin/env bash
# ==============================================================================
# AetherBridge: Script de Sincronización Inmediata con GitHub
# ==============================================================================

set -e

COMMIT_MSG="${1:-chore: sync updates with GitHub remote}"

# Verificar si hay cambios pendientes
if [ -z "$(git status --porcelain)" ]; then
    echo "⚡ Repositorio al día. No hay cambios pendientes por sincronizar."
    exit 0
fi

echo "🔄 Sincronizando cambios locales con https://github.com/paulosintel/AetherBridge..."
git add .
git commit -m "$COMMIT_MSG"
git push origin main
echo "✅ Sincronización con GitHub completada con éxito."
