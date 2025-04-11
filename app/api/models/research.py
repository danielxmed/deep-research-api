from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, model_validator
from enum import Enum


class Role(str, Enum):
    """Papéis para mensagens de chat."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class RecencyFilter(str, Enum):
    """Filtros de recência para pesquisa."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    NONE = "none"


class Message(BaseModel):
    """Modelo para mensagens enviadas para a API da Perplexity."""
    role: Role
    content: str


class PerplexityRequestOptions(BaseModel):
    """Opções para personalizar a requisição à API Perplexity."""
    temperature: float = Field(default=0.1, ge=0.0, lt=2.0, description="Controla a aleatoriedade da resposta")
    top_p: float = Field(default=0.95, ge=0.0, le=1.0, description="Limiar de amostragem de núcleo para controlar a diversidade")
    search_domain_filter: Optional[List[str]] = Field(default=None, description="Lista de domínios para filtrar resultados de pesquisa")
    search_recency_filter: Optional[RecencyFilter] = Field(default=None, description="Filtro de recência para resultados de pesquisa")
    frequency_penalty: float = Field(default=1.0, ge=0.0, le=2.0, description="Penalidade para tokens frequentes")
    presence_penalty: float = Field(default=0.0, ge=0.0, le=2.0, description="Penalidade para tokens já presentes")
    web_search_context_size: str = Field(default="high", description="Tamanho do contexto de pesquisa na web")
    
    @model_validator(mode='after')
    def validate_domain_filter(self):
        """Validar o filtro de domínio para garantir que não exceda o limite de 3."""
        if self.search_domain_filter and len(self.search_domain_filter) > 3:
            raise ValueError("O filtro de domínio está limitado a 3 domínios")
        return self


class DeepResearchRequest(BaseModel):
    """Modelo para solicitações de pesquisa profunda."""
    query: str = Field(..., min_length=5, max_length=500, description="Consulta de pesquisa")
    system_prompt: Optional[str] = Field(default="Você é um assistente de pesquisa acadêmica focado em produzir análises científicas profundas e extensas. Elabore respostas detalhadas, bem estruturadas e com fundamentação sólida, organizadas em seções claras com títulos e subtítulos. Priorize informações factuais baseadas em evidências. Inclua dados estatísticos relevantes e cite todas as fontes. Apresente múltiplas perspectivas quando apropriado. Sua resposta deve ter o formato de um artigo científico completo, com introdução, metodologia (quando aplicável), resultados, discussão e conclusão.", description="Instrução de sistema para guiar o comportamento do modelo")
    options: Optional[PerplexityRequestOptions] = Field(default=None, description="Opções para personalizar a solicitação")


class Citation(BaseModel):
    """Modelo para citações retornadas pela API."""
    url: str
    title: Optional[str] = None


class DeepResearchResponse(BaseModel):
    """Modelo para respostas de pesquisa profunda."""
    research_id: str = Field(..., description="ID único da pesquisa")
    query: str = Field(..., description="Consulta original")
    content: str = Field(..., description="Conteúdo da pesquisa formatado")
    raw_content: str = Field(..., description="Conteúdo da pesquisa não formatado")
    citations: List[str] = Field(default_factory=list, description="Lista de URLs de citação")
    usage: Dict[str, Any] = Field(default_factory=dict, description="Informações de uso de tokens")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais")


class ErrorResponse(BaseModel):
    """Modelo para respostas de erro."""
    error: bool = Field(default=True, description="Indicador de erro")
    message: str = Field(..., description="Mensagem de erro")
    code: str = Field(..., description="Código de erro")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detalhes adicionais do erro")