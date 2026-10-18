#!/usr/bin/env bash
# Interrompe a execução se ocorrer algum erro
set -o errexit

echo "Instalando dependências..."
pip install -r requirements.txt

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

echo "Aplicando migrações no banco de dados..."
python manage.py migrate