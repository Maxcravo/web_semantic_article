================================================================================
GUIA DE EXECUÇÃO DO SISTEMA A PARTIR DO GITHUB & CONFIGURAÇÃO DO MODELO GEMMA
================================================================================

REFERÊNCIA GERADA UTILIZANDO INTELIGÊNCIA ARTIFICIAL

Este guia descreve os passos necessários para clonar, configurar e executar o 
Agente Semântico utilizando o modelo Gemma a partir do repositório do GitHub.

O sistema possui duas interfaces de execução:
1. Interface Web Interativa (Streamlit) -> Recomendada.
2. Interface via Linha de Comando (CLI).

--------------------------------------------------------------------------------
1. REQUISITOS PRÉVIOS
--------------------------------------------------------------------------------
Antes de começar, certifique-se de ter instalado em seu computador:
- Git (para clonar o repositório)
- Python 3.13 ou superior
- Uma chave de API do Google Gemini (GEMINI_API_KEY)
  * Para obter sua chave de API, acesse o Google AI Studio em:
    https://aistudio.google.com/

--------------------------------------------------------------------------------
2. PASSO A PASSO PARA EXECUÇÃO
--------------------------------------------------------------------------------

PASSO 1: CLONAR O REPOSITÓRIO
Abra o terminal do seu sistema operacional e execute os seguintes comandos:
  git clone <URL_DO_REPOSITORIO_GITHUB>
  cd <NOME_DO_REPOSITORIO>

PASSO 2: INSTALAÇÃO DAS DEPENDÊNCIAS
Você pode optar por uma das duas formas abaixo para gerenciar o ambiente e as 
dependências. O projeto possui suporte nativo ao gerenciador de pacotes 'uv'.

Opção A: Utilizando o Gerenciador 'uv' (Recomendado - Mais rápido e moderno)
  Se você ainda não possui o 'uv' instalado, instale-o com o seguinte comando:
    No Linux/macOS:
      curl -LsSf https://astral.sh/uv/install.sh | sh
    No Windows (PowerShell):
      powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

  Após instalar o 'uv', execute o comando abaixo no diretório raiz do projeto para
  instalar todas as dependências automaticamente:
    uv sync

Opção B: Utilizando Python Virtualenv clássico e pip
  1. Crie o ambiente virtual:
     python -m venv .venv
  2. Ative o ambiente virtual:
     No Linux/macOS:
       source .venv/bin/activate
     No Windows (PowerShell):
       .venv\Scripts\Activate.ps1
     No Windows (Prompt de Comando):
       .venv\Scripts\activate.bat
  3. Instale as dependências listadas no pyproject.toml:
     pip install -e .

PASSO 3: CONFIGURAR O ARQUIVO DE VARIÁVEIS DE AMBIENTE (.env)
O sistema necessita das variáveis de ambiente corretas para acessar os modelos de
IA e endpoints SPARQL.

1. Crie um arquivo chamado `.env` na raiz do projeto (mesma pasta onde está o env_example.txt).
2. Adicione as seguintes variáveis de configuração no arquivo:

# ==============================================================================
# CONFIGURAÇÃO DE VARIÁVEIS DE AMBIENTE (.env)
# ==============================================================================
# Chave de API do Google Gemini (Necessária para executar o modelo Gemma)
GEMINI_API_KEY="SUA_CHAVE_DE_API_AQUI"

# Endpoint SPARQL Padrão para consultas na DBpedia
SPARQL_ENDPOINT="http://dbpedia.org/sparql"

# Endpoint SPARQL Padrão para consultas no Wikidata
WIKIDATA_ENDPOINT="https://query.wikidata.org/sparql"
# ==============================================================================

* Importante: Substitua "SUA_CHAVE_DE_API_AQUI" pela sua chave real de API do Google.

PASSO 4: EXECUTAR O SISTEMA

Interface Web (Streamlit) - Interface Recomendada:
  Se você utilizou o 'uv' (Opção A):
    uv run streamlit run app.py
  Se você utilizou venv/pip (Opção B):
    streamlit run app.py

--------------------------------------------------------------------------------
3. SOBRE A CONFIGURAÇÃO DO MODELO GEMMA E RAG VETORIAL
--------------------------------------------------------------------------------
- **Modelo Gemma:** Por padrão, o agente utiliza o modelo `gemma-4-31b-it` através
  da integração `langchain-google-genai` que se conecta via API do Gemini com a
  sua chave privada configurada no arquivo `.env`.
- **Mini-RAG da Ontologia:** Na primeira execução de qualquer uma das interfaces,
  o sistema criará automaticamente a base vetorial em `data/faiss_index/` a partir
  do arquivo de contexto da ontologia (`data/ontology_context.txt`). Para isso, 
  o sistema baixará do Hugging Face o modelo de embeddings local:
  `jinaai/jina-embeddings-v5-text-small`.
- **Estratégia do Agente:** O agente foi desenvolvido utilizando a arquitetura
  ReAct (Reasoning and Acting). Ele interage com o usuário propondo consultas
  SPARQL explicadas e permitindo que o usuário as refine e execute de forma
  híbrida e controlada na interface.
