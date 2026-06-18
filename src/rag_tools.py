import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.tools.retriever import create_retriever_tool

# Caminho para o arquivo da ontologia e diretório do índice
ONTOLOGY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ontology_context.txt")
FAISS_INDEX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "faiss_index")

def setup_ontology_retriever_tool():
    """
    Lê o contexto da ontologia, cria o banco de dados vetorial FAISS e salva em disco.
    Se o índice já existir, carrega do disco para evitar recriar os embeddings.
    Retorna uma 'tool' nativa do LangChain para o agente usá-la como um RAG.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente 'GEMINI_API_KEY' não está definida.")

    # 1. Definir o modelo de embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", google_api_key=api_key)
    
    # 2. Verificar se o índice FAISS já existe localmente
    if os.path.exists(FAISS_INDEX_DIR):
        print("Carregando o Vector Store FAISS do disco...")
        vectorstore = FAISS.load_local(FAISS_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
    else:
        print("Criando um novo Vector Store FAISS...")
        if not os.path.exists(ONTOLOGY_FILE):
            raise FileNotFoundError(f"Arquivo de contexto não encontrado: {ONTOLOGY_FILE}")
            
        # Carregar o documento
        loader = TextLoader(ONTOLOGY_FILE, encoding='utf-8')
        docs = loader.load()
        
        # Quebrar o texto em chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splits = text_splitter.split_documents(docs)
        
        # Criar o Vector Store com FAISS e salvar localmente
        vectorstore = FAISS.from_documents(splits, embeddings)
        vectorstore.save_local(FAISS_INDEX_DIR)
        print("Vector Store FAISS salvo no disco.")
    
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
