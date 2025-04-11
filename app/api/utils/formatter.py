import re
import markdown
from typing import Dict, Any, List, Optional
import uuid
import json
from datetime import datetime

class ScientificFormatter:
    """
    Classe para formatar respostas em formato de artigo científico.
    """
    
    @staticmethod
    def format_citations(citations: List[str]) -> str:
        """
        Formata as citações em estilo acadêmico.
        
        Args:
            citations: Lista de URLs de citação.
            
        Returns:
            String formatada com as citações em formato de referências.
        """
        if not citations:
            return ""
            
        references = ["## Referências\n"]
        
        for i, url in enumerate(citations, 1):
            # Formatar URL como referência
            references.append(f"[{i}] {url}\n")
            
        return "\n".join(references)
    
    @staticmethod
    def extract_sections(content: str) -> Dict[str, str]:
        """
        Extrai seções do conteúdo usando cabeçalhos markdown.
        
        Args:
            content: Conteúdo do artigo.
            
        Returns:
            Dict com seções extraídas.
        """
        # Padrão para encontrar cabeçalhos markdown
        pattern = r'^(#{1,3})\s+(.*?)$'
        lines = content.split('\n')
        sections = {}
        current_section = "Introdução"
        current_content = []
        
        # Se o conteúdo estiver vazio, retorne a seção padrão vazia
        if not content.strip():
            return {current_section: ""}
            
        # Primeiro, vamos pré-processar o texto para encontrar todos os cabeçalhos
        # Isso é útil para casos onde há apenas cabeçalhos sem conteúdo
        all_headers = []
        for line in lines:
            match = re.match(pattern, line, re.MULTILINE)
            if match:
                all_headers.append(match.group(2).strip())
        
        # Agora processamos o conteúdo para extrair as seções
        for line in lines:
            match = re.match(pattern, line, re.MULTILINE)
            if match:
                # Se encontrou um novo cabeçalho, salva a seção atual
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                    current_content = []
                
                # Define a nova seção
                current_section = match.group(2).strip()
            else:
                current_content.append(line)
                
        # Adiciona a última seção
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # Para cabeçalhos que não tiveram conteúdo associado, adicionamos uma string vazia
        for header in all_headers:
            if header not in sections:
                sections[header] = ""
            
        return sections
        
    @staticmethod
    def add_scientific_structure(content: str, query: str, citations: List[str]) -> str:
        """
        Adiciona estrutura de artigo científico ao conteúdo.
        
        Args:
            content: Conteúdo original.
            query: Consulta de pesquisa.
            citations: Lista de URLs de citação.
            
        Returns:
            Conteúdo formatado como artigo científico.
        """
        # Gerar título baseado na consulta
        title = f"# {query.strip().capitalize()}"
        
        # Adicionar metadados
        current_date = datetime.now().strftime("%d/%m/%Y")
        article_id = str(uuid.uuid4())[:8]
        
        metadata = f"""
    **ID do Artigo**: {article_id}  
    **Data de Publicação**: {current_date}  
    **Método**: Análise sistemática baseada em evidências  
    **Total de Fontes Consultadas**: {len(citations)}
    """
        
        # Verificar se o conteúdo já contém estrutura de seções ou precisa ser organizado
        has_sections = re.search(r'^#{1,3}\s+', content, re.MULTILINE)
        
        # Se não tiver seções, organizar o conteúdo
        if not has_sections:
            sections = ScientificFormatter.extract_sections(content)
            
            # Estrutura padrão de artigo científico
            structured_content = f"{title}\n\n{metadata}\n\n## Resumo\n\n"
            
            if "Introdução" in sections:
                structured_content += f"{sections['Introdução']}\n\n"
            else:
                first_paragraph = content.split('\n\n')[0] if '\n\n' in content else content
                structured_content += f"{first_paragraph}\n\n"
                
            structured_content += f"## Introdução\n\n"
            
            # Adicionar corpo do conteúdo
            main_content = '\n\n'.join([p for p in content.split('\n\n')[1:] if p])
            structured_content += f"{main_content}\n\n"
            
            # Adicionar conclusão se não existir
            if not any(s.lower().startswith('conclus') for s in sections.keys()):
                structured_content += f"## Conclusão\n\nEsta análise demonstra a complexidade e importância do tema abordado, fornecendo uma base sólida para futuras investigações científicas.\n\n"
        else:
            # Se já tiver seções, adicionar título e metadados
            if content.startswith('#'):
                # Se o conteúdo já começa com um título, adicionamos o título personalizado antes
                structured_content = f"{title}\n\n{metadata}\n\n{content}\n\n"
            else:
                structured_content = f"{title}\n\n{metadata}\n\n{content}\n\n"
        
        # Adicionar citações formatadas
        citation_text = ScientificFormatter.format_citations(citations)
        structured_content += citation_text
        
        return structured_content

    @staticmethod
    def format_response(response_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Formata a resposta completa da API para o formato de artigo científico.
        
        Args:
            response_data: Dados brutos da resposta da API.
            query: Consulta original.
            
        Returns:
            Dict com a resposta formatada.
        """
        try:
            # Verificar se temos a estrutura esperada de dados
            if "choices" not in response_data or not response_data.get("choices"):
                raise ValueError("Resposta da API não contém campo 'choices' válido")
                
            # Extrair conteúdo e citações
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # DEBUG: Verificar estrutura completa para encontrar onde estão as citações
            print("DEBUG - Estrutura da resposta para citações:")
            # Verificar todas as chaves de primeiro nível na resposta
            print(f"Chaves na resposta: {list(response_data.keys())}")
            
            # Verificar diferentes locais possíveis para as citações
            citations = []
            if "citations" in response_data:
                # Formato direto
                citations = response_data.get("citations", [])
                print(f"Citações encontradas no nível superior: {len(citations)}")
            elif "message" in response_data and "citations" in response_data.get("message", {}):
                # Algumas APIs colocam citações dentro da mensagem
                citations = response_data.get("message", {}).get("citations", [])
                print(f"Citações encontradas dentro da mensagem: {len(citations)}")
            elif "choices" in response_data and response_data.get("choices") and "citations" in response_data.get("choices", [{}])[0]:
                # Outra possibilidade é dentro do primeiro item de choices
                citations = response_data.get("choices", [{}])[0].get("citations", [])
                print(f"Citações encontradas dentro do primeiro choice: {len(citations)}")
            else:
                # Se não encontrar nenhuma citação, tentar extrair da mensagem
                try:
                    # Tenta encontrar citações no formato [1], [2] no conteúdo
                    citation_pattern = r'\[(\d+)\]\s+(http[s]?://[^\s]+)'
                    citation_matches = re.findall(citation_pattern, content)
                    if citation_matches:
                        citations = [url for _, url in citation_matches]
                        print(f"Citações extraídas do conteúdo: {len(citations)}")
                except Exception as e:
                    print(f"Erro ao tentar extrair citações do conteúdo: {str(e)}")
            
            usage = response_data.get("usage", {})
            research_id = response_data.get("research_id", str(uuid.uuid4()))
            
            # Formatar como artigo científico
            formatted_content = ScientificFormatter.add_scientific_structure(content, query, citations)
            
            # Construir resposta formatada
            formatted_response = {
                "research_id": research_id,
                "query": query,
                "content": formatted_content,
                "raw_content": content,
                "citations": citations,
                "usage": usage,
                "metadata": {
                    "model": response_data.get("model", ""),
                    "created": response_data.get("created", ""),
                    "formatting_timestamp": datetime.now().isoformat()
                }
            }
            
            return formatted_response
            
        except Exception as e:
            # Em caso de erro, retornar o mínimo de dados formatados com informação de erro
            error_message = str(e)
            
            # Tentar extrair conteúdo, se disponível
            content = ""
            if "choices" in response_data and response_data.get("choices"):
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return {
                "research_id": response_data.get("research_id", str(uuid.uuid4())),
                "query": query,
                "content": content,
                "raw_content": content,
                "citations": response_data.get("citations", []),
                "usage": response_data.get("usage", {}),
                "metadata": {
                    "model": response_data.get("model", ""),
                    "created": response_data.get("created", ""),
                    "formatting_timestamp": datetime.now().isoformat(),
                    "error": error_message,
                    "formatting_failed": True
                }
            }