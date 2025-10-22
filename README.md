# Vinsaura Saúde - Sistema de Gerenciamento Hospitalar com IA

## Visão Geral do Projeto

O Vinsaura Saúde é um sistema protótipo de gerenciamento hospitalar que integra funcionalidades de Inteligência Artificial para auxiliar médicos e equipe na gestão de informações de pacientes. O objetivo é otimizar a busca por dados relevantes e a sumarização de históricos, utilizando modelos de linguagem grande (LLMs) como Google Gemini e OpenAI (ChatGPT).

## Estrutura do Projeto

O projeto está organizado nos seguintes diretórios e arquivos principais:

-   `database/`: Contém a configuração do banco de dados (`database_manager.py`) e os modelos de dados (`models.py`) para pacientes, médicos, consultas e exames.
-   `llm_services/`: Módulos para interação com serviços de LLM. Atualmente inclui `gemini_service.py` (para embeddings e sumarização com Google Gemini) e `openai_service.py` (para sumarização com OpenAI).
-   `vector_store/`: Contém o `vector_manager.py`, responsável por gerar e gerenciar embeddings de textos (resultados de exames, planos de tratamento) para busca semântica.
-   `templates/`: Contém os arquivos HTML para a interface web (frontend).
-   `static/`: Contém arquivos estáticos como CSS (`style.css`) e JavaScript (`script.js`) para a interface web.
-   `main.py`: O ponto de entrada principal para a aplicação em modo CLI (Command Line Interface), demonstrando as funcionalidades de IA.
-   `api.py`: Implementa uma API RESTful usando Flask para expor as funcionalidades do backend a uma interface web ou outros clientes.
-   `config.py`: (A ser criado/utilizado para configurações globais, como chaves de API ou URLs de banco de dados).
-   `README.md`: Este documento.

## Backend

### Tecnologias Principais

-   **Python:** Linguagem de programação.
-   **SQLAlchemy:** ORM para interação com o banco de dados (SQLite por padrão).
-   **Flask:** Micro-framework web para a API RESTful.
-   **Google Gemini API:** Para geração de embeddings e sumarização de texto.
-   **OpenAI API (ChatGPT):** Para sumarização de texto.

### Configuração do Ambiente

1.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate  # No Windows
    # source .venv/bin/activate # No Linux/macOS
    ```

2.  **Instale as dependências Python:**
    ```bash
    pip install Flask SQLAlchemy google-generativeai openai
    ```
    *   **Nota sobre o proxy:** Se você encontrar erros de conexão (`OSError: Failed to parse: http://usuario:senha@proxy:porta`), verifique as configurações de proxy do seu sistema ou do `pip`.

3.  **Configuração das Chaves de API:**
    Para usar as funcionalidades reais do Google Gemini e OpenAI, você precisará de chaves de API. É **altamente recomendado** configurá-las como variáveis de ambiente:

    -   **Google Gemini:** Obtenha sua chave em [Google AI Studio](https://aistudio.google.com/). Defina a variável de ambiente `GEMINI_API_KEY`.
    -   **OpenAI (ChatGPT):** Obtenha sua chave em [OpenAI Platform](https://platform.openai.com/). Defina a variável de ambiente `OPENAI_API_KEY`.

    *Exemplo (Windows PowerShell):*
    ```powershell
    $env:GEMINI_API_KEY="SUA_CHAVE_GEMINI_AQUI"
    $env:OPENAI_API_KEY="SUA_CHAVE_OPENAI_AQUI"
    # Para tornar persistente, adicione às variáveis de ambiente do sistema.
    ```

### Executando o Backend (API Flask)

1.  **Certifique-se de que o ambiente virtual está ativado.**
2.  **Execute o arquivo `api.py`:**
    ```bash
    python api.py
    ```
    A API estará disponível em `http://127.0.0.1:5000/` por padrão.

### Endpoints da API

-   **GET /**
    -   **Descrição:** Página inicial da API, retorna o nome do hospital.
    -   **Exemplo:** `http://127.0.0.1:5000/`

-   **GET /api/patients**
    -   **Descrição:** Lista todos os pacientes cadastrados no sistema.
    -   **Exemplo:** `http://127.0.0.1:5000/api/patients`

-   **GET /api/search**
    -   **Descrição:** Realiza uma busca semântica por exames médicos.
    -   **Parâmetros:**
        -   `q` (obrigatório): O termo de busca (sintoma, diagnóstico, etc.).
    -   **Exemplo:** `http://127.0.0.1:5000/api/search?q=dor+no+joelho`

-   **GET /api/summarize**
    -   **Descrição:** Gera um resumo do histórico de um paciente usando um LLM.
    -   **Parâmetros:**
        -   `patient_name` (obrigatório): O nome do paciente.
        -   `service` (opcional): O serviço de LLM a ser usado (`gemini` ou `openai`). Padrão: `gemini`.
    -   **Exemplos:**
        -   `http://127.0.0.1:5000/api/summarize?patient_name=João+Pereira&service=gemini`
        -   `http://127.0.0.1:5000/api/summarize?patient_name=Maria+Fernandes&service=openai`

## Frontend

### Tecnologias Principais

-   **HTML5:** Estrutura da página.
-   **CSS3:** Estilização (cores, layout, detalhe da cruz).
-   **JavaScript (Vanilla JS):** Interação com a API do backend e atualização dinâmica da interface.

### Estrutura

-   `templates/index.html`: O arquivo HTML principal que define a estrutura da interface.
-   `static/style.css`: Contém as regras de estilo para o visual do hospital Vinsaura Saúde (verde claro, branco, detalhe da cruz).
-   `static/script.js`: Contém o código JavaScript para:
    -   Fazer requisições assíncronas (fetch) para os endpoints da API (`/api/search`, `/api/summarize`, `/api/patients`).
    -   Processar as respostas JSON da API.
    -   Atualizar dinamicamente as seções de resultados na página.

### Visual (Cores e Detalhes)

A interface visual do Vinsaura Saúde utiliza uma paleta de cores em verde claro e branco, com um detalhe de cruz, transmitindo uma sensação de saúde, calma e cuidado.

## Como Rodar o Projeto Completo

1.  Siga as instruções de **Configuração do Ambiente** acima.
2.  **Inicie o backend:** Abra um terminal, ative o ambiente virtual e execute `python api.py`.
3.  **Abra o frontend:** Com o backend rodando, abra seu navegador e acesse `http://127.0.0.1:5000/`. A página `index.html` será servida pelo Flask.

## Executando a CLI (Alternativa)

Se preferir usar a interface de linha de comando em vez da API web, você pode executar:

```bash
python main.py
```

## Próximos Passos e Melhorias Futuras

-   **Integração de outras IAs:** Explorar a integração de Adobe Firefly (para visualização de dados/imagens), Grammarly (para revisão de texto médico) e ElevenLabs (para geração de voz).
-   **Busca na Fiocruz:** Implementar a busca por doenças na fonte da Fiocruz, possivelmente indexando esses dados em um `VectorManager` separado.
-   **Autenticação e Autorização:** Adicionar um sistema de login para médicos e diferentes níveis de acesso.
-   **Upload de Exames:** Implementar a funcionalidade de upload de arquivos de exames (PDFs, imagens) e processamento (OCR, análise de imagem).
-   **Interface de Usuário Avançada:** Melhorar a interface web com frameworks JavaScript (React, Vue, Angular) para uma experiência mais rica.
-   **Persistência de Dados:** Configurar um banco de dados mais robusto (PostgreSQL, MySQL) em vez de SQLite para produção.
-   **Testes:** Adicionar testes unitários e de integração para garantir a robustez do sistema.
