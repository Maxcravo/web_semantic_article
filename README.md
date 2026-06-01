# Agente Semântico com Gemma e SPARQLWrapper

Este é um projeto em Python focado na criação de agentes baseados no framework [LangChain](https://python.langchain.com/), utilizando a biblioteca `google-genai` para acessar modelos da família Gemma (especificamente configurado para o `gemma4-27b`) e integrando a biblioteca `SPARQLWrapper` para realizar consultas em grafos de conhecimento na Web Semântica.

## Funcionalidades
- **Agente Autônomo:** Utiliza LangChain para tomada de decisão.
- **Modelos de Peso Aberto:** Configurado para se conectar à API Google utilizando modelos Gemma (ex: `gemma4-27b`).
- **Consultas Semânticas:** Ferramentas nativas do LangChain baseadas no `SPARQLWrapper` para gerar e executar consultas SPARQL.

## Como Executar

1. Crie um ambiente virtual e ative-o (opcional, mas recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   - Copie o arquivo `.env.example` para `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edite o arquivo `.env` inserindo sua chave de API do Google GenAI.

4. Execute o agente:
   ```bash
   python src/main.py
   ```
