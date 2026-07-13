from __future__ import annotations

import sys
from pathlib import Path

from app.config import PDF_DIR

_WD_FORMAT_PDF = 17


def gerar_pdf(docx_path: Path) -> tuple[Path | None, str | None]:
    """Converte DOCX para PDF. Devolve (caminho_pdf, erro)."""
    docx_path = Path(docx_path).resolve()
    if not docx_path.exists():
        return None, "Ficheiro DOCX nao encontrado."

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = (PDF_DIR / f"{docx_path.stem}.pdf").resolve()

    if pdf_path.exists() and pdf_path.stat().st_mtime >= docx_path.stat().st_mtime:
        return pdf_path, None

    if sys.platform != "win32":
        return None, "Conversao PDF so esta disponivel no Windows."

    word = None
    doc = None
    try:
        import pythoncom
        import win32com.client  # type: ignore

        pythoncom.CoInitialize()
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0

        doc = word.Documents.Open(str(docx_path), ReadOnly=True, AddToRecentFiles=False)
        try:
            doc.ExportAsFixedFormat(
                OutputFileName=str(pdf_path),
                ExportFormat=_WD_FORMAT_PDF,
                OpenAfterExport=False,
                OptimizeFor=0,
                CreateBookmarks=0,
            )
        except Exception:
            doc.SaveAs2(str(pdf_path), FileFormat=_WD_FORMAT_PDF)

        if pdf_path.exists():
            return pdf_path, None
        return None, "Word nao criou o ficheiro PDF."
    except Exception as exc:
        return None, f"Erro ao converter para PDF: {exc}"
    finally:
        if doc is not None:
            try:
                doc.Close(False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        try:
            import pythoncom

            pythoncom.CoUninitialize()
        except Exception:
            pass


def caminho_pdf_para_docx(nome_docx: str) -> Path:
    return PDF_DIR / f"{Path(nome_docx).stem}.pdf"
