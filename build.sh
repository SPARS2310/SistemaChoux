#!/usr/bin/env bash
# Salir si hay un error
set -o errexit

# ESTA ES LA CLAVE: Crear la carpeta y darle permisos totales de escritura
mkdir -p /var/data
chmod 777 /var/data

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate