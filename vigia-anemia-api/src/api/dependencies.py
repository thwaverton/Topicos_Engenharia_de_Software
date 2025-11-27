"""
Dependências do FastAPI para injeção de dependências.
"""
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from src.core.logging import CorrelationContext, get_logger
from src.infrastructure.auth_service import AuthService, get_auth_service
from src.infrastructure.queue_service import QueueService, get_queue_service
from src.services.hemograma_service import HemogramaService

logger = get_logger(__name__)


async def verify_token(
    authorization: Annotated[str, Header()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> dict:
    """
    Verifica o token JWT de autorização.
    
    Args:
        authorization: Header Authorization com Bearer token
        auth_service: Serviço de autenticação
    
    Returns:
        Payload do token decodificado
    
    Raises:
        HTTPException: Se o token for inválido ou ausente
    """
    # Verifica formato do header
    if not authorization.startswith("Bearer "):
        logger.warning("Token ausente ou formato inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso ausente ou inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extrai o token
    token = authorization.replace("Bearer ", "")
    
    # Valida o token
    is_valid, payload = await auth_service.validate_token(token)
    
    if not is_valid:
        logger.warning("Token inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


def get_hemograma_service(
    queue_service: Annotated[QueueService, Depends(get_queue_service)]
) -> HemogramaService:
    """
    Retorna uma instância do HemogramaService.
    
    Args:
        queue_service: Serviço de fila injetado
    
    Returns:
        Instância do HemogramaService
    """
    return HemogramaService(queue_service=queue_service)


async def get_correlation_id(
    x_correlation_id: Annotated[str | None, Header()] = None
) -> str:
    """
    Obtém ou gera um correlation ID para rastreamento.
    
    Args:
        x_correlation_id: Header X-Correlation-Id opcional
    
    Returns:
        Correlation ID
    """
    if x_correlation_id:
        correlation_id = x_correlation_id
    else:
        correlation_id = CorrelationContext.get_correlation_id()
    
    # Define no contexto para logs
    CorrelationContext.set_correlation_id(correlation_id)
    
    return correlation_id

