from __future__ import annotations

import datetime as dt
from pathlib import Path

import fitz

from src.pdf import markdown_to_pdf


def _build_report_stem(match_id: int, match_start_time: int) -> str:
    match_dt = dt.datetime.fromtimestamp(match_start_time).strftime("%Y-%m-%d_%H-%M")
    return f"match_{match_id}_{match_dt}"


def save_match_report(
    markdown_text: str, match_id: int, match_start_time: int, reports_dir: str = "reports"
) -> tuple[Path, Path]:
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    report_stem = _build_report_stem(match_id=match_id, match_start_time=match_start_time)
    markdown_path = reports_path / f"{report_stem}.md"
    pdf_path = reports_path / f"{report_stem}.pdf"

    markdown_path.write_text(markdown_text, encoding="utf-8")
    markdown_to_pdf(markdown_text=markdown_text, output_path=pdf_path)
    return markdown_path, pdf_path


def render_pdf_pages_to_png(pdf_path: Path, scale: float = 2.0) -> list[Path]:
    output_dir = pdf_path.parent / f"{pdf_path.stem}_pages"
    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths: list[Path] = []
    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            image_path = output_dir / f"{pdf_path.stem}_page_{page_index:02d}.png"
            pixmap.save(image_path)
            image_paths.append(image_path)

    return image_paths
