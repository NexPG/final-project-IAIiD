"""Build charts used by the defence deck."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "07_report"

INK = "#0F172A"
MUTED = "#64748B"
BLUE = "#2563EB"
SKY = "#93C5FD"
LIGHT = "#EFF6FF"
MINT = "#10B981"
AMBER = "#D97706"
CORAL = "#DC2626"
LINE = "#E2E8F0"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.edgecolor": LINE,
        "axes.labelcolor": MUTED,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "text.color": INK,
    }
)


def data_donut() -> None:
    """Source composition donut."""
    fig, ax = plt.subplots(figsize=(6.4, 5.0), dpi=220)
    values = [5732, 7695]
    labels = ["TWCS SpotifyCares", "Bitext Support"]
    colors = [BLUE, SKY]
    ax.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.34, "edgecolor": "white", "linewidth": 3},
    )
    ax.add_patch(Circle((0, 0), 0.62, color="white", zorder=2))
    ax.text(0, 0.1, "13 427", ha="center", va="center", fontsize=34, fontweight="bold", color=INK)
    ax.text(0, -0.18, "обращений", ha="center", va="center", fontsize=14, color=MUTED)
    total = sum(values)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=color)
        for color in colors
    ]
    legend_labels = [
        f"{label} — {value:,} ({value / total * 100:.0f}%)".replace(",", " ")
        for label, value in zip(labels, values, strict=True)
    ]
    fig.legend(
        handles,
        legend_labels,
        loc="lower center",
        ncol=1,
        frameon=False,
        fontsize=12.5,
        handlelength=1.1,
        handleheight=0.9,
        labelspacing=0.5,
        bbox_to_anchor=(0.5, 0.0),
    )
    ax.set_aspect("equal")
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    fig.subplots_adjust(bottom=0.24, top=0.98, left=0.08, right=0.92)
    fig.savefig(OUT / "fig_data.png", transparent=True, bbox_inches="tight")
    plt.close(fig)


def model_scores() -> None:
    """CV macro-F1 by model family."""
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=220)
    models = ["ComplementNB", "Calibrated SVC", "LogReg word+char", "LogReg word"]
    scores = [0.701, 0.775, 0.848, 0.855]
    colors = ["#CBD5E1", "#CBD5E1", SKY, BLUE]
    bars = ax.barh(models, scores, color=colors, height=0.56, zorder=3)
    for bar, score in zip(bars, scores, strict=True):
        ax.text(
            score + 0.008,
            bar.get_y() + bar.get_height() / 2,
            f"{score:.3f}",
            va="center",
            fontsize=13,
            fontweight="bold" if score == max(scores) else "normal",
            color=INK,
        )
    ax.set_xlim(0.6, 0.9)
    ax.set_xlabel("CV macro-F1", fontsize=12, labelpad=10)
    ax.grid(axis="x", color=LINE, linewidth=0.9, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=12.5)
    ax.tick_params(axis="x", labelsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "fig_models.png", transparent=True, bbox_inches="tight")
    plt.close(fig)


def per_class_recall() -> None:
    """Per-class recall with risk colouring."""
    classes = [
        "content",
        "app",
        "subscription",
        "account",
        "payment",
        "recommendations",
        "other",
    ]
    recalls = [0.40, 0.69, 0.92, 0.96, 0.97, 0.98, 0.98]
    colors = [CORAL, AMBER, BLUE, BLUE, BLUE, BLUE, BLUE]
    fig, ax = plt.subplots(figsize=(6.8, 4.8), dpi=220)
    bars = ax.barh(classes, recalls, color=colors, height=0.58, zorder=3)
    for bar, value in zip(bars, recalls, strict=True):
        ax.text(
            value + 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.2f}",
            va="center",
            fontsize=12.5,
            color=INK,
            fontweight="bold" if value < 0.7 else "normal",
        )
    ax.set_xlim(0, 1.08)
    ax.set_xlabel("Recall", fontsize=12, labelpad=10)
    ax.grid(axis="x", color=LINE, linewidth=0.9, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=12.5)
    ax.tick_params(axis="x", labelsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "fig_recall.png", transparent=True, bbox_inches="tight")
    plt.close(fig)


def business_architecture() -> None:
    """Clean, high-resolution business-level architecture scheme."""
    fig, ax = plt.subplots(figsize=(14, 10), dpi=200)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    def box(
        x,
        y,
        w,
        h,
        title,
        sub="",
        fill="white",
        edge=BLUE,
        title_color=INK,
        sub_color=MUTED,
        size=11.5,
        sub_size=8.5,
    ):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor=fill,
                edgecolor=edge,
                linewidth=1.4,
                zorder=2,
            )
        )
        ax.text(x + w / 2, y + h / 2 + (0.1 if sub else 0), title, ha="center", va="center",
                fontsize=size, fontweight="bold", color=title_color, zorder=3)
        if sub:
            ax.text(x + w / 2, y + h / 2 - 0.2, sub, ha="center", va="center", fontsize=sub_size,
                    color=sub_color, zorder=3)

    ax.text(0.4, 9.65, "Music Support Triage — бизнес-архитектура", fontsize=20,
            fontweight="bold", color=INK, va="top")
    ax.text(0.4, 9.25, "Пользователь → приложение → сервис → очередь", fontsize=11,
            color=MUTED, va="top")

    box(0.9, 7.5, 2.4, 1.0, "Пользователь")
    box(5.1, 7.5, 4.3, 1.0, "Мобильное / Web\nприложение", "канал обращения")
    ax.annotate("", xy=(5.0, 8.0), xytext=(3.4, 8.0),
                arrowprops={"arrowstyle": "<|-|>", "color": INK, "lw": 1.3})
    ax.text(4.2, 8.12, "запрос / ответ", ha="center", fontsize=8, color=MUTED)

    ax.annotate("", xy=(7.25, 6.55), xytext=(7.25, 7.45),
                arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 1.3})
    box(5.1, 5.35, 4.3, 1.05, "API Gateway / Backend",
        "аутентификация · лимиты · routing")

    ax.annotate("", xy=(7.25, 4.9), xytext=(7.25, 5.3),
                arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 1.3})
    ax.add_patch(
        FancyBboxPatch(
            (1.3, 2.5),
            11.4,
            2.4,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor=LIGHT,
            edgecolor=BLUE,
            linewidth=1.2,
            zorder=1,
        )
    )
    ax.text(1.55, 4.6, "Сервис классификации", fontsize=12, fontweight="bold", color=INK)
    box(1.7, 3.0, 3.2, 1.2, "Preprocessing", "язык · очистка · PII")
    box(5.4, 3.0, 3.2, 1.2, "Модель", "TF-IDF + LogReg · 7 классов",
        fill=BLUE, edge=BLUE, title_color="white", sub_color="white")
    box(9.1, 3.0, 3.2, 1.2, "Routing", "confidence · margin · очередь")
    for x1, x2 in ((4.9, 5.4), (8.6, 9.1)):
        ax.annotate("", xy=(x2, 3.6), xytext=(x1, 3.6),
                    arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 1.2})

    queue_y = 0.85
    queue_w = 1.7
    queue_x = [0.55 + i * 1.92 for i in range(7)]
    names = ["payment", "subscription", "account", "app", "recommendations", "content", "other"]
    ax.plot([7.0, 7.0], [2.5, 2.05], color=INK, lw=1.2)
    ax.plot([queue_x[0] + queue_w / 2, queue_x[-1] + queue_w / 2], [2.05, 2.05], color=INK, lw=1.2)
    for name, x in zip(names, queue_x, strict=True):
        center = x + queue_w / 2
        ax.annotate("", xy=(center, queue_y + 0.78), xytext=(center, 2.05),
                    arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 1.1})
        box(x, queue_y, queue_w, 0.78, name, fill="white", edge=SKY, title_color=INK, size=8.2)

    ax.text(0.55, 0.25, "7 классов → 7 очередей · низкая уверенность → manual_review",
            fontsize=10, color=MUTED)
    fig.tight_layout()
    fig.savefig(ROOT / "docs" / "02_architecture" / "architecture_business.png",
                bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data_donut()
    model_scores()
    per_class_recall()
    business_architecture()
    print("saved fig_data.png, fig_models.png, fig_recall.png, architecture_business.png")



if __name__ == "__main__":
    main()
