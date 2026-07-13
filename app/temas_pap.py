"""Temas oficiais das PAP por nome do aluno."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import AlunoRelatorio

TEMAS_POR_NOME: dict[str, str] = {
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

# Ordem oficial das colunas no resumo da turma (cabeçalho da grelha)
ORDEM_NOMES_TURMA: list[str] = [
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


def tema_para_nome(nome: str) -> str:
    return TEMAS_POR_NOME.get(nome, "")


def colunas_turma_ordenadas(
    alunos: list[AlunoRelatorio],
) -> list[tuple[str, AlunoRelatorio | None]]:
    """Devolve (nome oficial, aluno ou None) na ordem do cabeçalho."""
    por_nome = {a.nome: a for a in alunos}
    return [(nome, por_nome.get(nome)) for nome in ORDEM_NOMES_TURMA]
