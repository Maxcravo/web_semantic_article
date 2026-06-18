import os
import urllib.error
from collections import Counter
from langchain_core.tools import tool
from SPARQLWrapper import SPARQLWrapper, JSON

DEFAULT_ENDPOINT = os.getenv("SPARQL_ENDPOINT", "http://dbpedia.org/sparql")

@tool
def execute_sparql_aggregation(query: str) -> str:
    """
    Executa uma consulta SPARQL de agregação (GROUP BY, COUNT, ORDER BY) para descobrir propriedades
    mais frequentes globalmente ou localmente.
    
    Use esta ferramenta PRIMEIRO para descobrir estatísticas (ex: quais são os diretores mais comuns 
    em um conjunto de filmes, ou quais gêneros são mais prevalentes).
    
    Se esta consulta falhar por 'timeout' ou erro no servidor, você receberá uma mensagem de erro.
    Nesse caso, você DEVE usar a ferramenta de fallback 'analyze_local_frequencies' com uma query simples.
    
    Args:
        query: Uma string contendo a consulta SPARQL de agregação.
    """
    try:
        sparql = SPARQLWrapper(DEFAULT_ENDPOINT)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(15) # Timeout curto para evitar que o agente trave
        
        results = sparql.query().convert()
        bindings = results.get("results", {}).get("bindings", [])
        
        if not bindings:
            return "Nenhuma agregação encontrada para esta consulta."
            
        output = []
        for result in bindings:
            row = {var: result[var]["value"] for var in result}
            output.append(str(row))
            
        return "Resultados da Agregação (Top resultados):\n" + "\n".join(output)
        
    except urllib.error.URLError as e:
        return f"[TIMEOUT/ERRO DE REDE] A consulta SPARQL falhou ou excedeu o limite de tempo: {str(e)}. Use a ferramenta analyze_local_frequencies como fallback."
    except Exception as e:
        return f"[ERRO SPARQL] A consulta falhou: {str(e)}. Corrija a sintaxe ou use analyze_local_frequencies se for erro de processamento."

@tool
def analyze_local_frequencies(query_spo: str) -> str:
    """
    Ferramenta de fallback para calcular frequências localmente (no Python) quando a agregação 
    SPARQL dá timeout ou falha.
    
    O LLM deve fornecer uma consulta que retorne variáveis '?p' (propriedade) e '?o' (objeto/valor),
    limitando os resultados (ex: LIMIT 500) para extrairmos estatísticas sem sobrecarregar o endpoint.
    Exemplo: SELECT ?p ?o WHERE { ?s rdf:type dbo:Film . ?s ?p ?o } LIMIT 500
    
    Args:
        query_spo: Uma consulta SPARQL simples que DEVE retornar as variáveis '?p' e '?o'.
    """
    try:
        sparql = SPARQLWrapper(DEFAULT_ENDPOINT)
        sparql.setQuery(query_spo)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(20)
        
        results = sparql.query().convert()
        bindings = results.get("results", {}).get("bindings", [])
        
        if not bindings:
            return "A consulta não retornou resultados para processamento local."
            
        # Verifica se as variáveis estão presentes
        if len(bindings) > 0 and not ("p" in bindings[0] and "o" in bindings[0]):
            return "ERRO: A consulta deve selecionar as variáveis '?p' e '?o' explícitas."
            
        prop_counter = Counter()
        value_counter_by_prop = {}
        
        for result in bindings:
            p = result.get("p", {}).get("value", "")
            o = result.get("o", {}).get("value", "")
            
            if p and o:
                # Ignora propriedades de infraestrutura comum para focar no conteúdo
                if "w3.org/1999/02/22-rdf-syntax-ns#type" in p or "wiki" in p:
                    continue
                    
                prop_counter[p] += 1
                
                if p not in value_counter_by_prop:
                    value_counter_by_prop[p] = Counter()
                value_counter_by_prop[p][o] += 1
                
        if not prop_counter:
            return "Nenhuma propriedade útil encontrada para agregação."
            
        # Seleciona os top 3 predicados mais frequentes
        top_props = prop_counter.most_common(3)
        
        output = ["Análise de Frequência Local (Fallback processado em Python):"]
        for prop, count in top_props:
            output.append(f"\n- Predicado Frequente: <{prop}> (aparece {count} vezes)")
            
            # Pega os 3 valores mais comuns deste predicado
            top_values = value_counter_by_prop[prop].most_common(3)
            output.append("  Valores mais comuns para este predicado:")
            for val, v_count in top_values:
                # Trunca valores muito longos (como descrições)
                display_val = val[:50] + "..." if len(val) > 50 else val
                output.append(f"    * {display_val} ({v_count} ocorrências)")
                
        output.append("\nCom base nestas estatísticas, formule uma pergunta ao usuário (ex: 'Você prefere o valor X ou Y para a propriedade Z?') para refinar a busca.")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Erro no processamento local: {str(e)}"
