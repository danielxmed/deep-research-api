import httpx
import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings
from app.api.models.research import Message, DeepResearchRequest, PerplexityRequestOptions


class PerplexityApiException(Exception):
    """Exceção personalizada para erros da API Perplexity."""
    def __init__(self, message: str, status_code: int = None, response_body: Any = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


class PerplexityClient:
    """Cliente para interagir com a API Perplexity."""
    
    def __init__(self, api_key: str = None):
        """
        Inicializa o cliente da API Perplexity.
        
        Args:
            api_key: Chave de API da Perplexity. Se não fornecida, usa a chave das configurações.
        """
        self.api_key = api_key or settings.PERPLEXITY_API_KEY
        self.api_url = settings.PERPLEXITY_API_URL
        self.model = settings.PERPLEXITY_MODEL
        self.timeout = httpx.Timeout(settings.REQUEST_TIMEOUT_SECONDS)
    
    def _prepare_headers(self) -> Dict[str, str]:
        """
        Prepara os cabeçalhos para a requisição à API.
        
        Returns:
            Dict com os cabeçalhos HTTP.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _prepare_messages(self, query: str, system_prompt: Optional[str] = None) -> List[Message]:
        """
        Prepara as mensagens para a requisição à API.
        
        Args:
            query: A consulta do usuário.
            system_prompt: A instrução de sistema opcional.
            
        Returns:
            Lista de mensagens formatadas.
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": query})
        
        return messages
    
    def _prepare_payload(self, request: DeepResearchRequest) -> Dict[str, Any]:
        """
        Prepara o payload para a requisição à API Perplexity.
        
        Args:
            request: O objeto de solicitação de pesquisa profunda.
            
        Returns:
            Dict com o payload formatado.
        """
        # Preparar as mensagens
        messages = self._prepare_messages(request.query, request.system_prompt)
        
        # Configurar opções padrão se não fornecidas
        options = request.options or PerplexityRequestOptions()
        
        # Construir o payload base
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": options.temperature,
            "top_p": options.top_p,
            "frequency_penalty": options.frequency_penalty,
            "presence_penalty": options.presence_penalty,
            "max_tokens": settings.MAX_TOKEN_LIMIT,
            "stream": False,
            "web_search_options": {"search_context_size": options.web_search_context_size}
        }
        
        # Adicionar filtros opcionais se fornecidos
        if options.search_domain_filter:
            payload["search_domain_filter"] = options.search_domain_filter
            
        if options.search_recency_filter:
            payload["search_recency_filter"] = options.search_recency_filter
            
        return payload
    
    @retry(
        retry=retry_if_exception_type((httpx.RequestError, asyncio.TimeoutError)),
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.RETRY_BACKOFF_FACTOR)
    )
    async def execute_research(self, request: DeepResearchRequest) -> Dict[str, Any]:
        """
        Executa uma pesquisa profunda usando a API Perplexity.
        
        Args:
            request: O objeto de solicitação de pesquisa profunda.
            
        Returns:
            Dict com a resposta da API.
            
        Raises:
            PerplexityApiException: Se ocorrer um erro na comunicação com a API.
        """
        payload = self._prepare_payload(request)
        headers = self._prepare_headers()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )
                
                # Verificar se a resposta foi bem-sucedida
                response.raise_for_status()
                
                # Processar a resposta
                result = response.json()
                
                # Adicionar ID único
                result["research_id"] = str(uuid.uuid4())
                
                return result
                
        except httpx.HTTPStatusError as e:
            # Tentar extrair detalhes do erro da resposta
            error_message = "Erro na API Perplexity"
            error_details = None
            
            try:
                error_details = e.response.json()
                if "error" in error_details:
                    error_message = error_details["error"].get("message", error_message)
            except Exception:
                error_details = e.response.text
                
            raise PerplexityApiException(
                message=f"{error_message} (Status: {e.response.status_code})",
                status_code=e.response.status_code,
                response_body=error_details
            )
            
        except (httpx.RequestError, asyncio.TimeoutError) as e:
            raise PerplexityApiException(f"Erro de comunicação com a API: {str(e)}")
            
        except Exception as e:
            raise PerplexityApiException(f"Erro inesperado: {str(e)}")