"""Exportar e importar a pasta data/ para sincronizar PC ↔ Streamlit Cloud."""

from __future__ import annotations

import io
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from app.config import CONFIG_DIR, DATA_DIR, DB_PATH, EXPORT_DIR, RELATORIOS_DIR

_PASTAS = (CONFIG_DIR, RELATORIOS_DIR, EXPORT_DIR)
_FICHEIROS = (DB_PATH,)


def exportar_backup() -> bytes:
    """Cria um zip com a base de dados, configuração e relatórios."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for ficheiro in _FICHEIROS:
            if ficheiro.exists():
                zf.write(ficheiro, f"data/{ficheiro.relative_to(DATA_DIR).as_posix()}")
        for pasta in _PASTAS:
            if not pasta.exists():
                continue
            for caminho in pasta.rglob("*"):
                if caminho.is_file():
                    arco = f"data/{caminho.relative_to(DATA_DIR).as_posix()}"
                    zf.write(caminho, arco)
        zf.writestr(
            "meta.txt",
            f"exportado_em={datetime.now().isoformat()}\norigem={DATA_DIR}\n",
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
            raise ValueError("Backup inválido — não contém pasta data/.")
        for membro in membros:
            rel = membro.removeprefix("data/").replace("/", Path.sep)
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
