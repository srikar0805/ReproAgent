"""PDF/text extraction helpers."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


class PdfTextExtractionError(RuntimeError):
    pass


def extract_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace")

    if path.suffix.lower() != ".pdf":
        return path.read_text(encoding="utf-8", errors="replace")

    pypdf_text = _extract_with_pypdf(path)
    if pypdf_text.strip():
        return pypdf_text

    pdftotext_text = _extract_with_pdftotext(path)
    if pdftotext_text.strip():
        return pdftotext_text

    raise PdfTextExtractionError(
        "Could not extract text from PDF. Install the optional 'pypdf' extra "
        "or ensure pdftotext is available."
    )


def _extract_with_pypdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        return ""

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_with_pdftotext(path: Path) -> str:
    if shutil.which("pdftotext") is None:
        return ""

    result = subprocess.run(
        ["pdftotext", str(path), "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout
