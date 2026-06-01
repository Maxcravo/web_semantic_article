import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório base ao PATH para resolver imports do módulo 'src'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import create_semantic_agent

def main():
    # 1. Carregar variáveis de ambiente (como a GEMINI_API_KEY)
    load_dotenv()
    
    print("======================================================")
    print(" Inicializando Agente Semântico (Gemma4-27b + SPARQL) ")
    print("======================================================")
    
    # Verifica se a chave foi inserida
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "SUA_CHAVE_DE_API_AQUI":
        print("Aviso: Parece que a sua GEMINI_API_KEY no arquivo .env ainda é a padrão.")
        print("Certifique-se de adicionar uma chave válida antes de realizar uma requisição real.\n")
    
    try:
        agent_executor = create_semantic_agent()
    except Exception as e:
        print(f"Erro na inicialização do agente: {e}")
        return

    print("Agente pronto! Para sair, digite 'sair', 'exit' ou 'quit'.\n")
    
    # 2. Loop de interação com o usuário
    while True:
        try:
            user_input = input("Você: ")
            
            # Condição de saída
            if user_input.strip().lower() in ['sair', 'exit', 'quit']:
                print("Encerrando o assistente. Até logo!")
                break
                
            # Ignora entrada vazia
            if not user_input.strip():
                continue
                
            # Invocar a execução da query com contexto de sessão (Memória)
            print("\n[Pensando...]")
            response = agent_executor.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": "sessao_usuario_1"}}
            )
            
            # Extrai o output final do modelo
            print(f"\nAgente: {response.get('output')}\n")
            
        except KeyboardInterrupt:
            print("\nOperação cancelada pelo usuário. Encerrando.")
            break
        except Exception as e:
            print(f"\n[Erro] Falha ao processar sua requisição: {e}\n")

if __name__ == "__main__":
    main()
