import os
import sys
import time
import streamlit as st
import markdown
from dotenv import load_dotenv

# Adiciona o diretório base ao PATH para resolver imports do módulo 'src'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent import create_semantic_agent

# Carregar variáveis de ambiente (como a GEMINI_API_KEY)
load_dotenv()

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Agente",
    page_icon="🤖",
    layout="centered"
)

# Estilo global opcional para ajustar espaçamentos no markdown gerado
st.markdown("""
<style>
    .chat-bubble p {
        margin-bottom: 0 !important;
        
    }
    .chat-bubble {
        line-height: 1.5;
    }
    .chat-bubble pre {
        background-color: #2d2d2d !important;
        color: #f8f8f2 !important;
        padding: 12px;
        border-radius: 8px;
        overflow-x: auto;
        margin-top: 10px;
        margin-bottom: 10px;
        
    }
    .chat-bubble code {
        font-family: monospace;
        font-weight: 700;
        font-size: 15px;
    }
    /* Apenas para código inline (fora de tags pre) */
    .chat-bubble :not(pre) > code {
        background-color: #2d2d2d !important;
        color: rgb(28, 131, 225) !important;
        padding: 2px 6px;
        border-radius: 4px;
    }
    /* Para blocos de código (dentro de pre) */
    .chat-bubble pre code {
        background-color: transparent !important;
        color: inherit !important;
        padding: 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Barra Lateral (Cronômetro) ---
with st.sidebar:
    st.header("⏱️ Cronômetro de Interação")
    
    if "interaction_start_time" not in st.session_state:
        st.session_state.interaction_start_time = None
        
    if "interaction_duration" not in st.session_state:
        st.session_state.interaction_duration = None

    if st.session_state.interaction_start_time is None:
        if st.button("▶️ Iniciar Interação", use_container_width=True):
            st.session_state.interaction_start_time = time.time()
            st.session_state.interaction_duration = None
            st.rerun()
    else:
        elapsed = time.time() - st.session_state.interaction_start_time
        st.info(f"Em andamento: {int(elapsed // 60)}m {int(elapsed % 60)}s")
        
        if st.button("⏹️ Parar Interação", use_container_width=True):
            st.session_state.interaction_duration = time.time() - st.session_state.interaction_start_time
            st.session_state.interaction_start_time = None
            st.rerun()

    if st.session_state.interaction_duration is not None:
        duration = st.session_state.interaction_duration
        st.success(f"Duração total: {int(duration // 60)}m {int(duration % 60)}s")
        
    st.divider()
    st.header("Ontologia Personalizada")
    uploaded_file = st.file_uploader("Envie sua ontologia (ttl, owl, rdf, xml, txt)", type=["ttl", "owl", "rdf", "xml", "txt"])
    if uploaded_file is not None:
        if uploaded_file.size > 3 * 1024 * 1024:
            st.error("O arquivo excede o tamanho máximo de 3MB permitido.")
            st.session_state.ontology_context = None
        else:
            try:
                # Ler arquivo como utf-8
                content = uploaded_file.read().decode("utf-8")
                st.session_state.ontology_context = content
                st.success("Ontologia carregada com sucesso!")
            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {e}")
                st.session_state.ontology_context = None
    else:
        st.session_state.ontology_context = None

st.title("🤖 Agente Semântico")
st.markdown("Bem-vindo! Este assistente utiliza **Gemma4-31b + SPARQL** para ajudar a explorar e entender artigos do seu banco de dados semântico.")

# Verifica se a chave foi inserida
if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "SUA_CHAVE_DE_API_AQUI":
    st.warning("Aviso: Parece que a sua `GEMINI_API_KEY` no arquivo `.env` ainda é a padrão. Certifique-se de adicionar uma chave válida antes de realizar uma requisição real.")

# Inicializa o agente na sessão do Streamlit para manter o estado
if "agent_executor" not in st.session_state:
    try:
        with st.spinner("Inicializando o Agente Semântico..."):
            st.session_state.agent_executor = create_semantic_agent()
        st.toast("Agente inicializado com sucesso!", icon="✅")
    except Exception as e:
        st.error(f"Erro na inicialização do agente: {e}")
        st.stop()

# Função para renderizar as mensagens no estilo de app de mensagens
def render_message(role, content):
    # Converte markdown para HTML habilitando fenced_code para as crases triplas
    html_content = markdown.markdown(content, extensions=['fenced_code'])
    
    if role == "user":
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 20px;">
                <div class="chat-bubble" style="background-color: #DCF8C6; color: black; padding: 12px 20px; border-radius: 20px 20px 0px 20px; max-width: 80%; text-align: left; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                    {html_content}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                <div class="chat-bubble" style="background-color: #202225; color: #e3e4e8; padding: 12px 20px; border-radius: 20px 20px 20px 0px; max-width: 80%; text-align: left; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                    {html_content}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

import re
from src.sparql_tools import run_query_manually

# Inicializa o histórico de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

if "submit_system_prompt" not in st.session_state:
    st.session_state.submit_system_prompt = None

# Container para as mensagens
chat_container = st.container()

with chat_container:
    # Exibe mensagens do chat armazenadas no histórico
    for message in st.session_state.messages:
        render_message(message["role"], message["content"])

# --- HÍBRIDO: DETECÇÃO DE QUERY NA UI ---
pending_query = None
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_msg = st.session_state.messages[-1]["content"]
    match = re.search(r'```sparql\n(.*?)\n```', last_msg, re.IGNORECASE | re.DOTALL)
    if match:
        pending_query = match.group(1).strip()

if pending_query:
    st.info("💡 **O Agente propôs a query acima.** Você pode editá-la e executá-la manualmente, ou usar o chat abaixo para pedir mudanças em linguagem natural.")
    edited_query = st.text_area("Edite a query SPARQL (se necessário):", value=pending_query, height=200)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("▶️ Executar (DBpedia)", use_container_width=True):
            result = run_query_manually(edited_query, "dbpedia")
            st.session_state.submit_system_prompt = f"**Resultado da Query (DBpedia):**\n```json\n{result}\n```\nPor favor, responda o usuário e explique estes dados."
            st.rerun()
    with col2:
        if st.button("▶️ Executar (Wikidata)", use_container_width=True):
            result = run_query_manually(edited_query, "wikidata")
            st.session_state.submit_system_prompt = f"**Resultado da Query (Wikidata):**\n```json\n{result}\n```\nPor favor, responda o usuário e explique estes dados."
            st.rerun()
# --- FIM DO BLOCO HÍBRIDO ---

# Captura a entrada do usuário
prompt = st.chat_input("Digite sua pergunta ou comando aqui...")

if prompt or st.session_state.submit_system_prompt:
    actual_prompt = st.session_state.submit_system_prompt if st.session_state.submit_system_prompt else prompt
    
    # Limpa a flag
    st.session_state.submit_system_prompt = None
    
    # Se o prompt não for um resultado interno, exibe ele na tela
    if "Resultado da Query" not in actual_prompt:
        st.session_state.messages.append({"role": "user", "content": actual_prompt})
        with chat_container:
            render_message("user", actual_prompt)
    else:
        # Se for um resultado interno, também salva no histórico para o agente ter memória
        st.session_state.messages.append({"role": "user", "content": actual_prompt})
        with chat_container:
            render_message("user", "*(Executou a query no banco de dados e enviou os resultados para o agente)*")
    
    # Mostra um spinner enquanto o agente pensa
    with st.spinner("Pensando..."):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Invoca a execução da query com contexto de sessão
                ontology_ctx = st.session_state.get("ontology_context") or "Nenhuma ontologia personalizada carregada."
                response = st.session_state.agent_executor.invoke(
                    {"input": actual_prompt, "ontology_context": ontology_ctx},
                    config={"configurable": {"session_id": "sessao_streamlit_usuario"}}
                )
                
                # Extrai a resposta final do modelo
                output_text = response.get('output', "Desculpe, não consegui gerar uma resposta.")
                
                # Adiciona a resposta do agente ao histórico
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                
                # Renderiza a mensagem do assistente no container
                # O rerun logo abaixo fará a re-renderização, mas deixamos aqui como fallback
                
                # Rerun para atualizar a página (caso tenha um bloco sparql e precise mostrar o editor)
                st.rerun()
                
            except Exception as e:
                error_str = str(e)
                if ("500" in error_str or "503" in error_str or "504" in error_str) and attempt < max_attempts - 1:
                    st.toast(f"Erro 500 ou 503 recebido do modelo. Tentando novamente ({attempt + 1}/{max_attempts})...", icon="⏳")
                    time.sleep(2)
                    continue
                else:
                    error_msg = f"**[Erro]** Falha ao processar sua requisição após {attempt + 1} tentativas: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    st.rerun()
