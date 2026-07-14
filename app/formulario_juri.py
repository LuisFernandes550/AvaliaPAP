"""Interface Streamlit do formulário público dos júris."""

from __future__ import annotations

import re

import streamlit as st

from app.apresentacoes import (
    CRITERIOS_FORM_APRESENTACAO,
    NOTA_MAXIMA_FORM,
    NOTA_MINIMA_FORM,
    carregar_config_juris,
)

_CHAVES_CRITERIOS = [chave for chave, _ in CRITERIOS_FORM_APRESENTACAO]
_OPCOES_NOTA = list(range(NOTA_MINIMA_FORM, NOTA_MAXIMA_FORM + 1))

_AJUDA_CRITERIOS: dict[str, str] = {
    "expressao_oral": "Clareza na fala, fluência, contacto visual e uso adequado da voz e do corpo.",
    "capacidade_sintese": "Organização das ideias, foco nos pontos essenciais e respeito pelo tempo.",
    "recursos_apresentacao": "Qualidade dos slides, demonstrações, materiais de apoio e estratégias usadas.",
    "argumentacao_defesa": "Capacidade de responder às questões e defender as opções do projecto.",
}


def _juri_slug(nome: str) -> str:
    return re.sub(r"\W+", "_", nome.strip().lower())[:48]


def _notas_anteriores_formulario(
    storage,
    ano_letivo: str,
    aluno_id: int,
    juri_nome: str,
) -> dict[str, int]:
    return storage.obter_notas_juri_aluno(
        aluno_id, juri_nome, ano_letivo, apenas_formulario=True
    )


def _avaliacao_formulario_completa(notas: dict[str, int]) -> bool:
    if len(notas) < len(_CHAVES_CRITERIOS):
        return False
    if not all(chave in notas for chave in _CHAVES_CRITERIOS):
        return False
    return any(notas[chave] > NOTA_MINIMA_FORM for chave in _CHAVES_CRITERIOS)


