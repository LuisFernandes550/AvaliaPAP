"""Associa nomes oficiais dos alunos com base no ficheiro importado."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.storage import PapStorage

# ficheiro (substring) -> nome oficial
MAPEAMENTO: dict[str, str] = {
    "AdrianoSalucombo": "Adriano Ricardo David Salucombo",
    "AfonsoCosta": "Afonso Baptista dos Santos Costa",
    "AfonsoMatos": "Afonso Rodrigo Oliveira Matos",
    "BeatrizHenriques": "Beatriz Isabel Costa Henriques",
    "Bernardo": "Bernardo Ângelo Santos",
    "DinisLourenco": "Dinis Costa Lourenço",
    "DuarteFialho": "Duarte Nazaré Fialho",
    "FilipeMonteiro": "Filipe Alexandre Inácio Monteiro",
    "FranciscoJunior": "Francisco Luís Henriques Júnior",
    "GabrielBispo": "Gabriel Marinho Bispo",
    "Kau": "Kauã Silva Lima",
    "MariaSousa": "Maria Serafim Sousa",
    "RodrigoSantos": "Rodrigo Manuel Timóteo Santos",
    "RodrigoRoque": "Rodrigo Silva Roque",
    "RuiZina": "Rui Pedro de Sousa Zina",
    "TiagoFilipe": "Tiago Filipe da Silva",
    "TiagoMiguel": "Tiago Miguel Santos Silva",
    "TiagoCouto": "Tiago Pereira Couto",
    "VascoVila": "Vasco Pimentel Vila",
    "VladimiroPankratau": "Vladimiro Pankratau",
    "HugoVieira": "Hugo Miguel Vieira",
}

SEM_RELATORIO = [
    "Afonso Filipe Bondia de Jesus de Almeida Gama",
    "Guilherme Silva Ribeiro",
    "Miguel Lopes Capinha",
    "Rafael Coelho da Silva Graça",
]


def _nome_oficial(ficheiro: str) -> str | None:
    stem = Path(ficheiro).stem
    for chave, nome in MAPEAMENTO.items():
        if chave.lower() in stem.lower():
            if chave == "Bernardo" and "Bernardo" not in stem:
                continue
            if chave == "Kau" and "kau" not in stem.lower():
                continue
            return nome
    return None


def associar() -> None:
    storage = PapStorage()
    for aluno in storage.listar_alunos():
        novo = _nome_oficial(aluno.ficheiro)
        if not novo:
            print(f"? Sem mapeamento: {aluno.ficheiro} ({aluno.nome})")
            continue
        if aluno.nome != novo:
            storage.atualizar_aluno(aluno.id, nome=novo)
            print(f"OK {aluno.ficheiro}: {aluno.nome} -> {novo}")
        else:
            print(f"= {aluno.ficheiro}: {novo}")

    print("\nSem relatório importado (lista oficial):")
    for nome in SEM_RELATORIO:
        print(f"  - {nome}")


if __name__ == "__main__":
    associar()
