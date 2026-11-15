"""Render BPMN-style diagrams for the model lifecycle and retraining.

The diagrams use BPMN notation: circle events, rounded-rectangle tasks,
diamond gateways and directed sequence flows. Outputs are PNG files used in
the model card and monitoring documentation.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Polygon

ROOT = Path(__file__).resolve().parents[2]
OUT_MODEL = ROOT / "docs" / "03_experiments" / "model_bpmn.png"
OUT_RETRAIN = ROOT / "docs" / "06_monitoring" / "retrain_bpmn.png"

INK = "#0F172A"
BLUE = "#2563EB"
LIGHT = "#EFF6FF"
MUTED = "#64748B"
AMBER = "#D97706"
AMBER_FILL = "#FFF7E6"
GREEN = "#047857"
PAPER = "#F8FAFC"
WHITE = "#FFFFFF"

plt.rcParams["font.family"] = "DejaVu Sans"


def canvas(title: str, subtitle: str) -> tuple[plt.Figure, plt.Axes]:
    """Create a wide, high-resolution canvas with a title."""
    fig, ax = plt.subplots(figsize=(16.6, 10.2), dpi=180)
    ax.set_xlim(0, 16.6)
    ax.set_ylim(-0.45, 10.2)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)
    ax.text(0.35, 9.82, title, fontsize=21, fontweight="bold", color=INK, va="top")
    ax.text(0.35, 9.46, subtitle, fontsize=11.5, color=MUTED, va="top")
    return fig, ax


def band(ax: plt.Axes, y: float, label: str) -> None:
    """Draw a faint horizontal band with a phase label."""
    ax.add_patch(
        FancyBboxPatch(
            (0.35, y - 0.78),
            15.95,
            1.56,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor=PAPER,
            edgecolor="none",
            zorder=0,
        )
    )
    ax.text(0.45, y + 0.62, label, fontsize=9, fontweight="bold", color=MUTED, va="bottom")


def task(ax: plt.Axes, x: float, y: float, text: str, width: float = 2.2) -> None:
    """Draw a BPMN task."""
    ax.add_patch(
        FancyBboxPatch(
            (x - width / 2, y - 0.42),
            width,
            0.84,
            boxstyle="round,pad=0.02,rounding_size=0.14",
            facecolor=WHITE,
            edgecolor=BLUE,
            linewidth=1.6,
            zorder=3,
        )
    )
    ax.text(x, y, text, ha="center", va="center", fontsize=10.5, color=INK, zorder=4)


def gateway(
    ax: plt.Axes, x: float, y: float, text: str, half_width: float = 0.85
) -> None:
    """Draw an exclusive BPMN gateway."""
    ax.add_patch(
        Polygon(
            [(x, y + 0.62), (x + half_width, y), (x, y - 0.62), (x - half_width, y)],
            closed=True,
            facecolor=AMBER_FILL,
            edgecolor=AMBER,
            linewidth=1.8,
            zorder=3,
        )
    )
    ax.text(x, y, text, ha="center", va="center", fontsize=8.2, color=INK, zorder=4)


def event(ax: plt.Axes, x: float, y: float, end: bool = False, label: bool = True) -> None:
    """Draw a start or end event."""
    ax.add_patch(
        Circle(
            (x, y),
            0.25,
            facecolor=WHITE,
            edgecolor=INK if end else GREEN,
            linewidth=5.0 if end else 2.0,
            zorder=3,
        )
    )
    if label:
        ax.text(x, y - 0.43, "End" if end else "Start", ha="center", fontsize=8.5, color=MUTED)


def flow(ax: plt.Axes, points: list[tuple[float, float]], label: str | None = None) -> None:
    """Draw an orthogonal sequence flow with an arrow head and optional label."""
    for start, stop in zip(points[:-2], points[1:-1], strict=False):
        ax.plot([start[0], stop[0]], [start[1], stop[1]], color=INK, lw=1.4, zorder=2)
    ax.annotate(
        "",
        xy=points[-1],
        xytext=points[-2],
        arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 1.4, "mutation_scale": 13},
        zorder=2,
    )
    if label:
        lengths = [
            abs(b[0] - a[0]) + abs(b[1] - a[1])
            for a, b in zip(points[:-1], points[1:], strict=False)
        ]
        half = sum(lengths) / 2
        walked = 0.0
        for (a, b), length in zip(
            zip(points[:-1], points[1:], strict=False), lengths, strict=False
        ):
            if walked + length >= half:
                ratio = (half - walked) / length if length else 0.0
                mx = a[0] + (b[0] - a[0]) * ratio
                my = a[1] + (b[1] - a[1]) * ratio
                break
            walked += length
        ax.text(
            mx + 0.12,
            my + 0.1,
            label,
            fontsize=8.5,
            color=MUTED,
            bbox={"boxstyle": "round,pad=0.18", "facecolor": WHITE, "edgecolor": "none"},
            zorder=5,
        )


def legend(ax: plt.Axes) -> None:
    """Draw a compact BPMN legend."""
    y = 0.7
    event(ax, 0.75, y, label=False)
    ax.text(1.15, y, "событие", va="center", fontsize=9, color=MUTED)
    task(ax, 2.7, y, "", width=1.5)
    ax.text(3.6, y, "задача", va="center", fontsize=9, color=MUTED)
    gateway(ax, 5.3, y, "")
    ax.text(6.3, y, "развилка", va="center", fontsize=9, color=MUTED)
    ax.annotate(
        "",
        xy=(7.8, y),
        xytext=(7.35, y),
        arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 1.4},
    )
    ax.text(7.95, y, "поток", va="center", fontsize=9, color=MUTED)


def model_lifecycle() -> None:
    """Model lifecycle: data -> search -> test -> release -> monitoring."""
    fig, ax = canvas(
        "BPMN: жизненный цикл модели",
        "Music Support Triage · от данных до мониторинга, test открывается один раз",
    )
    band(ax, 7.0, "ПОДГОТОВКА И ОБУЧЕНИЕ")
    band(ax, 3.8, "РЕЛИЗ И ЭКСПЛУАТАЦИЯ")

    event(ax, 0.85, 7.0)
    task(ax, 2.65, 7.0, "Собрать TWCS\n+ Bitext")
    task(ax, 5.05, 7.0, "Очистка, PII,\ndedup")
    gateway(ax, 7.25, 7.0, "GE\n8/8?")
    task(ax, 9.45, 7.0, "80/20 split\n(source, label)")
    task(ax, 11.95, 7.0, "HalvingRandom\nSearchCV 120")
    gateway(ax, 14.45, 7.0, "CV ≥\n0.80?")

    task(ax, 14.45, 3.8, "Refit + OOF\nthreshold")
    task(ax, 11.95, 3.8, "Один замер\nна test")
    task(ax, 9.45, 3.8, "Artifact +\nmodel card")
    task(ax, 6.95, 3.8, "Docker /\nCompose")
    task(ax, 4.45, 3.8, "Prometheus /\nGrafana")
    event(ax, 2.15, 3.8, end=True)

    task(ax, 7.25, 8.85, "Исправить\nданные", width=1.9)
    task(ax, 14.45, 8.85, "Расширить\nпоиск", width=1.9)

    flow(ax, [(1.12, 7.0), (1.55, 7.0)])
    flow(ax, [(3.75, 7.0), (3.95, 7.0)])
    flow(ax, [(6.15, 7.0), (6.4, 7.0)])
    flow(ax, [(8.1, 7.0), (8.35, 7.0)])
    flow(ax, [(10.55, 7.0), (10.85, 7.0)])
    flow(ax, [(13.05, 7.0), (13.6, 7.0)])

    flow(ax, [(7.25, 7.62), (7.25, 8.43)], "нет")
    flow(ax, [(8.2, 8.85), (9.0, 8.85), (9.0, 7.9), (5.05, 7.9), (5.05, 7.42)])

    flow(ax, [(14.45, 7.62), (14.45, 8.43)], "нет")
    flow(ax, [(13.5, 8.85), (12.9, 8.85), (12.9, 7.9), (11.95, 7.9), (11.95, 7.42)])

    flow(ax, [(14.45, 6.38), (14.45, 4.22)], "да")
    flow(ax, [(13.35, 3.8), (13.05, 3.8)])
    flow(ax, [(10.85, 3.8), (10.55, 3.8)])
    flow(ax, [(8.35, 3.8), (8.05, 3.8)])
    flow(ax, [(5.85, 3.8), (5.55, 3.8)])
    flow(ax, [(3.35, 3.8), (2.4, 3.8)])

    ax.text(
        0.45,
        1.75,
        "Test не участвует в выборе: модель и порог фиксируются по CV/OOF,\n"
        "затем выполняется один замер и сохраняется версия артефакта.",
        fontsize=10.5,
        color=MUTED,
        linespacing=1.5,
    )
    legend(ax)
    fig.savefig(OUT_MODEL, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


def retraining() -> None:
    """Retraining: drift trigger -> feedback -> retrain -> canary -> promote."""
    fig, ax = canvas(
        "BPMN: переобучение по дрейфу",
        "Music Support Triage · событие → разбор → переобучение → canary → promotion",
    )
    band(ax, 7.0, "ТРИГГЕР И ПОДГОТОВКА")
    band(ax, 3.8, "ПРОВЕРКА И РЕЛИЗ")

    event(ax, 0.85, 7.0)
    task(ax, 2.7, 7.0, "Метрики и drift\nиз Prometheus")
    gateway(ax, 5.05, 7.0, "PSI > 0.2\nили F1\n−5 п.п.?", half_width=1.0)
    task(ax, 7.35, 7.0, "Разбор ошибок\n+ feedback")
    task(ax, 9.85, 7.0, "Новая разметка\nи проверка")
    task(ax, 12.35, 7.0, "Переобучение\nна новых данных")
    gateway(ax, 14.8, 7.0, "Валидация\nи тесты?", half_width=0.95)

    task(ax, 7.35, 8.85, "Продолжить\nмониторинг", width=1.9)
    event(ax, 9.7, 8.85, end=True)

    task(ax, 14.8, 3.8, "Shadow / canary\n5–10%")
    gateway(ax, 12.3, 3.8, "Метрики\nне хуже?", half_width=0.95)
    task(ax, 9.85, 3.8, "100% трафика")
    task(ax, 7.35, 3.8, "Обновить version\nи model card")
    event(ax, 4.85, 3.8, end=True)
    task(ax, 14.8, 1.6, "Rollback\nна текущую версию", width=2.2)
    event(ax, 12.3, 1.6, end=True)

    flow(ax, [(1.12, 7.0), (1.6, 7.0)])
    flow(ax, [(3.8, 7.0), (4.2, 7.0)])
    flow(ax, [(5.05, 7.62), (5.05, 8.85), (6.4, 8.85)], "нет")
    flow(ax, [(8.3, 8.85), (9.4, 8.85)])
    flow(ax, [(6.05, 7.0), (6.25, 7.0)], "да")
    flow(ax, [(8.45, 7.0), (8.75, 7.0)])
    flow(ax, [(10.95, 7.0), (11.25, 7.0)])
    flow(ax, [(13.45, 7.0), (13.85, 7.0)])

    flow(ax, [(14.8, 6.38), (14.8, 4.22)], "да")
    flow(ax, [(13.7, 3.8), (13.25, 3.8)])
    flow(ax, [(11.35, 3.8), (10.95, 3.8)], "да")
    flow(ax, [(8.75, 3.8), (8.45, 3.8)])
    flow(ax, [(6.25, 3.8), (5.1, 3.8)])

    flow(ax, [(15.75, 6.7), (16.05, 6.7), (16.05, 1.6), (15.9, 1.6)])
    flow(ax, [(12.3, 3.18), (12.3, 2.7), (14.8, 2.7), (14.8, 2.02)])
    flow(ax, [(13.7, 1.6), (12.55, 1.6)])

    ax.text(
        0.45,
        1.7,
        "Триггеры: PSI > 0.2 · KS p < 0.05 · macro-F1 −5 п.п. · manual review > 30% · median confidence < 0.60.\n"
        "Без human-verified feedback модель нельзя дообучать на собственных предсказаниях.",
        fontsize=10.2,
        color=MUTED,
        linespacing=1.5,
    )
    legend(ax)
    fig.savefig(OUT_RETRAIN, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


def main() -> None:
    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    OUT_RETRAIN.parent.mkdir(parents=True, exist_ok=True)
    model_lifecycle()
    retraining()
    print(f"saved {OUT_MODEL}")
    print(f"saved {OUT_RETRAIN}")


if __name__ == "__main__":
    main()
