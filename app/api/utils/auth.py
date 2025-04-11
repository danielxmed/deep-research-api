from fastapi import Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
from app.config import settings
import os

# Definir o esquema de autenticação por API Key no header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(request: Request, api_key: str = Depends(api_key_header)):
    """
    Middleware para verificar a API Key nas requisições.
    
    Args:
        request: Objeto da requisição.
        api_key: API Key extraída do header.
        
    Returns:
        bool: True se a autenticação for bem-sucedida.
        
    Raises:
        HTTPException: Se a autenticação falhar.
    """
    # Em ambiente de teste, podemos pular a verificação
    if os.getenv("PYTEST_RUNNING") == "1":
        return True
        
    # Verificar se a chave foi fornecida
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "message": "API Key não fornecida no header X-API-Key",
                "code": "missing_api_key",
                "details": None
            }
        )
        
    # Verificar se a chave está correta
    if api_key != settings.SCIFLOW_API_KEY:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "API Key inválida",
                "code": "invalid_api_key",
                "details": None
            }
        )
        
    return True