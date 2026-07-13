from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from app.config import PDF_DIR

_WD_FORMAT_PDF = 17


def caminho_pdf_para_docx(nome_docx: str) -> Path:
    return PDF_DIR / f"{Path(nome_docx).stem}.pdf"


def _pdf_actualizado(docx_path: Path, pdf_path: Path) -> bool:
    return pdf_path.exists() and pdf_path.stat().st_mtime >= docx_path.stat().st_mtime


def _gerar_pdf_word(docx_path: Path, pdf_path: Path) -> str | None:
    """Microsoft Word via COM (Windows). Devolve mensagem de erro ou None."""
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
            return None
        return "Word não criou o ficheiro PDF."
    except ImportError:
        return "pywin32 não instalado — execute: pip install pywin32"
    except Exception as exc:
        return f"Microsoft Word: {exc}"
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


def _caminhos_libreoffice() -> list[str]:
    candidatos = ["soffice", "libreoffice"]
    if sys.platform == "win32":
        for base in (
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        ):
            if base.exists():
                candidatos.append(str(base))
    return candidatos


def _gerar_pdf_libreoffice(docx_path: Path, pdf_path: Path) -> str | None:
    """LibreOffice headless (Windows/Linux). Devolve mensagem de erro ou None."""
    for comando in _caminhos_libreoffice():
        binario = shutil.which(comando) if not Path(comando).exists() else comando
        if not binario:
            continue
        try:
            resultado = subprocess.run(
                [
                    binario,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(pdf_path.parent),
                    str(docx_path),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if pdf_path.exists():
                return None
            detalhe = (resultado.stderr or resultado.stdout or "").strip()
            if detalhe:
                return f"LibreOffice: {detalhe[:200]}"
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return "LibreOffice demorou demasiado a converter."
        except Exception as exc:
            return f"LibreOffice: {exc}"
    return None


def docx_para_html(docx_path: Path) -> tuple[str | None, str | None]:
    """Pré-visualização HTML (funciona online sem Word). Devolve (html, erro)."""
    try:
        import mammoth
    except ImportError:
        return None, "mammoth não instalado"
    if not docx_path.exists():
        return None, "Ficheiro DOCX não encontrado."
    try:
        with docx_path.open("rb") as ficheiro:
            resultado = mammoth.convert_to_html(ficheiro)
        return resultado.value, None
    except Exception as exc:
        return None, str(exc)


def gerar_pdf(docx_path: Path) -> tuple[Path | None, str | None]:
    """Converte DOCX para PDF. Devolve (caminho_pdf, erro)."""
    docx_path = Path(docx_path).resolve()
    if not docx_path.exists():
        return None, "Ficheiro DOCX não encontrado — importe o .docx ou use backup completo."

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = caminho_pdf_para_docx(docx_path.name).resolve()

    if _pdf_actualizado(docx_path, pdf_path):
        return pdf_path, None

    erros: list[str] = []

    if sys.platform == "win32":
        erro_word = _gerar_pdf_word(docx_path, pdf_path)
        if erro_word is None and pdf_path.exists():
            return pdf_path, None
        if erro_word:
            erros.append(erro_word)

    erro_lo = _gerar_pdf_libreoffice(docx_path, pdf_path)
    if erro_lo is None and pdf_path.exists():
        return pdf_path, None
    if erro_lo:
        erros.append(erro_lo)

    if sys.platform != "win32" and not erros:
        erros.append("Instale LibreOffice para converter PDF no servidor.")

    if erros:
        return None, " · ".join(erros)

    if sys.platform == "win32":
        return None, "Instale Microsoft Word ou LibreOffice para gerar PDF."
    return None, "Conversão PDF indisponível neste ambiente."
