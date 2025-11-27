"""
Configurações centralizadas da aplicação.
Utiliza Pydantic Settings para validação e carregamento de variáveis de ambiente.
"""
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Configuration
    api_version: str = Field(default="v1", description="Versão da API")
    api_host: str = Field(default="0.0.0.0", description="Host da API")
    api_port: int = Field(default=8000, description="Porta da API")
    environment: str = Field(default="development", description="Ambiente de execução")
    api_title: str = Field(default="VIGIA-Anemia Infantil GO - API")
    api_description: str = Field(
        default="API de ingestão de hemogramas FHIR R4 para vigilância nutricional infantil"
    )
    
    # AWS SQS Configuration
    aws_region: str = Field(default="us-east-1", description="Região AWS")
    aws_access_key_id: str = Field(default="", description="AWS Access Key ID")
    aws_secret_access_key: str = Field(default="", description="AWS Secret Access Key")
    sqs_queue_url: str = Field(
        default="https://sqs.us-east-1.amazonaws.com/123456789/hemograma-queue",
        description="URL da fila SQS"
    )
    sqs_message_group_id: str = Field(
        default="hemograma-processing",
        description="Group ID para FIFO queue"
    )
    
    # Auth Service Configuration
    auth_service_url: str = Field(
        default="https://fhir.saude.go.gov.br/api/token",
        description="URL do serviço de autenticação"
    )
    jwt_secret_key: str = Field(
        default="change-me-in-production",
        description="Chave secreta para JWT"
    )
    jwt_algorithm: str = Field(default="HS256", description="Algoritmo JWT")
    token_expire_minutes: int = Field(default=60, description="Tempo de expiração do token")
    
    # Redis Cache Configuration
    redis_host: str = Field(default="localhost", description="Host do Redis")
    redis_port: int = Field(default=6379, description="Porta do Redis")
    redis_db: int = Field(default=0, description="Database do Redis")
    redis_password: str = Field(default="", description="Senha do Redis")
    redis_ttl: int = Field(default=3300, description="TTL do cache em segundos (55 min)")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Nível de log")
    log_format: str = Field(default="json", description="Formato de log")
    log_file: str = Field(default="logs/vigia-anemia-api.log", description="Arquivo de log")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Origens permitidas para CORS"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["GET", "POST", "OPTIONS"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    # FHIR Validation Configuration
    fhir_profile_url: str = Field(
        default="https://fhir.saude.go.gov.br/r4/exame/StructureDefinition/malote",
        description="URL do perfil FHIR"
    )
    fhir_strict_validation: bool = Field(
        default=True,
        description="Validação estrita de FHIR"
    )
    fhir_required_exams_count: int = Field(
        default=24,
        description="Número de exames simples obrigatórios"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, description="Limite de requisições por minuto")
    rate_limit_burst: int = Field(default=20, description="Burst de requisições")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Habilitar métricas Prometheus")
    metrics_port: int = Field(default=9090, description="Porta para métricas")
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Valida que o ambiente é um dos valores permitidos."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment deve ser um de: {allowed}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Valida que o nível de log é válido."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level deve ser um de: {allowed}")
        return v_upper
    
    @property
    def is_production(self) -> bool:
        """Retorna True se estiver em produção."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Retorna True se estiver em desenvolvimento."""
        return self.environment == "development"
    
    @property
    def api_prefix(self) -> str:
        """Retorna o prefixo da API."""
        return f"/api/{self.api_version}"


# Instância global de configurações
settings = Settings()

