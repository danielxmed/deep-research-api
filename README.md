# Sciflow Deep Research API

Uma API robusta para realizar pesquisas científicas profundas utilizando o modelo Sonar Deep Research da Perplexity AI.

## 📋 Descrição

A Sciflow Deep Research API é uma aplicação FastAPI projetada para realizar pesquisas científicas abrangentes e estruturadas. Ela utiliza o modelo Sonar Deep Research da Perplexity AI para gerar análises profundas e apresenta os resultados no formato de artigos científicos bem estruturados.

### Principais Recursos

- 🔍 **Pesquisa Científica Profunda**: Realiza análises abrangentes através do modelo Sonar Deep Research
- 📝 **Formatação de Artigo Científico**: Apresenta resultados como artigos acadêmicos estruturados
- 📊 **Citações e Referências**: Inclui e formata automaticamente as citações das fontes consultadas
- 🔄 **Controle de Taxa**: Limita o número de solicitações para evitar sobrecarga
- 🛡️ **Tratamento de Erros Robusto**: Gerencia falhas de forma elegante com mensagens claras
- 📈 **Monitoramento e Logging**: Registra solicitações e métricas para análise de desempenho

## 🚀 Tecnologias

- [FastAPI](https://fastapi.tiangolo.com/): Framework web assíncrono de alto desempenho
- [Uvicorn](https://www.uvicorn.org/): Servidor ASGI para aplicações Python
- [Perplexity AI API](https://docs.perplexity.ai/): Modelo Sonar Deep Research para pesquisas científicas
- [Python 3.11+](https://www.python.org/): Linguagem de programação
- [Google Cloud Run](https://cloud.google.com/run): Plataforma de deploy serverless

## 📥 Instalação

### Pré-requisitos

- Python 3.11+
- Conta na API da Perplexity com acesso ao modelo Sonar Deep Research

### Configuração

1. Clone o repositório:
    ```bash
    git clone https://github.com/danielxmed/sciflow-deepresearch-api.git
    cd sciflow-deepresearch-api
    ```

2. Crie e ative um ambiente virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3. Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

4. Configure as variáveis de ambiente:
    ```bash
    cp .env.example .env
    # Edite o arquivo .env com sua chave de API da Perplexity
    ```

## 🏃 Execução

### Localmente

Execute o servidor de desenvolvimento:

```bash
python -m app.main
```

Ou com Uvicorn diretamente:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Acesse a documentação da API em: http://localhost:8080/docs

### Docker

Para construir e executar com Docker:

```bash
docker build -t sciflow-deepresearch-api .
docker run -p 8080:8080 --env-file .env sciflow-deepresearch-api
```

## 📚 Uso da API

POST /api/v1/research/deep-research
X-API-Key: sua_chave_api_sciflow
Content-Type: application/json

#### Resposta

```json
{
  "research_id": "a2f2ce2d-7b7e-48f8-8b56-4509d39e1937",
  "query": "Impacto da IA no mercado de trabalho global na próxima década",
  "content": "# Impacto da IA no mercado de trabalho global na próxima década\n\n**ID do Artigo**: a2f2ce2d...",
  "raw_content": "AI's impact on global job markets through 2035 will be profound...",
  "citations": ["https://www.nexford.edu/insights/how-will-ai-affect-jobs", ...],
  "usage": {
    "prompt_tokens": 19,
    "completion_tokens": 1313,
    "total_tokens": 1332,
    "citation_tokens": 9478,
    "num_search_queries": 10
  },
  "metadata": {
    "model": "sonar-deep-research",
    "created": 1743529939,
    "formatting_timestamp": "2025-04-11T15:30:45.123456"
  }
}
```

## 🚢 Deploy

### Google Cloud Run

1. Configure o Google Cloud SDK e autentique-se:
    ```bash
    gcloud auth login
    gcloud config set project [SEU_ID_DO_PROJETO]
    ```

2. Construa e envie a imagem Docker:
    ```bash
    gcloud builds submit --tag gcr.io/[SEU_ID_DO_PROJETO]/sciflow-deepresearch-api
    ```

3. Crie um secret no Secret Manager:
    ```bash
    # Criar o secret
    gcloud secrets create perplexity-api-key --replication-policy="automatic"
    
    # Adicionar a versão do secret com o valor da chave
    echo -n "sua_chave_api_perplexity" | gcloud secrets versions add perplexity-api-key --data-file=-
    
    # Conceder permissão para a conta de serviço do Cloud Run acessar o secret
    gcloud secrets add-iam-policy-binding perplexity-api-key \
      --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
      --role="roles/secretmanager.secretAccessor"
    ```

4. Implante no Cloud Run com o secret:
    ```bash
    gcloud run deploy sciflow-deepresearch-api \
      --image gcr.io/[SEU_ID_DO_PROJETO]/sciflow-deepresearch-api \
      --platform managed \
      --allow-unauthenticated \
      --region us-central1 \
      --set-env-vars "ENVIRONMENT=production" \
      --update-secrets="PERPLEXITY_API_KEY=perplexity-api-key:latest"
    ```

## 📝 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

1. Fork o projeto
2. Crie sua branch de feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📞 Contato

Para dúvidas ou sugestões, entre em contato pelo email: [daniel@nobregamedtech.com.br]
