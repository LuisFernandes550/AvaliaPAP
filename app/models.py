from __future__ import annotations

import math
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AreaPAP(str, Enum):
    WEBSITE = "website"
    APLICACAO_MOVEL = "aplicacao_movel"
    ROBOTICA = "robotica"
    JOGO = "jogo"
    NAO_DETETADA = "nao_detetada"


AREA_LABELS = {
    AreaPAP.WEBSITE: "Website",
    AreaPAP.APLICACAO_MOVEL: "Aplicação móvel",
    AreaPAP.ROBOTICA: "Robótica",
    AreaPAP.JOGO: "Jogo",
    AreaPAP.NAO_DETETADA: "Área não detetada",
}


class CriterioAvaliacao(str, Enum):
    # A – Desenvolvimento do Projeto
    DEFINICAO_OBJETIVOS = "definicao_objetivos"
    QUALIDADE_CIENTIFICA = "qualidade_cientifica"
    PERTINENCIA_CRIATIVIDADE = "pertinencia_criatividade"
    PLANEAMENTO_RECURSOS = "planeamento_recursos"
    FASES_EXECUCAO = "fases_execucao"
    AUTONOMIA = "autonomia"
    RESPONSABILIDADE_PROJETO = "responsabilidade_projeto"
    # B – Relatório final
    OBJETIVIDADE = "objetividade"
    PERTINENCIA = "pertinencia"
    DIFICULDADES = "dificuldades"
    ANALISE_CRITICA = "analise_critica"
    RESPONSABILIDADE_RELATORIO = "responsabilidade_tempo"
    # C – Apresentação e Defesa do Projeto
    EXPRESSAO_ORAL = "expressao_oral"
    CAPACIDADE_SINTESE = "capacidade_sintese"
    RECURSOS_APRESENTACAO = "recursos_apresentacao"
    ARGUMENTACAO_DEFESA = "argumentacao_defesa"
    AUTOAVALIACAO = "autoavaliacao"


class SecaoAvaliacao(str, Enum):
    DESENVOLVIMENTO = "a"
    RELATORIO = "b"
    APRESENTACAO = "c"


SECAO_LABELS = {
    SecaoAvaliacao.DESENVOLVIMENTO: "A – Desenvolvimento do Projeto",
    SecaoAvaliacao.RELATORIO: "B – Relatório final",
    SecaoAvaliacao.APRESENTACAO: "C – Apresentação e Defesa do Projeto",
}

SECAO_PONDERACAO = {
    SecaoAvaliacao.DESENVOLVIMENTO: 0.50,
    SecaoAvaliacao.RELATORIO: 0.20,
    SecaoAvaliacao.APRESENTACAO: 0.30,
}

CRITERIO_LABELS = {
    CriterioAvaliacao.DEFINICAO_OBJETIVOS: "Definição dos objetivos do projeto",
    CriterioAvaliacao.QUALIDADE_CIENTIFICA: "Qualidade científica e técnica",
    CriterioAvaliacao.PERTINENCIA_CRIATIVIDADE: "Pertinência, criatividade e inovação",
    CriterioAvaliacao.PLANEAMENTO_RECURSOS: "Planeamento dos recursos necessários",
    CriterioAvaliacao.FASES_EXECUCAO: "Definição das fases de execução do projeto",
    CriterioAvaliacao.AUTONOMIA: "Autonomia",
    CriterioAvaliacao.RESPONSABILIDADE_PROJETO: "Sentido de responsabilidade e gestão do tempo",
    CriterioAvaliacao.OBJETIVIDADE: "Objetividade",
    CriterioAvaliacao.PERTINENCIA: "Pertinência das informações",
    CriterioAvaliacao.DIFICULDADES: "Identificação das dificuldades e meios de as superar",
    CriterioAvaliacao.ANALISE_CRITICA: "Capacidade de análise crítica",
    CriterioAvaliacao.RESPONSABILIDADE_RELATORIO: "Sentido de responsabilidade e gestão do tempo",
    CriterioAvaliacao.EXPRESSAO_ORAL: "Capacidade de expressão oral e de expressão corporal",
    CriterioAvaliacao.CAPACIDADE_SINTESE: "Capacidade de síntese",
    CriterioAvaliacao.RECURSOS_APRESENTACAO: (
        "Qualidade dos recursos/estratégias utilizadas na apresentação"
    ),
    CriterioAvaliacao.ARGUMENTACAO_DEFESA: "Qualidade de argumentação na defesa do projeto",
    CriterioAvaliacao.AUTOAVALIACAO: "Autoavaliação",
}

