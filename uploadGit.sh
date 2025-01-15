#!/bin/bash

# Obtiene la ruta del directorio donde se encuentra el script
script_dir=$(dirname "$0")

# Cambia al directorio donde está ubicado el repositorio
cd "$script_dir" || { echo "No se pudo cambiar al directorio"; exit 1; }

# Verifica si hay cambios en el repositorio
if git diff-index --quiet HEAD --; then
    echo "No hay cambios para hacer commit."
else
    # Agrega todos los cambios (archivos modificados, nuevos archivos, etc.)
    git add .

    # Realiza el commit con un mensaje personalizado
    read -p "Ingresa el mensaje del commit: " commit_message
    git commit -m "$commit_message"

    # Realiza el push a la rama remota actual
    git push
fi
