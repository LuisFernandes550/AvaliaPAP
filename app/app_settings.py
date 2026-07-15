"""Configurações gerais da aplicação (título, etc.)."""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.config import APP_SETTINGS_PATH

TITULO_PADRAO = "Plataforma de Gestão da Avaliação das PAPs"


@dataclass
class ConfiguracaoApp:
    titulo: str = TITULO_PADRAO


def carregar_configuracao_app() -> ConfiguracaoApp:
    if not APP_SETTINGS_PATH.exists():
        return ConfiguracaoApp()
    dados = json.loads(APP_SETTINGS_PATH.read_text(encoding="utf-8"))
    titulo = str(dados.get("titulo", TITULO_PADRAO)).strip()
    return ConfiguracaoApp(titulo=titulo or TITULO_PADRAO)


def guardar_configuracao_app(config: ConfiguracaoApp) -> None:
    APP_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    titulo = config.titulo.strip() or TITULO_PADRAO
    APP_SETTINGS_PATH.write_text(
        json.dumps({"titulo": titulo}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def titulo_app() -> str:
    return carregar_configuracao_app().titulo