def _estilos_formulario_juri() -> None:
    st.markdown(
        """
        <style>
        .pap-juri-form-wrap {
            max-width: 520px;
            margin: 0 auto;
        }
        .pap-juri-form-wrap h3 {
            font-size: 1.45rem;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            color: #1e3a5f;
        }
        .pap-juri-form-wrap h4 {
            font-size: 1.25rem;
            color: #1e3a5f;
        }
        .pap-juri-criterio-num {
            display: inline-block;
            background: #1e3a5f;
            color: white;
            font-size: 1rem;
            font-weight: 700;
            width: 1.75rem;
            height: 1.75rem;
            line-height: 1.75rem;
            text-align: center;
            border-radius: 50%;
            margin-right: 0.5rem;
        }
        .pap-juri-nota-grande {
            font-size: 2rem;
            font-weight: 800;
            color: #1e3a5f;
            text-align: center;
            margin: 0.35rem 0 0.75rem 0;
        }
        .pap-juri-estado {
            padding: 1rem 1.1rem;
            border-radius: 0.65rem;
            font-size: 1.1rem;
            line-height: 1.45;
            margin: 1rem 0;
        }
        .pap-juri-estado-ok {
            background: #dcfce7;
            border: 2px solid #16a34a;
            color: #14532d;
        }
        .pap-juri-estado-pendente {
            background: #fef9c3;
            border: 2px solid #ca8a04;
            color: #713f12;
        }
        .pap-juri-estado-sucesso {
            background: #dbeafe;
            border: 2px solid #2563eb;
            color: #1e3a8a;
        }
        @media (max-width: 1200px) {
            .pap-juri-form-wrap {
                max-width: 96vw;
                font-size: 1.15rem;
            }
            .pap-juri-form-wrap h3 { font-size: 1.65rem !important; }
            .pap-juri-form-wrap h4 { font-size: 1.4rem !important; }
            .pap-juri-nota-grande { font-size: 2.35rem !important; }
            .pap-juri-estado { font-size: 1.2rem !important; }
            div[data-testid="stRadio"] label p,
            div[data-testid="stSelectbox"] label p,
            div[data-testid="stSelectSlider"] label p {
                font-size: 1.15rem !important;
            }
            div[data-testid="stRadio"] label {
                min-height: 2.75rem;
                padding: 0.5rem 0.75rem !important;
            }
            div[data-testid="stButton"] button {
                min-height: 3.25rem;
                font-size: 1.15rem !important;
            }
            div[data-testid="stSelectSlider"] [data-baseweb="slider"] {
                margin-top: 0.75rem;
                margin-bottom: 0.75rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_estado_avaliacao(
    *,
    sucesso: dict | None,
    juri: str,
    nome_aluno: str,
    anteriores: dict[str, int],
) -> None:
    if sucesso and sucesso.get("juri") == juri and sucesso.get("aluno") == nome_aluno:
        st.markdown(
            f'<div class="pap-juri-estado pap-juri-estado-sucesso">'
            f"✓ <strong>Avaliação registada agora</strong> para "
            f"<strong>{nome_aluno}</strong>."
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    rotulos = dict(CRITERIOS_FORM_APRESENTACAO)
    if _avaliacao_formulario_completa(anteriores):
        linhas = " · ".join(
            f"{rotulos[chave][:28]}: <strong>{anteriores[chave]}</strong>"
            for chave in _CHAVES_CRITERIOS
            if chave in anteriores
        )
        st.markdown(
            f'<div class="pap-juri-estado pap-juri-estado-ok">'
            f"✓ <strong>Já registou</strong> avaliação para "
            f"<strong>{nome_aluno}</strong>.<br>{linhas}"
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div class="pap-juri-estado pap-juri-estado-pendente">'
        f"○ <strong>Ainda não registou</strong> avaliação para "
        f"<strong>{nome_aluno}</strong>."
        f"</div>",
        unsafe_allow_html=True,
    )


def renderizar_formulario_juri(storage) -> None:
    config = carregar_config_juris()
    alunos = storage.listar_alunos()

    _estilos_formulario_juri()

    _, col_centro, _ = st.columns([0.15, 1.7, 0.15])

    with col_centro:
        st.markdown('<div class="pap-juri-form-wrap">', unsafe_allow_html=True)

        st.markdown("### Avaliação da Defesa da PAP")
        st.caption(f"Ano letivo **{config.ano_letivo}** — secção **C – Apresentação e Defesa**")

        if not alunos:
            st.warning(
                "Ainda não há alunos importados na plataforma. "
                "Peça ao administrador para importar os relatórios."
            )
            return

        st.markdown("#### 1. Identificação")
        email = st.text_input(
            "Email (opcional)",
            placeholder="seu.email@escola.pt",
        )

        juri_fixo = st.query_params.get("juri", "").strip()
        if juri_fixo and juri_fixo in config.juris:
            st.markdown(f"**Júri:** {juri_fixo}")
            juri = juri_fixo
        else:
            juri = st.radio(
                "Nome do júri *",
                config.juris,
                horizontal=False,
            )

        opcoes_alunos = {a.nome: a.id for a in alunos}
        nomes_alunos = list(opcoes_alunos.keys())
        nome_aluno = st.selectbox(
            "Aluno a avaliar *",
            nomes_alunos,
            index=None,
            placeholder="Seleccione o aluno na lista",
        )
        if not nome_aluno:
            st.info("Seleccione o aluno para atribuir as notas.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        aluno_id = opcoes_alunos[nome_aluno]
        juri_id = _juri_slug(juri)
        anteriores = _notas_anteriores_formulario(
            storage, config.ano_letivo, aluno_id, juri
        )

        st.markdown("#### 2. Notas por parâmetro")
        st.caption("Toque na escala para escolher a nota (0 a 20).")

        notas: dict[str, int] = {}
        for num, (chave, rotulo) in enumerate(CRITERIOS_FORM_APRESENTACAO, start=1):
            valor_inicial = anteriores.get(chave, NOTA_MINIMA_FORM)
            with st.container(border=True):
                st.markdown(
                    f'<span class="pap-juri-criterio-num">{num}</span>'
                    f"**{rotulo}**",
                    unsafe_allow_html=True,
                )
                if chave in _AJUDA_CRITERIOS:
                    st.caption(_AJUDA_CRITERIOS[chave])
                notas[chave] = st.select_slider(
                    "Nota",
                    options=_OPCOES_NOTA,
                    value=int(valor_inicial),
                    key=f"juri_nota_{chave}_{aluno_id}_{juri_id}",
                    label_visibility="collapsed",
                )
                st.markdown(
                    f'<div class="pap-juri-nota-grande">{notas[chave]} / {NOTA_MAXIMA_FORM}</div>',
                    unsafe_allow_html=True,
                )

        sucesso = st.session_state.get("_juri_form_ok")
        _renderizar_estado_avaliacao(
            sucesso=sucesso,
            juri=juri,
            nome_aluno=nome_aluno,
            anteriores=anteriores,
        )

        col_env, col_lim = st.columns(2)
        enviar = col_env.button(
            "Registar avaliação",
            type="primary",
            use_container_width=True,
        )
        limpar = col_lim.button("Repor notas a 0", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    if limpar:
        for chave, _ in CRITERIOS_FORM_APRESENTACAO:
            st.session_state.pop(f"juri_nota_{chave}_{aluno_id}_{juri_id}", None)
        st.session_state.pop("_juri_form_ok", None)
        st.rerun()

    if enviar:
        if not juri.strip():
            st.error("Seleccione o nome do júri.")
            return
        if all(n == NOTA_MINIMA_FORM for n in notas.values()):
            st.error(
                "Todas as notas estão a **0**. Ajuste pelo menos uma nota antes de enviar."
            )
            return
        for chave, nota in notas.items():
            storage.guardar_avaliacao_juri(
                aluno_id,
                juri,
                chave,
                int(nota),
                config.ano_letivo,
                email_juri=email.strip(),
            )
        st.session_state["_juri_form_ok"] = {
            "juri": juri,
            "aluno": nome_aluno,
        }
        st.rerun()
