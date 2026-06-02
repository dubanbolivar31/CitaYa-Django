#!/usr/bin/env bash
# Script de build para Render
# Se ejecuta automáticamente antes de iniciar el servidor

set -o errexit  # Detiene el script si algún comando falla

# Instalar dependencias
pip install -r requirements.txt

# Recopilar archivos estáticos
python manage.py collectstatic --no-input

# Aplicar migraciones
python manage.py migrate
