# VIGIA-Anemia Infantil GO - API de Ingestão FHIR

Sistema de vigilância nutricional para detecção de anemia em crianças através da análise automatizada de hemogramas no estado de Goiás.

## 📋 Visão Geral

API REST que recebe hemogramas completos no formato FHIR R4 conforme especificação da SES-GO, validando a estrutura do payload JSON e enfileirando para processamento assíncrono.

## 🏗️ Arquitetura

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐      ┌─────────┐
│  Laboratório│─────▶│  API Gateway │─────▶│ FHIR Validator  │─────▶│  Queue  │
│   (Cliente) │      │  (FastAPI)   │      │   Service       │      │  (SQS)  │
└─────────────┘      └──────────────┘      └─────────────────┘      └─────────┘
                            │                       │
                            ▼                       ▼
                     ┌──────────────┐      ┌─────────────────┐
                     │ Auth Service │      │ Logging Service │
                     └──────────────┘      └─────────────────┘
```

## 🚀 Tecnologias

- **Python 3.11+**
- **FastAPI** - Framework web assíncrono
- **fhir.resources** - Validação de recursos FHIR R4
- **Pydantic** - Validação de dados
- **boto3** - AWS SQS para enfileiramento
- **pytest** - Testes unitários e de integração
- **uvicorn** - Servidor ASGI

## 📁 Estrutura do Projeto

```
vigia-anemia-api/
├── src/
│   ├── api/                    # Camada de apresentação (controllers)
│   ├── core/                   # Configurações e utilitários
│   ├── domain/                 # Modelos de domínio e entidades
│   ├── services/               # Lógica de negócio
│   ├── validators/             # Validadores customizados
│   └── infrastructure/         # Integrações externas (queue, auth)
├── tests/                      # Testes automatizados
├── docs/                       # Documentação adicional
└── scripts/                    # Scripts utilitários
```

## 🔧 Instalação

### Pré-requisitos

- Python 3.11 ou superior
- pip ou poetry
- AWS CLI configurado (para SQS)

### Setup

```bash
# Clone o repositório
cd vigia-anemia-api

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais
```

## ⚙️ Configuração

Edite o arquivo `.env`:

```env
# API Configuration
API_VERSION=v1
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# AWS SQS
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/hemograma-queue

# Auth Service
AUTH_SERVICE_URL=https://fhir.saude.go.gov.br/api/token
JWT_SECRET_KEY=your-secret-key-here

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_TTL=3300

# Logging
LOG_LEVEL=INFO
```

## 🏃 Execução

### Desenvolvimento

```bash
# Inicie o servidor de desenvolvimento
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Produção

```bash
# Inicie com Gunicorn
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

```bash
# Build da imagem
docker build -t vigia-anemia-api .

# Execute o container
docker run -p 8000:8000 --env-file .env vigia-anemia-api
```

## 📚 Documentação da API

Após iniciar o servidor, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🧪 Testes

```bash
# Execute todos os testes
pytest

# Com cobertura
pytest --cov=src --cov-report=html

# Apenas testes unitários
pytest tests/unit

# Apenas testes de integração
pytest tests/integration
```

## 📊 Endpoints

### POST /api/v1/exames/hemograma

Recebe um hemograma completo no formato FHIR R4.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Response 202 Accepted:**
```json
{
  "status": "accepted",
  "trackingId": "550e8400-e29b-41d4-a716-446655440000",
  "receivedAt": "2024-11-27T14:35:22-03:00",
  "estimatedProcessingTime": "5 minutos"
}
```

## 👥 Equipe

- **Felipe Brito** - Backend/API Developer
- **Gustavo Leite** - Data Engineer
- **Yuri Resende** - Infraestrutura/DevOps
- **Arnaldo** - Backend/SRE
- **Thwaverton** - QA/Tester

## 📄 Licença

Este projeto é parte do sistema VIGIA-Anemia Infantil GO da Secretaria de Saúde do Estado de Goiás.

