"""Build the defence deck and the slide-by-slide speech.

The deck is intentionally visual: short labels, KPI cards, diagrams and charts,
with the full argument moved into speaker notes and ``speech.md``.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "07_report" / "presentation.pptx"
SPEECH_PATH = ROOT / "docs" / "07_report" / "speech.md"

INK = RGBColor(15, 23, 42)
SLATE = RGBColor(51, 65, 85)
MUTED = RGBColor(100, 116, 139)
LINE = RGBColor(226, 232, 240)
PAPER = RGBColor(248, 250, 252)
WHITE = RGBColor(255, 255, 255)
BLUE = RGBColor(37, 99, 235)
BLUE_LIGHT = RGBColor(219, 234, 254)
SKY = RGBColor(96, 165, 250)
MINT = RGBColor(16, 185, 129)
MINT_LIGHT = RGBColor(209, 250, 229)
AMBER = RGBColor(217, 119, 6)
AMBER_LIGHT = RGBColor(254, 243, 199)
CORAL = RGBColor(220, 38, 38)
CORAL_LIGHT = RGBColor(254, 226, 226)

FONT = "Arial"
MONO = "Consolas"


def add_text(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    size: float = 14,
    bold: bool = False,
    color: RGBColor = INK,
    align=PP_ALIGN.LEFT,
    font: str = FONT,
    anchor=MSO_ANCHOR.TOP,
    line_spacing: float = 1.08,
) -> None:
    """Add a text box with consistent formatting."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    frame.vertical_anchor = anchor
    for index, line in enumerate(text.split("\n")):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = line
        paragraph.alignment = align
        paragraph.line_spacing = line_spacing
        paragraph.space_after = Pt(0)
        for run in paragraph.runs:
            run.font.name = font
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = color


