import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'

    # MongoDB
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/tourism_db')

    # Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # ── 로컬 LLM (Ollama) ─────────────────────────────────────────────────────
    # 모델 후보: gemma4:26b | llama3.1:8b | mistral:7b | qwen2.5:14b
    OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
    LLM_MODEL   = os.environ.get('LLM_MODEL',   'gemma4:26b')
