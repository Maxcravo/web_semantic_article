from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from src.llm_wrapper import get_gemma_llm
from src.sparql_tools import execute_sparql_query

def create_semantic_agent():
    """
    Orquestra a criação do Agente LangChain usando o modelo Gemma.
    Configura as ferramentas (tools) de consulta SPARQL.
    """
    # 1. Instanciar o LLM
    llm = get_gemma_llm(model_name="gemma4-27b")
    
    # 2. Definir a lista de ferramentas disponíveis para o agente
    tools = [execute_sparql_query]
    
    # 3. Criar o prompt do sistema para direcionar o papel e comportamento do modelo
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Você é um assistente especializado em Web Semântica e Grafos de Conhecimento.
Sua principal tarefa é ajudar o usuário a responder perguntas transformando a intenção dele em consultas SPARQL
para o endpoint configurado, usando as ferramentas disponíveis.

Siga estas instruções:
- Analise a pergunta do usuário.
- Se a pergunta demandar busca de fatos, crie uma consulta SPARQL sintaticamente correta.
- Chame a ferramenta `execute_sparql_query` enviando a consulta.
- Ao receber o resultado da ferramenta, interprete os dados e devolva uma resposta final clara, coesa e amigável para o usuário.
- Se a consulta falhar, tente reformulá-la e buscar novamente.
"""),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 4. Construir o agente com capacidade de "Tool Calling"
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 5. Criar e retornar o executor que roda o loop de interação agente-ferramenta
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor
