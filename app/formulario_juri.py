"""Interface Streamlit do formulário público dos júris."""

from __future__ import annotations

import streamlit as st

from app.apresentacoes import (
    CRITERIOS_FORM_APRESENTACAO,
    NOTA_MAXIMA_FORM,
    NOTA_MINIMA_FORM,
    carregar_config_juris,
)

_AJUDA_CRITERIOS: dict[str, str] = {
    "expressao_oral": "Clareza na fala, fluência, contacto visual e uso adequado da voz e do corpo.",
    "capacidade_sintese": "Organização das ideias, foco nos pontos essenciais e respeito pelo tempo.",
    "recursos_apresentacao": "Qualidade dos slides, demonstrações, materiais de apoio e estratégias usadas.",
    "argumentacao_defesa": "Capacidade de responder às questões e defender as opções do projecto.",
}


def _notas_existentes(
    storage,
    ano_letivo: str,
    aluno_id: int,
    juri_nome: str,
) -> dict[str, int]:
    return {
        a.criterio: a.nota
        for a in storage.listar_avaliacoes_juri(ano_letivo)
        if a.aluno_id == aluno_id and a.juri_nome == juri_nome
    }


def _estilos_formulario_juri() -> None:
    st.markdown(
        """
        <style>
        .pap-juri-form-wrap {
            max-width: 480px;
            margin: 0 auto;
        }
        .pap-juri-form-wrap h3 {
            font-size: 1.15rem;
            margin-top: 1.25rem;
            margin-bottom: 0.35rem;
            color: #1e3a5f;
        }
        .pap-juri-criterio-num {
            display: inline-block;
            background: #1e3a5f;
            color: white;
            font-size: 0.75rem;
            font-weight: 700;
            width: 1.4rem;
            height: 1.4rem;
            line-height: 1.4rem;
            text-align: center;
            border-radius: 50%;
            margin-right: 0.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_formulario_juri(storage) -> None:
    config = carregar_config_juris()
    alunos = storage.listar_alunos()

    _estilos_formulario_juri()

    _, col_centro, _ = st.columns([1, 1.35, 1])

    with col_centro:
        st.markdown('<div class="pap-juri-form-wrap">', unsafe_allow_html=True)

        st.markdown(f"### Avaliação da Defesa da PAP")
        st.caption(f"Ano letivo **{config.ano_letivo}** — secção **C – Apresentação e Defesa**")

        if not alunos:
            st.warning(
                "Ainda não há alunos importados na plataforma. "
                "Peça ao administrador para importar os relatórios."
            )
            return

        resultado = st.session_state.pop("_juri_form_ok", None)
        if resultado:
            st.success(
                f"Avaliação de **{resultado['aluno']}** registada com sucesso "
                f"({resultado['juri']})."
            )

        st.markdown("#### 1. Identificação")
        email = st.text_input(
            "Email (opcional)",
            placeholder="seu.email@escola.pt",
            help="Para contacto, se necessário.",
        )
        juri = st.selectbox("Nome do júri *", config.juris)
        opcoes_alunos = {a.nome: a.id for a in alunos}
        nome_aluno = st.selectbox("Aluno a avaliar *", list(opcoes_alunos.keys()))
        aluno_id = opcoes_alunos[nome_aluno]

        existentes = _notas_existentes(storage, config.ano_letivo, aluno_id, juri)
        if existentes:
            rotulos = dict(CRITERIOS_FORM_APRESENTACAO)
            linhas = [
                f"- {rotulos.get(chave, chave)}: **{nota}** val."
                for chave, nota in existentes.items()
            ]
            st.warning(
                f"**{juri}** já avaliou **{nome_aluno}**. "
                "As notas abaixo substituem a avaliação anterior."
            )
            st.markdown("\n".join(linhas))

        st.markdown("#### 2. Notas por parâmetro")
        st.caption("Escala de **0 a 20** — arraste o cursor ou clique na barra.")

        notas: dict[str, int] = {}
        for num, (chave, rotulo) in enumerate(CRITERIOS_FORM_APRESENTACAO, start=1):
            valor_inicial = existentes.get(chave, NOTA_MINIMA_FORM)
            with st.container(border=True):
                st.markdown(
                    f'<span class="pap-juri-criterio-num">{num}</span>'
                    f"**{rotulo}**",
                    unsafe_allow_html=True,
                )
                if chave in _AJUDA_CRITERIOS:
                    st.caption(_AJUDA_CRITERIOS[chave])
                notas[chave] = st.slider(
                    "Nota",
                    min_value=NOTA_MINIMA_FORM,
                    max_value=NOTA_MAXIMA_FORM,
                    value=int(valor_inicial),
                    step=1,
                    key=f"juri_nota_{chave}_{aluno_id}",
                    label_visibility="collapsed",
                )
                st.markdown(f"Nota seleccionada: **{notas[chave]}** / {NOTA_MAXIMA_FORM}")

        col_env, col_lim = st.columns(2)
        enviar = col_env.button(
            "Registar avaliação",
            type="primary",
            use_container_width=True,
        )
        limpar = col_lim.button("Repor notas", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    if limpar:
        for chave, _ in CRITERIOS_FORM_APRESENTACAO:
            st.session_state.pop(f"juri_nota_{chave}_{aluno_id}", None)
        st.rerun()

    if enviar:
        if not juri.strip():
            st.error("Seleccione o nome do júri.")
            return
        if all(n == NOTA_MINIMA_FORM for n in notas.values()):
            st.error(
                "Todas as notas estão a **0**. Confirme que pretende mesmo "
                "registar zeros ou ajuste as notas antes de enviar."
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
