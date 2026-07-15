"""Exportar e importar dados para sincronizar PC ↔ Streamlit Cloud.

O backup inclui um *dump* JSON da base de dados (funciona quer em Postgres/
Supabase, quer em SQLite) e os ficheiros binários que continuam em disco
(PDFs de pré-visualização, .docx e o Excel exportado).
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime

from app import db
from app.config import DATA_DIR, EXPORT_DIR, PDF_DIR, RELATORIOS_DIR

_DB_DUMP_NOME = "db_dump.json"

# Pastas com ficheiros binários a incluir no zip.
_PASTAS_ESSENCIAIS = (PDF_DIR, EXPORT_DIR)
_PASTAS_COMPLETAS = (RELATORIOS_DIR, EXPORT_DIR)  # RELATORIOS_DIR já contém os PDFs


def exportar_backup(*, completo: bool = False) -> bytes:
    """Cria zip com o dump da BD e os ficheiros; completo inclui também .docx."""
    pastas = _PASTAS_COMPLETAS if completo else _PASTAS_ESSENCIAIS
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            _DB_DUMP_NOME,
            json.dumps(db.exportar_dados(), ensure_ascii=False),
        )
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
                f"motor={'postgres' if db.IS_POSTGRES else 'sqlite'}\n"
            ),
        )
    return buffer.getvalue()


def importar_backup(conteudo: bytes) -> tuple[int, list[str]]:
    """Restaura um backup: reescreve a BD e os ficheiros em disco.

    Devolve (número de itens restaurados, avisos).
    """
    avisos: list[str] = []
    restaurados = 0
    with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
        nomes = zf.namelist()

        # 1) Restaurar a base de dados a partir do dump JSON.
        dump_membro = next(
            (m for m in nomes if m.replace("\\", "/").endswith(_DB_DUMP_NOME)), None
        )
        if dump_membro:
            try:
                dados = json.loads(zf.read(dump_membro).decode("utf-8"))
                restaurados += db.importar_dados(dados)
            except Exception as exc:  # noqa: BLE001
                avisos.append(f"Falha ao restaurar a base de dados: {exc}")
        else:
            avisos.append(
                "Backup antigo sem dump da base de dados — só ficheiros restaurados."
            )

        # 2) Restaurar os ficheiros binários (PDFs, .docx, Excel).
        membros = [
            m for m in nomes if m.replace("\\", "/").startswith("data/") and not m.endswith("/")
        ]
        for membro in membros:
            rel = membro.replace("\\", "/").removeprefix("data/")
            destino = DATA_DIR / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(zf.read(membro))
            restaurados += 1

        if not dump_membro and not membros:
            raise ValueError("Backup inválido — sem dump da BD nem ficheiros.")

    return restaurados, avisos


def descricao_armazenamento() -> str:
    from app.config import EM_STREAMLIT_CLOUD

    if db.IS_POSTGRES:
        return "Supabase (Postgres — persistente)"
    if EM_STREAMLIT_CLOUD:
        return "Streamlit Cloud (temporário — reinicia vazio)"
    return f"Local: {DATA_DIR}"