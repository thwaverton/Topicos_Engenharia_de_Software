"""
Serviço de enfileiramento de mensagens usando AWS SQS.
Responsável por enviar hemogramas validados para processamento assíncrono.
"""
import json
from typing import Optional
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

from src.core.config import settings
from src.core.logging import get_logger
from src.domain.models import QueueMessage

logger = get_logger(__name__)


class QueueService:
    """Serviço para enfileiramento de mensagens no AWS SQS."""
    
    def __init__(self):
        """Inicializa o cliente SQS."""
        self.sqs_client = boto3.client(
            'sqs',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        self.queue_url = settings.sqs_queue_url
        logger.info("QueueService inicializado", queue_url=self.queue_url)
    
    def send_message(self, message: QueueMessage) -> tuple[bool, Optional[str]]:
        """
        Envia uma mensagem para a fila SQS.
        
        Args:
            message: Mensagem a ser enfileirada
        
        Returns:
            Tupla (success, message_id ou error_message)
        """
        try:
            # Serializa a mensagem para JSON
            message_body = message.model_dump_json()
            
            # Prepara parâmetros da mensagem
            send_params = {
                'QueueUrl': self.queue_url,
                'MessageBody': message_body,
                'MessageAttributes': {
                    'TrackingId': {
                        'StringValue': str(message.tracking_id),
                        'DataType': 'String'
                    },
                    'LaboratoryCNES': {
                        'StringValue': message.laboratory_cnes,
                        'DataType': 'String'
                    },
                    'PatientCPF': {
                        'StringValue': message.patient_cpf,
                        'DataType': 'String'
                    },
                    'CorrelationId': {
                        'StringValue': message.correlation_id,
                        'DataType': 'String'
                    }
                }
            }
            
            # Se for FIFO queue, adiciona MessageGroupId e MessageDeduplicationId
            if self.queue_url.endswith('.fifo'):
                send_params['MessageGroupId'] = settings.sqs_message_group_id
                send_params['MessageDeduplicationId'] = str(message.tracking_id)
            
            # Envia mensagem
            response = self.sqs_client.send_message(**send_params)
            
            message_id = response.get('MessageId')
            
            logger.info(
                "Mensagem enfileirada com sucesso",
                message_id=message_id,
                tracking_id=str(message.tracking_id),
                correlation_id=message.correlation_id
            )
            
            return True, message_id
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(
                "Erro ao enfileirar mensagem",
                error_code=error_code,
                error_message=error_message,
                tracking_id=str(message.tracking_id),
                correlation_id=message.correlation_id
            )
            
            return False, f"{error_code}: {error_message}"
            
        except Exception as e:
            logger.error(
                "Erro inesperado ao enfileirar mensagem",
                error=str(e),
                tracking_id=str(message.tracking_id),
                correlation_id=message.correlation_id
            )
            
            return False, str(e)
    
    def get_queue_attributes(self) -> Optional[dict]:
        """
        Obtém atributos da fila (tamanho, mensagens em voo, etc.).
        
        Returns:
            Dicionário com atributos da fila ou None em caso de erro
        """
        try:
            response = self.sqs_client.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=[
                    'ApproximateNumberOfMessages',
                    'ApproximateNumberOfMessagesNotVisible',
                    'ApproximateNumberOfMessagesDelayed'
                ]
            )
            
            return response.get('Attributes', {})
            
        except ClientError as e:
            logger.error(
                "Erro ao obter atributos da fila",
                error_code=e.response['Error']['Code'],
                error_message=e.response['Error']['Message']
            )
            return None


# Instância singleton do serviço de fila
_queue_service_instance: Optional[QueueService] = None


def get_queue_service() -> QueueService:
    """
    Retorna a instância singleton do QueueService.
    Usado para injeção de dependências no FastAPI.
    
    Returns:
        Instância do QueueService
    """
    global _queue_service_instance
    
    if _queue_service_instance is None:
        _queue_service_instance = QueueService()
    
    return _queue_service_instance

