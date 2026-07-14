"""Formulário público para avaliação da defesa da PAP pelos júris."""

import streamlit as st

from app.formulario_juri import renderizar_formulario_juri
from app.storage import PapStorage

st.set_page_config(
    page_title="Formulário Júri — PAP",
    page_icon="🎤",
    layout="centered",
)

storage = PapStorage()
renderizar_formulario_juri(storage)
