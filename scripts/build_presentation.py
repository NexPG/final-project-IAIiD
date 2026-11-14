"""Generate the 15-slide defence deck from the project results."""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "07_report" / "presentation.pptx"
NAVY = RGBColor(16, 42, 82)
BLUE = RGBColor(47, 111, 237)
GREY = RGBColor(90, 100, 115)
LIGHT = RGBColor(238, 243, 252)


def add_title(slide, text: str, subtitle: str | None = None) -> None:
    title = slide.shapes.add_textbox(Inches(0.7), Inches(0.45), Inches(12.0), Inches(0.8))
    frame = title.text_frame
    frame.text = text
    frame.paragraphs[0].font.size = Pt(30)
    frame.paragraphs[0].font.bold = True
    frame.paragraphs[0].font.color.rgb = NAVY
    if subtitle:
        sub = slide.shapes.add_textbox(Inches(0.7), Inches(1.18), Inches(12.0), Inches(0.4))
        p = sub.text_frame.paragraphs[0]
        p.text = subtitle
        p.font.size = Pt(15)
        p.font.color.rgb = GREY


def add_bullets(slide, items: list[str], left=0.8, top=1.7, width=11.8, height=5.4, size=20) -> None:
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    for index, item in enumerate(items):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.text = item
        p.level = 0
        p.font.size = Pt(size)
        p.font.color.rgb = RGBColor(35, 45, 60)
        p.space_after = Pt(9)


def add_table(slide, rows: list[list[str]], left=0.8, top=1.8, width=11.8, height=4.6, font_size=14) -> None:
    shape = slide.shapes.add_table(len(rows), len(rows[0]), Inches(left), Inches(top), Inches(width), Inches(height))
    table = shape.table
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = value
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(font_size)
                paragraph.font.color.rgb = RGBColor(30, 40, 55)
                if r == 0:
                    paragraph.font.bold = True
                    paragraph.font.color.rgb = RGBColor(255, 255, 255)
            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = NAVY
            elif r % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = LIGHT


def add_image(slide, path: Path, left: float, top: float, width: float) -> None:
    if path.exists():
        slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(width))


def add_footer(slide, number: int) -> None:
    box = slide.shapes.add_textbox(Inches(11.7), Inches(7.1), Inches(1.0), Inches(0.3))
    p = box.text_frame.paragraphs[0]
    p.text = str(number)
    p.alignment = PP_ALIGN.RIGHT
    p.font.size = Pt(10)
    p.font.color.rgb = GREY


