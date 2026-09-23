# Use uma imagem Python oficial
FROM python:3.11.9-slim

# Instalar dependências do sistema (drivers ODBC)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de requisitos
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Adicionar backend ao PYTHONPATH para imports funcionarem
ENV PYTHONPATH=/app/backend:$PYTHONPATH

# Expor porta
EXPOSE 8080

# Comando para iniciar a aplicação
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} backend.app.checklist_main:app"]
