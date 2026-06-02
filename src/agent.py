from SPARQLWrapper import sparql_dataframe
from langchain_core.prompts import PromptTemplate
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from src.llm_wrapper import get_gemma_llm
from src.sparql_tools import execute_sparql_query, format_as_csv, save_to_file
from src.rag_tools import setup_ontology_retriever_tool

# Dicionário global para armazenar o histórico de diferentes sessões (memória)
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Prompt estrito no padrão ReAct (Reasoning and Acting) com memória
REACT_PROMPT = """Você é um assistente de IA especializado em Web Semântica.
Sua tarefa é ajudar o usuário respondendo perguntas, construindo consultas SPARQL baseadas na ontologia e transformando os dados.

REGRAS:
1. Sempre use a ferramenta `search_ontology_context` PRIMEIRO, se a pergunta do usuário demandar conhecimento sobre o domínio (quais classes ou propriedades usar para Filmes, Pessoas, etc).
2. Construa a consulta SPARQL rigorosamente e use a ferramenta `execute_sparql_query` para rodá-la.
3. Formate a resposta baseada no pedido. Se o usuário pedir CSV, chame a ferramenta `format_as_csv`. Se pedir para salvar, chame `save_to_file`. Caso contrário, forneça uma resposta natural.

Você tem acesso às seguintes ferramentas:

{tools}

Para usar uma ferramenta, você DEVE usar EXATAMENTE este formato abaixo (as chaves Thought/Action/Action Input/Observation são sensíveis a maiúsculas):

Thought: Pensamento sobre o que devo fazer a seguir.
Action: O nome da ferramenta a ser usada (deve ser estritamente um destes: [{tool_names}]).
Action Input: O texto/entrada que será passado para a ferramenta.
Observation: O resultado bruto da ação.

... (este ciclo Thought/Action/Action Input/Observation pode se repetir múltiplas vezes)

Quando você tiver a resposta final (seja uma explicação textual, um CSV formatado, ou uma confirmação de salvamento), você DEVE usar OBRIGATORIAMENTE este formato:

Thought: Eu agora sei a resposta final e posso exibi-la ao usuário.
Final Answer: A resposta final clara, coesa e completa para o usuário.

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
    tools = [execute_sparql_query, format_as_csv, save_to_file]
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
        handle_parsing_errors="Houve um problema de formatação na sua resposta (Parse Error). Lembre-se que você DEVE usar o formato exato 'Thought: ... Action: ... Action Input: ...' ou então 'Thought: ... Final Answer: ...'."
    )
    
    # 7. Encapsular o executor com o gerenciador de histórico
    agent_with_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    
    return agent_with_history
