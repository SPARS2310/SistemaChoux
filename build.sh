#!/usr/bin/env bash
set -o errexit

# Crear la carpeta de la base de datos si no existe y darle permisos
mkdir -p /var/data
chmod 777 /var/data

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate