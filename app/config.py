import os
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Carregar variáveis do .env se não estiver em produção
if os.getenv("ENVIRONMENT") != "production":
    load_dotenv()

class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Configurações gerais
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Sciflow Deep Research API"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Configurações da API Perplexity
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
    PERPLEXITY_API_URL: str = "https://api.perplexity.ai/chat/completions"
    PERPLEXITY_MODEL: str = "sonar-deep-research"
    
    # Validação da chave da API Perplexity
    @field_validator("PERPLEXITY_API_KEY")
    def validate_perplexity_api_key(cls, v):
        if not v and os.getenv("ENVIRONMENT") != "test":
            raise ValueError("PERPLEXITY_API_KEY não está definida")
        return v
    
    # Parâmetros padrão otimizados para pesquisa científica
    DEFAULT_TEMPERATURE: float = 0.1  # Menor temperatura para respostas mais focadas e factuais
    DEFAULT_TOP_P: float = 0.95  # Valor alto para manter diversidade em tópicos complexos
    DEFAULT_FREQUENCY_PENALTY: float = 1.0  # Reduzir repetições
    DEFAULT_PRESENCE_PENALTY: float = 0.0  # Sem penalidade de presença
    DEFAULT_WEB_SEARCH_CONTEXT_SIZE: str = "high"  # Contexto máximo para pesquisas científicas
    
    # Configurações de segurança e limitação de taxa
    RATE_LIMIT_REQUESTS: int = 20
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    MAX_TOKEN_LIMIT: int = 8000  # Limite alto para artigos científicos longos
    
    # Configurações de timeout e retry
    REQUEST_TIMEOUT_SECONDS: int = 120
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0

# Instância global das configurações
settings = Settings()