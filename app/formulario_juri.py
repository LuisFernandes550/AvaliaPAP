"""Interface Streamlit do formulário público dos júris."""

from __future__ import annotations

import streamlit as st

from app.apresentacoes import (
    CRITERIOS_FORM_APRESENTACAO,
    NOTA_MAXIMA_FORM,
    NOTA_MINIMA_FORM,
    carregar_config_juris,
)


def _escolher_da_lista(
    label: str,
    opcoes: list[str],
    *,
    horizontal: bool = False,
) -> str | None:
    """Botões de opção: escolha só da lista, sem campo de texto (não abre teclado)."""
    try:
        return st.radio(label, opcoes, index=None, horizontal=horizontal)
    except TypeError:
        return st.radio(label, opcoes, horizontal=horizontal)


def renderizar_formulario_juri(storage) -> None:
    config = carregar_config_juris()
    alunos = storage.listar_alunos()

    st.markdown(
        f"### Avaliação da Defesa da PAP — Ano letivo {config.ano_letivo}"
    )
    st.caption(
        "Atribua uma nota de **0 a 20** a cada parâmetro da secção "
        "**C – Apresentação e Defesa do Projeto**."
    )

    if not alunos:
        st.warning(
            "Ainda não há alunos importados na plataforma. "
            "Peça ao administrador para importar os relatórios."
        )
        return

    if st.session_state.pop("_juri_form_ok", False):
        st.success("Avaliação registada com sucesso. Pode submeter outra avaliação.")

    with st.form("form_juri_apresentacao", clear_on_submit=False):
        email = st.text_input("Email", placeholder="seu.email@escola.pt")
        juri = _escolher_da_lista("Nome do júri *", config.juris)
        opcoes_alunos = {a.nome: a.id for a in alunos}
        nomes_alunos = list(opcoes_alunos.keys())
        nome_aluno = _escolher_da_lista("Aluno a avaliar *", nomes_alunos)
        st.divider()
        notas: dict[str, int] = {}
        for chave, rotulo in CRITERIOS_FORM_APRESENTACAO:
            notas[chave] = st.slider(
                f"{rotulo} *",
                min_value=NOTA_MINIMA_FORM,
                max_value=NOTA_MAXIMA_FORM,
                value=NOTA_MINIMA_FORM,
                step=1,
            )
        col_env, col_lim = st.columns(2)
        enviar = col_env.form_submit_button("Enviar", type="primary", use_container_width=True)
        limpar = col_lim.form_submit_button("Limpar formulário", use_container_width=True)

    if limpar:
        st.rerun()

    if enviar:
        if not juri or str(juri) not in config.juris:
            st.error("Seleccione o nome do júri na lista.")
            return
        if not nome_aluno or nome_aluno not in opcoes_alunos:
            st.error("Seleccione o aluno na lista.")
            return
        aluno_id = opcoes_alunos[nome_aluno]
        for chave, nota in notas.items():
            storage.guardar_avaliacao_juri(
                aluno_id,
                juri,
                chave,
                int(nota),
                config.ano_letivo,
                email_juri=email.strip(),
            )
        st.session_state["_juri_form_ok"] = True
        st.rerun()
