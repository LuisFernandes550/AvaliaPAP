"""Camada de ligação à base de dados.

Usa Postgres (Supabase) quando existe ``DATABASE_URL``; caso contrário, SQLite
local. O objetivo é persistir os dados de forma fiável na Streamlit Cloud, onde
o disco é temporário e reinicia vazio.

Todas as queries usam o placeholder ``?`` (estilo SQLite). Para Postgres, o
placeholder é convertido para ``%s`` automaticamente.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.config import DATABASE_URL, DB_PATH

IS_POSTGRES = bool(DATABASE_URL)

# Definição da chave primária auto-incremental conforme o motor.
PK_AUTO = "SERIAL PRIMARY KEY" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"

if IS_POSTGRES:  # pragma: no cover - depende do ambiente
    import psycopg2
    import psycopg2.extras
    from psycopg2 import IntegrityError as _PgIntegrityError

    INTEGRITY_ERRORS: tuple = (_PgIntegrityError,)
else:
    INTEGRITY_ERRORS = (sqlite3.IntegrityError,)


class _PgConn:
    """Adaptador para a ligação Postgres com a mesma interface do sqlite3.

    Expõe ``execute(sql, params)`` que devolve um cursor, convertendo o
    placeholder ``?`` para ``%s``.
    """

    def __init__(self, raw) -> None:
        self._raw = raw

    def execute(self, sql: str, params=()):  # noqa: ANN001
        cur = self._raw.cursor()
        cur.execute(sql.replace("?", "%s"), tuple(params) if params else None)
        return cur

    def commit(self) -> None:
        self._raw.commit()


@contextmanager
def get_conn() -> Iterator:
    """Devolve uma ligação (SQLite ou Postgres) que faz commit ao sair."""
    if IS_POSTGRES:
        raw = psycopg2.connect(
            DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor
        )
        try:
            yield _PgConn(raw)
            raw.commit()
        except Exception:
            raw.rollback()
            raise
        finally:
            raw.close()
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        raw = sqlite3.connect(str(DB_PATH.resolve()))
        raw.row_factory = sqlite3.Row
        try:
            yield raw
            raw.commit()
        finally:
            raw.close()


# --------------------------------------------------------------------------- #
# Armazenamento chave-valor para configurações (instruções, nomes, júris, app)
# --------------------------------------------------------------------------- #

_kv_pronto = False


def _garantir_kv() -> None:
    global _kv_pronto
    if _kv_pronto:
        return
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS config_kv (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
            """
        )
    _kv_pronto = True


def kv_get(chave: str) -> str | None:
    _garantir_kv()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT valor FROM config_kv WHERE chave = ?", (chave,)
        ).fetchone()
    if not row:
        return None
    return row["valor"]


def kv_set(chave: str, valor: str) -> None:
    _garantir_kv()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO config_kv (chave, valor) VALUES (?, ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
            """,
            (chave, valor),
        )


# --------------------------------------------------------------------------- #
# Exportação/importação dos dados (backup independente do motor)
# --------------------------------------------------------------------------- #

# Ordem de inserção (pais antes dos filhos, por causa das chaves estrangeiras).
_TABELAS_BACKUP = (
    "utilizadores",
    "alunos",
    "avaliacoes",
    "resumos_capitulos",
    "avaliacoes_juri",
    "materiais_drive",
    "config_kv",
)
# Tabelas com id SERIAL cuja sequência precisa de ser reposta no Postgres.
_TABELAS_SERIAL = (
    "utilizadores",
    "alunos",
    "avaliacoes",
    "resumos_capitulos",
    "avaliacoes_juri",
)


def exportar_dados() -> dict[str, list[dict]]:
    """Devolve todas as tabelas relevantes como listas de dicionários."""
    _garantir_kv()
    saida: dict[str, list[dict]] = {}
    with get_conn() as conn:
        for tabela in _TABELAS_BACKUP:
            try:
                rows = conn.execute(f"SELECT * FROM {tabela}").fetchall()
            except Exception:
                rows = []
            saida[tabela] = [dict(r) for r in rows]
    return saida


def importar_dados(dados: dict[str, list[dict]]) -> int:
    """Substitui o conteúdo das tabelas pelo backup. Devolve nº de registos."""
    _garantir_kv()
    total = 0
    with get_conn() as conn:
        # Apagar sessões e tabelas (filhos antes dos pais).
        try:
            conn.execute("DELETE FROM sessoes_auth")
        except Exception:
            pass
        for tabela in reversed(_TABELAS_BACKUP):
            conn.execute(f"DELETE FROM {tabela}")
        # Inserir na ordem de dependência.
        for tabela in _TABELAS_BACKUP:
            for linha in dados.get(tabela, []):
                if not linha:
                    continue
                cols = list(linha.keys())
                col_sql = ", ".join(cols)
                marcadores = ", ".join(["?"] * len(cols))
                conn.execute(
                    f"INSERT INTO {tabela} ({col_sql}) VALUES ({marcadores})",
                    tuple(linha[c] for c in cols),
                )
                total += 1
        # Repor as sequências no Postgres para evitar colisões de id.
        if IS_POSTGRES:
            for tabela in _TABELAS_SERIAL:
                conn.execute(
                    f"SELECT setval(pg_get_serial_sequence('{tabela}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {tabela}), 1), "
                    f"(SELECT COUNT(*) FROM {tabela}) > 0)"
                )
    return total
