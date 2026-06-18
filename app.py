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
    page_title="Agente Semântico",
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
</style>
""", unsafe_allow_html=True)

st.title("🤖 Agente Semântico de Artigos")
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
    # Converte markdown para HTML (ex: texto em negrito, listas)
    html_content = markdown.markdown(content)
    
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
                <div class="chat-bubble" style="background-color: #F1F0F0; color: black; padding: 12px 20px; border-radius: 20px 20px 20px 0px; max-width: 80%; text-align: left; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                    {html_content}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# Inicializa o histórico de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Container para as mensagens
chat_container = st.container()

with chat_container:
    # Exibe mensagens do chat armazenadas no histórico
    for message in st.session_state.messages:
        render_message(message["role"], message["content"])

# Captura a entrada do usuário
if prompt := st.chat_input("Digite sua pergunta ou comando aqui..."):
    # Adiciona a mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Renderiza a mensagem recém-enviada do usuário imediatamente no container
    with chat_container:
        render_message("user", prompt)
    
    # Mostra um spinner enquanto o agente pensa
    with st.spinner("Pensando..."):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Invoca a execução da query com contexto de sessão
                response = st.session_state.agent_executor.invoke(
                    {"input": prompt},
                    config={"configurable": {"session_id": "sessao_streamlit_usuario"}}
                )
                
                # Extrai a resposta final do modelo
                output_text = response.get('output', "Desculpe, não consegui gerar uma resposta.")
                
                # Adiciona a resposta do agente ao histórico
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                
                # Renderiza a mensagem do assistente no container
                with chat_container:
                    render_message("assistant", output_text)
                    
                # Sai do loop de tentativas se foi bem sucedido
                break
                
            except Exception as e:
                error_str = str(e)
                # Verifica se é um erro 500 ou 503 e se ainda temos tentativas
                if ("500" in error_str or "503" in error_str) and attempt < max_attempts - 1:
                    st.toast(f"Erro 500 ou 503 recebido do modelo. Tentando novamente ({attempt + 1}/{max_attempts})...", icon="⏳")
                    time.sleep(2) # Pausa curta antes de tentar novamente
                    continue
                else:
                    error_msg = f"**[Erro]** Falha ao processar sua requisição após {attempt + 1} tentativas: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    break
