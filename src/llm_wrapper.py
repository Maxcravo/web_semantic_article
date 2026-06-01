import os
from langchain_google_genai import ChatGoogleGenAI

def get_gemma_llm(model_name: str = "gemma4-27b-it", temperature: float = 0.0):
    """
    Inicializa o modelo Gemma via integração do Google GenAI para LangChain.
    O nome do modelo pode ser ajustado conforme a disponibilidade na API ou Vertex AI.
    
    Args:
        model_name (str): Nome do modelo na plataforma do Google (ex: 'gemma4-27b').
        temperature (float): Criatividade da geração do modelo.
    
    Returns:
        ChatGoogleGenAI: Instância do LLM compatível com LangChain.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente 'GEMINI_API_KEY' não está definida.")
        
    # Inicializando o modelo através da biblioteca langchain-google-genai
    # (Que utiliza por baixo a infraestrutura da Google GenAI)
    llm = ChatGoogleGenAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature
    )
    return llm
