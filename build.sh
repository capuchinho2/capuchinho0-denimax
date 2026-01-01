#!/usr/bin/env bash
# build.sh - Script de build para instalar dependências do sistema e Python

set -o errexit  # Exit on error

echo "📦 Instalando pacotes do sistema (ODBC drivers)..."
apt-get update
apt-get install -y unixodbc unixodbc-dev

echo "🐍 Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build concluído com sucesso!"
