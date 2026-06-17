"""Render a stored markdown report to PDF using fpdf2 (pure Python, no system deps).

Chosen over WeasyPrint to avoid GTK/Cairo native dependencies on Windows.
"""

from __future__ import annotations

from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Map common Unicode punctuation to latin-1-safe equivalents (fpdf core fonts).
_REPLACEMENTS = {
    "-": "-",
    "-": "-",  # noqa: RUF001
    "•": "-",
    "≥": ">=",
    "≤": "<=",
    "“": '"',
    "”": '"',
    "‘": "'",  # noqa: RUF001
    "’": "'",  # noqa: RUF001
    "…": "...",
}


def _latin1(text: str) -> str:
    for k, v in _REPLACEMENTS.items():
        text = text.replace(k, v)
    # fpdf2 core fonts are latin-1; drop anything else rather than crashing.
    return text.encode("latin-1", "ignore").decode("latin-1")


def render_report_pdf(title: str, body_md: str) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(18, 18, 18)
    pdf.add_page()

    def write(text: str, *, size: int, style: str = "", gap: float = 1.5) -> None:
        pdf.set_font("Helvetica", style=style, size=size)
        pdf.multi_cell(
            0, size * 0.5, _latin1(text), markdown=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )
        pdf.ln(gap)

    for raw in body_md.splitlines():
        line = raw.rstrip()
        if not line:
            pdf.ln(2)
            continue
        if line.startswith("### "):
            write(line[4:], size=12, style="B", gap=1)
        elif line.startswith("## "):
            pdf.ln(1)
            write(line[3:], size=14, style="B", gap=1)
        elif line.startswith("# "):
            write(line[2:], size=18, style="B", gap=2)
        elif line.startswith("- "):
            # Render bullets with a hanging indent.
            pdf.set_font("Helvetica", size=11)
            pdf.set_x(22)
            pdf.multi_cell(
                0,
                5.5,
                _latin1("- " + line[2:].replace("_", "")),
                markdown=True,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
        else:
            write(line.replace("_", ""), size=11, gap=1)

    out = pdf.output()
    return bytes(out)
