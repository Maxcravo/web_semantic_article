import os
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from dotenv import load_dotenv


def get_gemma_llm(model_name: str = "gemma-4-31b-it", temperature: float = 0.4, timeoutTime = 90 ):
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    print(api_key)
    
    """
    Inicializa o modelo Gemma via integração do Google GenAI para LangChain.
    O nome do modelo pode ser ajustado conforme a disponibilidade na API ou Vertex AI.
    
    Args:
        model_name (str): Nome do modelo na plataforma do Google (ex: 'gemma4-27b').
        temperature (float): Criatividade da geração do modelo.
    
    Returns:
        ChatGoogleGenAI: Instância do LLM compatível com LangChain.
    """
    
    if not api_key:
        raise ValueError("A variável de ambiente 'GEMINI_API_KEY' não está definida.")
        
    # Inicializando o modelo através da biblioteca langchain-google-genai
    # (Que utiliza por baixo a infraestrutura da Google GenAI)
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        timeout= timeoutTime
    )
    return llm
