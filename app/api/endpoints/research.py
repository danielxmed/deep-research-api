from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import time
import asyncio
import uuid
from datetime import datetime

from app.config import settings
from app.api.models.research import DeepResearchRequest, DeepResearchResponse, ErrorResponse
from app.api.utils.perplexity import PerplexityClient, PerplexityApiException
from app.api.utils.formatter import ScientificFormatter

# Criar router
router = APIRouter()

# Armazenamento em memória para controle de taxa (em produção, use Redis)
request_tracker = {}

async def rate_limit_check(request: Request) -> bool:
    """
    Middleware para verificar limites de taxa.
    
    Args:
        request: Objeto da solicitação.
        
    Returns:
        bool: True se dentro do limite, False se excedeu.
        
    Raises:
        HTTPException: Se o limite de taxa for excedido.
    """
    client_ip = request.client.host
    current_time = time.time()
    
    # Limpar entradas antigas
    cutoff_time = current_time - settings.RATE_LIMIT_WINDOW_SECONDS
    for ip in list(request_tracker.keys()):
        request_tracker[ip] = [timestamp for timestamp in request_tracker[ip] if timestamp > cutoff_time]
        if not request_tracker[ip]:
            del request_tracker[ip]
    
    # Verificar limite de taxa
    if client_ip in request_tracker:
        if len(request_tracker[client_ip]) >= settings.RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail=f"Limite de taxa excedido. Tente novamente em {settings.RATE_LIMIT_WINDOW_SECONDS} segundos."
            )
    else:
        request_tracker[client_ip] = []
    
    # Registrar solicitação
    request_tracker[client_ip].append(current_time)
    
    return True

async def log_request(request_data: Dict[str, Any], response_data: Dict[str, Any]) -> None:
    """
    Função para registrar solicitações e respostas (em produção, use um serviço de logging adequado).
    
    Args:
        request_data: Dados da solicitação.
        response_data: Dados da resposta.
    """
    # Em produção, integre com um serviço de logging como Stackdriver, CloudWatch, etc.
    print(f"[{datetime.now().isoformat()}] Request ID: {response_data.get('research_id', 'unknown')}")
    print(f"Query: {request_data.get('query', 'N/A')}")
    print(f"Tokens used: {response_data.get('usage', {}).get('total_tokens', 0)}")

@router.post(
    "/deep-research",
    response_model=DeepResearchResponse,
    responses={
        200: {"model": DeepResearchResponse, "description": "Pesquisa bem-sucedida"},
        400: {"model": ErrorResponse, "description": "Solicitação inválida"},
        429: {"model": ErrorResponse, "description": "Limite de taxa excedido"},
        500: {"model": ErrorResponse, "description": "Erro interno do servidor"},
    },
    summary="Realizar pesquisa científica profunda",
    description="Endpoint para realizar pesquisa científica profunda usando o modelo Sonar Deep Research da Perplexity AI."
)
async def deep_research(
    request: DeepResearchRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(rate_limit_check)
) -> Dict[str, Any]:
    """
    Endpoint para realizar pesquisa científica profunda.
    
    Args:
        request: Objeto com os parâmetros da solicitação de pesquisa.
        background_tasks: Tarefas em segundo plano para logging.
        _: Resultado da verificação de limite de taxa.
        
    Returns:
        Dict com os resultados da pesquisa formatados.
        
    Raises:
        HTTPException: Em caso de erros de solicitação ou de API.
    """
    try:
        # Inicializar cliente da API
        client = PerplexityClient()
        
        # Executar pesquisa
        result = await client.execute_research(request)
        
        # Formatar resposta como artigo científico
        formatted_response = ScientificFormatter.format_response(result, request.query)
        
        # Registrar solicitação em segundo plano
        background_tasks.add_task(log_request, request.dict(), formatted_response)
        
        return formatted_response
        
    except PerplexityApiException as e:
        # Erro da API Perplexity
        error_code = "perplexity_api_error"
        status_code = e.status_code if e.status_code else 500
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "message": str(e),
                "code": error_code,
                "details": e.response_body
            }
        )
        
    except HTTPException:
        # Re-lançar exceções HTTP existentes
        raise
        
    except Exception as e:
        # Erro inesperado
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Erro interno do servidor: {str(e)}",
                "code": "internal_server_error",
                "details": None
            }
        )