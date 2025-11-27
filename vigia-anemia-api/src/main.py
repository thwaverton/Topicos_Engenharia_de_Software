"""
Aplicação principal FastAPI.
Ponto de entrada da API de ingestão de hemogramas FHIR.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import hemograma_router
from src.core.config import settings
from src.core.logging import configure_logging, get_logger

# Configura logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    
    Startup:
    - Configura logging
    - Inicializa conexões (Redis, SQS, etc.)
    
    Shutdown:
    - Fecha conexões
    - Limpa recursos
    """
    # Startup
    logger.info(
        "Iniciando VIGIA-Anemia API",
        environment=settings.environment,
        version=settings.api_version
    )
    
    yield
    
    # Shutdown
    logger.info("Encerrando VIGIA-Anemia API")


# Cria aplicação FastAPI
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Registra rotas
app.include_router(
    hemograma_router,
    prefix=settings.api_prefix
)


@app.get("/")
async def root():
    """Endpoint raiz da API."""
    return {
        "service": "VIGIA-Anemia Infantil GO - API",
        "version": settings.api_version,
        "status": "running",
        "docs": f"{settings.api_prefix}/docs"
    }


@app.get("/health")
async def health():
    """Endpoint de health check global."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": settings.api_version
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas."""
    logger.error(
        "Exceção não tratada",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Erro interno do servidor"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )

