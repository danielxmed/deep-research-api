import pytest
import re
from app.api.utils.formatter import ScientificFormatter

# Dados de exemplo para testes
SAMPLE_QUERY = "Impacto da energia solar na matriz energética global"
SAMPLE_CONTENT = """A energia solar está se tornando uma parte cada vez mais importante da matriz energética global.

Esta forma de energia renovável tem experimentado um crescimento exponencial nas últimas décadas.

Muitos países estão implementando políticas para incentivar a adoção de painéis solares, tanto em escala doméstica quanto industrial.

A redução de custos tem sido um fator crucial para este crescimento, com o preço dos painéis solares caindo mais de 80% na última década."""

SAMPLE_CITATIONS = [
    "https://www.example.com/solar-energy-report-2024",
    "https://www.example.org/renewable-energy-trends"
]

SAMPLE_API_RESPONSE = {
    "id": "test-id-12345",
    "research_id": "test-research-id",
    "model": "sonar-deep-research",
    "created": 1743529939,
    "usage": {
        "prompt_tokens": 19,
        "completion_tokens": 130,
        "total_tokens": 149,
        "citation_tokens": 500,
        "num_search_queries": 5
    },
    "citations": SAMPLE_CITATIONS,
    "choices": [
        {
            "index": 0,
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": SAMPLE_CONTENT
            }
        }
    ]
}

def test_format_citations():
    """Testa a formatação de citações."""
    
    # Chamar a função de formatação
    citations_text = ScientificFormatter.format_citations(SAMPLE_CITATIONS)
    
    # Verificar o formato
    assert "## Referências" in citations_text
    assert "[1] https://www.example.com/solar-energy-report-2024" in citations_text
    assert "[2] https://www.example.org/renewable-energy-trends" in citations_text

def test_extract_sections_from_plain_text():
    """Testa a extração de seções de texto sem formatação."""
    
    # Chamar a função de extração
    sections = ScientificFormatter.extract_sections(SAMPLE_CONTENT)
    
    # Verificar se a seção padrão está presente
    assert "Introdução" in sections
    assert sections["Introdução"] == SAMPLE_CONTENT

def test_extract_sections_from_formatted_text():
    """Testa a extração de seções de texto já formatado com cabeçalhos markdown."""
    
    # Conteúdo formatado com cabeçalhos
    formatted_content = """# Impacto da Energia Solar

## Introdução
A energia solar está se tornando importante.

## Desenvolvimento Tecnológico
Os avanços tecnológicos têm sido rápidos.

## Impacto Econômico
Os custos estão caindo drasticamente.

### Empregos no Setor
Muitos empregos estão sendo criados.
"""
    
    # Chamar a função de extração
    sections = ScientificFormatter.extract_sections(formatted_content)
    
    # Verificar as seções extraídas
    assert "Introdução" in sections
    assert "Desenvolvimento Tecnológico" in sections
    assert "Impacto Econômico" in sections
    assert "Empregos no Setor" in sections
    
    # Verificar o conteúdo de uma seção
    assert "A energia solar está se tornando importante." in sections["Introdução"]
    assert "Os avanços tecnológicos têm sido rápidos." in sections["Desenvolvimento Tecnológico"]

def test_add_scientific_structure_to_plain_text():
    """Testa a adição de estrutura científica a texto sem formatação."""
    
    # Chamar a função de estruturação
    structured_content = ScientificFormatter.add_scientific_structure(
        SAMPLE_CONTENT, 
        SAMPLE_QUERY, 
        SAMPLE_CITATIONS
    )
    
    # Verificar elementos da estrutura
    assert SAMPLE_QUERY.capitalize() in structured_content
    assert "ID do Artigo" in structured_content
    assert "Data de Publicação" in structured_content
    assert "## Resumo" in structured_content
    assert "## Introdução" in structured_content
    assert "## Conclusão" in structured_content
    assert "## Referências" in structured_content
    
    # Verificar se o conteúdo original está presente
    assert "energia solar está se tornando" in structured_content
    assert "crescimento exponencial" in structured_content
    
    # Verificar se as citações estão presentes
    assert "https://www.example.com/solar-energy-report-2024" in structured_content
    assert "https://www.example.org/renewable-energy-trends" in structured_content

