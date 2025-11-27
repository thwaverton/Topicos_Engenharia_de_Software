"""
Core module - Configurações e utilitários centrais da aplicação.
"""
from src.core.config import settings
from src.core.logging import configure_logging, get_logger, CorrelationContext

__all__ = [
    "settings",
    "configure_logging",
    "get_logger",
    "CorrelationContext",
]

