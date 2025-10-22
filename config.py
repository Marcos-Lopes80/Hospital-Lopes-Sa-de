import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env no diretório raiz do projeto
load_dotenv()

# --- Chaves de API ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# --- Configurações do Projeto ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DB_PATH = os.getenv("DB_PATH", "./ia_coletor.db")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss.index")

# --- Configurações do GitHub ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER")
PROJECT_NUMBER = os.getenv("PROJECT_NUMBER")
VIEW_NAME = os.getenv("VIEW_NAME")

DATABASE_URL = f"sqlite:///{DB_PATH}"