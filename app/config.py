import os
import json
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Constantes para acesso a secrets
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SECRETS_DIR = os.getenv("SECRETS_DIR", "/run/secrets")  # Diretório padrão para secrets montados no Cloud Run

def get_secret(secret_name: str) -> str:
    """
    Obtém um valor de secret do Cloud Run em produção ou do .env em desenvolvimento.
    
    Args:
        secret_name: Nome do secret a ser obtido
        
    Returns:
        Valor do secret ou string vazia se não encontrado
    """
    # Em produção, tenta ler do sistema de secrets do Cloud Run
    if ENVIRONMENT == "production":
        secret_path = Path(f"{SECRETS_DIR}/{secret_name}")
        if secret_path.exists():
            return secret_path.read_text().strip()
            
        # Alternativa: alguns secrets são montados como JSON
        secret_json_path = Path(f"{SECRETS_DIR}/{secret_name}.json")
        if secret_json_path.exists():
            try:
                return json.loads(secret_json_path.read_text())["value"]
            except (json.JSONDecodeError, KeyError):
                pass
                
    # Em desenvolvimento, carrega do .env
    if ENVIRONMENT != "production":
        if not os.path.isfile('.env') and os.path.isfile('.env.example'):
            print("AVISO: Arquivo .env não encontrado. Usando .env.example")
            load_dotenv('.env.example')
        else:
            load_dotenv()
            
    # Retornar valor da variável de ambiente ou vazio
    return os.getenv(secret_name, "")

class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Configurações gerais
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Sciflow Deep Research API"
    ENVIRONMENT: str = ENVIRONMENT
    
    # Configurações da API Perplexity
    PERPLEXITY_API_KEY: str = get_secret("PERPLEXITY_API_KEY")
    PERPLEXITY_API_URL: str = "https://api.perplexity.ai/chat/completions"
    PERPLEXITY_MODEL: str = "sonar-deep-research"
    SCIFLOW_API_KEY: str = get_secret("SCIFLOW_API_KEY")

    
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
    REQUEST_TIMEOUT_SECONDS: int = 2490
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0

# Instância global das configurações
settings = Settings()