from __future__ import annotations

# pyright: reportMissingImports=false
import re
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib import colors  # type: ignore[reportMissingImports]
    from reportlab.lib.pagesizes import A4  # type: ignore[reportMissingImports]
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore[reportMissingImports]
    from reportlab.lib.units import mm  # type: ignore[reportMissingImports]
    from reportlab.platypus import (  # type: ignore[reportMissingImports]
        ListFlowable,
        ListItem,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
    )
except ImportError as exc:
    raise ImportError("Missing dependency: reportlab. Install it with `pip install reportlab` and run again.") from exc


EMOJI_PATTERN = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
EMOJI_FALLBACKS = {
    "🏆": "[MVP]",
    "💀": "[WORST]",
    "🧠": "[SMART]",
    "🏹": "[CARRY]",
    "🐊": "[CROCODILE]",
    "🏗️": "[OBJECTIVES]",
}


def _resolve_font_family() -> tuple[str, str, str, str | None]:
    from reportlab.pdfbase import pdfmetrics  # type: ignore[reportMissingImports]
    from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[reportMissingImports]

    # Prefer Unicode-capable fonts to correctly render Cyrillic text.
    candidates = [
        (
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\consola.ttf",
            "Arial",
            "Arial-Bold",
            "Consolas",
        ),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "DejaVuSans",
            "DejaVuSans-Bold",
            "DejaVuSansMono",
        ),
    ]

    for regular_path, bold_path, mono_path, regular_name, bold_name, mono_name in candidates:
        if not (Path(regular_path).exists() and Path(bold_path).exists() and Path(mono_path).exists()):
            continue
        pdfmetrics.registerFont(TTFont(regular_name, regular_path))
        pdfmetrics.registerFont(TTFont(bold_name, bold_path))
        pdfmetrics.registerFont(TTFont(mono_name, mono_path))
        emoji_font_name: str | None = None
        emoji_font_path = Path("C:\\Windows\\Fonts\\seguiemj.ttf")
        if emoji_font_path.exists():
            emoji_font_name = "SegoeUIEmoji"
            pdfmetrics.registerFont(TTFont(emoji_font_name, str(emoji_font_path)))
        return regular_name, bold_name, mono_name, emoji_font_name

    # Fallback still works for Latin text, but may not render Cyrillic.
    return "Helvetica", "Helvetica-Bold", "Courier", None


def _replace_emojis_for_pdf(text: str, emoji_font_name: str | None) -> str:
    def _sub(match: re.Match[str]) -> str:
        emoji = match.group(0)
        if emoji_font_name is not None:
            return f"<font name='{emoji_font_name}'>{emoji}</font>"
        return EMOJI_FALLBACKS.get(emoji, "")

    return EMOJI_PATTERN.sub(_sub, text)


def _format_inline_markdown(
    text: str,
    code_font_name: str,
    bold_font_name: str,
    emoji_font_name: str | None,
) -> str:
    text = _replace_emojis_for_pdf(text, emoji_font_name)
    text = re.sub(r"\*\*(.+?)\*\*", rf"<font name='{bold_font_name}'>\1</font>", text)
    text = re.sub(r"`(.+?)`", rf"<font name='{code_font_name}'>\1</font>", text)
    return text


