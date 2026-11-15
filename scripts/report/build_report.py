"""Build DOCX/PDF report from docs/07_report/report.md."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs" / "07_report" / "report.md"
OUT = ROOT / "docs" / "07_report" / "report.docx"
NAVY = RGBColor(16, 42, 82)
GREY = RGBColor(90, 100, 115)


def add_inline(paragraph, text: str) -> None:
    """Add text with **bold**, `code` and [label](url) support."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    parts = re.split(r"(\*\*.*?\*\*|`[^`]+`)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9)
        else:
            paragraph.add_run(part)


def set_cell_font(cell, size: int = 8, bold: bool = False, color: RGBColor | None = None) -> None:
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(size)
            run.bold = bold
            if color:
                run.font.color.rgb = color


def parse_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and lines[index].strip().startswith("|"):
        raw = lines[index].strip().strip("|")
        cells = [cell.strip() for cell in raw.split("|")]
        if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            rows.append(cells)
        index += 1
    return rows, index


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    document = Document()
    section = document.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)

    styles = document.styles
    styles["Normal"].font.name = "Calibri"
    styles["Normal"].font.size = Pt(10)
    styles["Normal"].paragraph_format.space_after = Pt(4)
    styles["Normal"].paragraph_format.line_spacing = 1.05
    for level, size in ((1, 20), (2, 14), (3, 12)):
        style = styles[f"Heading {level}"]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.color.rgb = NAVY
        style.paragraph_format.space_before = Pt(8 if level > 1 else 0)
        style.paragraph_format.space_after = Pt(4)

    index = 0
    in_code = False
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code = not in_code
            index += 1
            continue
        if in_code:
            paragraph = document.add_paragraph()
            run = paragraph.add_run(line)
            run.font.name = "Consolas"
            run.font.size = Pt(8)
            index += 1
            continue
        if not stripped:
            index += 1
            continue
        if stripped.startswith("![") and "](" in stripped:
            match = re.match(r"!\[[^\]]*\]\(([^)]+)\)", stripped)
            if match:
                image_path = (SOURCE.parent / match.group(1)).resolve()
                if image_path.exists():
                    document.add_picture(str(image_path), width=Inches(6.4))
            index += 1
            continue
        if stripped.startswith("|"):
            rows, index = parse_table(lines, index)
            if rows:
                table = document.add_table(rows=len(rows), cols=len(rows[0]))
                table.style = "Light Grid Accent 1"
                for r, row in enumerate(rows):
                    for c, value in enumerate(row):
                        if c < len(table.rows[r].cells):
                            cell = table.rows[r].cells[c]
                            cell.text = value.replace("**", "").replace("`", "")
                            set_cell_font(cell, size=8, bold=(r == 0))
            continue
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            if level == 1:
                paragraph = document.add_paragraph()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = paragraph.add_run(text)
                run.bold = True
                run.font.size = Pt(20)
                run.font.color.rgb = NAVY
            else:
                document.add_heading(text, level=min(level, 3))
            index += 1
            continue
        if stripped.startswith("- "):
            paragraph = document.add_paragraph(style="List Bullet")
            add_inline(paragraph, stripped[2:])
            index += 1
            continue
        numbered = re.match(r"^\d+\.\s+(.*)", stripped)
        if numbered:
            paragraph = document.add_paragraph(style="List Number")
            add_inline(paragraph, numbered.group(1))
            index += 1
            continue
        if stripped.startswith(">"):
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.left_indent = Cm(0.5)
            run = paragraph.add_run(stripped.lstrip("> ").strip())
            run.italic = True
            run.font.color.rgb = GREY
            index += 1
            continue
        paragraph = document.add_paragraph()
        add_inline(paragraph, stripped)
        index += 1

    # Footer with page number.
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Music Support Triage · ")
    field = footer.add_run()
    fld = field._r.makeelement(qn("w:fldSimple"), {qn("w:instr"): "PAGE"})
    field._r.addnext(fld)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUT)
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
