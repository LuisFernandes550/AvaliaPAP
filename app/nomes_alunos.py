"""Nomes oficiais da turma, temas e mapeamento por ficheiro importado."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from app.config import NOMES_ALUNOS_PATH

if TYPE_CHECKING:
    from app.models import AlunoRelatorio

_MAPEAMENTO_FICHEIRO: dict[str, str] = {
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

_TEMAS_PADRAO: dict[str, str] = {
    "Adriano Ricardo David Salucombo": (
        "EduKids - Plataforma Interativa de Aprendizagem para Educação Infantil"
    ),
    "Afonso Baptista dos Santos Costa": (
        "GFF - Aplicação Móvel para Gestão Financeira Familiar"
    ),
    "Afonso Filipe Bondia de Jesus de Almeida Gama": (
        "EcoBot - Robô Inteligente para Recolha de Resíduos em Eventos"
    ),
    "Afonso Rodrigo Oliveira Matos": "Ragnarök Kombat - Jogo de Luta 3D",
    "Beatriz Isabel Costa Henriques": (
        "DoIt - Aplicação Móvel Inteligente para Gestão de Tarefas e Projetos"
    ),
    "Bernardo Ângelo Santos": (
        "BrebasMotors - Plataforma Web para Gestão e Divulgação de uma "
        "Concessionária Automóvel"
    ),
    "Dinis Costa Lourenço": (
        "Suplfy - Plataforma de Comércio Eletrónico para Suplementação Desportiva"
    ),
    "Duarte Nazaré Fialho": (
        "SayPlay - Plataforma Educativa para Apoio ao Desenvolvimento da Fala Infantil"
    ),
    "Filipe Alexandre Inácio Monteiro": "Bloodware - Jogo FPS 3D Baseado em Missões",
    "Francisco Luís Henriques Júnior": (
        "Manitou MT-928 - Miniatura Telecomandada da Manitou MT-928"
    ),
    "Gabriel Marinho Bispo": (
        "GoDeeper - Plataforma Web de Divulgação e Gestão do Grupo de Jovens "
        "da Igreja Baptista de Caldas da Rainha"
    ),
    "Guilherme Silva Ribeiro": (
        "LeviOn - Lâmpada Inteligente com Levitação Magnética e Funcionalidades Multimédia"
    ),
    "Kauã Silva Lima": (
        "RoboRaul - Evento de Robótica para alunos do 1º ciclo (4º ano)"
    ),
    "Maria Serafim Sousa": (
        "RoboRaul - Evento de Robótica para alunos do 1º ciclo (4º ano)"
    ),
    "Miguel Lopes Capinha": (
        "Dream Foundations: 5D Arcadium - Jogo de Aventura 3D com Minijogos de Arcade"
    ),
    "Rafael Coelho da Silva Graça": (
        'Febras Website v2 - Plataforma Web do Restaurante "O Febras"'
    ),
    "Rodrigo Manuel Timóteo Santos": "Dragon Tower - Jogo 3D de Mundo Aberto",
    "Rodrigo Silva Roque": (
        "StocX - Plataforma Web de Gestão do Inventário da Escola"
    ),
    "Rui Pedro de Sousa Zina": (
        "Trypia - Plataforma de Pesquisa e Reserva de Viagens, Hotéis e Experiências"
    ),
    "Tiago Filipe da Silva": (
        "Job For All - Plataforma Web de Divulgação e Gestão de Ofertas de Emprego"
    ),
    "Tiago Miguel Santos Silva": (
        "H2O Analytics - Sistema Autónomo de Monitorização e Análise Georreferenciada "
        "da Qualidade da Água"
    ),
    "Tiago Pereira Couto": (
        "Footmania - Aplicação móvel para Gestão de Torneio de Futebol"
    ),
    "Vasco Pimentel Vila": (
        "Sentinela Vermelha - Sistema Inteligente de Deteção e Registo de "
        "Infrações ao Sinal Vermelho"
    ),
    "Vladimiro Pankratau": (
        "ComércioLocal - Plataforma Web de Promoção do Comércio Local das "
        "Caldas da Rainha"
    ),
    "Hugo Miguel Vieira": "BladeSlinger - Jogo FPS de Ação com Ondas de Inimigos",
}

_ORDEM_PADRAO: list[str] = [
    "Adriano Ricardo David Salucombo",
    "Afonso Baptista dos Santos Costa",
    "Afonso Rodrigo Oliveira Matos",
    "Beatriz Isabel Costa Henriques",
    "Bernardo Ângelo Santos",
    "Dinis Costa Lourenço",
    "Duarte Nazaré Fialho",
    "Filipe Alexandre Inácio Monteiro",
    "Francisco Luís Henriques Júnior",
    "Gabriel Marinho Bispo",
    "Hugo Miguel Vieira",
    "Kauã Silva Lima",
    "Maria Serafim Sousa",
    "Rodrigo Manuel Timóteo Santos",
    "Rodrigo Silva Roque",
    "Rui Pedro de Sousa Zina",
    "Tiago Filipe da Silva",
    "Tiago Miguel Santos Silva",
    "Tiago Pereira Couto",
    "Vasco Pimentel Vila",
    "Vladimiro Pankratau",
]


@dataclass
class AlunoTurma:
    nome: str
    chave_ficheiro: str = ""
    tema: str = ""


def _chave_por_nome() -> dict[str, str]:
    return {nome: chave for chave, nome in _MAPEAMENTO_FICHEIRO.items()}


def nomes_turma_default() -> list[AlunoTurma]:
    chaves = _chave_por_nome()
    return [
        AlunoTurma(
            nome=nome,
            chave_ficheiro=chaves.get(nome, ""),
            tema=_TEMAS_PADRAO.get(nome, ""),
        )
        for nome in _ORDEM_PADRAO
    ]


def carregar_nomes_turma() -> list[AlunoTurma]:
    if not NOMES_ALUNOS_PATH.exists():
        return nomes_turma_default()
    dados = json.loads(NOMES_ALUNOS_PATH.read_text(encoding="utf-8"))
    alunos = [
        AlunoTurma(
            nome=str(item.get("nome", "")).strip(),
            chave_ficheiro=str(item.get("chave_ficheiro", "")).strip(),
            tema=str(item.get("tema", "")).strip(),
        )
        for item in dados
        if str(item.get("nome", "")).strip()
    ]
    return alunos or nomes_turma_default()


def guardar_nomes_turma(alunos: list[AlunoTurma]) -> None:
    NOMES_ALUNOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "nome": a.nome.strip(),
            "chave_ficheiro": a.chave_ficheiro.strip(),
            "tema": a.tema.strip(),
        }
        for a in alunos
        if a.nome.strip()
    ]
    NOMES_ALUNOS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def tema_para_nome(nome: str) -> str:
    for aluno in carregar_nomes_turma():
        if aluno.nome == nome:
            return aluno.tema
    return _TEMAS_PADRAO.get(nome, "")


def colunas_turma_ordenadas(
    alunos: list[AlunoRelatorio],
) -> list[tuple[str, AlunoRelatorio | None]]:
    por_nome = {a.nome: a for a in alunos}
    return [
        (entry.nome, por_nome.get(entry.nome))
        for entry in carregar_nomes_turma()
    ]


def _corresponde_chave(stem: str, chave: str) -> bool:
    chave = chave.strip()
    if not chave:
        return False
    stem_lower = stem.lower()
    chave_lower = chave.lower()
    if chave_lower not in stem_lower:
        return False
    if chave_lower == "bernardo" and "bernardo" not in stem:
        return False
    if chave_lower == "kau" and "kau" not in stem_lower:
        return False
    return True


def nome_por_ficheiro(
    nome_ficheiro: str,
    alunos: list[AlunoTurma] | None = None,
) -> str | None:
    if alunos is None:
        alunos = carregar_nomes_turma()
    stem = Path(nome_ficheiro).stem
    for entry in alunos:
        if _corresponde_chave(stem, entry.chave_ficheiro):
            return entry.nome
    return None


def aplicar_nomes_a_alunos(storage) -> tuple[int, list[str]]:
    """Actualiza nomes/temas dos alunos importados com base na configuração."""
    alunos_cfg = carregar_nomes_turma()
    actualizados = 0
    avisos: list[str] = []
    for aluno in storage.listar_alunos():
        novo_nome = nome_por_ficheiro(aluno.ficheiro, alunos_cfg)
        if not novo_nome:
            avisos.append(f"Sem mapeamento: {aluno.ficheiro}")
            continue
        novo_tema = tema_para_nome(novo_nome)
        if novo_nome != aluno.nome or (novo_tema and novo_tema != aluno.tema_pap):
            storage.atualizar_aluno(
                aluno.id,
                nome=novo_nome,
                tema_pap=novo_tema or aluno.tema_pap,
            )
            actualizados += 1
    return actualizados, avisos