CRITERIOS_POR_SECAO: dict[SecaoAvaliacao, list[CriterioAvaliacao]] = {
    # Ordem igual à folha Avaliação da Acta Excel
    SecaoAvaliacao.DESENVOLVIMENTO: [
        CriterioAvaliacao.DEFINICAO_OBJETIVOS,
        CriterioAvaliacao.QUALIDADE_CIENTIFICA,
        CriterioAvaliacao.PERTINENCIA_CRIATIVIDADE,
        CriterioAvaliacao.PLANEAMENTO_RECURSOS,
        CriterioAvaliacao.FASES_EXECUCAO,
        CriterioAvaliacao.AUTONOMIA,
        CriterioAvaliacao.RESPONSABILIDADE_PROJETO,
    ],
    SecaoAvaliacao.RELATORIO: [
        CriterioAvaliacao.OBJETIVIDADE,
        CriterioAvaliacao.PERTINENCIA,
        CriterioAvaliacao.DIFICULDADES,
        CriterioAvaliacao.ANALISE_CRITICA,
        CriterioAvaliacao.RESPONSABILIDADE_RELATORIO,
    ],
    SecaoAvaliacao.APRESENTACAO: [
        CriterioAvaliacao.EXPRESSAO_ORAL,
        CriterioAvaliacao.CAPACIDADE_SINTESE,
        CriterioAvaliacao.RECURSOS_APRESENTACAO,
        CriterioAvaliacao.ARGUMENTACAO_DEFESA,
    ],
}

# Critérios da secção B avaliados automaticamente pela IA
CRITERIOS_IA = [
    CriterioAvaliacao.OBJETIVIDADE,
    CriterioAvaliacao.PERTINENCIA,
    CriterioAvaliacao.DIFICULDADES,
    CriterioAvaliacao.ANALISE_CRITICA,
]

CRITERIO_MANUAL = CriterioAvaliacao.RESPONSABILIDADE_RELATORIO

CRITERIOS_MANUAIS = [
    c for secao in SecaoAvaliacao for c in CRITERIOS_POR_SECAO[secao] if c not in CRITERIOS_IA
] + [CriterioAvaliacao.AUTOAVALIACAO]

# Etiquetas curtas para a grelha do resumo da turma
RESUMO_COLUNAS: list[tuple[str, CriterioAvaliacao]] = [
    ("A: Objetivos", CriterioAvaliacao.DEFINICAO_OBJETIVOS),
    ("A: Qual. científ.", CriterioAvaliacao.QUALIDADE_CIENTIFICA),
    ("A: Pert./inov.", CriterioAvaliacao.PERTINENCIA_CRIATIVIDADE),
    ("A: Recursos", CriterioAvaliacao.PLANEAMENTO_RECURSOS),
    ("A: Fases", CriterioAvaliacao.FASES_EXECUCAO),
    ("A: Autonomia", CriterioAvaliacao.AUTONOMIA),
    ("A: Resp./tempo", CriterioAvaliacao.RESPONSABILIDADE_PROJETO),
    ("B: Objetividade", CriterioAvaliacao.OBJETIVIDADE),
    ("B: Pertinência", CriterioAvaliacao.PERTINENCIA),
    ("B: Dificuldades", CriterioAvaliacao.DIFICULDADES),
    ("B: Análise", CriterioAvaliacao.ANALISE_CRITICA),
    ("B: Resp./tempo", CriterioAvaliacao.RESPONSABILIDADE_RELATORIO),
    ("C: Expr. oral", CriterioAvaliacao.EXPRESSAO_ORAL),
    ("C: Síntese", CriterioAvaliacao.CAPACIDADE_SINTESE),
    ("C: Recursos ap.", CriterioAvaliacao.RECURSOS_APRESENTACAO),
    ("C: Argumentação", CriterioAvaliacao.ARGUMENTACAO_DEFESA),
]


