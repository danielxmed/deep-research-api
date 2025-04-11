import os
import httpx
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field # field_validator não é mais necessário aqui
from typing import List, Dict, Any, Optional

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

# *** DEFINIR A LISTA FIXA DE DOMÍNIOS AQUI ***
TRUSTED_MEDICAL_DOMAINS = [
    "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov", "scielo.org",
    "scholar.google.com", "nejm.org", "jamanetwork.com", "thelancet.com",
    "bmj.com", "journals.plos.org", "annals.org"
]
# Garantir que não excedemos o limite de 10
if len(TRUSTED_MEDICAL_DOMAINS) > 10:
    print(f"ALERTA: A lista TRUSTED_MEDICAL_DOMAINS tem {len(TRUSTED_MEDICAL_DOMAINS)} domínios, "
          "mas o limite da Perplexity é 10. Apenas os 10 primeiros serão usados.")
    # Ou lançar um erro, ou truncar a lista:
    # TRUSTED_MEDICAL_DOMAINS = TRUSTED_MEDICAL_DOMAINS[:10]

# --- Modelos Pydantic ---

class ResearchQuery(BaseModel):
    """Modelo de entrada para a query de pesquisa. O filtro de domínio é fixo."""
    query: str = Field(..., description="A pergunta ou tópico para a pesquisa aprofundada.")
    # Removido: search_domains: Optional[List[str]] = Field(...)
    # Removido: Validador check_domain_format


# Modelos de resposta da Perplexity (PerplexityUsage, PerplexityMessage, etc.) - permanecem os mesmos...
class PerplexityUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    citation_tokens: Optional[int] = None
    num_search_queries: Optional[int] = None

class PerplexityMessage(BaseModel):
    role: str
    content: str

class PerplexityChoice(BaseModel):
    index: int
    finish_reason: str
    message: PerplexityMessage
    delta: Optional[Dict[str, Any]] = None

class PerplexityResponse(BaseModel):
    id: str
    model: str
    created: int
    usage: PerplexityUsage
    citations: Optional[List[str]] = None
    object: str
    choices: List[PerplexityChoice]

# --- Configuração da API FastAPI ---
app = FastAPI(
    title="SciFlow Deep Research API",
    description=(
        "API para realizar pesquisas aprofundadas usando Perplexity Sonar Deep Research. "
        f"A busca é **limitada aos seguintes domínios**: {', '.join(TRUSTED_MEDICAL_DOMAINS[:10])}" # Atualiza descrição
    ),
    version="1.2.0" # Version bump indicando mudança de comportamento
)

# --- Variáveis Globais e Configuração ---
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

if not PERPLEXITY_API_KEY:
    print("ALERTA: Variável de ambiente PERPLEXITY_API_KEY não definida.")


# --- Endpoint da API ---

@app.post("/deep-research",
          response_model=PerplexityResponse,
          summary="Realiza pesquisa aprofundada com Perplexity (domínios fixos)", # Atualiza sumário
          tags=["Research"])
async def perform_deep_research(
    research_input: ResearchQuery = Body(...) # Modelo de entrada atualizado
):
    """
    Recebe uma query de pesquisa, envia para a API Perplexity Sonar Deep Research
    e retorna o relatório completo gerado.

    **Importante:** A busca é automaticamente restrita a um conjunto pré-definido
    de domínios científicos e médicos confiáveis para garantir a qualidade das fontes.
    """
    if not PERPLEXITY_API_KEY:
         raise HTTPException(status_code=500, detail="Chave da API Perplexity não configurada no servidor.")

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # --- Definição dos Parâmetros para Perplexity ---
    payload = {
        "model": "sonar-deep-research",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um assistente de pesquisa especializado em gerar análises profundas e "
                    "detalhadas sobre tópicos complexos, especialmente na área médica e científica, "
                    "baseado *exclusivamente* nas fontes de pesquisa fornecidas pelo filtro de domínio. " # Pode reforçar aqui
                    "Seu objetivo é produzir uma resposta abrangente, bem estruturada, baseada em evidências, "
                    "citando fontes relevantes, similar a uma seção de revisão de literatura de um artigo científico. "
                    "Maximize a profundidade e a extensão da resposta dentro dos domínios permitidos."
                )
            },
            {
                "role": "user",
                "content": research_input.query
            }
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        # *** ADICIONA O FILTRO DE DOMÍNIO FIXO AQUI ***
        "search_domain_filter": TRUSTED_MEDICAL_DOMAINS[:10], # Garante que não passamos de 10
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "year",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0.1,
        "frequency_penalty": 1.0,
        "web_search_options": {
            "search_context_size": "high"
            }
    }

    # Removemos a lógica condicional que adicionava o filtro baseado na entrada

    # --- Realizar a chamada para a API Perplexity ---
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            print(f"Enviando requisição para Perplexity com query: {research_input.query[:50]}...")
            print(f"Usando filtro de domínio fixo: {TRUSTED_MEDICAL_DOMAINS[:10]}") # Log
            response = await client.post(PERPLEXITY_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            print("Requisição para Perplexity bem-sucedida.")

            perplexity_data = PerplexityResponse(**response.json())
            return perplexity_data

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Gateway Timeout: A API Perplexity demorou muito para responder.")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Erro ao conectar com a API Perplexity: {exc}")
        except httpx.HTTPStatusError as exc:
            error_detail = f"Erro da API Perplexity: Status {exc.response.status_code}"
            try:
                 error_body = exc.response.json()
                 error_detail += f" - {error_body.get('error', {}).get('message', exc.response.text)}"
            except Exception:
                 error_detail += f" - {exc.response.text}"
            raise HTTPException(status_code=exc.response.status_code, detail=error_detail)
        except Exception as e:
             print(f"Erro inesperado: {e}")
             raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno inesperado: {e}")

# --- Execução local para teste (opcional) ---
if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor localmente com Uvicorn em http://127.0.0.1:8000")
    print(f"Filtro de domínio está fixo para: {TRUSTED_MEDICAL_DOMAINS[:10]}")
    print("Certifique-se de ter a variável de ambiente PERPLEXITY_API_KEY definida (ou em um arquivo .env)")
    uvicorn.run(app, host="127.0.0.1", port=8000)