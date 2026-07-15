from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _ler_config(chave: str, default: str = "") -> str:
    """Lê variável do ambiente ou dos Secrets do Streamlit Cloud."""
    valor = os.getenv(chave, "").strip()
    if valor:
        return valor
    try:
        import streamlit as st

        if chave in st.secrets:
            return str(st.secrets[chave]).strip()
    except Exception:
        pass
    return default


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


EM_STREAMLIT_CLOUD = _em_streamlit_cloud()


def _resolver_llm_provider() -> str:
    explicito = _ler_config("LLM_PROVIDER")
    if explicito:
        return explicito.lower()
    if EM_STREAMLIT_CLOUD:
        if _ler_config("GEMINI_API_KEY"):
            return "gemini"
        if _ler_config("OPENAI_API_KEY"):
            return "openai"
        return "auto"
    return "ollama"


DATA_DIR = _resolver_data_dir()
RELATORIOS_DIR = DATA_DIR / "relatorios"
PDF_DIR = RELATORIOS_DIR / "pdf"
CONFIG_DIR = DATA_DIR / "config"
EXPORT_DIR = DATA_DIR / "export"
DB_PATH = DATA_DIR / "pap.db"
INSTRUCOES_PATH = CONFIG_DIR / "instrucoes.json"
APP_SETTINGS_PATH = CONFIG_DIR / "app.json"
NOMES_ALUNOS_PATH = CONFIG_DIR / "nomes_alunos.json"
JURIS_APRESENTACAO_PATH = CONFIG_DIR / "juris_apresentacao.json"
ACTA_MODELO_PATH = BASE_DIR / "assets" / "Acta_Pap2526.xlsx"
ACTA_PATH = EXPORT_DIR / "Acta_Pap2526.xlsx"

for pasta in (DATA_DIR, RELATORIOS_DIR, PDF_DIR, CONFIG_DIR, EXPORT_DIR):
    pasta.mkdir(parents=True, exist_ok=True)

# Motor de IA: ollama (local, gratuito) | openai (ChatGPT) | gemini | auto
LLM_PROVIDER = _resolver_llm_provider()
OLLAMA_BASE_URL = _ler_config("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = _ler_config("OLLAMA_MODEL", "llama3.2")

OPENAI_API_KEY = _ler_config("OPENAI_API_KEY")
OPENAI_MODEL = _ler_config("OPENAI_MODEL", "gpt-4o-mini")

GEMINI_API_KEY = _ler_config("GEMINI_API_KEY")
GEMINI_MODEL = _ler_config("GEMINI_MODEL", "gemini-2.0-flash")

NOTA_MINIMA = 1
NOTA_MAXIMA = 20

# Autenticação — altere no .env antes do primeiro arranque
ADMIN_USERNAME = _ler_config("PAP_ADMIN_USER", "admin")
ADMIN_PASSWORD = _ler_config("PAP_ADMIN_PASSWORD", "admin")
ADMIN_NOME = _ler_config("PAP_ADMIN_NOME", "Administrador")


def obter_config_ia() -> dict[str, str]:
    """Lê a configuração de IA em tempo de execução (Secrets do Streamlit Cloud)."""
    gemini_key = _ler_config("GEMINI_API_KEY")
    openai_key = _ler_config("OPENAI_API_KEY")
    provider = _ler_config("LLM_PROVIDER")
    if not provider:
        if EM_STREAMLIT_CLOUD:
            if gemini_key:
                provider = "gemini"
            elif openai_key:
                provider = "openai"
            else:
                provider = "auto"
        else:
            provider = "ollama"
    return {
        "provider": provider.lower(),
        "ollama_base_url": _ler_config("OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollama_model": _ler_config("OLLAMA_MODEL", "llama3.2"),
        "openai_api_key": openai_key,
        "openai_model": _ler_config("OPENAI_MODEL", "gpt-4o-mini"),
        "gemini_api_key": gemini_key,
        "gemini_model": _ler_config("GEMINI_MODEL", "gemini-2.0-flash"),
    }
