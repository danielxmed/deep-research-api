from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time
import uvicorn
import os
from typing import Dict, Any

from app.config import settings
from app.api.endpoints import research

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para realização de pesquisas científicas profundas usando a Perplexity AI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT != "production" else ["https://sciflow.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para medir tempo de resposta
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Handlers de exceção
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        error_info = {
            "loc": " -> ".join([str(loc) for loc in error["loc"]]),
            "msg": error["msg"],
            "type": error["type"],
        }
        errors.append(error_info)
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True, 
            "message": "Erro de validação nos dados de entrada",
            "code": "validation_error",
            "details": errors
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        # Usar o formato detalhado já definido
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                **exc.detail
            },
        )
    else:
        # Criar formato padrão
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": str(exc.detail),
                "code": f"http_{exc.status_code}",
                "details": None
            },
        )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Erro interno do servidor",
            "code": "internal_server_error",
            "details": str(exc) if settings.ENVIRONMENT != "production" else None
        },
    )

# Rota de verificação de saúde
@app.get("/health", tags=["Sistema"])
async def health_check() -> Dict[str, Any]:
    """
    Verifica o status de saúde da API.
    """
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

# Incluir routers
app.include_router(
    research.router,
    prefix=f"{settings.API_V1_STR}/research",
    tags=["Research"]
)

# Para execução local
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)