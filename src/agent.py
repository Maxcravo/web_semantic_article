from SPARQLWrapper import sparql_dataframe
from langchain_core.prompts import PromptTemplate
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from src.llm_wrapper import get_gemma_llm
from src.sparql_tools import execute_sparql_query, format_as_csv, save_to_file
from src.rag_tools import setup_ontology_retriever_tool
from src.statistical_tools import execute_sparql_aggregation, analyze_local_frequencies

# Dicionário global para armazenar o histórico de diferentes sessões (memória)
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Prompt estrito no padrão ReAct (Reasoning and Acting) com memória
REACT_PROMPT = """Você é um assistente de IA especializado em Web Semântica, projetado para atuar como um CHATBOT COLABORATIVO.
Sua tarefa é ajudar o usuário respondendo perguntas, construindo consultas SPARQL baseadas na ontologia e transformando os dados.

EVITE LOOPS INTERNOS EXTENSOS. O seu fluxo de trabalho não deve ser resolvido todo de uma vez em background. Você deve trabalhar em ETAPAS CURTAS, pausando o uso de ferramentas para consultar a opinião do usuário constantemente.

O SEU FLUXO DE TRABALHO DEVE SEGUIR ESTA LÓGICA INTERATIVA:

Fase 1: Contexto e Proposta de Query
1. Ao receber a pergunta inicial, use `search_ontology_context` se demandar conhecimento sobre o domínio.
2. Formule uma query SPARQL inicial baseada no que você entendeu.
3. PARE IMEDIATAMENTE. Use a `Final Answer` para mostrar a query ao usuário, explicar o que ela faz e PERGUNTAR se ele concorda com a abordagem ou se deseja modificar/adicionar algum filtro.

Fase 2: Execução, Estatísticas e Filtros (Após a aprovação do usuário)
4. Quando o usuário aprovar a query, use as ferramentas de agregação (`execute_sparql_aggregation` ou `analyze_local_frequencies` como fallback) para entender os resultados parciais.
5. PARE NOVAMENTE. Use a `Final Answer` para apresentar as frequências e estatísticas encontradas. Formule uma pergunta de múltipla escolha ou aberta (ex: "Notei que a maioria dos filmes encontrados são de Ação ou Comédia. Deseja focar em um desses gêneros antes de eu trazer todos os resultados?").

Fase 3: Resposta Definitiva
6. Quando o usuário responder à sua pergunta de refinamento, use `execute_sparql_query` para fazer a consulta filtrada definitiva e entregue os dados formatados na `Final Answer`.

REGRAS:
- Formate a resposta baseada no pedido (CSV, salvar arquivo, etc).
- SEJA UM CHATBOT: Você não precisa resolver o problema todo em um único pensamento. Faça uma ação, mostre ao usuário, peça feedback.
- PREFIXOS SPARQL: Ao construir QUALQUER query SPARQL, você DEVE OBRIGATORIAMENTE adicionar no topo os prefixos essenciais (ex: PREFIX wd: <http://www.wikidata.org/entity/>, PREFIX wdt: <http://www.wikidata.org/prop/direct/>),PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
 . NUNCA gere uma query ou passe-a para as ferramentas sem declarar explicitamente os prefixos que você está usando.
- TRANSPARÊNCIA OBRIGATÓRIA DA QUERY: Em toda interação (Fase 1, 2 ou 3) que envolver o planejamento, execução ou análise de uma consulta, você DEVE exibir a query SPARQL correspondente ao usuário dentro de um bloco de código markdown (```sparql ... 
```).

Você tem acesso às seguintes ferramentas:

{tools}

Para usar uma ferramenta, você DEVE usar EXATAMENTE este formato abaixo (as chaves Thought/Action/Action Input/Observation são sensíveis a maiúsculas):

Thought: Pensamento sobre o que devo fazer a seguir.
Action: O nome da ferramenta a ser usada (deve ser estritamente um destes: [{tool_names}]).
Action Input: O texto/entrada que será passado para a ferramenta.
Observation: O resultado bruto da ação.

... (este ciclo Thought/Action/Action Input/Observation pode se repetir para resolver UMA fase, mas não a tarefa inteira)

Quando você quiser falar com o usuário (seja para propor uma query, mostrar estatísticas e pedir opinião, ou dar os dados finais), você DEVE INTERROMPER o uso de ferramentas e usar OBRIGATORIAMENTE este formato:

Thought: Cheguei a um ponto onde preciso validar com o usuário, mostrar a query ou pedir feedback.
Final Answer: A sua mensagem conversacional para o usuário (pergunta, proposta ou resposta final).
```sparql
# A query SPARQL exata utilizada ou proposta nesta interação deve ser inserida aqui

Histórico de Conversação (Memória das iterações passadas):
{chat_history}

Nova Entrada do Usuário: {input}
{agent_scratchpad}"""

def create_semantic_agent():
    """
    Cria o Agente no padrão ReAct utilizando o modelo Gemma,
    adicionando as tools de SPARQL e a tool de Mini-RAG para contexto da ontologia.
    """
    # 1. Instanciar o LLM
    llm = get_gemma_llm()
    
    # 2. Configurar a Tool de Mini-RAG (Ontologia via FAISS e Google Embeddings)
    # Obs: Só funcionará perfeitamente se a chave da API estiver no ambiente na hora da execução
    try:
        rag_tool = setup_ontology_retriever_tool()
    except Exception as e:
        print(f"Aviso: Falha ao carregar a ferramenta RAG. ({e})")
        rag_tool = None
    
    # 3. Definir a lista de ferramentas disponíveis
    tools = [execute_sparql_query, format_as_csv, save_to_file, execute_sparql_aggregation, analyze_local_frequencies]
    if rag_tool:
        tools.insert(0, rag_tool)
    
    # 4. Criar o Prompt do ReAct
    prompt = PromptTemplate.from_template(REACT_PROMPT)
    
    # 5. Construir o agente seguindo a arquitetura clássica ReAct
    agent = create_react_agent(llm, tools, prompt)
    
    # 6. Criar o executor do agente com tratamento de erro de parse (muito comum em ReAct)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors="Houve um problema de formatação na sua resposta (Parse Error). Lembre-se que você DEVE usar o formato exato 'Thought: ... Action: ... Action Input: ...' ou então 'Thought: ... Final Answer: ...'.",
        max_execution_time= 60,
        max_iterations=5
    )
    
    # 7. Encapsular o executor com o gerenciador de histórico
    agent_with_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    
    return agent_with_history