def media_secao(
    avaliacoes: dict[CriterioAvaliacao, "ResultadoCriterio"],
    secao: SecaoAvaliacao,
) -> float | None:
    notas = [
        avaliacoes[c].nota
        for c in CRITERIOS_POR_SECAO[secao]
        if c in avaliacoes
    ]
    return (sum(notas) / len(notas)) if notas else None


def arredondar_excel(valor: float, casas: int = 0) -> float:
    """Arredondamento igual ao ROUND do Excel (0.5 arredonda para cima)."""
    factor = 10**casas
    return math.floor(valor * factor + 0.5) / factor


def media_secao_arredondada(
    avaliacoes: dict[CriterioAvaliacao, "ResultadoCriterio"],
    secao: SecaoAvaliacao,
) -> float | None:
    """Média da secção com 1 casa decimal, como na folha Avaliação (linhas 22, 29, 35)."""
    media = media_secao(avaliacoes, secao)
    return arredondar_excel(media, 1) if media is not None else None


def avaliacao_final(avaliacoes: dict[CriterioAvaliacao, "ResultadoCriterio"]) -> float | None:
    """Média ponderada com totais de secção já arredondados (linha 37 da Acta)."""
    contrib = 0.0
    for secao, peso in SECAO_PONDERACAO.items():
        media = media_secao_arredondada(avaliacoes, secao)
        if media is None:
            return None
        contrib += media * peso
    return arredondar_excel(contrib, 1)


def nota_final_arredondada(avaliacoes: dict[CriterioAvaliacao, "ResultadoCriterio"]) -> int | None:
    """Nota final inteira (linha 38 da Acta: =ROUND(média ponderada, 0))."""
    final = avaliacao_final(avaliacoes)
    if final is None:
        return None
    return int(arredondar_excel(final, 0))


# Capítulos principais dos relatórios de PAP (comuns a todas as áreas)
CAPITULOS_PAP = {
    "introducao": "1. Introdução",
    "planificacao": "2. Planificação do projeto",
    "implementacao": "3. Implementação do projeto",
    "problemas": "4. Problemas e soluções encontradas",
    "conclusao": "5. Conclusão",
}


class AlunoRelatorio(BaseModel):
    id: Optional[int] = None
    nome: str
    titulo_pap: str
    tema_pap: str = ""
    area_pap: AreaPAP = AreaPAP.NAO_DETETADA
    ficheiro: str
    texto_extraido: str = ""
    importado_em: datetime = Field(default_factory=datetime.now)


class ResultadoCriterio(BaseModel):
    criterio: CriterioAvaliacao
    nota: int = Field(ge=1, le=20)
    comentario: str = ""
    fonte: str = "manual"
    avaliado_em: datetime = Field(default_factory=datetime.now)


class AvaliacaoRelatorio(BaseModel):
    aluno_id: int
    resultados: list[ResultadoCriterio] = Field(default_factory=list)


class InstrucoesAvaliacao(BaseModel):
    instrucoes_gerais: str = ""
    areas: dict[str, str] = Field(
        default_factory=lambda: {
            "website": "",
            "aplicacao_movel": "",
            "robotica": "",
            "jogo": "",
        }
    )
    capitulos: dict[str, str] = Field(
        default_factory=lambda: {chave: "" for chave in CAPITULOS_PAP}
    )
