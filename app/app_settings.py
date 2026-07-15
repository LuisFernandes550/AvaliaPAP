"""Configurações gerais da aplicação (título, etc.)."""

from __future__ import annotations

import json
from dataclasses import dataclass

from app import db
from app.config import APP_SETTINGS_PATH

TITULO_PADRAO = "Plataforma de Gestão da Avaliação das PAPs"

_KV_APP = "config_app"


@dataclass
class ConfiguracaoApp:
    titulo: str = TITULO_PADRAO


def carregar_configuracao_app() -> ConfiguracaoApp:
    valor = db.kv_get(_KV_APP)
    if valor is not None:
        dados = json.loads(valor)
        titulo = str(dados.get("titulo", TITULO_PADRAO)).strip()
        return ConfiguracaoApp(titulo=titulo or TITULO_PADRAO)
    if APP_SETTINGS_PATH.exists():
        dados = json.loads(APP_SETTINGS_PATH.read_text(encoding="utf-8"))
        titulo = str(dados.get("titulo", TITULO_PADRAO)).strip()
        config = ConfiguracaoApp(titulo=titulo or TITULO_PADRAO)
        guardar_configuracao_app(config)
        return config
    return ConfiguracaoApp()


def guardar_configuracao_app(config: ConfiguracaoApp) -> None:
    titulo = config.titulo.strip() or TITULO_PADRAO
    db.kv_set(_KV_APP, json.dumps({"titulo": titulo}, ensure_ascii=False))


def titulo_app() -> str:
    return carregar_configuracao_app().titulo