def main() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # 1. Title
    slide = prs.slides.add_slide(blank)
    bg = slide.shapes.add_shape(1, Inches(0), Inches(0), prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()
    title = slide.shapes.add_textbox(Inches(0.9), Inches(2.2), Inches(11.5), Inches(1.0))
    p = title.text_frame.paragraphs[0]
    p.text = "Music Support Triage"
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    sub = slide.shapes.add_textbox(Inches(0.9), Inches(3.25), Inches(11.5), Inches(1.2))
    p = sub.text_frame.paragraphs[0]
    p.text = "Классификация обращений в поддержку музыкального сервиса"
    p.font.size = Pt(24)
    p.font.color.rgb = RGBColor(210, 225, 250)
    team = slide.shapes.add_textbox(Inches(0.9), Inches(5.2), Inches(11.5), Inches(0.8))
    p = team.text_frame.paragraphs[0]
    p.text = "Максим Федулаев · Владимир Егоров · Айдар Мугизов · Евгений Кононов · Александр Аксенов"
    p.font.size = Pt(15)
    p.font.color.rgb = RGBColor(190, 210, 240)

    # 2. Problem
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Проблема и бизнес-задача", "Ручная сортировка тикетов = задержка и ошибки маршрутизации")
    add_bullets(slide, [
        "Пользователь пишет в поддержку через приложение, сайт, email, чат или Twitter.",
        "Первая линия вручную определяет тему и очередь.",
        "Ошибка маршрута → тикет ждёт не того специалиста, растёт время ответа.",
        "Нужен сервис: тема + очередь + top-3 + безопасный fallback в manual review.",
        "Учебный прототип, не production-продукт: важны архитектура, эксперименты, тесты, деплой и мониторинг.",
    ])

    # 3. Task
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Задача, вход и выход", "7 классов, single-label, 7 очередей + manual_review")
    add_bullets(slide, [
        "Вход: текст обращения; опционально subject, channel, locale.",
        "Выход: topic, confidence, margin, top-3, queue, needs_human_review, model_version.",
        "Метрики: CV macro-F1, test macro-F1 + 95% CI, per-class recall, coverage, selective precision.",
        "Порог: confidence ≥ 0.85 и margin ≥ 0.05, иначе manual_review.",
        "Классы: payment, subscription, account, app, recommendations, content, other.",
    ], width=7.2)
    add_table(slide, [
        ["Класс", "Очередь"],
        ["payment", "billing"],
        ["subscription", "subscriptions"],
        ["account", "account_support"],
        ["app", "technical_support"],
        ["recommendations", "recommendations"],
        ["content", "content_support"],
        ["other", "general_support"],
    ], left=8.2, top=1.8, width=4.3, height=4.4, font_size=13)

    # 4. Data
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Данные и split", "80/20, стратификация по (source, label), группы conversation_id")
    add_table(slide, [
        ["Источник", "Всего", "Train", "Test"],
        ["TWCS SpotifyCares", "5 732", "4 558", "1 174"],
        ["Bitext Customer Support", "7 695", "6 155", "1 540"],
        ["Всего", "13 427", "10 713", "2 714"],
    ], top=1.8, height=1.8, font_size=16)
    add_bullets(slide, [
        "Synthetic исключён: реальных данных достаточно.",
        "Test frozen: открывается один раз после выбора модели и порога.",
        "Validation не нужен: 5-fold CV на train.",
        "Test-метки weak: это ограничение, а не «золотая» разметка.",
        "На реальном TWCS macro-F1 = 0.739, overall = 0.855.",
    ], top=4.1, size=19)

    # 5. Business architecture
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Архитектура: общая схема", "Пользователь → сервис → 7 классов")
    add_image(slide, ROOT / "docs" / "02_architecture" / "architecture_overview.png", 0.5, 1.5, 7.2)
    add_bullets(slide, [
        "Модульный монолит FastAPI.",
        "Online-инференс, embedded model.",
        "Preprocessing → модель → routing.",
        "Низкая уверенность → manual_review.",
        "Техническая схема — на следующем слайде.",
    ], left=8.2, top=1.9, width=4.4, size=17)

    # 6. Technical architecture
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Техническая архитектура", "PII, routing, Prometheus и ML-lifecycle")
    add_image(slide, ROOT / "docs" / "02_architecture" / "architecture.png", 0.35, 1.45, 12.6)
    add_bullets(slide, [
        "Три узких места: модель, очередь, drift.",
        "Model artifact read-only, checksum и rollback.",
        "Prometheus/Grafana и structured logs.",
    ], top=6.35, size=14)

    # 7. API
    slide = prs.slides.add_slide(blank)
    add_title(slide, "API и routing", "Контракт, ошибки, SLA, OpenAPI")
    add_bullets(slide, [
        "POST /v1/classify — один запрос.",
        "POST /v1/classify/batch — до 100.",
        "POST /v1/feedback — feedback оператора.",
        "GET /healthcheck, /model-info, /metrics.",
        "Единый error envelope + X-Request-ID.",
        "OpenAPI: docs/02_architecture/openapi.json.",
        "p95 ≤ 500 мс; 5xx < 1%.",
    ], width=6.8, size=18)
    add_table(slide, [
        ["Поле ответа", "Пример"],
        ["topic / queue", "payment / billing"],
        ["confidence", "0.93"],
        ["needs_human_review", "false"],
        ["top_k", "3 класса"],
    ], left=7.8, top=1.9, width=4.8, height=3.2, font_size=13)

    # 8. Experiments
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Эксперименты: сравнение моделей", "5-fold CV, HalvingRandomSearchCV, test не используется")
    add_image(slide, ROOT / "docs" / "07_report" / "cv_models.png", 0.6, 1.6, 6.4)
    add_table(slide, [
        ["Модель", "CV macro-F1"],
        ["LogReg word", "0.855 ± 0.048"],
        ["LogReg word+char", "0.848 ± 0.038"],
        ["Calibrated SVC", "0.775 ± 0.012"],
        ["ComplementNB", "0.701 ± 0.006"],
    ], left=7.3, top=1.8, width=5.4, height=3.2, font_size=14)
    add_bullets(slide, [
        "120 кандидатов на семейство, factor=2, 3 раунда.",
        "Выбрана LogReg word: лучший mean CV и проще.",
    ], left=7.3, top=5.2, width=5.4, size=15)

    # 9. Test results
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Финальный test — один раз", "Macro-F1 0.855, 95% CI [0.791; 0.908]")
    add_table(slide, [
        ["Метрика", "Значение"],
        ["Accuracy", "0.963"],
        ["Macro-F1", "0.855"],
        ["Weighted-F1", "0.963"],
        ["Bootstrap 95% CI", "[0.791; 0.908]"],
        ["Coverage", "0.881"],
        ["Selective precision", "0.989"],
    ], top=1.8, height=3.8, font_size=16)
    add_bullets(slide, [
        "Bitext: accuracy 0.998, macro-F1 0.713.",
        "TWCS: accuracy 0.917, macro-F1 0.739.",
        "Overall смешивает источники — это указано в отчёте.",
    ], top=5.75, size=15)

    # 10. Testing
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Тестирование", "37 тестов, 8/8 GE, smoke, load test")
    add_bullets(slide, [
        "Unit: очистка, PII, маппинг, split, dedup, routing.",
        "Model: overall, per-class, robustness, edge, behavior, adversarial, subgroup.",
        "API: contract, batch, feedback, 422/503, OpenAPI, error envelope.",
        "Data: pandas + 8/8 Great Expectations, dirty copy rejected.",
        "Load: 20 RPS, 30 s, 600 requests, 0 errors, p95 9.74 ms.",
        "Найденная проблема: отрицание «I don't want to cancel…, I need a receipt» → subscription, manual.",
    ], size=17)

    # 11. Deployment
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Деплой", "Docker + Compose: api, Prometheus, Grafana")
    add_bullets(slide, [
        "Multi-stage Dockerfile, python:3.12-slim, non-root, healthcheck.",
        "Модель и конфиги монтируются read-only.",
        "Compose: api + Prometheus + Grafana.",
        "Smoke 5/5; Docker load test p95 52.72 ms.",
        "Rollback: предыдущий artifact + перезапуск.",
        "CI/CD на GitHub не используется: локальный quality gate.",
    ], width=6.8)
    add_table(slide, [
        ["Проверка", "Результат"],
        ["Image size", "716 MB"],
        ["Model version", "search-logreg_word-2026…"],
        ["Compose", "все healthy"],
    ], left=7.9, top=1.9, width=4.7, height=2.4, font_size=13)

    # 12. Monitoring
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Мониторинг", "3 уровня, Grafana, 7 алертов, drift")
    add_bullets(slide, [
        "Инфраструктура: RPS, 5xx, p95, model_loaded.",
        "Продукт: topics, queues, manual review rate.",
        "Модель: confidence median, confidence histogram.",
        "7 алертов: API down, model not ready, 5xx, latency, manual rate, other share, confidence.",
        "Grafana dashboard: http://localhost:3000.",
        "Drift: PSI 0.003, KS 0.020, p=0.346; alert TriageApiDown проверен в firing.",
    ], size=17)

    # 13. AI/ethics
    slide = prs.slides.add_slide(blank)
    add_title(slide, "ИИ-ассистенты, этика, ограничения", "Ассистент — черновик, ответственность — на команде")
    add_bullets(slide, [
        "Ассистенты: TZ, исследование данных, код, тесты, Docker, MLflow/GE, отчёт.",
        "Проверено: запуск, линтеры, тесты, метрики, ссылки; исправлены ошибки.",
        "Не делегировалось: таксономия, выводы, этика, защита.",
        "PII маскируется, сырые данные не коммитятся, LLM в инференсе не используется.",
        "Ограничения: weak labels, mixed-source test, редкие content/app, TWCS license.",
    ], size=17)

    # 14. Next steps
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Ограничения и следующий шаг", "Честный прототип, а не production")
    add_bullets(slide, [
        "Weak-метки: нужна human-verified подвыборка для gold-оценки.",
        "Редкие классы: content 5 test, app 54 test.",
        "Domain shift: production drift требует реальных логов.",
        "Следующий шаг: human feedback loop, калибровка, retraining по событию.",
        "Результат: воспроизводимый сквозной кейс с работающим сервисом и честными границами.",
    ], size=20)

    # 15. Roles / thanks
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Команда", "Роли по этапам")
    add_table(slide, [
        ["Участник", "Этап"],
        ["Максим Федулаев", "2. Архитектура"],
        ["Владимир Егоров", "3. Эксперименты"],
        ["Айдар Мугизов", "4. Тестирование"],
        ["Евгений Кононов", "5. Деплой"],
        ["Александр Аксенов", "6. Мониторинг"],
    ], top=1.9, height=3.2, font_size=16)
    add_bullets(slide, ["Этап 1 «Задача» — вся команда.", "Спасибо за внимание!"], top=5.5, size=20)

    for index, slide in enumerate(prs.slides, start=1):
        add_footer(slide, index)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
