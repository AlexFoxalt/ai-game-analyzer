from __future__ import annotations

from pathlib import Path

import fitz

from src.pdf import markdown_to_pdf


def save_match_report(markdown_text: str, markdown_path: Path, pdf_path: Path) -> tuple[Path, Path]:
    markdown_path.write_text(markdown_text, encoding="utf-8")
    markdown_to_pdf(markdown_text=markdown_text, output_path=pdf_path)
    return markdown_path, pdf_path


def render_pdf_pages_to_png(
    pdf_path: Path, output_dir: Path, image_prefix: str = "report", scale: float = 2.0
) -> list[Path]:
    image_paths: list[Path] = []
    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            image_path = output_dir / f"{image_prefix}_{page_index}.png"
            pixmap.save(image_path)
            image_paths.append(image_path)

    return image_paths
