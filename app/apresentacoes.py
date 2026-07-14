"""Avaliação da defesa da PAP por júri (formulário + agregação para a Acta)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.config import JURIS_APRESENTACAO_PATH, NOTA_MAXIMA
from app.models import CriterioAvaliacao, ResultadoCriterio, arredondar_excel

ANO_LETIVO_APRESENTACAO = "2025/26"
NOTA_MINIMA_FORM = 0
NOTA_MAXIMA_FORM = NOTA_MAXIMA
NUM_JURIS = 5

# Parâmetros do formulário (Google Form TGPSI) → chave interna
CRITERIOS_FORM_APRESENTACAO: list[tuple[str, str]] = [
    ("capacidade_sintese", "Capacidade de síntese"),
    ("argumentacao_defesa", "Qualidade de argumentação na defesa do projeto"),
    ("adequacao_recursos", "Adequação dos recursos utilizados na exposição"),
    ("estrategias_apresentacao", "Qualidade das estratégias utilizadas na apresentação"),
]

_CHAVES_FORM = {chave for chave, _ in CRITERIOS_FORM_APRESENTACAO}
_LABELS_FORM = dict(CRITERIOS_FORM_APRESENTACAO)


@dataclass
class ConfigJurisApresentacao:
    ano_letivo: str = ANO_LETIVO_APRESENTACAO
    juris: list[str] = field(
        default_factory=lambda: [f"Júri {i}" for i in range(1, NUM_JURIS + 1)]
    )


@dataclass
class AvaliacaoJuri:
    aluno_id: int
    juri_nome: str
    criterio: str
    nota: int
    ano_letivo: str
    email_juri: str = ""
    avaliado_em: datetime = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.avaliado_em is None:
            self.avaliado_em = datetime.now()


def carregar_config_juris() -> ConfigJurisApresentacao:
    if not JURIS_APRESENTACAO_PATH.exists():
        return ConfigJurisApresentacao()
    dados = json.loads(JURIS_APRESENTACAO_PATH.read_text(encoding="utf-8"))
    juris = [str(j).strip() for j in dados.get("juris", []) if str(j).strip()]
    if len(juris) < NUM_JURIS:
        for i in range(len(juris) + 1, NUM_JURIS + 1):
            juris.append(f"Júri {i}")
    return ConfigJurisApresentacao(
        ano_letivo=str(dados.get("ano_letivo", ANO_LETIVO_APRESENTACAO)).strip()
        or ANO_LETIVO_APRESENTACAO,
        juris=juris[:NUM_JURIS],
    )


def guardar_config_juris(config: ConfigJurisApresentacao) -> None:
    JURIS_APRESENTACAO_PATH.parent.mkdir(parents=True, exist_ok=True)
    JURIS_APRESENTACAO_PATH.write_text(
        json.dumps(
            {"ano_letivo": config.ano_letivo, "juris": config.juris[:NUM_JURIS]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def label_criterio_form(chave: str) -> str:
    return _LABELS_FORM.get(chave, chave)


def _media_notas(notas: list[int | float]) -> float | None:
    if not notas:
        return None
    return sum(notas) / len(notas)


def calcular_medias_criterio(
    avaliacoes: list[AvaliacaoJuri],
    aluno_id: int,
    criterio: str,
) -> float | None:
    notas = [a.nota for a in avaliacoes if a.aluno_id == aluno_id and a.criterio == criterio]
    return _media_notas(notas)


def calcular_medias_aluno(
    avaliacoes: list[AvaliacaoJuri],
    aluno_id: int,
) -> dict[str, float | None]:
    return {
        chave: calcular_medias_criterio(avaliacoes, aluno_id, chave)
        for chave, _ in CRITERIOS_FORM_APRESENTACAO
    }


def nota_recursos_apresentacao(medias: dict[str, float | None]) -> int | None:
    """Combina adequação de recursos + estratégias numa nota para a Acta."""
    rec = medias.get("adequacao_recursos")
    est = medias.get("estrategias_apresentacao")
    if rec is None and est is None:
        return None
    if rec is None:
        return int(arredondar_excel(est, 0))  # type: ignore[arg-type]
    if est is None:
        return int(arredondar_excel(rec, 0))
    return int(arredondar_excel((rec + est) / 2, 0))


def sincronizar_medias_para_acta(
    storage,
    ano_letivo: str | None = None,
) -> tuple[int, list[str]]:
    """
    Calcula médias dos júris e grava na tabela avaliacoes (secção C).
    Devolve (nº critérios actualizados, avisos).
    """
    config = carregar_config_juris()
    ano = ano_letivo or config.ano_letivo
    avaliacoes = storage.listar_avaliacoes_juri(ano)
    avisos: list[str] = []
    actualizados = 0

    for aluno in storage.listar_alunos():
        medias = calcular_medias_aluno(avaliacoes, aluno.id)
        if not any(v is not None for v in medias.values()):
            continue

        mapeamento: list[tuple[CriterioAvaliacao, Optional[int]]] = [
            (CriterioAvaliacao.CAPACIDADE_SINTESE, _nota_acta(medias.get("capacidade_sintese"))),
            (
                CriterioAvaliacao.ARGUMENTACAO_DEFESA,
                _nota_acta(medias.get("argumentacao_defesa")),
            ),
            (CriterioAvaliacao.RECURSOS_APRESENTACAO, nota_recursos_apresentacao(medias)),
        ]

        for criterio, nota in mapeamento:
            if nota is None:
                continue
            storage.guardar_avaliacao(
                aluno.id,
                ResultadoCriterio(
                    criterio=criterio,
                    nota=nota,
                    comentario=f"Média dos júris ({ano})",
                    fonte=f"júri ({ano})",
                ),
            )
            actualizados += 1

    if actualizados == 0:
        avisos.append("Nenhuma avaliação de júri encontrada para sincronizar.")
    return actualizados, avisos


def _nota_acta(media: float | None) -> int | None:
    if media is None:
        return None
    return int(max(1, min(NOTA_MAXIMA, arredondar_excel(media, 0))))
