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
