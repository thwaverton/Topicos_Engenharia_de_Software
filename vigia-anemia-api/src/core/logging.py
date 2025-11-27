"""
Configuração de logging estruturado para a aplicação.
Utiliza structlog para logs em formato JSON com correlation ID.
"""
import logging
import sys
from typing import Any, Dict
from uuid import uuid4

import structlog
from structlog.types import EventDict, Processor

from src.core.config import settings


def add_correlation_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Adiciona correlation ID ao log se não existir.
    O correlation ID é usado para rastrear requisições através do sistema.
    """
    if "correlation_id" not in event_dict:
        event_dict["correlation_id"] = str(uuid4())
    return event_dict


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Adiciona contexto da aplicação aos logs."""
    event_dict["app"] = "vigia-anemia-api"
    event_dict["environment"] = settings.environment
    event_dict["version"] = settings.api_version
    return event_dict


def configure_logging() -> None:
    """
    Configura o sistema de logging da aplicação.
    
    - Em desenvolvimento: logs coloridos e legíveis
    - Em produção: logs em JSON para ingestão por sistemas de monitoramento
    """
    
    # Processadores comuns para todos os ambientes
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_correlation_id,
        add_app_context,
    ]
    
    if settings.is_development:
        # Desenvolvimento: logs coloridos e legíveis
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # Produção: logs em JSON
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    
    # Configura structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configura logging padrão do Python
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )
    
    # Reduz verbosidade de bibliotecas externas
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Retorna um logger configurado para o módulo especificado.
    
    Args:
        name: Nome do módulo (geralmente __name__)
    
    Returns:
        Logger estruturado configurado
    """
    return structlog.get_logger(name)


# Contexto de correlação para rastreamento de requisições
class CorrelationContext:
    """Gerencia o correlation ID para rastreamento de requisições."""
    
    @staticmethod
    def set_correlation_id(correlation_id: str) -> None:
        """Define o correlation ID no contexto."""
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    
    @staticmethod
    def get_correlation_id() -> str:
        """Retorna o correlation ID atual ou gera um novo."""
        # Tenta obter do contexto, senão gera novo
        return str(uuid4())
    
    @staticmethod
    def clear() -> None:
        """Limpa o contexto de correlação."""
        structlog.contextvars.clear_contextvars()

