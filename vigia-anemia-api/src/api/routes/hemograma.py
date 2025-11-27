"""
Rotas da API para ingestão de hemogramas FHIR.
"""
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.api.dependencies import (
    get_correlation_id,
    get_hemograma_service,
    verify_token,
)
from src.core.logging import get_logger
from src.domain.models import ErrorResponse, HemogramaResponse
from src.services.hemograma_service import HemogramaService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/exames",
    tags=["Hemogramas"],
    dependencies=[Depends(verify_token)]
)


@router.post(
    "/hemograma",
    response_model=HemogramaResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {
            "description": "Hemograma aceito para processamento assíncrono",
            "model": HemogramaResponse
        },
        400: {
            "description": "Estrutura FHIR inválida",
            "model": ErrorResponse
        },
        401: {
            "description": "Token de acesso ausente ou inválido",
            "model": ErrorResponse
        },
        422: {
            "description": "Dados inconsistentes (CPF/CNES inválidos)",
            "model": ErrorResponse
        },
        500: {
            "description": "Erro interno do servidor",
            "model": ErrorResponse
        }
    },
    summary="Recebe hemograma completo em formato FHIR R4",
    description="""
    Endpoint para ingestão de hemogramas completos no formato FHIR R4 conforme 
    especificação da SES-GO.
    
    **Requisitos:**
    - Bundle FHIR tipo "collection"
    - 1 exame composto (LOINC 58410-2 - CBC panel)
    - 24 exames simples obrigatórios
    - 1 amostra (Specimen) de sangue
    - Identificação do laboratório (CNES)
    - Identificação do paciente (CPF)
    - Responsável técnico e responsável pelo resultado
    
    **Processamento:**
    O hemograma é validado e enfileirado para processamento assíncrono.
    Um tracking ID é retornado para rastreamento do processamento.
    
    **Tempo estimado de processamento:** 5 minutos
    """
)
async def receive_hemograma(
    request: Request,
    hemograma_service: Annotated[HemogramaService, Depends(get_hemograma_service)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
) -> HemogramaResponse | JSONResponse:
    """
    Recebe e processa um hemograma completo em formato FHIR R4.
    
    Args:
        request: Requisição HTTP com o Bundle FHIR no body
        hemograma_service: Serviço de processamento de hemogramas
        correlation_id: ID de correlação para rastreamento
    
    Returns:
        HemogramaResponse com tracking ID em caso de sucesso
        ErrorResponse em caso de erro
    """
    try:
        # Extrai o Bundle FHIR do body
        bundle: Dict[str, Any] = await request.json()
        
        logger.info(
            "Hemograma recebido",
            correlation_id=correlation_id,
            bundle_type=bundle.get("type"),
            entries_count=len(bundle.get("entry", []))
        )
        
        # Processa o hemograma
        success, result = await hemograma_service.process_hemograma(
            bundle=bundle,
            correlation_id=correlation_id
        )
        
        if success:
            # Sucesso - retorna 202 Accepted
            return result
        else:
            # Erro de validação - retorna 400 Bad Request
            error_response = ErrorResponse(
                status="error",
                code="INVALID_FHIR_STRUCTURE",
                message="Estrutura FHIR inválida ou dados inconsistentes",
                errors=result,
                correlation_id=correlation_id
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.model_dump()
            )
    
    except ValueError as e:
        # Erro de parsing JSON
        logger.error(
            "JSON malformado",
            correlation_id=correlation_id,
            error=str(e)
        )
        
        error_response = ErrorResponse(
            status="error",
            code="INVALID_JSON",
            message="JSON malformado",
            correlation_id=correlation_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump()
        )
    
    except Exception as e:
        # Erro inesperado
        logger.error(
            "Erro inesperado ao processar hemograma",
            correlation_id=correlation_id,
            error=str(e),
            exc_info=True
        )
        
        error_response = ErrorResponse(
            status="error",
            code="INTERNAL_SERVER_ERROR",
            message="Erro interno do servidor",
            correlation_id=correlation_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )


@router.get(
    "/health",
    tags=["Health"],
    summary="Verifica saúde do serviço de hemogramas",
    dependencies=[]  # Não requer autenticação
)
async def health_check() -> dict:
    """
    Endpoint de health check.
    
    Returns:
        Status do serviço
    """
    return {
        "status": "healthy",
        "service": "hemograma-ingestion",
        "version": "1.0.0"
    }

