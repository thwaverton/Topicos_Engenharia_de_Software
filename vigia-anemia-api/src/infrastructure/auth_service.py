"""
Serviço de autenticação e validação de tokens JWT.
Integra com o serviço de autorização da SES-GO.
"""
from datetime import datetime, timedelta
from typing import Optional

import httpx
from jose import JWTError, jwt

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Serviço de autenticação e validação de tokens."""
    
    def __init__(self):
        """Inicializa o serviço de autenticação."""
        self.auth_service_url = settings.auth_service_url
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        logger.info("AuthService inicializado", auth_url=self.auth_service_url)
    
    async def validate_token(self, token: str) -> tuple[bool, Optional[dict]]:
        """
        Valida um token JWT.
        
        Args:
            token: Token JWT a ser validado
        
        Returns:
            Tupla (is_valid, payload ou None)
        """
        try:
            # Decodifica e valida o token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verifica expiração
            exp = payload.get("exp")
            if exp:
                exp_datetime = datetime.fromtimestamp(exp)
                if exp_datetime < datetime.utcnow():
                    logger.warning("Token expirado", exp=exp_datetime)
                    return False, None
            
            logger.info("Token validado com sucesso", sub=payload.get("sub"))
            return True, payload
            
        except JWTError as e:
            logger.warning("Token inválido", error=str(e))
            return False, None
        except Exception as e:
            logger.error("Erro ao validar token", error=str(e))
            return False, None
    
    async def get_token_from_auth_service(
        self,
        certificate_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Obtém um token do serviço de autorização da SES-GO.
        
        Args:
            certificate_path: Caminho para o certificado digital (mTLS)
        
        Returns:
            Token de acesso ou None em caso de erro
        """
        try:
            async with httpx.AsyncClient() as client:
                # Em produção, usar mTLS com certificado digital
                response = await client.get(
                    self.auth_service_url,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    
                    logger.info(
                        "Token obtido do serviço de autorização",
                        expires_in=data.get("expires_in")
                    )
                    
                    return token
                else:
                    logger.error(
                        "Erro ao obter token",
                        status_code=response.status_code,
                        response=response.text
                    )
                    return None
                    
        except httpx.RequestError as e:
            logger.error("Erro de rede ao obter token", error=str(e))
            return None
        except Exception as e:
            logger.error("Erro inesperado ao obter token", error=str(e))
            return None
    
    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Cria um token JWT de acesso.
        
        Args:
            data: Dados a serem incluídos no token
            expires_delta: Tempo de expiração customizado
        
        Returns:
            Token JWT codificado
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.token_expire_minutes
            )
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt


# Instância singleton do serviço de autenticação
_auth_service_instance: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """
    Retorna a instância singleton do AuthService.
    Usado para injeção de dependências no FastAPI.
    
    Returns:
        Instância do AuthService
    """
    global _auth_service_instance
    
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    
    return _auth_service_instance

