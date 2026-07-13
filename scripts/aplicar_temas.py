"""Preenche o campo tema_pap para todos os alunos na base de dados."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.storage import PapStorage
from app.temas_pap import TEMAS_POR_NOME, tema_para_nome


def aplicar_temas() -> None:
    storage = PapStorage()
    for aluno in storage.listar_alunos():
        tema = tema_para_nome(aluno.nome)
        if tema and aluno.tema_pap != tema:
            storage.atualizar_aluno(aluno.id, tema_pap=tema)
            print(f"OK {aluno.nome}: {tema[:60]}...")
        elif tema:
            print(f"= {aluno.nome}")
        else:
            print(f"? Sem tema: {aluno.nome}")

    print("\nTemas na lista sem aluno importado:")
    nomes_bd = {a.nome for a in storage.listar_alunos()}
    for nome in TEMAS_POR_NOME:
        if nome not in nomes_bd:
            print(f"  - {nome}")


if __name__ == "__main__":
    aplicar_temas()
