"""Interface Streamlit do formulário público dos júris."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from app.apresentacoes import (
    CRITERIOS_FORM_APRESENTACAO,
    NOTA_MAXIMA_FORM,
    NOTA_MINIMA_FORM,
    carregar_config_juris,
    verificar_senha_formulario,
)

_SESSAO_ACESSO_OK = "_juri_acesso_ok"


def _portao_palavra_passe(config) -> bool:
    """Pede a palavra-passe de acesso. Devolve True se o acesso está autorizado."""
    if not config.protegido:
        return True
    if st.session_state.get(_SESSAO_ACESSO_OK):
        return True

    _estilos_letra_maior()
    st.markdown("### Avaliação da Defesa da PAP")
    st.caption("Acesso restrito — introduza a palavra-passe fornecida pela escola.")

    with st.form("form_juri_acesso", clear_on_submit=False):
        senha = st.text_input("Palavra-passe", type="password")
        entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

    if entrar:
        if verificar_senha_formulario(config, senha):
            st.session_state[_SESSAO_ACESSO_OK] = True
            st.rerun()
        else:
            st.error("Palavra-passe incorrecta.")
    return False


def _estilos_letra_maior() -> None:
    """Aumenta o tamanho da letra do formulário, sobretudo em tablets."""
    st.markdown(
        """
        <style>
        section.main h3 { font-size: 1.65rem !important; }
        section.main .stCaption, section.main [data-testid="stCaptionContainer"] p {
            font-size: 1rem !important;
        }
        div[data-testid="stForm"] label p { font-size: 1.1rem !important; }
        div[data-testid="stForm"] input { font-size: 1.05rem !important; }
        div[data-testid="stForm"] [data-baseweb="select"] div { font-size: 1.05rem !important; }
        div[data-testid="stForm"] .stSlider label p { font-size: 1.15rem !important; }
        div[data-testid="stForm"] [data-testid="stSliderThumbValue"] {
            font-size: 1.1rem !important;
        }
        div[data-testid="stForm"] button p { font-size: 1.15rem !important; }
        @media (max-width: 1200px) {
            section.main h3 { font-size: 1.9rem !important; }
            div[data-testid="stForm"] label p { font-size: 1.3rem !important; }
            div[data-testid="stForm"] input { font-size: 1.25rem !important; }
            div[data-testid="stForm"] [data-baseweb="select"] div {
                font-size: 1.25rem !important;
            }
            div[data-testid="stForm"] .stSlider label p { font-size: 1.35rem !important; }
            div[data-testid="stForm"] [data-testid="stSliderThumbValue"],
            div[data-testid="stForm"] [data-testid="stTickBarMin"],
            div[data-testid="stForm"] [data-testid="stTickBarMax"] {
                font-size: 1.25rem !important;
            }
            div[data-testid="stForm"] button p { font-size: 1.35rem !important; }
            div[data-testid="stForm"] button {
                min-height: 3.1rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _impedir_teclado_nas_caixas() -> None:
    """Marca os campos das caixas de seleção como não editáveis.

    No tablet, evita que o teclado do ecrã apareça (e tape as opções) quando
    se abre uma caixa de seleção, mantendo a lista a abrir normalmente.
    """
    components.html(
        """
        <script>
        (function() {
            var doc = window.parent ? window.parent.document : document;
            function aplicar() {
                var inputs = doc.querySelectorAll('[data-baseweb="select"] input');
                inputs.forEach(function(inp) {
                    inp.setAttribute('inputmode', 'none');
                    inp.setAttribute('readonly', 'readonly');
                    inp.setAttribute('autocomplete', 'off');
                });
            }
            aplicar();
            try {
                var obs = new MutationObserver(aplicar);
                obs.observe(doc.body, { childList: true, subtree: true });
            } catch (e) {}
        })();
        </script>
        """,
        height=0,
    )


_CHAVES_WIDGETS = ["juri_email", "juri_nome_sel", "juri_aluno_sel"] + [
    f"juri_nota_{chave}" for chave, _ in CRITERIOS_FORM_APRESENTACAO
]


def _escolher_da_lista(
    label: str,
    opcoes: list[str],
    *,
    placeholder: str,
    key: str,
) -> str | None:
    """Caixa de seleção sem pesquisa (não abre teclado no tablet)."""
    kwargs: dict = {"index": None, "placeholder": placeholder, "key": key}
    try:
        return st.selectbox(label, opcoes, filter_mode=None, **kwargs)
    except TypeError:
        return st.selectbox(label, opcoes, **kwargs)


def renderizar_formulario_juri(storage) -> None:
    config = carregar_config_juris()

    if not _portao_palavra_passe(config):
        return

    alunos = storage.listar_alunos()

    _estilos_letra_maior()

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
        email = st.text_input(
            "Email", placeholder="seu.email@escola.pt", key="juri_email"
        )
        juri = _escolher_da_lista(
            "Nome do júri *",
            config.juris,
            placeholder="Seleccione o seu nome",
            key="juri_nome_sel",
        )
        opcoes_alunos = {a.nome: a.id for a in alunos}
        nomes_alunos = list(opcoes_alunos.keys())
        nome_aluno = _escolher_da_lista(
            "Aluno a avaliar *",
            nomes_alunos,
            placeholder="Seleccione o aluno",
            key="juri_aluno_sel",
        )
        st.divider()
        notas: dict[str, int] = {}
        for chave, rotulo in CRITERIOS_FORM_APRESENTACAO:
            notas[chave] = st.slider(
                f"{rotulo} *",
                min_value=NOTA_MINIMA_FORM,
                max_value=NOTA_MAXIMA_FORM,
                value=NOTA_MINIMA_FORM,
                step=1,
                key=f"juri_nota_{chave}",
            )
        col_env, col_lim = st.columns(2)
        enviar = col_env.form_submit_button("Enviar", type="primary", use_container_width=True)
        limpar = col_lim.form_submit_button("Limpar formulário", use_container_width=True)

    _impedir_teclado_nas_caixas()

    if limpar:
        for chave_widget in _CHAVES_WIDGETS:
            st.session_state.pop(chave_widget, None)
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
