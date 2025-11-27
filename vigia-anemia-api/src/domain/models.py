"""
Modelos de domínio da aplicação.
Define as entidades e value objects do sistema.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ExamStatus(str, Enum):
    """Status do exame no sistema."""
    RECEIVED = "received"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LoincCode(str, Enum):
    """Códigos LOINC dos exames obrigatórios do hemograma."""
    # Exame composto
    CBC_PANEL = "58410-2"
    
    # Série vermelha
    HEMACEAS = "789-8"
    HEMOGLOBINA = "718-7"
    HEMATOCRITO = "4544-3"
    VCM = "787-2"
    HCM = "785-6"
    CHCM = "786-4"
    RDW = "788-0"
    
    # Série branca
    LEUCOCITOS = "6690-2"
    PROMIELOCITOS = "781-5"
    MIELOCITOS = "748-4"
    METAMIELOCITOS = "739-3"
    BASTONETES = "763-3"
    SEGMENTADOS = "768-2"
    MONOCITOS = "742-7"
    EOSINOFILOS = "711-2"
    BASOFILOS = "704-7"
    LINFOCITOS = "731-0"
    LINFOCITOS_ATIPICOS = "29262-3"
    PRO_LINFOCITOS = "6863-5"
    BLASTOS = "708-8"
    
    # Plaquetas
    PLAQUETAS = "777-3"
    PLAQUETOCRITO = "32266-7"
    VPM = "32623-1"
    PDW = "32207-3"


class ValidationError(BaseModel):
    """Erro de validação detalhado."""
    field: str = Field(..., description="Campo que falhou na validação")
    expected: str = Field(..., description="Valor esperado")
    received: str = Field(..., description="Valor recebido")
    description: str = Field(..., description="Descrição do erro")


class HemogramaResponse(BaseModel):
    """Resposta de sucesso ao receber um hemograma."""
    status: str = Field(default="accepted", description="Status da operação")
    tracking_id: UUID = Field(
        default_factory=uuid4,
        description="ID único para rastreamento do hemograma"
    )
    received_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Data/hora de recebimento"
    )
    estimated_processing_time: str = Field(
        default="5 minutos",
        description="Tempo estimado de processamento"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "accepted",
                "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
                "received_at": "2024-11-27T14:35:22.123456",
                "estimated_processing_time": "5 minutos"
            }
        }


class ErrorResponse(BaseModel):
    """Resposta de erro padronizada."""
    status: str = Field(default="error", description="Status da operação")
    code: str = Field(..., description="Código do erro")
    message: str = Field(..., description="Mensagem de erro")
    errors: Optional[List[ValidationError]] = Field(
        default=None,
        description="Lista de erros de validação detalhados"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="ID de correlação para rastreamento"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "code": "INVALID_FHIR_STRUCTURE",
                "message": "Estrutura FHIR inválida",
                "errors": [
                    {
                        "field": "Bundle.entry[0].resource.code.coding[0].code",
                        "expected": "58410-2",
                        "received": "58410-1",
                        "description": "Código LOINC do exame composto inválido"
                    }
                ],
                "correlation_id": "abc123-def456-ghi789"
            }
        }


class QueueMessage(BaseModel):
    """Mensagem a ser enfileirada para processamento assíncrono."""
    tracking_id: UUID = Field(..., description="ID de rastreamento do hemograma")
    fhir_bundle: dict = Field(..., description="Bundle FHIR completo")
    received_at: datetime = Field(..., description="Data/hora de recebimento")
    laboratory_cnes: str = Field(..., description="CNES do laboratório")
    patient_cpf: str = Field(..., description="CPF do paciente")
    correlation_id: str = Field(..., description="ID de correlação")
    
    @field_validator("laboratory_cnes")
    @classmethod
    def validate_cnes(cls, v: str) -> str:
        """Valida formato do CNES (7 dígitos)."""
        if not v.isdigit() or len(v) != 7:
            raise ValueError("CNES deve conter exatamente 7 dígitos")
        return v
    
    @field_validator("patient_cpf")
    @classmethod
    def validate_cpf_format(cls, v: str) -> str:
        """Valida formato básico do CPF (11 dígitos)."""
        cpf_digits = ''.join(filter(str.isdigit, v))
        if len(cpf_digits) != 11:
            raise ValueError("CPF deve conter exatamente 11 dígitos")
        return cpf_digits

