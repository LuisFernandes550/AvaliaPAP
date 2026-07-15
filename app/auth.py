"""Autenticação local de utilizadores (SQLite + bcrypt)."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import bcrypt

from app import db
from app.config import ADMIN_NOME, ADMIN_PASSWORD, ADMIN_USERNAME
from app.db import PK_AUTO, get_conn as _conn


@dataclass
class Utilizador:
    id: int
    username: str
    nome: str
    role: str
    ativo: bool
    criado_em: datetime


class AuthStorage:
    def __init__(self, db_path=None) -> None:
        self._init_db()
        self._bootstrap_admin()

    @staticmethod
    def _conn():
        return _conn()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS utilizadores (
                    id {PK_AUTO},
                    username TEXT NOT NULL UNIQUE,
                    nome TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'professor',
                    ativo INTEGER NOT NULL DEFAULT 1,
                    criado_em TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ix_utilizadores_username_lower
                ON utilizadores (LOWER(username))
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessoes_auth (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    criada_em TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES utilizadores(id)
                )
                """
            )

    def criar_sessao(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        agora = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO sessoes_auth (token, user_id, criada_em)
                VALUES (?, ?, ?)
                """,
                (token, user_id, agora),
            )
        return token

    def utilizador_por_token_sessao(self, token: str) -> Optional[Utilizador]:
        if not token.strip():
            return None
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT u.* FROM sessoes_auth s
                JOIN utilizadores u ON u.id = s.user_id
                WHERE s.token = ? AND u.ativo = 1
                """,
                (token.strip(),),
            ).fetchone()
        if not row:
            return None
        return self._row_utilizador(row)

    def revogar_sessao(self, token: str) -> None:
        if not token.strip():
            return
        with self._conn() as conn:
            conn.execute("DELETE FROM sessoes_auth WHERE token = ?", (token.strip(),))

    def _bootstrap_admin(self) -> None:
        with self._conn() as conn:
            count = int(
                conn.execute(
                    "SELECT COUNT(*) AS n FROM utilizadores"
                ).fetchone()["n"]
            )
            if count > 0:
                return
            self._criar_utilizador(
                conn,
                ADMIN_USERNAME,
                ADMIN_PASSWORD,
                ADMIN_NOME,
                "admin",
            )

    @staticmethod
    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def _verificar_password(password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            return False

    @staticmethod
    def _row_utilizador(row) -> Utilizador:
        return Utilizador(
            id=int(row["id"]),
            username=row["username"],
            nome=row["nome"],
            role=row["role"],
            ativo=bool(row["ativo"]),
            criado_em=datetime.fromisoformat(row["criado_em"]),
        )

    def _criar_utilizador(
        self,
        conn,
        username: str,
        password: str,
        nome: str,
        role: str,
    ) -> int:
        agora = datetime.now().isoformat()
        cursor = conn.execute(
            """
            INSERT INTO utilizadores (username, nome, password_hash, role, ativo, criado_em)
            VALUES (?, ?, ?, ?, 1, ?)
            RETURNING id
            """,
            (
                username.strip(),
                nome.strip(),
                self._hash_password(password),
                role,
                agora,
            ),
        )
        return int(cursor.fetchone()["id"])

    def autenticar(self, username: str, password: str) -> Optional[Utilizador]:
        if not username.strip() or not password:
            return None
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM utilizadores
                WHERE LOWER(username) = LOWER(?) AND ativo = 1
                """,
                (username.strip(),),
            ).fetchone()
        if not row or not self._verificar_password(password, row["password_hash"]):
            return None
        return self._row_utilizador(row)

    def criar_utilizador(
        self,
        username: str,
        password: str,
        nome: str,
        role: str = "professor",
    ) -> Utilizador:
        try:
            with self._conn() as conn:
                user_id = self._criar_utilizador(conn, username, password, nome, role)
                row = conn.execute(
                    "SELECT * FROM utilizadores WHERE id = ?", (user_id,)
                ).fetchone()
            return self._row_utilizador(row)
        except db.INTEGRITY_ERRORS as exc:
            raise ValueError("Já existe um utilizador com esse nome.") from exc

    def listar_utilizadores(self) -> list[Utilizador]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM utilizadores ORDER BY LOWER(username)"
            ).fetchall()
        return [self._row_utilizador(r) for r in rows]

    def alterar_password(self, user_id: int, password_nova: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE utilizadores SET password_hash = ? WHERE id = ?",
                (self._hash_password(password_nova), user_id),
            )

    def alterar_nome(self, user_id: int, nome: str) -> None:
        nome = nome.strip()
        if not nome:
            raise ValueError("Indique um nome válido.")
        with self._conn() as conn:
            conn.execute(
                "UPDATE utilizadores SET nome = ? WHERE id = ?",
                (nome, user_id),
            )

    def definir_ativo(self, user_id: int, ativo: bool) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE utilizadores SET ativo = ? WHERE id = ?",
                (1 if ativo else 0, user_id),
            )

    def redefinir_password(self, user_id: int, password_nova: str) -> None:
        self.alterar_password(user_id, password_nova)
