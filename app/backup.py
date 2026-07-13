"""Exportar e importar a pasta data/ para sincronizar PC ↔ Streamlit Cloud."""

from __future__ import annotations

import io
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from app.config import CONFIG_DIR, DATA_DIR, DB_PATH, EXPORT_DIR, RELATORIOS_DIR

_PASTAS_COMPLETAS = (CONFIG_DIR, RELATORIOS_DIR, EXPORT_DIR)
_PASTAS_ESSENCIAIS = (CONFIG_DIR, EXPORT_DIR)
_FICHEIROS = (DB_PATH,)


def exportar_backup(*, completo: bool = False) -> bytes:
    """Cria zip com bd + config; opcionalmente inclui relatórios .docx/.pdf."""
    pastas = _PASTAS_COMPLETAS if completo else _PASTAS_ESSENCIAIS
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for ficheiro in _FICHEIROS:
            if ficheiro.exists():
                zf.write(ficheiro, f"data/{ficheiro.relative_to(DATA_DIR).as_posix()}")
        for pasta in pastas:
            if not pasta.exists():
                continue
            for caminho in pasta.rglob("*"):
                if caminho.is_file():
                    arco = f"data/{caminho.relative_to(DATA_DIR).as_posix()}"
                    zf.write(caminho, arco)
        zf.writestr(
            "meta.txt",
            (
                f"exportado_em={datetime.now().isoformat()}\n"
                f"origem={DATA_DIR}\n"
                f"completo={completo}\n"
            ),
        )
    return buffer.getvalue()


def importar_backup(conteudo: bytes) -> tuple[int, list[str]]:
    """
    Restaura um backup sobre DATA_DIR.
    Devolve (número de ficheiros restaurados, avisos).
    """
    avisos: list[str] = []
    restaurados = 0
    with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
        membros = [m for m in zf.namelist() if m.startswith("data/") and not m.endswith("/")]
        if not membros:
            # Windows pode gravar barras invertidas no zip
            membros = [
                m.replace("\\", "/")
                for m in zf.namelist()
                if m.replace("\\", "/").startswith("data/") and not m.endswith("/")
            ]
        if not membros:
            raise ValueError("Backup inválido — não contém pasta data/.")
        for membro in membros:
            rel = membro.replace("\\", "/").removeprefix("data/")
            destino = DATA_DIR / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(zf.read(membro))
            restaurados += 1
    return restaurados, avisos


def descricao_armazenamento() -> str:
    from app.config import EM_STREAMLIT_CLOUD

    if EM_STREAMLIT_CLOUD:
        return "Streamlit Cloud (temporário — reinicia vazio)"
    return f"Local: {DATA_DIR}"
