"""Temas oficiais das PAP por nome do aluno (delegado em nomes_alunos)."""

from __future__ import annotations

from app.nomes_alunos import (
    carregar_nomes_turma,
    colunas_turma_ordenadas,
    tema_para_nome,
)

# Compatibilidade com código/scripts antigos
TEMAS_POR_NOME = {
    a.nome: a.tema for a in carregar_nomes_turma() if a.tema
}
ORDEM_NOMES_TURMA = [a.nome for a in carregar_nomes_turma()]

__all__ = [
    "TEMAS_POR_NOME",
    "ORDEM_NOMES_TURMA",
    "carregar_nomes_turma",
    "colunas_turma_ordenadas",
    "tema_para_nome",
]
