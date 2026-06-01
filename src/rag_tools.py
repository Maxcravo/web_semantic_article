import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.tools.retriever import create_retriever_tool

# Caminho para o arquivo da ontologia
ONTOLOGY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ontology_context.txt")

def setup_ontology_retriever_tool():
    """
    Lê o contexto da ontologia, cria o banco de dados vetorial FAISS em memória
    e retorna uma 'tool' nativa do LangChain para o agente usá-la como um RAG.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente 'GEMINI_API_KEY' não está definida.")

    if not os.path.exists(ONTOLOGY_FILE):
        raise FileNotFoundError(f"Arquivo de contexto não encontrado: {ONTOLOGY_FILE}")
        
    # 1. Carregar o documento
    loader = TextLoader(ONTOLOGY_FILE, encoding='utf-8')
    docs = loader.load()
    
    # 2. Quebrar o texto em chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)
    
    # 3. Gerar Embeddings usando o Google GenAI
    # 'models/embedding-001' é o modelo de embedding padrão e leve do Google
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    
    # 4. Criar o Vector Store com FAISS local na memória
    vectorstore = FAISS.from_documents(splits, embeddings)
    
    # 5. Configurar o Retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    
    # 6. Criar e retornar a ferramenta (Tool)
    tool = create_retriever_tool(
        retriever,
        name="search_ontology_context",
        description="""Pesquisa no documento de contexto da ontologia. 
Use isto SEMPRE ANTES de formular a query SPARQL para saber quais classes e propriedades utilizar para o domínio requisitado (ex: pessoas, filmes, lugares, etc)."""
    )
    
    return tool
