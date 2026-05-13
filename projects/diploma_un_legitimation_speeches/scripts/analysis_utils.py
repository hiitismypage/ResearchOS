"""
Statistical analysis and figure generation for coded UNGDC data.
Produces frequency tables, co-occurrence matrices, temporal trend charts,
and a regional distribution chart — all intended for Chapter 4.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

from config import (
    FIGURE_DPI,
    FIGURE_STYLE,
    FIGURE_PALETTE,
    FIGURE_WIDTH,
    FIGURE_HEIGHT,
    PERIODS,
    VIOLATION_LABELS,
    STRATEGY_LABELS,
    REGIONAL_GROUPS,
)


def assign_period(year: int) -> str:
    for label, (start, end) in PERIODS.items():
        if start <= year <= end:
            return label
    return "Unknown"


def assign_region(iso3: str) -> str:
    for region, members in REGIONAL_GROUPS.items():
        if iso3 in members:
            return region
    return "Other"


def build_frequency_table(coded: pd.DataFrame) -> dict[str, pd.Series]:
    """
    Computes frequency counts for strategies and violations across all coded passages.
    Input: DataFrame with columns 'manual_strategy_code', 'manual_violation_code'.
    Returns dict with 'strategies' and 'violations' Series (sorted descending).
    """
    strats = (
        coded["manual_strategy_code"]
        .replace("", pd.NA)
        .dropna()
        .map(lambda x: STRATEGY_LABELS.get(x, x))
        .value_counts()
    )
    viols = (
        coded["manual_violation_code"]
        .replace("", pd.NA)
        .dropna()
        .map(lambda x: VIOLATION_LABELS.get(x, x))
        .value_counts()
    )
    return {"strategies": strats, "violations": viols}


def build_cooccurrence_matrix(coded: pd.DataFrame) -> pd.DataFrame:
    """
    Builds a strategy × violation co-occurrence matrix.
    Rows = strategies, columns = violation types; cell = count of passages coded with both.
    """
    df = coded[
        (coded["manual_strategy_code"] != "") & (coded["manual_violation_code"] != "")
    ].copy()

    df["strategy_label"] = df["manual_strategy_code"].map(STRATEGY_LABELS)
    df["violation_label"] = df["manual_violation_code"].map(VIOLATION_LABELS)

    matrix = pd.crosstab(df["strategy_label"], df["violation_label"])
    strategy_order = [v for v in STRATEGY_LABELS.values() if v in matrix.index]
    violation_order = [v for v in VIOLATION_LABELS.values() if v in matrix.columns]
    return matrix.reindex(index=strategy_order, columns=violation_order, fill_value=0)


def build_temporal_trends(coded: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    """
    Computes strategy distribution across the four analytical periods.
    Returns a DataFrame with periods as index and strategy labels as columns.
    """
    merged = coded.merge(
        cases[["country_iso3", "year", "period"]],
        on=["country_iso3", "year"],
        how="left",
    )

    merged = merged[merged["manual_strategy_code"] != ""]
    merged["strategy_label"] = merged["manual_strategy_code"].map(STRATEGY_LABELS)
    merged["period"] = merged["period"].fillna(merged["year"].apply(assign_period))

    pivot = merged.groupby(["period", "strategy_label"]).size().unstack(fill_value=0)
    period_order = list(PERIODS.keys())
    pivot = pivot.reindex([p for p in period_order if p in pivot.index])
    return pivot


def build_regional_distribution(coded: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    merged = coded.merge(cases[["country_iso3", "year"]], on=["country_iso3", "year"], how="left")
    merged = merged[merged["manual_strategy_code"] != ""]
    merged["region"] = merged["country_iso3"].apply(assign_region)
    merged["strategy_label"] = merged["manual_strategy_code"].map(STRATEGY_LABELS)
    pivot = merged.groupby(["region", "strategy_label"]).size().unstack(fill_value=0)
    return pivot


def _save_figure(fig: plt.Figure, path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path.name}")


def plot_strategy_frequencies(freqs: pd.Series, output_path: Path) -> None:
    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT * 0.8))

    colors = sns.color_palette(FIGURE_PALETTE, n_colors=len(freqs))
    freqs.sort_values().plot(kind="barh", ax=ax, color=colors[::-1], edgecolor="white")

    ax.set_xlabel("Number of coded passages", fontsize=12)
    ax.set_title("Distribution of Legitimation Strategies (all periods)", fontsize=13, pad=12)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.tick_params(axis="y", labelsize=10)

    for bar in ax.patches:
        width = bar.get_width()
        ax.text(width + 0.2, bar.get_y() + bar.get_height() / 2,
                str(int(width)), va="center", fontsize=9)

    fig.tight_layout()
    _save_figure(fig, output_path, "strategy frequencies")


def plot_violation_frequencies(freqs: pd.Series, output_path: Path) -> None:
    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH * 0.85, FIGURE_HEIGHT * 0.7))

    colors = sns.color_palette("Oranges_d", n_colors=len(freqs))
    freqs.sort_values().plot(kind="barh", ax=ax, color=colors[::-1], edgecolor="white")

    ax.set_xlabel("Number of coded passages", fontsize=12)
    ax.set_title("Distribution of Alleged Violation Types (all periods)", fontsize=13, pad=12)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.tick_params(axis="y", labelsize=10)

    for bar in ax.patches:
        width = bar.get_width()
        ax.text(width + 0.2, bar.get_y() + bar.get_height() / 2,
                str(int(width)), va="center", fontsize=9)

    fig.tight_layout()
    _save_figure(fig, output_path, "violation frequencies")


def plot_cooccurrence_heatmap(matrix: pd.DataFrame, output_path: Path) -> None:
    if matrix.empty:
        print("  Skipped co-occurrence heatmap: no data.")
        return

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))

    sns.heatmap(
        matrix,
        ax=ax,
        annot=True,
        fmt="d",
        cmap="Blues",
        linewidths=0.5,
        linecolor="#cccccc",
        cbar_kws={"label": "Co-occurrence count"},
    )

    ax.set_title("Strategy × Violation Type Co-occurrence", fontsize=13, pad=12)
    ax.set_xlabel("Alleged Violation Type", fontsize=11)
    ax.set_ylabel("Legitimation Strategy", fontsize=11)
    plt.xticks(rotation=30, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)

    fig.tight_layout()
    _save_figure(fig, output_path, "co-occurrence heatmap")


def plot_temporal_trends(trends: pd.DataFrame, output_path: Path) -> None:
    if trends.empty:
        print("  Skipped temporal trends: no data.")
        return

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))

    palette = sns.color_palette("tab10", n_colors=len(trends.columns))
    for i, col in enumerate(trends.columns):
        ax.plot(
            range(len(trends)),
            trends[col].values,
            marker="o",
            linewidth=2,
            label=col,
            color=palette[i],
        )

    ax.set_xticks(range(len(trends)))
    ax.set_xticklabels(trends.index, rotation=15, ha="right", fontsize=9)
    ax.set_ylabel("Coded passages (count)", fontsize=11)
    ax.set_title("Legitimation Strategies by Historical Period", fontsize=13, pad=12)
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1), fontsize=8, title="Strategy")
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    fig.tight_layout()
    _save_figure(fig, output_path, "temporal trends")


def plot_temporal_trends_stacked(trends: pd.DataFrame, output_path: Path) -> None:
    if trends.empty:
        return

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))

    trends_pct = trends.div(trends.sum(axis=1), axis=0) * 100
    palette = sns.color_palette("tab10", n_colors=len(trends_pct.columns))

    trends_pct.plot(kind="bar", stacked=True, ax=ax, color=palette, edgecolor="white", width=0.6)

    ax.set_ylabel("Share of coded passages (%)", fontsize=11)
    ax.set_title("Strategy Distribution by Period (percentage)", fontsize=13, pad=12)
    ax.set_xticklabels(trends_pct.index, rotation=15, ha="right", fontsize=9)
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1), fontsize=8, title="Strategy")
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.0f%%"))

    fig.tight_layout()
    _save_figure(fig, output_path, "stacked temporal trends")


def plot_regional_distribution(regional: pd.DataFrame, output_path: Path) -> None:
    if regional.empty:
        print("  Skipped regional distribution: no data.")
        return

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))

    palette = sns.color_palette("tab10", n_colors=len(regional.columns))
    regional.plot(kind="bar", ax=ax, color=palette, edgecolor="white", width=0.7)

    ax.set_xlabel("UN Regional Group", fontsize=11)
    ax.set_ylabel("Coded passages (count)", fontsize=11)
    ax.set_title("Legitimation Strategies by UN Regional Group", fontsize=13, pad=12)
    ax.set_xticklabels(regional.index, rotation=20, ha="right", fontsize=9)
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1), fontsize=8, title="Strategy")
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    fig.tight_layout()
    _save_figure(fig, output_path, "regional distribution")


def export_tables(
    freqs: dict,
    matrix: pd.DataFrame,
    trends: pd.DataFrame,
    tables_dir: Path,
) -> None:
    tables_dir.mkdir(parents=True, exist_ok=True)

    freqs["strategies"].to_frame("count").to_csv(tables_dir / "frequency_strategies.csv")
    freqs["violations"].to_frame("count").to_csv(tables_dir / "frequency_violations.csv")
    matrix.to_csv(tables_dir / "cooccurrence_matrix.csv")
    trends.to_csv(tables_dir / "temporal_trends.csv")

    print(f"  Tables saved to {tables_dir}/")
