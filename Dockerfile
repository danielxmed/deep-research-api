FROM python:3.11-slim

WORKDIR /app

# Copiar requerimentos e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Expor porta para a aplicação
EXPOSE 8080

# Configuração de variáveis de ambiente para produção
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Comando para rodar a aplicação
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}