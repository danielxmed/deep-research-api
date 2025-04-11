#!/usr/bin/env python
"""
Script para testar o acesso aos secrets.
Use: python scripts/test_secrets.py
"""

import os
import sys
import json
from pathlib import Path
import pytest
from app.config import get_secret

def test_secrets_access():
    """Testa o acesso aos secrets configurados."""
    
    print("Testando acesso aos secrets...\n")
    
    # Variáveis de ambiente
    environment = os.getenv("ENVIRONMENT", "development")
    print(f"Ambiente: {environment}")
    
    # Definir secrets a testar
    secrets_to_test = ["PERPLEXITY_API_KEY"]
    secrets_dir = os.getenv("SECRETS_DIR", "/run/secrets")
    
    # Verificar se estamos em produção
    if environment == "production":
        print(f"\nVerificando secrets no diretório: {secrets_dir}")
        
        # Verificar se o diretório existe
        if not os.path.isdir(secrets_dir):
            print(f"ERRO: Diretório de secrets {secrets_dir} não encontrado!")
            print("Isso pode indicar que os secrets não estão montados corretamente.")
            return False
            
        # Verificar cada secret
        for secret_name in secrets_to_test:
            secret_path = Path(f"{secrets_dir}/{secret_name}")
            secret_json_path = Path(f"{secrets_dir}/{secret_name}.json")
            
            print(f"\nVerificando secret: {secret_name}")
            
            if secret_path.exists():
                print(f"✓ Secret {secret_name} encontrado como arquivo")
                # Mostrar apenas primeiros caracteres para segurança
                value = secret_path.read_text().strip()
                masked_value = value[:3] + "*" * (len(value) - 6) + value[-3:] if len(value) > 6 else "***"
                print(f"  Valor: {masked_value}")
            elif secret_json_path.exists():
                print(f"✓ Secret {secret_name} encontrado como JSON")
                try:
                    json_content = json.loads(secret_json_path.read_text())
                    if "value" in json_content:
                        value = json_content["value"]
                        masked_value = value[:3] + "*" * (len(value) - 6) + value[-3:] if len(value) > 6 else "***"
                        print(f"  Valor: {masked_value}")
                    else:
                        print("  AVISO: Chave 'value' não encontrada no JSON")
                except json.JSONDecodeError:
                    print("  ERRO: Falha ao decodificar JSON")
            else:
                print(f"✗ Secret {secret_name} NÃO encontrado!")
                
            # Verificar variável de ambiente também
            env_value = os.getenv(secret_name)
            if env_value:
                print(f"✓ Variável de ambiente {secret_name} definida")
                masked_env = env_value[:3] + "*" * (len(env_value) - 6) + env_value[-3:] if len(env_value) > 6 else "***"
                print(f"  Valor: {masked_env}")
            else:
                print(f"✗ Variável de ambiente {secret_name} NÃO definida")
    else:
        # Em desenvolvimento, verificar variáveis de ambiente
        print("\nVerificando variáveis de ambiente:")
        for secret_name in secrets_to_test:
            env_value = os.getenv(secret_name)
            if env_value:
                print(f"✓ Variável {secret_name} definida")
                masked_env = env_value[:3] + "*" * (len(env_value) - 6) + env_value[-3:] if len(env_value) > 6 else "***" 
                print(f"  Valor: {masked_env}")
            else:
                print(f"✗ Variável {secret_name} NÃO definida")
                
    print("\nTeste de secrets concluído.")
    return True

if __name__ == "__main__":
    # Adicionar o diretório raiz ao PATH para importações
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    # Testar acesso aos secrets
    success = test_secrets_access()
    
    # Sair com código de erro se falhou
    if not success:
        sys.exit(1)