import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.models.research import DeepResearchRequest
from app.api.utils.perplexity import PerplexityClient, PerplexityApiException

# Cliente de teste
client = TestClient(app)

# Dados de exemplo para testes
SAMPLE_QUERY = "Impacto da IA no mercado de trabalho global na próxima década"
SAMPLE_REQUEST = {
    "query": SAMPLE_QUERY,
    "system_prompt": "Seja conciso e preciso.",
    "options": {
        "temperature": 0.1,
        "top_p": 0.95,
        "frequency_penalty": 1.0
    }
}

SAMPLE_API_RESPONSE = {
    "id": "test-id-12345",
    "research_id": "test-research-id",
    "model": "sonar-deep-research",
    "created": 1743529939,
    "usage": {
        "prompt_tokens": 19,
        "completion_tokens": 1313,
        "total_tokens": 1332,
        "citation_tokens": 9478,
        "num_search_queries": 10
    },
    "citations": [
        "https://www.example.com/source1",
        "https://www.example.com/source2"
    ],
    "choices": [
        {
            "index": 0,
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "# Análise do Impacto da IA\n\nA inteligência artificial terá efeitos profundos no mercado de trabalho global."
            }
        }
    ]
}

@pytest.mark.asyncio
async def test_deep_research_success():
    """Testa o endpoint de pesquisa profunda com resposta bem-sucedida."""
    
    # Mock da função de cliente da API
    with patch.object(PerplexityClient, 'execute_research', new_callable=AsyncMock) as mock_execute:
        # Configurar o mock para retornar a resposta de exemplo
        mock_execute.return_value = SAMPLE_API_RESPONSE
        
        # Fazer a solicitação para o endpoint
        response = client.post("/api/v1/research/deep-research", json=SAMPLE_REQUEST)
        
        # Verificar se a resposta foi bem-sucedida
        assert response.status_code == 200
        
        # Verificar o conteúdo da resposta
        data = response.json()
        assert data["query"] == SAMPLE_QUERY
        assert "content" in data
        assert "raw_content" in data
        assert "citations" in data
        assert len(data["citations"]) == 2
        assert "usage" in data
        assert "metadata" in data
        
        # Verificar se o cliente foi chamado com os parâmetros corretos
        called_request = mock_execute.call_args[0][0]
        assert isinstance(called_request, DeepResearchRequest)
        assert called_request.query == SAMPLE_QUERY
        assert called_request.system_prompt == "Seja conciso e preciso."
        assert called_request.options.temperature == 0.1
        assert called_request.options.top_p == 0.95

@pytest.mark.asyncio
async def test_deep_research_api_error():
    """Testa o comportamento do endpoint quando a API da Perplexity retorna um erro."""
    
    # Mock da função de cliente da API
    with patch.object(PerplexityClient, 'execute_research', new_callable=AsyncMock) as mock_execute:
        # Configurar o mock para lançar uma exceção da API
        mock_execute.side_effect = PerplexityApiException(
            message="API Error: Invalid key",
            status_code=401,
            response_body={"error": {"message": "Invalid API key"}}
        )
        
        # Fazer a solicitação para o endpoint
        response = client.post("/api/v1/research/deep-research", json=SAMPLE_REQUEST)
        
        # Verificar se o código de status é o esperado
        assert response.status_code == 401
        
        # Verificar a estrutura da resposta de erro
        data = response.json()
        assert data["error"] is True
        assert "Invalid API key" in data["message"]
        assert data["code"] == "perplexity_api_error"

@pytest.mark.asyncio
async def test_deep_research_validation_error():
    """Testa validação de entrada para o endpoint de pesquisa profunda."""
    
    # Criar solicitação inválida (faltando query obrigatória)
    invalid_request = {
        "system_prompt": "Seja conciso e preciso.",
        "options": {
            "temperature": 0.1
        }
    }
    
    # Fazer a solicitação para o endpoint
    response = client.post("/api/v1/research/deep-research", json=invalid_request)
    
    # Verificar se o código de status é o esperado
    assert response.status_code == 422
    
    # Verificar a estrutura da resposta de erro
    data = response.json()
    assert data["error"] is True
    assert data["code"] == "validation_error"
    assert len(data["details"]) > 0
    
    # Verificar se o campo obrigatório faltante foi mencionado
    field_errors = [error for error in data["details"] if "query" in error["loc"]]
    assert len(field_errors) > 0

def test_deep_research_invalid_options():
    """Testa validação de opções para o endpoint de pesquisa profunda."""
    
    # Criar solicitação com opções inválidas
    invalid_options_request = {
        "query": SAMPLE_QUERY,
        "options": {
            "temperature": 3.0,  # Fora do intervalo válido (0-2)
            "top_p": 1.5  # Fora do intervalo válido (0-1)
        }
    }
    
    # Fazer a solicitação para o endpoint
    response = client.post("/api/v1/research/deep-research", json=invalid_options_request)
    
    # Verificar se o código de status é o esperado
    assert response.status_code == 422
    
    # Verificar a estrutura da resposta de erro
    data = response.json()
    assert data["error"] is True
    assert data["code"] == "validation_error"
    
    # Verificar se os campos com valores inválidos foram mencionados
    temp_errors = [error for error in data["details"] if "temperature" in error["loc"]]
    top_p_errors = [error for error in data["details"] if "top_p" in error["loc"]]
    
    assert len(temp_errors) > 0
    assert len(top_p_errors) > 0