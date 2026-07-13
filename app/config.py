from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _em_streamlit_cloud() -> bool:
    if os.getenv("STREAMLIT_RUNTIME_ENVIRONMENT") == "cloud":
        return True
    return str(BASE_DIR).startswith("/mount/src")


def _resolver_data_dir() -> Path:
    override = os.getenv("PAP_DATA_DIR", "").strip()
    if override:
        return Path(override)
    if _em_streamlit_cloud():
        return Path("/tmp/avaliapap/data")
    return BASE_DIR / "data"


DATA_DIR = _resolver_data_dir()
RELATORIOS_DIR = DATA_DIR / "relatorios"
PDF_DIR = RELATORIOS_DIR / "pdf"
CONFIG_DIR = DATA_DIR / "config"
EXPORT_DIR = DATA_DIR / "export"
DB_PATH = DATA_DIR / "pap.db"
INSTRUCOES_PATH = CONFIG_DIR / "instrucoes.json"
APP_SETTINGS_PATH = CONFIG_DIR / "app.json"
NOMES_ALUNOS_PATH = CONFIG_DIR / "nomes_alunos.json"
ACTA_MODELO_PATH = BASE_DIR / "assets" / "Acta_Pap2526.xlsx"
ACTA_PATH = EXPORT_DIR / "Acta_Pap2526.xlsx"

for pasta in (DATA_DIR, RELATORIOS_DIR, PDF_DIR, CONFIG_DIR, EXPORT_DIR):
    pasta.mkdir(parents=True, exist_ok=True)

# Motor de IA: ollama (local, gratuito) | openai (ChatGPT) | gemini | auto
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

NOTA_MINIMA = 1
NOTA_MAXIMA = 20

# Autenticação — altere no .env antes do primeiro arranque
ADMIN_USERNAME = os.getenv("PAP_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("PAP_ADMIN_PASSWORD", "admin")
ADMIN_NOME = os.getenv("PAP_ADMIN_NOME", "Administrador")