def markdown_to_pdf(markdown_text: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    regular_font_name, bold_font_name, code_font_name, emoji_font_name = _resolve_font_family()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Dota 2 Match Report",
    )

    styles = getSampleStyleSheet()
    accent_color = colors.HexColor("#2563EB")
    text_color = colors.HexColor("#111827")
    muted_color = colors.HexColor("#6B7280")
    section_bg = colors.HexColor("#F3F6FB")

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontName=bold_font_name,
        fontSize=22,
        leading=26,
        textColor=text_color,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["BodyText"],
        fontName=regular_font_name,
        fontSize=9.5,
        leading=12,
        textColor=muted_color,
        spaceAfter=10,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName=bold_font_name,
        fontSize=13,
        leading=16,
        textColor=accent_color,
        backColor=section_bg,
        borderPadding=(5, 8, 5),
        spaceBefore=12,
        spaceAfter=8,
    )
    h2_mvp_style = ParagraphStyle(
        "H2Mvp",
        parent=h2_style,
        textColor=colors.HexColor("#A16207"),
        backColor=colors.HexColor("#FEF3C7"),
    )
    h2_worst_style = ParagraphStyle(
        "H2Worst",
        parent=h2_style,
        textColor=colors.HexColor("#92400E"),
        backColor=colors.HexColor("#FDE7D8"),
    )
    h3_style = ParagraphStyle(
        "H3",
        parent=styles["Heading3"],
        fontName=bold_font_name,
        fontSize=11.5,
        leading=15,
        textColor=text_color,
        spaceBefore=8,
        spaceAfter=5,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["BodyText"],
        fontName=bold_font_name,
        fontSize=10.2,
        leading=13,
        textColor=accent_color,
        spaceBefore=4,
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName=regular_font_name,
        fontSize=10.5,
        leading=15.2,
        textColor=text_color,
        spaceAfter=5,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body_style,
        leftIndent=0,
        spaceAfter=3,
    )
    player_palettes = [
        {
            "heading_bg": colors.HexColor("#EEF4FF"),
            "heading_text": colors.HexColor("#1D4ED8"),
            "label_text": colors.HexColor("#1E40AF"),
            "body_text": colors.HexColor("#1F2937"),
            "bullet_text": colors.HexColor("#1F2937"),
        },
        {
            "heading_bg": colors.HexColor("#ECFDF5"),
            "heading_text": colors.HexColor("#047857"),
            "label_text": colors.HexColor("#065F46"),
            "body_text": colors.HexColor("#1F2937"),
            "bullet_text": colors.HexColor("#1F2937"),
        },
        {
            "heading_bg": colors.HexColor("#FEF3F2"),
            "heading_text": colors.HexColor("#B42318"),
            "label_text": colors.HexColor("#912018"),
            "body_text": colors.HexColor("#1F2937"),
            "bullet_text": colors.HexColor("#1F2937"),
        },
    ]

    report_ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    story = [
        Paragraph("Dota 2 Match Report", title_style),
        Paragraph(f"Generated at {report_ts}", subtitle_style),
        Spacer(1, 2),
    ]

    bullet_items: list[ListItem] = []
    current_bullet_font_name = regular_font_name
    current_bullet_font_size = 7
    in_player_section = False
    player_idx = -1
    current_player_body_style = body_style
    current_player_label_style = label_style
    current_player_h3_style = h3_style
    current_player_bullet_style = bullet_style

    def flush_bullets() -> None:
        nonlocal bullet_items
        if not bullet_items:
            return
        story.append(
            ListFlowable(
                bullet_items,
                bulletType="bullet",
                start="disc",
                bulletFontName=current_bullet_font_name,
                bulletFontSize=current_bullet_font_size,
                bulletIndent=2,
                leftIndent=12,
                spaceBefore=1,
                spaceAfter=6,
            )
        )
        bullet_items = []

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_bullets()
            story.append(Spacer(1, 2))
            continue

        if line.startswith("### "):
            flush_bullets()
            title_text = line[4:]
            if "игрок" in title_text.lower() or "player" in title_text.lower():
                in_player_section = True
                player_idx += 1
                palette = player_palettes[player_idx % len(player_palettes)]
                current_player_h3_style = ParagraphStyle(
                    f"PlayerH3{player_idx}",
                    parent=h3_style,
                    textColor=palette["heading_text"],
                    backColor=palette["heading_bg"],
                    borderPadding=(4, 7, 4),
                )
                current_player_label_style = ParagraphStyle(
                    f"PlayerLabel{player_idx}",
                    parent=label_style,
                    textColor=palette["label_text"],
                )
                current_player_body_style = ParagraphStyle(
                    f"PlayerBody{player_idx}",
                    parent=body_style,
                    textColor=palette["body_text"],
                )
                current_player_bullet_style = ParagraphStyle(
                    f"PlayerBullet{player_idx}",
                    parent=bullet_style,
                    textColor=palette["bullet_text"],
                )
            else:
                in_player_section = False
                current_player_h3_style = h3_style
                current_player_label_style = label_style
                current_player_body_style = body_style
                current_player_bullet_style = bullet_style

            story.append(
                Paragraph(
                    _format_inline_markdown(title_text, code_font_name, bold_font_name, emoji_font_name),
                    current_player_h3_style,
                )
            )
            continue

        if line.startswith("## "):
            flush_bullets()
            in_player_section = False
            current_player_h3_style = h3_style
            current_player_label_style = label_style
            current_player_body_style = body_style
            current_player_bullet_style = bullet_style
            h2_title = line[3:]
            lowered_h2 = h2_title.lower()
            if "mvp" in lowered_h2:
                selected_h2_style = h2_mvp_style
            elif "худший игрок" in lowered_h2 or "shit player" in lowered_h2:
                selected_h2_style = h2_worst_style
            else:
                selected_h2_style = h2_style
            story.append(
                Paragraph(
                    _format_inline_markdown(h2_title, code_font_name, bold_font_name, emoji_font_name),
                    selected_h2_style,
                )
            )
            continue

        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            flush_bullets()
            use_label_style = current_player_label_style if in_player_section else label_style
            story.append(
                Paragraph(
                    _format_inline_markdown(line[2:-2], code_font_name, bold_font_name, emoji_font_name),
                    use_label_style,
                )
            )
            continue

        if line.startswith("- "):
            bullet_items.append(
                ListItem(
                    Paragraph(
                        _format_inline_markdown(line[2:], code_font_name, bold_font_name, emoji_font_name),
                        current_player_bullet_style if in_player_section else bullet_style,
                    )
                )
            )
            continue

        flush_bullets()
        story.append(
            Paragraph(
                _format_inline_markdown(line, code_font_name, bold_font_name, emoji_font_name),
                current_player_body_style if in_player_section else body_style,
            )
        )

    flush_bullets()

    def draw_page_chrome(canvas, _doc) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#E5E7EB"))
        canvas.setLineWidth(0.8)
        canvas.line(16 * mm, 286 * mm, 194 * mm, 286 * mm)
        canvas.setFont(regular_font_name, 8.5)
        canvas.setFillColor(muted_color)
        canvas.drawRightString(194 * mm, 8 * mm, f"Page {_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_page_chrome, onLaterPages=draw_page_chrome)
    return output_path