def add_paragraphs(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    items: list[str],
    size: float = 14,
    color: RGBColor = SLATE,
    gap: float = 8,
) -> None:
    """Add a simple bullet list."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = f"•  {item}"
        paragraph.space_after = Pt(gap)
        paragraph.line_spacing = 1.05
        for run in paragraph.runs:
            run.font.name = FONT
            run.font.size = Pt(size)
            run.font.color.rgb = color


def add_rect(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: RGBColor = WHITE,
    line: RGBColor | None = LINE,
    radius: float = 0.08,
    shape=MSO_SHAPE.ROUNDED_RECTANGLE,
):
    """Add a flat rounded card or rectangle."""
    rect = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    rect.fill.solid()
    rect.fill.fore_color.rgb = fill
    if line is None:
        rect.line.fill.background()
    else:
        rect.line.color.rgb = line
        rect.line.width = Pt(1)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        rect.adjustments[0] = radius
    rect.shadow.inherit = False
    return rect


def add_chip(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    fill: RGBColor = BLUE_LIGHT,
    color: RGBColor = BLUE,
    size: float = 11,
    bold: bool = True,
) -> None:
    """Add a compact rounded label."""
    add_rect(slide, x, y, w, h, fill=fill, line=None, radius=0.5)
    add_text(
        slide,
        x,
        y,
        w,
        h,
        text,
        size=size,
        bold=bold,
        color=color,
        align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )


def add_kpi(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    value: str,
    label: str,
    accent: RGBColor = BLUE,
    sub: str | None = None,
) -> None:
    """Add a KPI card with a top accent bar."""
    add_rect(slide, x, y, w, h, fill=WHITE, line=LINE, radius=0.07)
    add_rect(slide, x, y, w, 0.07, fill=accent, line=None, radius=0.0, shape=MSO_SHAPE.RECTANGLE)
    add_text(slide, x + 0.24, y + 0.2, w - 0.4, 0.55, value, size=27, bold=True, color=accent)
    add_text(slide, x + 0.24, y + 0.78, w - 0.4, 0.35, label, size=11, color=MUTED)
    if sub:
        add_text(slide, x + 0.24, y + 1.1, w - 0.4, 0.3, sub, size=9.5, color=MUTED)


def add_header(slide, kicker: str, title: str, subtitle: str | None = None) -> None:
    """Slide header with stage kicker, title and optional subtitle."""
    add_rect(slide, 0.55, 0.48, 0.08, 0.62, fill=BLUE, line=None, radius=0.0,
             shape=MSO_SHAPE.RECTANGLE)
    add_text(slide, 0.78, 0.42, 11.6, 0.3, kicker.upper(), size=10.5, bold=True, color=BLUE)
    add_text(slide, 0.76, 0.7, 11.9, 0.62, title, size=28, bold=True, color=INK)
    if subtitle:
        add_text(slide, 0.78, 1.27, 11.9, 0.35, subtitle, size=13.5, color=MUTED)


def add_footer(slide, number: int) -> None:
    """Thin footer with project name and slide number."""
    add_rect(slide, 0.55, 7.12, 12.23, 0.012, fill=LINE, line=None, radius=0.0,
             shape=MSO_SHAPE.RECTANGLE)
    add_text(slide, 0.55, 7.18, 7.0, 0.24, "Music Support Triage · 2026", size=8.5, color=MUTED)
    add_text(slide, 11.7, 7.16, 1.1, 0.26, str(number), size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def add_image_fit(slide, path: Path, x: float, y: float, w: float, h: float) -> None:
    """Place an image inside a box without distortion."""
    width, height = Image.open(path).size
    scale = min(w / width, h / height)
    new_w, new_h = width * scale, height * scale
    left = x + (w - new_w) / 2
    top = y + (h - new_h) / 2
    slide.shapes.add_picture(str(path), Inches(left), Inches(top), Inches(new_w), Inches(new_h))


def add_notes(slide, text: str) -> None:
    """Put the speech fragment into PowerPoint speaker notes."""
    slide.notes_slide.notes_text_frame.text = text


def slide_title(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, 13.333, 7.5, fill=INK, line=None, radius=0.0,
             shape=MSO_SHAPE.RECTANGLE)

    add_rect(slide, 9.55, 0.95, 3.35, 3.35, fill=BLUE, line=None, radius=0.5,
             shape=MSO_SHAPE.OVAL)
    add_text(slide, 9.55, 1.55, 3.35, 1.7, "7", size=128, bold=True, color=WHITE,
             align=PP_ALIGN.CENTER)
    add_text(slide, 9.55, 3.35, 3.35, 0.4, "тем", size=23, bold=True, color=BLUE_LIGHT,
             align=PP_ALIGN.CENTER)
    add_text(slide, 9.55, 4.55, 3.35, 0.4, "→ 7 очередей", size=16, color=SKY,
             align=PP_ALIGN.CENTER)
    add_text(slide, 9.55, 5.0, 3.35, 0.4, "+ manual_review", size=12.5, color=MUTED,
             align=PP_ALIGN.CENTER)

    add_text(slide, 0.8, 1.55, 8.6, 0.3, "ИТОГОВЫЙ ПРОЕКТ · ИНТЕГРАЦИЯ ИИ", size=11.5,
             bold=True, color=SKY)
    add_text(slide, 0.78, 1.95, 8.7, 1.2, "Music Support\nTriage", size=50, bold=True, color=WHITE,
             line_spacing=0.92)
    add_rect(slide, 0.82, 3.52, 1.35, 0.06, fill=SKY, line=None, radius=0.0,
             shape=MSO_SHAPE.RECTANGLE)
    add_text(
        slide,
        0.82,
        3.75,
        8.0,
        1.0,
        "Классификация обращений в поддержку\nмузыкального сервиса",
        size=21,
        color=BLUE_LIGHT,
        line_spacing=1.12,
    )
    add_text(slide, 0.82, 5.0, 8.2, 0.35,
             "Задача → архитектура → эксперименты → тесты → деплой → мониторинг",
             size=12, color=SKY)
    add_text(
        slide,
        0.82,
        6.35,
        8.6,
        0.35,
        "Максим Федулаев · Владимир Егоров · Айдар Мугизов · Евгений Кононов · Александр Аксенов",
        size=10.5,
        color=RGBColor(203, 213, 225),
    )
    add_text(slide, 0.82, 6.72, 8.6, 0.3,
             "github.com/NexPG/final-project-IAIiD", size=9.5, color=MUTED)
    add_text(slide, 11.9, 7.16, 0.9, 0.26, "1", size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def slide_problem(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(
        slide,
        "01 · Бизнес-контекст",
        "Тикет должен попасть в нужную очередь",
        "С первого раза — без ручной сортировки и лишних передач.",
    )
    cards = [
        ("01", "Ручная сортировка", "оператор читает каждый тикет", BLUE),
        ("02", "Ошибка маршрута", "тикет ждёт не того специалиста", AMBER),
        ("03", "Долгий ответ", "растёт время первой реакции", CORAL),
    ]
    for index, (number, title, subtitle, color) in enumerate(cards):
        y = 1.75 + index * 1.55
        add_rect(slide, 7.55, y, 5.05, 1.35, fill=WHITE, line=LINE, radius=0.08)
        add_text(slide, 7.8, y + 0.22, 0.8, 0.45, number, size=22, bold=True, color=color)
        add_text(slide, 8.6, y + 0.2, 3.8, 0.4, title, size=15.5, bold=True, color=INK)
        add_text(slide, 8.6, y + 0.66, 3.8, 0.4, subtitle, size=11.5, color=MUTED)
    add_text(slide, 0.8, 5.6, 6.2, 0.9,
             "Цель — не заменить оператора,\nа дать ему быстрый и безопасный черновик маршрута.",
             size=15, color=SLATE, line_spacing=1.15)
    add_footer(slide, 2)


def slide_task(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(
        slide,
        "02 · Что делает система",
        "Текст → тема → очередь",
        "Один запрос — один предсказанный класс и безопасный fallback.",
    )
    flow = [
        (0.75, "ВХОД", "Текст обращения", "subject · channel · locale", BLUE),
        (5.0, "МОДЕЛЬ", "TF-IDF + LogReg", "top-3 · confidence · margin", MINT),
        (9.25, "ВЫХОД", "Тема + очередь", "manual_review при риске", AMBER),
    ]
    for x, label, title, subtitle, color in flow:
        add_rect(slide, x, 1.9, 3.35, 1.65, fill=WHITE, line=LINE, radius=0.08)
        add_rect(slide, x, 1.9, 3.35, 0.07, fill=color, line=None, radius=0.0,
                 shape=MSO_SHAPE.RECTANGLE)
        add_text(slide, x + 0.25, 2.12, 2.9, 0.3, label, size=9.5, bold=True, color=color)
        add_text(slide, x + 0.25, 2.48, 2.9, 0.4, title, size=17, bold=True, color=INK)
        add_text(slide, x + 0.25, 2.98, 2.9, 0.3, subtitle, size=10.5, color=MUTED)
    for x in (4.15, 8.4):
        add_text(slide, x, 2.55, 0.75, 0.4, "→", size=25, color=SKY, align=PP_ALIGN.CENTER)

    chips = [
        ("payment", 1.85, 1.25),
        ("subscription", 3.25, 1.55),
        ("account", 4.95, 1.2),
        ("app", 6.3, 0.9),
        ("recommendations", 7.35, 1.8),
        ("content", 9.3, 1.15),
        ("other", 10.6, 0.95),
    ]
    for name, x, width in chips:
        add_chip(slide, x, 4.15, width, 0.5, name, fill=BLUE_LIGHT, color=BLUE, size=11)
    add_rect(slide, 0.75, 5.25, 11.8, 0.85, fill=AMBER_LIGHT, line=None, radius=0.12)
    add_text(slide, 1.0, 5.43, 11.3, 0.5,
             "confidence < 0.70  или  margin < 0.05   →   manual_review",
             size=15, bold=True, color=AMBER, align=PP_ALIGN.CENTER)
    add_footer(slide, 3)


def slide_data(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "03 · Данные", "Два реальных источника",
               "Synthetic исключён: для учебного кейса хватает реальных обращений.")
    add_image_fit(slide, ROOT / "docs" / "07_report" / "fig_data.png", 0.6, 1.55, 4.2, 5.1)
    kpis = [
        ("13 427", "всего обращений", BLUE, "TWCS + Bitext"),
        ("2", "реальных источника", MINT, "без synthetic"),
        ("10 713", "train", BLUE, "80% пула"),
        ("2 714", "test", AMBER, "20% · frozen"),
    ]
    positions = [(5.25, 1.7), (9.0, 1.7), (5.25, 3.4), (9.0, 3.4)]
    for (value, label, color, sub), (x, y) in zip(kpis, positions, strict=True):
        add_kpi(slide, x, y, 3.5, 1.45, value, label, accent=color, sub=sub)
    add_chip(slide, 5.25, 5.25, 2.35, 0.48, "80/20 split", fill=BLUE_LIGHT, color=BLUE)
    add_chip(slide, 7.75, 5.25, 2.75, 0.48, "стратификация", fill=BLUE_LIGHT, color=BLUE)
    add_chip(slide, 10.65, 5.25, 1.85, 0.48, "5-fold CV", fill=MINT_LIGHT, color=MINT)
    add_text(slide, 5.25, 6.0, 7.3, 0.6,
             "Группы held-out по conversation_id · test открывается один раз",
             size=11.5, color=MUTED)
    add_footer(slide, 4)


def slide_architecture(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "04 · Архитектура", "Модульный монолит",
               "Один сервис, один потребитель, небольшая нагрузка.")
    add_rect(slide, 0.45, 1.55, 6.95, 5.15, fill=WHITE, line=LINE, radius=0.05)
    add_image_fit(
        slide,
        ROOT / "docs" / "02_architecture" / "architecture_business.png",
        0.6,
        1.68,
        6.65,
        4.9,
    )
    cards = [
        ("Монолит", "проще запускать и сопровождать", BLUE),
        ("Online", "ответ нужен в момент обращения", MINT),
        ("Fallback", "низкая уверенность → manual", AMBER),
    ]
    for index, (title, text, color) in enumerate(cards):
        y = 1.7 + index * 1.45
        add_rect(slide, 7.75, y, 4.85, 1.2, fill=WHITE, line=LINE, radius=0.08)
        add_rect(slide, 7.75, y, 0.08, 1.2, fill=color, line=None, radius=0.0,
                 shape=MSO_SHAPE.RECTANGLE)
        add_text(slide, 8.0, y + 0.18, 4.3, 0.35, title, size=15, bold=True, color=INK)
        add_text(slide, 8.0, y + 0.6, 4.3, 0.4, text, size=11, color=MUTED)
    add_text(slide, 7.75, 6.15, 4.9, 0.5,
             "Микросервисы были бы overengineering.", size=11.5, color=MUTED)
    add_footer(slide, 5)


def slide_technical(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "05 · Компоненты", "Три узких места",
               "Модель, очередь и drift закрыты readiness, retry и мониторингом.")
    add_rect(slide, 0.35, 1.62, 12.65, 4.55, fill=WHITE, line=LINE, radius=0.04)
    add_image_fit(slide, ROOT / "docs" / "02_architecture" / "architecture.png",
                  0.45, 1.7, 12.45, 4.4)
    badges = [
        ("Модель", "503 · readiness · rollback", BLUE),
        ("Очередь", "retry · manual fallback", AMBER),
        ("Drift", "PSI · KS · retrain", MINT),
    ]
    for index, (title, text, color) in enumerate(badges):
        x = 0.55 + index * 4.05
        add_rect(slide, x, 6.28, 3.85, 0.55, fill=WHITE, line=LINE, radius=0.4)
        add_text(slide, x + 0.2, 6.36, 0.8, 0.35, title, size=10, bold=True, color=color)
        add_text(slide, x + 1.0, 6.37, 2.7, 0.35, text, size=9.5, color=MUTED)
    add_footer(slide, 6)


def slide_api(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "06 · Контракт", "Шесть endpoint'ов",
               "REST, Pydantic-валидация, единый error envelope.")
    endpoints = [
        ("POST", "/v1/classify", "один тикет"),
        ("POST", "/v1/classify/batch", "до 100"),
        ("POST", "/v1/feedback", "решение оператора"),
        ("GET", "/healthcheck", "readiness"),
        ("GET", "/model-info", "версия модели"),
        ("GET", "/metrics", "Prometheus"),
    ]
    for index, (method, path, note) in enumerate(endpoints):
        y = 1.7 + index * 0.74
        fill = MINT_LIGHT if method == "POST" else BLUE_LIGHT
        color = MINT if method == "POST" else BLUE
        add_chip(slide, 0.7, y, 0.8, 0.42, method, fill=fill, color=color, size=9.5)
        add_text(slide, 1.65, y + 0.02, 3.4, 0.4, path, size=13.5, bold=True, color=INK,
                 font=MONO)
        add_text(slide, 5.0, y + 0.04, 2.1, 0.35, note, size=10.5, color=MUTED)

    add_rect(slide, 7.35, 1.65, 5.3, 3.55, fill=INK, line=None, radius=0.06)
    add_text(slide, 7.6, 1.82, 4.8, 0.3, "POST /v1/classify", size=10, bold=True, color=SKY,
             font=MONO)
    add_text(
        slide,
        7.6,
        2.2,
        4.8,
        2.6,
        '{\n  "topic": "payment",\n  "queue": "billing",\n  "confidence": 0.93,\n'
        '  "margin": 0.41,\n  "needs_human_review": false\n}',
        size=12.5,
        color=RGBColor(226, 232, 240),
        font=MONO,
        line_spacing=1.22,
    )
    add_chip(slide, 7.35, 5.45, 1.55, 0.48, "OpenAPI", fill=BLUE_LIGHT, color=BLUE, size=10.5)
    add_chip(slide, 9.05, 5.45, 1.7, 0.48, "p95 ≤ 500 мс", fill=MINT_LIGHT, color=MINT, size=10.5)
    add_chip(slide, 10.9, 5.45, 1.6, 0.48, "5xx < 1%", fill=AMBER_LIGHT, color=AMBER, size=10.5)
    add_text(slide, 0.7, 6.35, 6.4, 0.4, "X-Request-ID · единый формат ошибок", size=11, color=MUTED)
    add_footer(slide, 7)


def slide_experiments(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "07 · Эксперименты", "4 семейства, 120 кандидатов",
               "Выбор только по CV: test не участвовал.")
    add_image_fit(slide, ROOT / "docs" / "07_report" / "fig_models.png", 0.55, 1.55, 7.2, 4.7)
    cards = [
        ("120", "кандидатов на семейство", BLUE),
        ("5-fold", "StratifiedGroupKFold", MINT),
        ("0.855", "лучший CV macro-F1", AMBER),
    ]
    for index, (value, label, color) in enumerate(cards):
        y = 1.65 + index * 1.5
        add_kpi(slide, 8.0, y, 4.65, 1.3, value, label, accent=color)
    add_text(slide, 8.0, 6.3, 4.7, 0.4,
             "HalvingRandomSearchCV · factor 2", size=11, color=MUTED)
    add_footer(slide, 8)


def slide_test(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "08 · Один замер на test", "Macro-F1 0.855",
               "Качество на 2 714 отложенных обращениях.")
    kpis = [
        ("0.855", "Macro-F1", BLUE, "95% CI [0.791; 0.908]"),
        ("0.963", "Accuracy", MINT, "weighted-F1 0.963"),
        ("0.979", "Selective precision", AMBER, "на auto-routed"),
        ("0.948", "Coverage", SKY, "review rate 0.052"),
    ]
    for index, (value, label, color, sub) in enumerate(kpis):
        add_kpi(slide, 0.55 + index * 3.12, 1.7, 2.9, 1.55, value, label, accent=color, sub=sub)

    add_rect(slide, 0.55, 3.65, 12.2, 2.2, fill=WHITE, line=LINE, radius=0.06)
    add_text(slide, 0.85, 3.85, 4.0, 0.35, "Bootstrap 95% CI", size=11, bold=True, color=MUTED)
    left, right = 2.0, 11.4
    low, high = 0.75, 0.95

    def px(value: float) -> float:
        return left + (value - low) / (high - low) * (right - left)

    axis_y = 4.85
    add_rect(slide, left, axis_y, right - left, 0.012, fill=LINE, line=None, radius=0.0,
             shape=MSO_SHAPE.RECTANGLE)
    for tick in (0.80, 0.85, 0.90):
        add_rect(slide, px(tick), axis_y - 0.06, 0.012, 0.12, fill=MUTED, line=None,
                 radius=0.0, shape=MSO_SHAPE.RECTANGLE)
        add_text(slide, px(tick) - 0.3, axis_y + 0.14, 0.6, 0.3, f"{tick:.2f}", size=9.5,
                 color=MUTED, align=PP_ALIGN.CENTER)
    add_rect(slide, px(0.791), axis_y - 0.05, px(0.908) - px(0.791), 0.1, fill=BLUE_LIGHT,
             line=None, radius=0.5)
    add_rect(slide, px(0.855) - 0.07, axis_y - 0.17, 0.14, 0.34, fill=BLUE, line=None,
             radius=0.5)
    add_text(slide, px(0.791) - 0.35, axis_y - 0.45, 0.7, 0.3, "0.791", size=10.5, bold=True,
             color=BLUE, align=PP_ALIGN.CENTER)
    add_text(slide, px(0.908) - 0.35, axis_y - 0.45, 0.7, 0.3, "0.908", size=10.5, bold=True,
             color=BLUE, align=PP_ALIGN.CENTER)
    add_text(slide, px(0.855) - 0.8, axis_y + 0.45, 1.6, 0.3, "0.855", size=12, bold=True,
             color=BLUE, align=PP_ALIGN.CENTER)
    add_text(slide, 0.85, 6.15, 11.6, 0.4,
             "TWCS отдельно: macro-F1 0.739 — честная граница, а не результат выбора по test.",
             size=11.5, color=MUTED)
    add_footer(slide, 9)


def slide_errors(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "09 · Error analysis", "Где модель ошибается",
               "Редкие классы тянут macro-F1 вниз, но routing остаётся безопасным.")
    add_image_fit(slide, ROOT / "docs" / "07_report" / "fig_recall.png", 0.5, 1.5, 6.55, 4.9)
    add_rect(slide, 7.35, 1.6, 5.3, 3.05, fill=CORAL_LIGHT, line=CORAL, radius=0.06)
    add_text(slide, 7.6, 1.78, 4.8, 0.3, "НАЙДЕННЫЙ БАГ", size=9.5, bold=True, color=CORAL)
    add_text(
        slide,
        7.6,
        2.12,
        4.8,
        1.1,
        "«I don't want to cancel my subscription, I need a receipt»",
        size=12.5,
        color=INK,
        line_spacing=1.15,
    )
    add_text(slide, 7.6, 2.95, 4.8, 0.3, "Отрицание и два интента в одном тексте.",
             size=10.5, color=MUTED)
    add_text(slide, 7.6, 3.35, 4.8, 0.3, "→ subscription · confidence 0.647", size=12,
             bold=True, color=CORAL)
    add_text(slide, 7.6, 3.82, 4.8, 0.5, "→ manual_review: безопасный fallback", size=11.5,
             color=SLATE)
    add_rect(slide, 7.35, 4.75, 5.3, 1.15, fill=AMBER_LIGHT, line=None, radius=0.08)
    add_text(slide, 7.6, 4.92, 4.8, 0.3, "content 0.40 · app 0.69", size=14, bold=True, color=AMBER)
    add_text(slide, 7.6, 5.32, 4.8, 0.3, "редкие классы: мало поддержки в test", size=10.5,
             color=MUTED)
    add_text(slide, 0.55, 6.5, 12.0, 0.35,
             "Ошибки не маскируются accuracy 0.963: смотрим per-class recall.",
             size=11.5, color=MUTED)
    add_footer(slide, 10)


def slide_testing(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "10 · Тестирование", "38 тестов закрывают весь путь",
               "Unit, data, model и integration — плюс data validation и load test.")
    columns = [
        ("01", "Unit", "текст, PII, маппинг", "split, dedup, routing", BLUE),
        ("02", "Model", "quality, per-class", "robustness, edge, subgroup", MINT),
        ("03", "API", "contract, batch, feedback", "422/503, error envelope", AMBER),
    ]
    for index, (number, title, line1, line2, color) in enumerate(columns):
        x = 0.65 + index * 3.95
        add_rect(slide, x, 1.65, 3.65, 2.45, fill=WHITE, line=LINE, radius=0.07)
        add_text(slide, x + 0.25, 1.85, 0.7, 0.4, number, size=18, bold=True, color=color)
        add_text(slide, x + 0.25, 2.3, 3.1, 0.4, title, size=17, bold=True, color=INK)
        add_text(slide, x + 0.25, 2.85, 3.1, 0.65, line1, size=11.5, color=SLATE)
        add_text(slide, x + 0.25, 3.4, 3.1, 0.65, line2, size=11.5, color=SLATE)

    add_rect(slide, 0.65, 4.45, 12.1, 1.3, fill=PAPER, line=LINE, radius=0.06)
    metrics = [
        ("38", "тестов"),
        ("8/8", "GE clean"),
        ("4/8", "dirty поймано"),
        ("5/5", "smoke"),
        ("52.72", "p95, мс"),
    ]
    for index, (value, label) in enumerate(metrics):
        x = 0.9 + index * 2.4
        add_text(slide, x, 4.6, 2.0, 0.5, value, size=22, bold=True, color=BLUE)
        add_text(slide, x, 5.12, 2.0, 0.3, label, size=10, color=MUTED)
    add_text(slide, 0.65, 6.2, 11.9, 0.35,
             "CI на GitHub Actions: ruff, mypy, pytest; Docker и smoke — локально.",
             size=11, color=MUTED)
    add_footer(slide, 11)


def slide_deploy(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "11 · Деплой", "Docker + Compose",
               "Одна команда поднимает api, Prometheus и Grafana.")
    steps = [
        (0.7, "Dockerfile", "multi-stage · non-root"),
        (4.35, "Image", "716 MB · healthcheck"),
        (8.0, "Compose", "api + monitoring"),
    ]
    for x, title, subtitle in steps:
        add_rect(slide, x, 1.75, 3.3, 1.15, fill=WHITE, line=LINE, radius=0.08)
        add_text(slide, x + 0.25, 1.95, 2.8, 0.4, title, size=16, bold=True, color=INK)
        add_text(slide, x + 0.25, 2.38, 2.85, 0.3, subtitle, size=10.5, color=MUTED)
    for x in (4.05, 7.7):
        add_text(slide, x, 2.05, 0.5, 0.4, "→", size=24, color=SKY, align=PP_ALIGN.CENTER)

    services = [("api", BLUE), ("prometheus", AMBER), ("grafana", MINT)]
    for index, (name, color) in enumerate(services):
        add_chip(slide, 11.55, 1.72 + index * 0.52, 1.25, 0.4, name, fill=WHITE, color=color,
                 size=9.5)
    add_text(slide, 11.4, 3.35, 1.5, 0.3, "3 сервиса", size=9.5, color=MUTED,
             align=PP_ALIGN.CENTER)

    kpis = [
        ("5/5", "smoke", BLUE),
        ("0", "ошибок load", MINT),
        ("52.72", "p95, мс", AMBER),
    ]
    for index, (value, label, color) in enumerate(kpis):
        add_kpi(slide, 0.7 + index * 4.05, 3.3, 3.7, 1.35, value, label, accent=color)

    add_rect(slide, 0.7, 5.25, 11.9, 0.5, fill=INK, line=None, radius=0.08)
    add_text(slide, 0.9, 5.35, 11.5, 0.3,
             "$ docker compose -f docker/docker-compose.yml up -d --wait", size=10.5,
             color=RGBColor(226, 232, 240), font=MONO)
    add_text(slide, 0.7, 6.35, 11.9, 0.3,
             "Feedback — SQLite-volume · rollback = предыдущий artifact + перезапуск.",
             size=10, color=MUTED)
    add_footer(slide, 12)


def slide_monitoring(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "12 · Мониторинг", "Три уровня метрик",
               "Инфраструктура, продукт и модель — плюс 7 алертов и drift.")
    levels = [
        ("Инфраструктура", "RPS · 5xx · p95", "model_loaded", BLUE),
        ("Продукт", "темы · очереди", "manual review rate", MINT),
        ("Модель", "confidence", "drift PSI / KS", AMBER),
    ]
    for index, (title, line1, line2, color) in enumerate(levels):
        x = 0.65 + index * 3.95
        add_rect(slide, x, 1.65, 3.65, 1.75, fill=WHITE, line=LINE, radius=0.07)
        add_rect(slide, x, 1.65, 3.65, 0.07, fill=color, line=None, radius=0.0,
                 shape=MSO_SHAPE.RECTANGLE)
        add_text(slide, x + 0.25, 1.88, 3.1, 0.4, title, size=15.5, bold=True, color=INK)
        add_text(slide, x + 0.25, 2.38, 3.1, 0.35, line1, size=11.5, color=SLATE)
        add_text(slide, x + 0.25, 2.8, 3.1, 0.35, line2, size=11.5, color=SLATE)

    add_rect(slide, 0.65, 3.65, 12.1, 1.55, fill=PAPER, line=LINE, radius=0.06)
    add_text(slide, 0.9, 3.82, 2.0, 0.35, "7 алертов", size=14, bold=True, color=INK)
    alerts = [
        "API down", "model not ready", "5xx", "latency",
        "review rate", "other share", "confidence",
    ]
    for index, alert in enumerate(alerts):
        row, col = divmod(index, 4)
        x = 2.95 + col * 2.45
        y = 3.78 + row * 0.68
        add_chip(slide, x, y, 2.25, 0.4, alert, fill=WHITE, color=SLATE, size=9.5,
                 bold=False)
    add_text(slide, 0.9, 5.45, 11.8, 0.35,
             "PSI 0.003 · KS 0.020 · TriageApiDown проверен в firing", size=12, bold=True,
             color=MINT)
    add_text(slide, 0.9, 5.85, 11.8, 0.3,
             "Alert rules — monitoring/alerts.yml · Grafana dashboard — Music Support Triage",
             size=10, color=MUTED)
    add_footer(slide, 13)


def slide_ai(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "13 · Как мы работали", "Агент — рутина, решения — команда",
               "Ассистент ускорял механическую работу, но не заменял инженерные решения.")
    add_rect(slide, 0.65, 1.65, 5.8, 2.6, fill=BLUE_LIGHT, line=None, radius=0.06)
    add_text(slide, 0.95, 1.85, 5.2, 0.35, "АГЕНТ ДЕЛАЛ", size=10, bold=True, color=BLUE)
    add_paragraphs(
        slide,
        0.95,
        2.3,
        5.2,
        2.8,
        [
            "шаблонный код и CLI-обёртки",
            "склейку шагов pipeline в один запуск",
            "черновики автотестов",
            "прогон проверок и поиск багов",
        ],
        size=13.5,
        color=SLATE,
        gap=8,
    )
    add_rect(slide, 6.85, 1.65, 5.85, 2.6, fill=MINT_LIGHT, line=None, radius=0.06)
    add_text(slide, 7.15, 1.85, 5.2, 0.35, "КОМАНДА ДЕЛАЛА", size=10, bold=True, color=MINT)
    add_paragraphs(
        slide,
        7.15,
        2.3,
        5.2,
        2.8,
        [
            "задачу, таксономию и данные",
            "архитектуру и контракт",
            "выбор модели и порога",
            "выводы, этику и защиту",
        ],
        size=13.5,
        color=SLATE,
        gap=8,
    )
    add_rect(slide, 0.65, 4.55, 12.05, 0.85, fill=INK, line=None, radius=0.08)
    add_text(slide, 0.9, 4.75, 11.5, 0.45,
             "PII маскируется · LLM не в инференсе · ответственность на команде",
             size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, 0.65, 5.95, 11.9, 0.3,
             "Каждый сгенерированный фрагмент: review → запуск → тесты → сверка с артефактами.",
             size=10.5, color=MUTED)
    add_footer(slide, 14)


def slide_final(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header(slide, "14 · Честный итог", "Ограничения и следующий шаг",
               "Прототип показывает путь, но не выдаёт себя за production.")
    limits = [
        ("Weak-метки", "test не human-verified", AMBER),
        ("Смешанный test", "overall 0.855 vs TWCS 0.739", CORAL),
        ("Редкие классы", "content 0.40 · app 0.69", BLUE),
    ]
    for index, (title, text, color) in enumerate(limits):
        y = 1.65 + index * 1.45
        add_rect(slide, 0.65, y, 6.3, 1.2, fill=WHITE, line=LINE, radius=0.07)
        add_rect(slide, 0.65, y, 0.08, 1.2, fill=color, line=None, radius=0.0,
                 shape=MSO_SHAPE.RECTANGLE)
        add_text(slide, 0.95, y + 0.18, 5.7, 0.35, title, size=14.5, bold=True, color=INK)
        add_text(slide, 0.95, y + 0.62, 5.7, 0.35, text, size=11, color=MUTED)

    add_rect(slide, 7.35, 1.65, 5.35, 4.35, fill=PAPER, line=LINE, radius=0.06)
    add_text(slide, 7.65, 1.85, 4.7, 0.35, "СЛЕДУЮЩИЙ ШАГ", size=10, bold=True, color=BLUE)
    steps = [
        ("1", "Human-verified подвыборка"),
        ("2", "Переобучение по дрейфу"),
        ("3", "Canary + мониторинг"),
    ]
    for index, (number, text) in enumerate(steps):
        y = 2.35 + index * 1.05
        add_rect(slide, 7.65, y, 0.45, 0.45, fill=BLUE, line=None, radius=0.5)
        add_text(slide, 7.65, y + 0.06, 0.45, 0.32, number, size=13, bold=True, color=WHITE,
                 align=PP_ALIGN.CENTER)
        add_text(slide, 8.3, y + 0.05, 4.0, 0.4, text, size=13.5, bold=True, color=INK)
    add_text(slide, 7.65, 5.45, 4.7, 0.3, "BPMN-схема переобучения — в документации.",
             size=9.5, color=MUTED)

    add_text(slide, 0.65, 6.05, 1.2, 0.3, "Команда", size=10.5, bold=True, color=INK)
    add_text(
        slide,
        1.7,
        6.05,
        11.0,
        0.55,
        "Задача — все · Архитектура — Максим · Эксперименты — Владимир · "
        "Тесты — Айдар · Деплой — Евгений · Мониторинг — Александр",
        size=10.5,
        color=SLATE,
    )
    add_text(slide, 0.65, 6.62, 11.0, 0.35, "Спасибо! Готовы к вопросам.",
             size=13, bold=True, color=BLUE)
    add_footer(slide, 15)


SPEECH: list[tuple[str, str]] = [
    (
        "Титул",
        "Добрый день. Мы — команда Music Support Triage. Наш кейс — классификация обращений "
        "в поддержку музыкального сервиса: по тексту определить тему и направить тикет в нужную "
        "очередь. Покажем путь от задачи до мониторинга и честно обозначим границы решения.",
    ),
    (
        "Проблема",
        "Сегодня первую линию сортирует человек. Это медленно и дорого: ошибка маршрута отправляет "
        "тикет не тому специалисту, а пользователь дольше ждёт ответа. Наша цель — не заменить "
        "оператора, а дать ему быстрый и безопасный черновик маршрута.",
    ),
    (
        "Задача",
        "На входе — текст обращения и опциональные метаданные. Модель возвращает тему, уверенность, "
        "top-3 и очередь. Если уверенность ниже 0.70 или отрыв от второго класса меньше 0.05, тикет "
        "уходит в manual_review. Семь тем покрывают основные сценарии поддержки.",
    ),
    (
        "Данные",
        "Мы используем два реальных источника: TWCS SpotifyCares и Bitext Customer Support, всего "
        "13 427 обращений. Synthetic исключён. Делим 80 на 20 со стратификацией по источнику и классу, "
        "группы держим по conversation_id. Test замораживаем и открываем один раз.",
    ),
    (
        "Архитектура",
        "Архитектура — модульный монолит на FastAPI. Для одного потребителя и небольшой нагрузки "
        "микросервисы были бы overengineering. Внутри — preprocessing, модель и routing; низкая "
        "уверенность уходит в manual_review. Такую схему просто запускать и сопровождать.",
    ),
    (
        "Техническая схема",
        "На технической схеме три узких места. Модель: readiness, checksum и rollback. Очередь: retry "
        "и manual fallback. Данные: мониторинг drift и переобучение. Эти же места закрыты метриками "
        "и алертами.",
    ),
    (
        "API",
        "Контракт — шесть endpoint'ов: classify, batch, feedback, healthcheck, model-info и metrics. "
        "Ответ содержит тему, очередь, confidence, margin, top-3 и версию модели. Ошибки — единый "
        "конверт с X-Request-ID, SLA — p95 до 500 миллисекунд.",
    ),
    (
        "Эксперименты",
        "Эксперименты: четыре семейства моделей, 120 кандидатов на семейство, HalvingRandomSearchCV "
        "и 5-fold StratifiedGroupKFold. Лучший CV macro-F1 — 0.855 у LogReg на word TF-IDF. Word+char "
        "дал 0.848, SVC и ComplementNB заметно слабее. Test в выборе не участвовал.",
    ),
    (
        "Результат на test",
        "На test macro-F1 0.855, accuracy 0.963, selective precision 0.979 при coverage 0.948. "
        "Bootstrap 95% интервал — от 0.791 до 0.908. Но overall смешивает источники: на реальном "
        "TWCS macro-F1 0.739. Это важная граница, а не красивый результат.",
    ),
    (
        "Ошибки",
        "По классам видно, где больно: content 0.40, app 0.69. Найденный баг — отрицание: "
        "«I don't want to cancel my subscription, I need a receipt» модель отнесла к subscription "
        "с уверенностью 0.647 и отправила в manual_review. Классификация ошибочна, но routing "
        "сработал безопасно.",
    ),
    (
        "Тестирование",
        "Тестирование: 38 тестов — unit, data, model и integration. Great Expectations 8 из 8; "
        "на испорченной копии ловит 4 нарушения. Smoke 5 из 5, load test 20 запросов в секунду без "
        "ошибок, p95 52.72 миллисекунды в Docker. CI на GitHub Actions проверяет ruff, mypy и pytest.",
    ),
    (
        "Деплой",
        "Деплой — Docker и Compose: api, Prometheus и Grafana. Multi-stage образ 716 мегабайт, "
        "non-root, healthcheck. Feedback хранится в SQLite-volume и переживает перезапуск. Rollback — "
        "предыдущий artifact и перезапуск.",
    ),
    (
        "Мониторинг",
        "Мониторинг трёхуровневый: инфраструктура, продукт и модель. Семь алертов: API down, model not "
        "ready, 5xx, latency, manual review rate, other share и низкая confidence. Drift: PSI 0.003, "
        "KS 0.020. Алерт API down проверен в firing.",
    ),
    (
        "ИИ-ассистенты",
        "ИИ-ассистент у нас выполнял рутину: шаблонный код, склейку шагов pipeline, черновики тестов, "
        "прогон проверок и поиск багов. Задачу, данные, архитектуру, выбор модели, выводы и защиту "
        "делала команда. Каждый фрагмент проверялся запуском и тестами.",
    ),
    (
        "Ограничения и следующий шаг",
        "Ограничения честные: weak-метки, смешанный test и редкие классы. Следующий шаг — "
        "human-verified подвыборка, переобучение по дрейфу и canary-раскатка. Спасибо, готовы к вопросам.",
    ),
]


def write_speech() -> None:
    """Write a readable speech document with per-slide timing."""
    lines = [
        "# Речь к защите",
        "",
        "**Формат:** 15 слайдов, 5 минут выступления + 2 минуты вопросов.  ",
        "**Файл:** [`presentation.pdf`](presentation.pdf) · [`presentation.pptx`](presentation.pptx).",
        "",
        "Текст ниже встроен в заметки докладчика PPTX. Ориентир по времени — 20–30 секунд на слайд.",
        "",
    ]
    for index, (title, text) in enumerate(SPEECH, start=1):
        lines.append(f"## Слайд {index}. {title}")
        lines.append("")
        lines.append("*~25–30 секунд*")
        lines.append("")
        lines.append(text)
        lines.append("")
    lines.extend(
        [
            "## Возможные вопросы",
            "",
            "**Почему не LLM?** Узкая классификация в 7 классов: TF-IDF + LogReg быстрее,",
            "дешевле и интерпретируемее. LLM не даёт гарантированного контракта и сложнее",
            "контролируется; его можно добавить для объяснений, но не для маршрутизации.",
            "",
            "**Почему macro-F1, а не accuracy?** Классы несбалансированы, а редкие темы важны.",
            "Accuracy 0.963 маскирует content 0.40; macro-F1 показывает худший класс.",
            "",
            "**Почему weak-метки?** У TWCS нет официальных тем. Мы честно измеряем согласие",
            "с weak-метками, а human-verified подвыборка — следующий шаг.",
            "",
            "**Что изменится в production?** PostgreSQL вместо SQLite, model registry, canary,",
            "реальные логи, human feedback loop и переобучение по дрейфу.",
            "",
        ]
    )
    SPEECH_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPEECH_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    builders = [
        slide_title,
        slide_problem,
        slide_task,
        slide_data,
        slide_architecture,
        slide_technical,
        slide_api,
        slide_experiments,
        slide_test,
        slide_errors,
        slide_testing,
        slide_deploy,
        slide_monitoring,
        slide_ai,
        slide_final,
    ]
    for builder in builders:
        builder(prs)

    for slide, (_, text) in zip(prs.slides, SPEECH, strict=True):
        add_notes(slide, text)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    write_speech()
    print(f"saved {OUT}")
    print(f"saved {SPEECH_PATH}")


if __name__ == "__main__":
    main()