def test_add_scientific_structure_to_formatted_text():
    """Testa a adição de estrutura científica a texto já formatado."""
    
    # Conteúdo formatado com cabeçalhos
    formatted_content = """## Introdução
A energia solar está se tornando importante.

## Análise de Tendências
Os avanços tecnológicos têm sido rápidos.

## Conclusão
O futuro da energia solar é promissor."""
    
    # Chamar a função de estruturação
    structured_content = ScientificFormatter.add_scientific_structure(
        formatted_content, 
        SAMPLE_QUERY, 
        SAMPLE_CITATIONS
    )
    
    # Verificar se manteve os cabeçalhos originais
    assert "## Introdução" in structured_content
    assert "## Análise de Tendências" in structured_content
    assert "## Conclusão" in structured_content
    
    # Verificar se adicionou elementos estruturais
    assert SAMPLE_QUERY.capitalize() in structured_content
    assert "ID do Artigo" in structured_content
    assert "## Referências" in structured_content

def test_format_response():
    """Testa a formatação completa da resposta da API."""
    
    # Formatar a resposta
    formatted_response = ScientificFormatter.format_response(SAMPLE_API_RESPONSE, SAMPLE_QUERY)
    
    # Verificar a estrutura da resposta
    assert formatted_response["research_id"] == "test-research-id"
    assert formatted_response["query"] == SAMPLE_QUERY
    assert "content" in formatted_response
    assert "raw_content" in formatted_response
    assert "citations" in formatted_response
    assert "usage" in formatted_response
    assert "metadata" in formatted_response
    
    # Verificar conteúdo formatado
    assert SAMPLE_QUERY.capitalize() in formatted_response["content"]
    assert "ID do Artigo" in formatted_response["content"]
    assert "## Referências" in formatted_response["content"]
    
    # Verificar conteúdo original
    assert formatted_response["raw_content"] == SAMPLE_CONTENT
    
    # Verificar citações
    assert formatted_response["citations"] == SAMPLE_CITATIONS
    
    # Verificar metadados
    assert formatted_response["metadata"]["model"] == "sonar-deep-research"
    assert "formatting_timestamp" in formatted_response["metadata"]

def test_format_response_error_handling():
    """Testa o tratamento de erros na formatação da resposta."""
    
    # Criar uma resposta incompleta da API
    incomplete_response = {
        "research_id": "test-error-id",
        # Faltando choices e outros campos importantes
    }
    
    # Formatar a resposta incompleta
    result = ScientificFormatter.format_response(incomplete_response, SAMPLE_QUERY)
    
    # Verificar se mesmo com dados incompletos retorna uma estrutura válida
    assert result["research_id"] == "test-error-id"
    assert result["query"] == SAMPLE_QUERY
    assert "content" in result
    assert "raw_content" in result
    assert "citations" in result
    assert "usage" in result
    assert "metadata" in result
    
    # Verificar se o metadata contém informação do erro
    assert "error" in result["metadata"]
    assert result["metadata"]["formatting_failed"] is True

def test_format_citations_empty():
    """Testa a formatação de citações com lista vazia."""
    
    # Chamar a função com lista vazia
    citations_text = ScientificFormatter.format_citations([])
    
    # Verificar que retorna uma string vazia
    assert citations_text == ""

def test_extract_sections_edge_cases():
    """Testa a extração de seções em casos extremos."""
    
    # Teste com string vazia
    empty_sections = ScientificFormatter.extract_sections("")
    assert "Introdução" in empty_sections
    assert empty_sections["Introdução"] == ""
    
    # Teste com apenas cabeçalhos sem conteúdo
    headers_only = "## Seção 1\n\n## Seção 2\n\n## Seção 3"
    header_sections = ScientificFormatter.extract_sections(headers_only)
    assert "Seção 1" in header_sections
    assert "Seção 2" in header_sections
    assert "Seção 3" in header_sections
    assert header_sections["Seção 1"] == ""
    assert header_sections["Seção 2"] == ""
    assert header_sections["Seção 3"] == ""