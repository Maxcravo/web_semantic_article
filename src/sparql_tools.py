import os
from langchain_core.tools import tool
from SPARQLWrapper import SPARQLWrapper, JSON

# Define o endpoint a ser utilizado (por padrão DBpedia)
DEFAULT_ENDPOINT = os.getenv("SPARQL_ENDPOINT", "http://dbpedia.org/sparql")

@tool
def execute_sparql_query(query: str) -> str:
    """
    Executa uma consulta SPARQL em um endpoint da Web Semântica.
    Utilize esta ferramenta para buscar dados estruturados, descobrir relações e extrair entidades de grafos de conhecimento.
    
    Args:
        query: Uma string contendo a consulta SPARQL estrita e válida.
    """
    try:
        # Configura a conexão
        sparql = SPARQLWrapper(DEFAULT_ENDPOINT)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        
        # Executa a query
        results = sparql.query().convert()
        
        # Formata o retorno JSON para uma representação amigável ao LLM
        bindings = results.get("results", {}).get("bindings", [])
        if not bindings:
            # Caso a consulta retorne verdadeiro/falso (ASK query)
            if "boolean" in results:
                return str(results["boolean"])
            return "A consulta foi executada com sucesso, mas não retornou resultados."
            
        output = []
        for result in bindings:
            # Puxa o valor resolvido para cada variável mapeada no retorno do SPARQL
            row = {var: result[var]["value"] for var in result}
            output.append(str(row))
            
        return "\n".join(output)
        
    except Exception as e:
        return f"Erro ao executar a consulta SPARQL: {str(e)}"

@tool
def format_as_csv(data_string: str) -> str:
    """
    Converte os resultados da execução de uma consulta (em formato string de dicionários) para CSV.
    
    Args:
        data_string: A string contendo as linhas de dados (normalmente a saída direta de `execute_sparql_query`).
    """
    import csv
    import io
    import ast
    
    try:
        lines = [line.strip() for line in data_string.strip().split('\n') if line.strip()]
        data = []
        for line in lines:
            try:
                row = ast.literal_eval(line)
                if isinstance(row, dict):
                    data.append(row)
            except Exception:
                pass
                
        if not data:
            return "Erro: Não foi possível parsear os dados para conversão CSV."

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    except Exception as e:
        return f"Erro ao formatar para CSV: {str(e)}"

@tool
def save_to_file(content: str, filename: str) -> str:
    """
    Salva uma string (texto livre, CSV ou JSON) em um arquivo no disco.
    Utilize quando o usuário pedir explicitamente para salvar um arquivo.
    
    Args:
        content: O conteúdo em texto a ser salvo.
        filename: O nome/caminho do arquivo (ex: 'resultados.csv', 'dados.json').
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Arquivo '{filename}' salvo com sucesso."
    except Exception as e:
        return f"Erro ao salvar o arquivo: {str(e)}"
