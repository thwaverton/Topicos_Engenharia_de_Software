# Multi-stage build para otimizar tamanho da imagem

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Cria usuário não-root para segurança
RUN useradd -m -u 1000 apiuser && \
    mkdir -p /app/logs && \
    chown -R apiuser:apiuser /app

# Copia dependências do builder
COPY --from=builder /root/.local /home/apiuser/.local

# Copia código da aplicação
COPY --chown=apiuser:apiuser src/ /app/src/
COPY --chown=apiuser:apiuser .env.example /app/.env

# Configura PATH para incluir pacotes do usuário
ENV PATH=/home/apiuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Muda para usuário não-root
USER apiuser

# Expõe porta da API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Comando de inicialização
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

