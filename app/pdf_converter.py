"""Caminhos dos PDFs de pré-visualização (upload manual — sem conversão automática)."""

from __future__ import annotations

from pathlib import Path

from app.config import PDF_DIR


def caminho_pdf_para_docx(nome_docx: str) -> Path:
    """PDF associado ao relatório .docx (mesmo nome, extensão .pdf)."""
    return PDF_DIR / f"{Path(nome_docx).stem}.pdf"


def guardar_pdf(conteudo: bytes, nome_destino: str) -> Path:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    destino = PDF_DIR / Path(nome_destino).name
    destino.write_bytes(conteudo)
    return destino
