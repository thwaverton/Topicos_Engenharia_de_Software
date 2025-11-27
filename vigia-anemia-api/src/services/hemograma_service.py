"""
Serviço de processamento de hemogramas.
Orquestra a validação FHIR e enfileiramento para processamento assíncrono.
"""
from datetime import datetime
from typing import Any, Dict, Tuple
from uuid import uuid4

from src.core.logging import get_logger
from src.domain.models import HemogramaResponse, QueueMessage, ValidationError
from src.infrastructure.queue_service import QueueService
from src.validators.fhir_validator import FHIRValidator

logger = get_logger(__name__)


class HemogramaService:
    """Serviço de negócio para processamento de hemogramas."""
    
    def __init__(self, queue_service: QueueService):
        """
        Inicializa o serviço de hemogramas.
        
        Args:
            queue_service: Serviço de enfileiramento
        """
        self.queue_service = queue_service
        self.fhir_validator = FHIRValidator()
        logger.info("HemogramaService inicializado")
    
    def extract_metadata(self, bundle: Dict[str, Any]) -> Tuple[str, str]:
        """
        Extrai metadados do Bundle FHIR (CNES do laboratório e CPF do paciente).
        
        Args:
            bundle: Bundle FHIR
        
        Returns:
            Tupla (laboratory_cnes, patient_cpf)
        """
        laboratory_cnes = "0000000"  # Default
        patient_cpf = "00000000000"  # Default
        
        entries = bundle.get("entry", [])
        
        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "Observation":
                continue
            
            # Extrai CPF do paciente
            subject = resource.get("subject", {})
            identifier = subject.get("identifier", {})
            if identifier.get("system") == "https://fhir.saude.go.gov.br/sid/cpf":
                patient_cpf = identifier.get("value", patient_cpf)
            
            # Extrai CNES do laboratório
            performers = resource.get("performer", [])
            for performer in performers:
                if performer.get("id") == "laboratorio":
                    lab_identifier = performer.get("identifier", {})
                    if lab_identifier.get("system") == "https://fhir.saude.go.gov.br/sid/cnes":
                        laboratory_cnes = lab_identifier.get("value", laboratory_cnes)
            
            # Se já encontrou ambos, pode parar
            if laboratory_cnes != "0000000" and patient_cpf != "00000000000":
                break
        
        return laboratory_cnes, patient_cpf
    
    async def process_hemograma(
        self,
        bundle: Dict[str, Any],
        correlation_id: str
    ) -> Tuple[bool, HemogramaResponse | list[ValidationError]]:
        """
        Processa um hemograma completo.
        
        Fluxo:
        1. Valida estrutura FHIR
        2. Extrai metadados
        3. Enfileira para processamento assíncrono
        4. Retorna resposta de aceitação
        
        Args:
            bundle: Bundle FHIR do hemograma
            correlation_id: ID de correlação da requisição
        
        Returns:
            Tupla (success, response ou errors)
        """
        logger.info(
            "Iniciando processamento de hemograma",
            correlation_id=correlation_id
        )
        
        # Passo 1: Validação FHIR
        is_valid, errors = self.fhir_validator.validate(bundle)
        
        if not is_valid:
            logger.warning(
                "Hemograma rejeitado - validação FHIR falhou",
                correlation_id=correlation_id,
                error_count=len(errors)
            )
            return False, errors
        
        # Passo 2: Extração de metadados
        laboratory_cnes, patient_cpf = self.extract_metadata(bundle)
        
        logger.info(
            "Metadados extraídos",
            correlation_id=correlation_id,
            laboratory_cnes=laboratory_cnes,
            patient_cpf=patient_cpf[:3] + "***" + patient_cpf[-2:]  # Mascarado para log
        )
        
        # Passo 3: Preparação da mensagem para fila
        tracking_id = uuid4()
        received_at = datetime.utcnow()
        
        queue_message = QueueMessage(
            tracking_id=tracking_id,
            fhir_bundle=bundle,
            received_at=received_at,
            laboratory_cnes=laboratory_cnes,
            patient_cpf=patient_cpf,
            correlation_id=correlation_id
        )
        
        # Passo 4: Enfileiramento
        success, result = self.queue_service.send_message(queue_message)
        
        if not success:
            logger.error(
                "Falha ao enfileirar hemograma",
                correlation_id=correlation_id,
                tracking_id=str(tracking_id),
                error=result
            )
            # Retorna erro de enfileiramento
            return False, [ValidationError(
                field="queue",
                expected="mensagem enfileirada",
                received="erro",
                description=f"Falha ao enfileirar: {result}"
            )]
        
        # Passo 5: Resposta de sucesso
        response = HemogramaResponse(
            status="accepted",
            tracking_id=tracking_id,
            received_at=received_at,
            estimated_processing_time="5 minutos"
        )
        
        logger.info(
            "Hemograma aceito e enfileirado com sucesso",
            correlation_id=correlation_id,
            tracking_id=str(tracking_id),
            message_id=result
        )
        
        return True, response

