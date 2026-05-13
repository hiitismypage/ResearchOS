"""
correspondence.py
-----------------
Correspondence analysis (CA) for the 33-case manual corpus.

CA is performed via SVD (no external CA library required).

Input tables (analysis_output/tables/):
  - communicative_roles.csv               (one row per coded segment)
  - frequency_strategies.csv              (manual strategy counts)

Output figures (analysis_output/figures/ca/):
  fig1 — CA biplot: communicative roles × Cold War blocs
  fig2 — CA biplot: communicative roles × historical periods
  fig3 — Scree plots for both analyses
  fig4 — CA biplot: manual strategies × blocs

Output tables (analysis_output/tables/):
  ca_roles_by_bloc_coords.csv
  ca_roles_by_period_coords.csv
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

warnings.filterwarnings("ignore", category=FutureWarning)
matplotlib.use("Agg")

# ─────────────────────────────────────────────────────────── paths ──────────
ROOT = Path(__file__).resolve().parents[2]
TABLES_IN   = ROOT / "analysis_output" / "tables"
TABLES_OUT  = ROOT / "analysis_output" / "tables"
FIGURES_OUT = ROOT / "analysis_output" / "figures" / "ca"
FIGURES_OUT.mkdir(parents=True, exist_ok=True)

FIGURE_DPI   = 150
FIGURE_STYLE = "seaborn-v0_8-whitegrid"

# ─────────────────────────────────────────────────── palette constants ───────
HABERMAS_TYPE_COLORS: dict[str, str] = {
    "communicative": "#1a9850",
    "normative":     "#2166ac",
    "dramaturgical": "#c2a5cf",
    "strategic":     "#d73027",
}
HABERMAS_TYPES = ["communicative", "normative", "dramaturgical", "strategic"]
ROLE_HABERMAS: dict[str, str] = {
    "justification":      "communicative",
    "dialogue_appeal":    "communicative",
    "legal_normative":    "normative",
    "sovereignty_norm":   "normative",
    "historical_context": "dramaturgical",
    "victim_narrative":   "dramaturgical",
    "denial":             "strategic",
    "counter_accusation": "strategic",
    "delegitimation":     "strategic",
}

BLOC_COLORS: dict[str, str] = {
    "Western bloc":        "#2166ac",
    "Soviet/Eastern bloc": "#d6604d",
    "Non-Aligned Movement":"#4dac26",
}
BLOC_MARKERS: dict[str, str] = {
    "Western bloc":        "s",
    "Soviet/Eastern bloc": "D",
    "Non-Aligned Movement":"^",
}

PERIOD_COLORS: dict[str, str] = {
    "Cold War (1946–1989)":                 "#4575b4",
    "Post–Cold War (1990–2001)":            "#74add1",
    "Post-9/11 Security Turn (2002–2013)":  "#f46d43",
    "Post-2014 Normative Fragmentation":    "#d73027",
}
PERIOD_ORDER = [
    "Cold War (1946–1989)",
    "Post–Cold War (1990–2001)",
    "Post-9/11 Security Turn (2002–2013)",
    "Post-2014 Normative Fragmentation",
]
PERIOD_SHORT: dict[str, str] = {
    "Cold War (1946–1989)":                "Cold War\n(1946–89)",
    "Post–Cold War (1990–2001)":           "Post–CW\n(1990–01)",
    "Post-9/11 Security Turn (2002–2013)": "Post-9/11\n(2002–13)",
    "Post-2014 Normative Fragmentation":   "Post-2014",
}


# ─────────────────────────────────────────────────── CA implementation ───────
class CorrespondenceAnalysis:
    """Simple correspondence analysis via generalised SVD."""

    def __init__(self, n_components: int = 2) -> None:
        self.n_components = n_components

    def fit(self, data: pd.DataFrame) -> "CorrespondenceAnalysis":
        N = data.values.astype(float)
        n = N.sum()
        P = N / n

        self.r_masses_ = P.sum(axis=1)           # row masses
        self.c_masses_ = P.sum(axis=0)            # column masses

        # Residuals from independence model
        r_mat = self.r_masses_[:, np.newaxis]
        c_mat = self.c_masses_[np.newaxis, :]
        S = (P - r_mat * c_mat) / np.sqrt(r_mat * c_mat)

        U, sigma, Vt = np.linalg.svd(S, full_matrices=False)
        k = min(self.n_components, len(sigma))

        self.singular_values_ = sigma
        self.inertia_         = (sigma ** 2)
        self.total_inertia_   = self.inertia_.sum()
        self.explained_inertia_ = self.inertia_ / self.total_inertia_

        # Standard coordinates
        Dr_inv_sqrt = np.diag(1.0 / np.sqrt(self.r_masses_))
        Dc_inv_sqrt = np.diag(1.0 / np.sqrt(self.c_masses_))

        # Principal coordinates
        self.row_coords_    = Dr_inv_sqrt @ U[:, :k] * sigma[:k]
        self.col_coords_    = Dc_inv_sqrt @ Vt[:k, :].T * sigma[:k]

        self.row_labels_    = list(data.index)
        self.col_labels_    = list(data.columns)
        return self

    def row_contrib(self) -> np.ndarray:
        """Contribution of each row to each axis (%)."""
        num = self.r_masses_[:, np.newaxis] * (self.row_coords_ ** 2)
        return num / self.inertia_[np.newaxis, :len(self.row_coords_[0])] * 100

    def col_contrib(self) -> np.ndarray:
        num = self.c_masses_[:, np.newaxis] * (self.col_coords_ ** 2)
        return num / self.inertia_[np.newaxis, :len(self.col_coords_[0])] * 100


# ─────────────────────────────────────────────────── helpers ─────────────────
def _arrow_text(ax, x, y, label, color, ha="left", va="bottom", size=9):
    ax.annotate(
        label, xy=(x, y), xytext=(x, y),
        fontsize=size, color=color, fontweight="bold",
        ha=ha, va=va,
    )


def _add_axis_lines(ax):
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.axvline(0, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)


def _expand_lim(ax, factor=0.18):
    for setter, getter in [(ax.set_xlim, ax.get_xlim), (ax.set_ylim, ax.get_ylim)]:
        lo, hi = getter()
        pad = (hi - lo) * factor
        setter(lo - pad, hi + pad)


# ─────────────────────────────────────────────────── load data ───────────────
def load_segments() -> pd.DataFrame:
    df = pd.read_csv(TABLES_IN / "communicative_roles.csv")
    period_cat = pd.CategoricalDtype(categories=PERIOD_ORDER, ordered=True)
    if "period" in df.columns:
        df["period"] = df["period"].astype(period_cat)
    return df


# ──────────────────────────────────────────── figure 1: roles × blocs ────────
def fig1_roles_by_bloc(segments: pd.DataFrame) -> CorrespondenceAnalysis:
    ROLES_ORDER = [
        "justification", "dialogue_appeal",
        "legal_normative", "sovereignty_norm",
        "historical_context", "victim_narrative",
        "denial", "counter_accusation", "delegitimation",
    ]
    BLOCS = ["Western bloc", "Soviet/Eastern bloc", "Non-Aligned Movement"]
    BLOC_SHORT = {
        "Western bloc":        "Western",
        "Soviet/Eastern bloc": "Soviet/East.",
        "Non-Aligned Movement":"Non-Aligned",
    }

    segs = segments[segments["dominant_role"].isin(ROLES_ORDER)]
    ct = (
        segs.groupby(["dominant_role", "bloc"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=ROLES_ORDER, fill_value=0)
        .reindex(columns=BLOCS, fill_value=0)
    )
    ct = ct[ct.sum(axis=1) > 0]

    ca = CorrespondenceAnalysis(n_components=2).fit(ct)

    # Save coordinates
    coords_rows = pd.DataFrame(
        ca.row_coords_, index=ca.row_labels_,
        columns=["Dim1", "Dim2"],
    )
    coords_cols = pd.DataFrame(
        ca.col_coords_, index=ca.col_labels_,
        columns=["Dim1", "Dim2"],
    )
    pd.concat([coords_rows.assign(type="role"),
               coords_cols.assign(type="bloc")]).to_csv(
        TABLES_OUT / "ca_roles_by_bloc_coords.csv"
    )

    pct1 = ca.explained_inertia_[0] * 100
    pct2 = ca.explained_inertia_[1] * 100

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(9, 7))
    _add_axis_lines(ax)

    # Plot roles (rows)
    for i, role in enumerate(ca.row_labels_):
        x, y = ca.row_coords_[i]
        ht = ROLE_HABERMAS.get(role, "communicative")
        color = HABERMAS_TYPE_COLORS[ht]
        ax.scatter(x, y, s=90, color=color, zorder=3, marker="o", alpha=0.85)
        label = role.replace("_", " ")
        ha = "left" if x >= 0 else "right"
        ax.annotate(
            label, xy=(x, y),
            xytext=(x + (0.025 if x >= 0 else -0.025), y + 0.015),
            fontsize=8, color=color, fontweight="bold", ha=ha,
        )

    # Plot blocs (columns) — larger markers, different shapes
    for j, bloc in enumerate(ca.col_labels_):
        x, y = ca.col_coords_[j]
        color = BLOC_COLORS.get(bloc, "black")
        marker = BLOC_MARKERS.get(bloc, "s")
        ax.scatter(x, y, s=180, color=color, marker=marker, zorder=4,
                   edgecolors="white", linewidth=1.2)
        short = BLOC_SHORT.get(bloc, bloc)
        ha = "left" if x >= 0 else "right"
        ax.annotate(
            short, xy=(x, y),
            xytext=(x + (0.03 if x >= 0 else -0.03), y + 0.02),
            fontsize=10, color=color, fontweight="bold", ha=ha,
        )

    # Legend — Habermas types
    legend_handles = [
        mpatches.Patch(color=HABERMAS_TYPE_COLORS[ht], label=ht.capitalize())
        for ht in HABERMAS_TYPES
    ]
    bloc_handles = [
        plt.scatter([], [], marker=BLOC_MARKERS[b], color=BLOC_COLORS[b],
                    s=100, label=b, edgecolors="white", linewidth=1)
        for b in BLOCS
    ]
    leg1 = ax.legend(handles=legend_handles, title="Habermas type",
                     fontsize=8, title_fontsize=8, loc="upper right", frameon=True)
    ax.add_artist(leg1)
    ax.legend(handles=bloc_handles, title="Cold War bloc",
              fontsize=8, title_fontsize=8, loc="lower right", frameon=True)

    _expand_lim(ax)
    ax.set_xlabel(f"Dimension 1 ({pct1:.1f}% inertia)", fontsize=10)
    ax.set_ylabel(f"Dimension 2 ({pct2:.1f}% inertia)", fontsize=10)
    ax.set_title(
        "Correspondence Analysis: Communicative Roles × Cold War Blocs\n"
        f"(Total inertia = {ca.total_inertia_:.4f}  |  n = 102 coded segments)",
        fontsize=11,
    )
    fig.tight_layout()
    out = FIGURES_OUT / "fig1_ca_roles_by_bloc.png"
    fig.savefig(out, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")
    return ca


# ─────────────────────────────────────── figure 2: roles × periods ───────────
def fig2_roles_by_period(segments: pd.DataFrame) -> CorrespondenceAnalysis:
    ROLES_ORDER = [
        "justification", "dialogue_appeal",
        "legal_normative", "sovereignty_norm",
        "historical_context", "victim_narrative",
        "denial", "counter_accusation", "delegitimation",
    ]
    avail_periods = [p for p in PERIOD_ORDER if segments["period"].eq(p).any()]

    segs = segments[segments["dominant_role"].isin(ROLES_ORDER)]
    ct = (
        segs.groupby(["dominant_role", "period"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=ROLES_ORDER, fill_value=0)
        .reindex(columns=avail_periods, fill_value=0)
    )
    ct = ct[ct.sum(axis=1) > 0]

    ca = CorrespondenceAnalysis(n_components=2).fit(ct)

    coords_rows = pd.DataFrame(
        ca.row_coords_, index=ca.row_labels_,
        columns=["Dim1", "Dim2"],
    )
    coords_cols = pd.DataFrame(
        ca.col_coords_, index=ca.col_labels_,
        columns=["Dim1", "Dim2"],
    )
    pd.concat([coords_rows.assign(type="role"),
               coords_cols.assign(type="period")]).to_csv(
        TABLES_OUT / "ca_roles_by_period_coords.csv"
    )

    pct1 = ca.explained_inertia_[0] * 100
    pct2 = ca.explained_inertia_[1] * 100

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(9, 7))
    _add_axis_lines(ax)

    # Plot roles (rows)
    for i, role in enumerate(ca.row_labels_):
        x, y = ca.row_coords_[i]
        ht = ROLE_HABERMAS.get(role, "communicative")
        color = HABERMAS_TYPE_COLORS[ht]
        ax.scatter(x, y, s=90, color=color, zorder=3, marker="o", alpha=0.85)
        label = role.replace("_", " ")
        ha = "left" if x >= 0 else "right"
        ax.annotate(
            label, xy=(x, y),
            xytext=(x + (0.025 if x >= 0 else -0.025), y + 0.015),
            fontsize=8, color=color, fontweight="bold", ha=ha,
        )

    # Plot periods (columns)
    for j, period in enumerate(ca.col_labels_):
        x, y = ca.col_coords_[j]
        color = PERIOD_COLORS.get(period, "black")
        short = PERIOD_SHORT.get(period, period)
        ax.scatter(x, y, s=200, color=color, marker="D", zorder=4,
                   edgecolors="white", linewidth=1.2)
        ha = "left" if x >= 0 else "right"
        ax.annotate(
            short, xy=(x, y),
            xytext=(x + (0.03 if x >= 0 else -0.03), y + 0.02),
            fontsize=9, color=color, fontweight="bold", ha=ha,
        )

    legend_handles = [
        mpatches.Patch(color=HABERMAS_TYPE_COLORS[ht], label=ht.capitalize())
        for ht in HABERMAS_TYPES
    ]
    period_handles = [
        plt.scatter([], [], marker="D", color=PERIOD_COLORS.get(p, "gray"),
                    s=80, label=PERIOD_SHORT.get(p, p), edgecolors="white")
        for p in avail_periods
    ]
    leg1 = ax.legend(handles=legend_handles, title="Habermas type",
                     fontsize=8, title_fontsize=8, loc="upper right", frameon=True)
    ax.add_artist(leg1)
    ax.legend(handles=period_handles, title="Period",
              fontsize=8, title_fontsize=8, loc="lower right", frameon=True)

    _expand_lim(ax)
    ax.set_xlabel(f"Dimension 1 ({pct1:.1f}% inertia)", fontsize=10)
    ax.set_ylabel(f"Dimension 2 ({pct2:.1f}% inertia)", fontsize=10)
    ax.set_title(
        "Correspondence Analysis: Communicative Roles × Historical Periods\n"
        f"(Total inertia = {ca.total_inertia_:.4f}  |  n = 102 coded segments)",
        fontsize=11,
    )
    fig.tight_layout()
    out = FIGURES_OUT / "fig2_ca_roles_by_period.png"
    fig.savefig(out, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")
    return ca


# ─────────────────────────────────────────── figure 3: scree plots ───────────
def fig3_scree(ca_bloc: CorrespondenceAnalysis,
               ca_period: CorrespondenceAnalysis) -> None:
    plt.style.use(FIGURE_STYLE)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    for ax, ca, title in zip(
        axes,
        [ca_bloc, ca_period],
        ["Roles × Blocs", "Roles × Periods"],
    ):
        n_dims = len(ca.inertia_)
        pcts = ca.explained_inertia_ * 100
        cum_pcts = np.cumsum(pcts)
        x = np.arange(1, n_dims + 1)

        bars = ax.bar(x, pcts, color="#4575b4", alpha=0.8, edgecolor="white")
        ax2 = ax.twinx()
        ax2.plot(x, cum_pcts, "o-", color="#d73027", linewidth=1.5, markersize=5)
        ax2.set_ylabel("Cumulative inertia (%)", fontsize=9, color="#d73027")
        ax2.set_ylim(0, 110)
        ax2.tick_params(axis="y", colors="#d73027")

        for bar, pct in zip(bars, pcts):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{pct:.1f}%", ha="center", va="bottom", fontsize=8,
            )
        ax.set_xlabel("Dimension", fontsize=9)
        ax.set_ylabel("Inertia (%)", fontsize=9)
        ax.set_xticks(x)
        ax.set_title(f"Scree Plot — {title}\n(Total inertia = {ca.total_inertia_:.4f})", fontsize=10)

    fig.tight_layout()
    out = FIGURES_OUT / "fig3_scree_plots.png"
    fig.savefig(out, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ──────────────────────────────────── figure 4: strategies × blocs ───────────
def fig4_strategies_by_bloc(segments: pd.DataFrame) -> None:
    """CA on manual_strategy_code × bloc."""
    BLOCS = ["Western bloc", "Soviet/Eastern bloc", "Non-Aligned Movement"]
    BLOC_SHORT = {
        "Western bloc":        "Western",
        "Soviet/Eastern bloc": "Soviet/East.",
        "Non-Aligned Movement":"Non-Aligned",
    }

    if "manual_strategy_code" not in segments.columns:
        print("  [skip fig4] manual_strategy_code column missing in segments")
        return

    segs = segments[segments["manual_strategy_code"].notna() &
                    segments["bloc"].isin(BLOCS)]
    ct = (
        segs.groupby(["manual_strategy_code", "bloc"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=BLOCS, fill_value=0)
    )
    ct = ct[ct.sum(axis=1) > 0]
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        print("  [skip fig4] insufficient data for CA")
        return

    ca = CorrespondenceAnalysis(n_components=2).fit(ct)
    pct1 = ca.explained_inertia_[0] * 100
    pct2 = ca.explained_inertia_[1] * 100

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(9, 7))
    _add_axis_lines(ax)

    # Strategy colours — cycle through a neutral palette
    strategy_colors = plt.cm.tab10(np.linspace(0, 1, len(ca.row_labels_)))

    for i, strat in enumerate(ca.row_labels_):
        x, y = ca.row_coords_[i]
        color = strategy_colors[i]
        ax.scatter(x, y, s=80, color=color, zorder=3, marker="o", alpha=0.85)
        ha = "left" if x >= 0 else "right"
        ax.annotate(
            strat, xy=(x, y),
            xytext=(x + (0.025 if x >= 0 else -0.025), y + 0.015),
            fontsize=8, color=color, fontweight="bold", ha=ha,
        )

    for j, bloc in enumerate(ca.col_labels_):
        x, y = ca.col_coords_[j]
        color = BLOC_COLORS.get(bloc, "black")
        marker = BLOC_MARKERS.get(bloc, "s")
        ax.scatter(x, y, s=200, color=color, marker=marker, zorder=4,
                   edgecolors="white", linewidth=1.2)
        short = BLOC_SHORT.get(bloc, bloc)
        ha = "left" if x >= 0 else "right"
        ax.annotate(
            short, xy=(x, y),
            xytext=(x + (0.03 if x >= 0 else -0.03), y + 0.025),
            fontsize=10, color=color, fontweight="bold", ha=ha,
        )

    bloc_handles = [
        plt.scatter([], [], marker=BLOC_MARKERS[b], color=BLOC_COLORS[b],
                    s=100, label=b, edgecolors="white")
        for b in BLOCS
    ]
    ax.legend(handles=bloc_handles, title="Cold War bloc",
              fontsize=8, title_fontsize=8, loc="lower right", frameon=True)

    _expand_lim(ax)
    ax.set_xlabel(f"Dimension 1 ({pct1:.1f}% inertia)", fontsize=10)
    ax.set_ylabel(f"Dimension 2 ({pct2:.1f}% inertia)", fontsize=10)
    ax.set_title(
        "Correspondence Analysis: Legitimation Strategies × Cold War Blocs\n"
        f"(Total inertia = {ca.total_inertia_:.4f}  |  manual codes)",
        fontsize=11,
    )
    fig.tight_layout()
    out = FIGURES_OUT / "fig4_ca_strategies_by_bloc.png"
    fig.savefig(out, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ────────────────────────────────────────────────────── main ─────────────────
def main() -> None:
    print("Loading data…")
    segments = load_segments()
    print(f"  Segments: {len(segments)} coded")

    print("\n=== Correspondence Analysis ===")
    ca_bloc   = fig1_roles_by_bloc(segments)
    ca_period = fig2_roles_by_period(segments)
    fig3_scree(ca_bloc, ca_period)
    fig4_strategies_by_bloc(segments)

    # Print inertia summary
    print("\n--- Inertia summary ---")
    for label, ca in [("Roles × Blocs", ca_bloc), ("Roles × Periods", ca_period)]:
        dims = [
            f"Dim{i+1}: {ca.explained_inertia_[i]*100:.1f}%"
            for i in range(min(3, len(ca.inertia_)))
        ]
        print(f"  {label}: total = {ca.total_inertia_:.4f}  |  " + "  ".join(dims))

    print("\n=== Done ===")
    print(f"Tables  : {TABLES_OUT}/")
    print(f"Figures : {FIGURES_OUT}/")
    print("\nFigures produced:")
    print("  fig1 — CA biplot: communicative roles × Cold War blocs")
    print("  fig2 — CA biplot: communicative roles × historical periods")
    print("  fig3 — Scree plots for both analyses")
    print("  fig4 — CA biplot: manual strategies × blocs")


if __name__ == "__main__":
    main()
