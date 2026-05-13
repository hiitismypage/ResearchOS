"""
statistical_tests.py
---------------------
Chi-square / Fisher's exact tests on the 33-case manual corpus.

Input tables (analysis_output/tables/):
  - communicative_situation_profiles.csv  (one row per case)
  - frequency_strategies.csv              (strategy counts)
  - communicative_roles.csv               (one row per coded segment)

Output figures (analysis_output/figures/stats/):
  fig1 — Habermas types × bloc: stacked bar + chi-square annotation
  fig2 — Habermas types × period: stacked bar + chi-square annotation
  fig3 — Post-hoc pairwise bloc comparisons (Fisher's exact)
  fig4 — Strategy codes × bloc: heatmap of adjusted residuals
  fig5 — Strategic vs. communicative+normative+dramaturgical trend by period

Output tables (analysis_output/tables/):
  chi2_habermas_by_bloc.csv
  chi2_habermas_by_period.csv
  fisher_pairwise_blocs.csv
  chi2_strategies_by_bloc.csv
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
from scipy.stats import chi2_contingency, fisher_exact

warnings.filterwarnings("ignore", category=FutureWarning)
matplotlib.use("Agg")

# ─────────────────────────────────────────────────────────── paths ──────────
ROOT = Path(__file__).resolve().parents[2]
TABLES_IN  = ROOT / "analysis_output" / "tables"
TABLES_OUT = ROOT / "analysis_output" / "tables"
FIGURES_OUT = ROOT / "analysis_output" / "figures" / "stats"
FIGURES_OUT.mkdir(parents=True, exist_ok=True)

FIGURE_DPI   = 150
FIGURE_STYLE = "seaborn-v0_8-whitegrid"

# ───────────────────────────────────────────────── palette constants ─────────
HABERMAS_TYPE_COLORS: dict[str, str] = {
    "communicative": "#1a9850",
    "normative":     "#2166ac",
    "dramaturgical": "#c2a5cf",
    "strategic":     "#d73027",
}
HABERMAS_TYPES = ["communicative", "normative", "dramaturgical", "strategic"]

BLOC_COLORS: dict[str, str] = {
    "Western bloc":        "#2166ac",
    "Soviet/Eastern bloc": "#d6604d",
    "Non-Aligned Movement":"#4dac26",
}
BLOC_SHORT: dict[str, str] = {
    "Western bloc":        "Western",
    "Soviet/Eastern bloc": "Soviet/\nEastern",
    "Non-Aligned Movement":"Non-Aligned",
}

PERIOD_ORDER = [
    "Cold War (1946–1989)",
    "Post–Cold War (1990–2001)",
    "Post-9/11 Security Turn (2002–2013)",
    "Post-2014 Normative Fragmentation",
]
PERIOD_SHORT: dict[str, str] = {
    "Cold War (1946–1989)":                    "Cold War\n(1946–89)",
    "Post–Cold War (1990–2001)":               "Post–Cold War\n(1990–2001)",
    "Post-9/11 Security Turn (2002–2013)":     "Post-9/11\n(2002–13)",
    "Post-2014 Normative Fragmentation":       "Post-2014\nFrag.",
}


# ─────────────────────────────────────────────────── helpers ─────────────────
def sig_stars(p: float) -> str:
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    if p < 0.10:  return "†"
    return "n.s."


def adjusted_residuals(obs: np.ndarray) -> np.ndarray:
    """Standardized (adjusted) residuals for a contingency table."""
    chi2, _, _, expected = chi2_contingency(obs)
    row_sums = obs.sum(axis=1, keepdims=True)
    col_sums = obs.sum(axis=0, keepdims=True)
    n = obs.sum()
    std = np.sqrt(
        expected
        * (1 - row_sums / n)
        * (1 - col_sums / n)
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        res = np.where(std > 0, (obs - expected) / std, 0.0)
    return res


def run_chi2(contingency: pd.DataFrame, label: str) -> dict:
    # drop all-zero rows/columns before chi2 (zero marginals cause ValueError)
    ct = contingency.loc[contingency.sum(axis=1) > 0, contingency.sum(axis=0) > 0]
    obs = ct.values.astype(float)
    chi2, p, dof, expected = chi2_contingency(obs)
    n = obs.sum()
    min_dim = min(obs.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else np.nan
    pct_low = (expected < 5).sum() / expected.size * 100
    validity_note = f"  ⚠ {pct_low:.0f}% cells expected<5 — interpret with caution; prefer Fisher's exact" if pct_low > 20 else ""
    result = {
        "test": label,
        "chi2": round(chi2, 4),
        "df": dof,
        "p_value": round(p, 6),
        "cramers_v": round(cramers_v, 4),
        "sig": sig_stars(p),
        "n": int(n),
        "pct_cells_expected_lt5": round(pct_low, 1),
    }
    print(f"  χ²({dof}) = {chi2:.3f}, p = {p:.4f} {sig_stars(p)}  |  V = {cramers_v:.3f}  [{label}]{validity_note}")
    return result


# ────────────────────────────────────────────────────── load data ─────────────
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, int, int]:
    profiles = pd.read_csv(TABLES_IN / "communicative_situation_profiles.csv")
    segments = pd.read_csv(TABLES_IN / "communicative_roles.csv")

    # Normalise habermas_type column
    for df in [profiles, segments]:
        if "habermas_type" not in df.columns and "dominant_habermas_type" in df.columns:
            df["habermas_type"] = df["dominant_habermas_type"]

    # Derive dominant habermas type per case from pct columns in profiles
    pct_cols = [c for c in profiles.columns if c.startswith("pct_") and not c.startswith("pct_un")]
    ht_cols  = [f"pct_{ht}" for ht in HABERMAS_TYPES if f"pct_{ht}" in profiles.columns]
    if ht_cols:
        profiles["dominant_habermas_type"] = profiles[ht_cols].idxmax(axis=1).str.replace("pct_", "")
    else:
        profiles["dominant_habermas_type"] = "normative"  # fallback

    # Period ordering
    period_cat = pd.CategoricalDtype(categories=PERIOD_ORDER, ordered=True)
    for df in [profiles, segments]:
        if "period" in df.columns:
            df["period"] = df["period"].astype(period_cat)

    n_total      = len(segments)
    n_classified = int((segments["habermas_type"] != "unclassified").sum())
    return profiles, segments, n_total, n_classified


# ──────────────────────────────────────── contingency builders ───────────────
def build_habermas_by_bloc(segments: pd.DataFrame) -> pd.DataFrame:
    """Count coded segments by (bloc, habermas_type)."""
    ct = (
        segments.groupby(["bloc", "habermas_type"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=HABERMAS_TYPES, fill_value=0)
    )
    return ct


def build_habermas_by_period(segments: pd.DataFrame) -> pd.DataFrame:
    avail = [p for p in PERIOD_ORDER if p in segments["period"].cat.categories
             and segments["period"].eq(p).any()]
    ct = (
        segments.groupby(["period", "habermas_type"])
        .size()
        .unstack(fill_value=0)
        .reindex(avail)
        .reindex(columns=HABERMAS_TYPES, fill_value=0)
    )
    return ct


# ─────────────────────────────────────────────────── figure 1 ────────────────
def fig1_habermas_by_bloc(segments: pd.DataFrame, results: list[dict]) -> None:
    ct = build_habermas_by_bloc(segments)
    pcts = ct.div(ct.sum(axis=1), axis=0) * 100

    test = run_chi2(ct, "Habermas type × bloc")
    results.append(test)
    ct.to_csv(TABLES_OUT / "chi2_habermas_by_bloc.csv")

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(8, 5))
    bottom = np.zeros(len(pcts))
    bloc_labels = [BLOC_SHORT.get(b, b) for b in pcts.index]

    for ht in HABERMAS_TYPES:
        vals = pcts[ht].values if ht in pcts.columns else np.zeros(len(pcts))
        bars = ax.bar(
            bloc_labels, vals, bottom=bottom,
            color=HABERMAS_TYPE_COLORS[ht], label=ht.capitalize(),
            edgecolor="white", linewidth=0.6,
        )
        for bar, val in zip(bars, vals):
            if val > 9:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.0f}%", ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold",
                )
        bottom += vals

    ann = f"χ²({test['df']}) = {test['chi2']:.2f}, p = {test['p_value']:.3f} {test['sig']}  |  V = {test['cramers_v']:.3f}"
    ax.text(0.98, 0.97, ann, transform=ax.transAxes,
            ha="right", va="top", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))
    ax.set_ylabel("% of coded segments", fontsize=10)
    ax.set_ylim(0, 112)
    ax.set_title(
        "Habermas Action Types by Cold War Bloc\n(% of classified segments; Fisher's exact for pairwise tests)",
        fontsize=11,
    )
    ax.legend(title="Habermas type", fontsize=9, title_fontsize=9,
              loc="upper left", frameon=True)
    fig.tight_layout()
    out = FIGURES_OUT / "fig1_habermas_by_bloc.png"
    fig.savefig(out, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ─────────────────────────────────────────────────── figure 2 ────────────────
def fig2_habermas_by_period(segments: pd.DataFrame, results: list[dict]) -> None:
    ct = build_habermas_by_period(segments)
    pcts = ct.div(ct.sum(axis=1), axis=0) * 100

    test = run_chi2(ct, "Habermas type × period")
    results.append(test)
    ct.to_csv(TABLES_OUT / "chi2_habermas_by_period.csv")

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(10, 5))
    bottom = np.zeros(len(pcts))
    period_labels = [PERIOD_SHORT.get(str(p), str(p)) for p in pcts.index]

    for ht in HABERMAS_TYPES:
        vals = pcts[ht].values if ht in pcts.columns else np.zeros(len(pcts))
        bars = ax.bar(
            period_labels, vals, bottom=bottom,
            color=HABERMAS_TYPE_COLORS[ht], label=ht.capitalize(),
            edgecolor="white", linewidth=0.6,
        )
        for bar, val in zip(bars, vals):
            if val > 9:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.0f}%", ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold",
                )
        bottom += vals

    ann = f"χ²({test['df']}) = {test['chi2']:.2f}, p = {test['p_value']:.3f} {test['sig']}  |  V = {test['cramers_v']:.3f}"
    ax.text(0.98, 0.97, ann, transform=ax.transAxes,
            ha="right", va="top", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))
    ax.set_ylabel("% of coded segments", fontsize=10)
    ax.set_ylim(0, 112)
    ax.set_title(
        "Habermas Action Types by Historical Period\n(% of classified segments; Fisher's exact for pairwise tests)",
        fontsize=11,
    )
    ax.legend(title="Habermas type", fontsize=9, title_fontsize=9,
              loc="upper left", frameon=True)
    fig.tight_layout()
    out = FIGURES_OUT / "fig2_habermas_by_period.png"
    fig.savefig(out, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ─────────────────────────────────────────────────── figure 3 ────────────────
def fig3_fisher_pairwise(segments: pd.DataFrame, results: list[dict]) -> None:
    """Pairwise Fisher's exact: for each pair of blocs, test each Habermas type."""
    blocs = ["Western bloc", "Soviet/Eastern bloc", "Non-Aligned Movement"]
    pairs = [
        ("Western bloc", "Soviet/Eastern bloc"),
        ("Western bloc", "Non-Aligned Movement"),
        ("Soviet/Eastern bloc", "Non-Aligned Movement"),
    ]

    records: list[dict] = []
    for ht in HABERMAS_TYPES:
        for b1, b2 in pairs:
            n1_yes = segments[(segments["bloc"] == b1) & (segments["habermas_type"] == ht)].shape[0]
            n1_no  = segments[(segments["bloc"] == b1) & (segments["habermas_type"] != ht)].shape[0]
            n2_yes = segments[(segments["bloc"] == b2) & (segments["habermas_type"] == ht)].shape[0]
            n2_no  = segments[(segments["bloc"] == b2) & (segments["habermas_type"] != ht)].shape[0]
            table = np.array([[n1_yes, n1_no], [n2_yes, n2_no]])
            if table.sum() == 0 or (n1_yes + n2_yes) == 0:
                or_, p = np.nan, 1.0
            else:
                or_, p = fisher_exact(table, alternative="two-sided")
            records.append({
                "habermas_type": ht,
                "bloc_1": b1,
                "bloc_2": b2,
                "n1_yes": n1_yes,
                "n2_yes": n2_yes,
                "odds_ratio": round(or_, 3) if not np.isnan(or_) else np.nan,
                "p_value": round(p, 4),
                "sig": sig_stars(p),
            })

    df_r = pd.DataFrame(records)
    df_r.to_csv(TABLES_OUT / "fisher_pairwise_blocs.csv", index=False)
    results.extend(df_r.to_dict("records"))

    # Heatmap: p-values for each (ht × pair)
    pair_labels = [f"{BLOC_SHORT[b1].replace(chr(10),' ')} vs\n{BLOC_SHORT[b2].replace(chr(10),' ')}"
                   for b1, b2 in pairs]
    pmat = np.ones((len(HABERMAS_TYPES), len(pairs)))
    for i, ht in enumerate(HABERMAS_TYPES):
        for j, (b1, b2) in enumerate(pairs):
            row = df_r[(df_r["habermas_type"] == ht) & (df_r["bloc_1"] == b1) & (df_r["bloc_2"] == b2)]
            if not row.empty:
                pmat[i, j] = row["p_value"].values[0]

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(7, 4))
    cmap = plt.cm.RdYlGn_r
    im = ax.imshow(pmat, cmap=cmap, vmin=0, vmax=0.20, aspect="auto")
    ax.set_xticks(range(len(pairs)))
    ax.set_xticklabels(pair_labels, fontsize=9)
    ax.set_yticks(range(len(HABERMAS_TYPES)))
    ax.set_yticklabels([ht.capitalize() for ht in HABERMAS_TYPES], fontsize=10)
    for i in range(len(HABERMAS_TYPES)):
        for j in range(len(pairs)):
            p = pmat[i, j]
            txt = f"{p:.3f}\n{sig_stars(p)}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8,
                    color="black" if p > 0.05 else "white")
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("p-value (Fisher's exact)", fontsize=8)
    ax.set_title(
        "Pairwise Bloc Comparisons — Fisher's Exact Test\n"
        "(cell = p-value; green = significant at p < 0.05)",
        fontsize=10,
    )
    fig.tight_layout()
    out = FIGURES_OUT / "fig3_fisher_pairwise.png"
    fig.savefig(out, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ─────────────────────────────────────────────────── figure 4 ────────────────
def fig4_adjusted_residuals(segments: pd.DataFrame, results: list[dict]) -> None:
    """Adjusted residuals heatmap: roles × blocs."""
    ROLES_ORDER = [
        "justification", "dialogue_appeal",
        "legal_normative", "sovereignty_norm",
        "historical_context", "victim_narrative",
        "denial", "counter_accusation", "delegitimation",
    ]
    BLOCS_ORDER = ["Western bloc", "Soviet/Eastern bloc", "Non-Aligned Movement"]

    if "dominant_role" not in segments.columns:
        print("  [skip fig4] dominant_role column missing")
        return

    segs_valid = segments[segments["dominant_role"].isin(ROLES_ORDER)]
    ct = (
        segs_valid.groupby(["dominant_role", "bloc"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=ROLES_ORDER, fill_value=0)
        .reindex(columns=BLOCS_ORDER, fill_value=0)
    )

    # Drop roles with zero total (chi-square requires all expected > 0)
    ct = ct[ct.sum(axis=1) > 0]

    test = run_chi2(ct, "Role × bloc (adjusted residuals)")
    results.append(test)
    ct.to_csv(TABLES_OUT / "chi2_strategies_by_bloc.csv")

    adj_res = adjusted_residuals(ct.values.astype(float))
    actual_roles = list(ct.index)

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(8, max(4, len(actual_roles) * 0.7)))
    vmax = max(3.0, np.abs(adj_res).max())
    im = ax.imshow(adj_res, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")

    ax.set_xticks(range(len(BLOCS_ORDER)))
    ax.set_xticklabels([BLOC_SHORT[b] for b in BLOCS_ORDER], fontsize=10)
    ax.set_yticks(range(len(actual_roles)))
    role_labels = [r.replace("_", " ").title() for r in actual_roles]
    ax.set_yticklabels(role_labels, fontsize=9)

    for i in range(len(actual_roles)):
        for j in range(len(BLOCS_ORDER)):
            v = adj_res[i, j]
            marker = " *" if abs(v) >= 1.96 else ""
            ax.text(j, i, f"{v:.1f}{marker}", ha="center", va="center",
                    fontsize=8, color="black" if abs(v) < 2 else "white")

    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.04)
    cbar.set_label("Adjusted residual  (|z| ≥ 1.96 = p < 0.05)", fontsize=8)
    ann = f"χ²({test['df']}) = {test['chi2']:.2f}, p = {test['p_value']:.3f} {test['sig']}  |  V = {test['cramers_v']:.3f}"
    ax.set_title(
        f"Communicative Roles × Bloc — Adjusted Residuals\n{ann}",
        fontsize=10,
    )
    fig.tight_layout()
    out = FIGURES_OUT / "fig4_adjusted_residuals.png"
    fig.savefig(out, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ─────────────────────────────────────────────────── figure 5 ────────────────
def fig5_strategic_trend(segments: pd.DataFrame, results: list[dict]) -> None:
    """Strategic vs. communicative/normative/dramaturgical — trend across periods."""
    avail = [p for p in PERIOD_ORDER if segments["period"].eq(p).any()]

    counts = (
        segments.groupby(["period", "habermas_type"])
        .size()
        .unstack(fill_value=0)
        .reindex(avail)
        .reindex(columns=HABERMAS_TYPES, fill_value=0)
    )
    pcts = counts.div(counts.sum(axis=1), axis=0) * 100

    # Fisher's exact: strategic vs. non-strategic, first period vs. last
    if len(avail) >= 2:
        first, last = avail[0], avail[-1]
        n_str_f = int(counts.loc[first, "strategic"])
        n_nst_f = int(counts.loc[first, [h for h in HABERMAS_TYPES if h != "strategic"]].sum())
        n_str_l = int(counts.loc[last, "strategic"])
        n_nst_l = int(counts.loc[last, [h for h in HABERMAS_TYPES if h != "strategic"]].sum())
        table = np.array([[n_str_f, n_nst_f], [n_str_l, n_nst_l]])
        or_, p_trend = fisher_exact(table, alternative="two-sided")
        trend_ann = (f"Fisher's exact ({PERIOD_SHORT.get(str(first), first).replace(chr(10),' ')}"
                     f" vs {PERIOD_SHORT.get(str(last), last).replace(chr(10),' ')}): "
                     f"OR = {or_:.2f}, p = {p_trend:.3f} {sig_stars(p_trend)}")
        results.append({
            "test": "Strategic trend Fisher",
            "period_1": str(first), "period_2": str(last),
            "odds_ratio": round(or_, 3), "p_value": round(p_trend, 4),
            "sig": sig_stars(p_trend),
        })
    else:
        trend_ann = ""

    plt.style.use(FIGURE_STYLE)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1.8, 1]})

    # Left: stacked bar
    ax = axes[0]
    bottom = np.zeros(len(pcts))
    period_labels = [PERIOD_SHORT.get(str(p), str(p)) for p in pcts.index]
    for ht in HABERMAS_TYPES:
        vals = pcts[ht].values if ht in pcts.columns else np.zeros(len(pcts))
        bars = ax.bar(
            period_labels, vals, bottom=bottom,
            color=HABERMAS_TYPE_COLORS[ht], label=ht.capitalize(),
            edgecolor="white", linewidth=0.6,
        )
        for bar, val in zip(bars, vals):
            if val > 9:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.0f}%", ha="center", va="center",
                    fontsize=8, color="white", fontweight="bold",
                )
        bottom += vals
    ax.set_xticks(range(len(period_labels)))
    ax.set_xticklabels(period_labels, rotation=0, fontsize=8)
    ax.set_ylabel("% of coded segments", fontsize=10)
    ax.set_ylim(0, 112)
    ax.set_title("Habermas Types across Periods", fontsize=10)
    ax.legend(title="Habermas type", fontsize=8, title_fontsize=8, frameon=True)

    # Right: strategic % line + dots
    ax2 = axes[1]
    strat_pct = pcts["strategic"].values if "strategic" in pcts.columns else np.zeros(len(pcts))
    x = np.arange(len(period_labels))
    ax2.plot(x, strat_pct, marker="o", color=HABERMAS_TYPE_COLORS["strategic"],
             linewidth=2, markersize=7)
    for xi, yi in zip(x, strat_pct):
        ax2.text(xi, yi + 0.8, f"{yi:.1f}%", ha="center", va="bottom", fontsize=8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(period_labels, rotation=0, fontsize=7)
    ax2.set_ylabel("% Strategic action", fontsize=10)
    ax2.set_ylim(0, max(strat_pct) * 1.5 + 2 if strat_pct.max() > 0 else 10)
    ax2.set_title("Strategic Action Trend", fontsize=10)

    if trend_ann:
        fig.text(0.5, -0.04, trend_ann, ha="center", fontsize=8,
                 bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", alpha=0.9))

    fig.suptitle(
        "Strategic vs. Communicative Action — Temporal Dynamics\n(classified segments; Fisher's exact for period comparison)",
        fontsize=11, y=1.02,
    )
    fig.tight_layout()
    out = FIGURES_OUT / "fig5_strategic_trend.png"
    fig.savefig(out, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ────────────────────────────────────────────────────── main ─────────────────
def main() -> None:
    print("Loading data…")
    profiles, segments, n_total, n_classified = load_data()
    print(f"  Profiles: {len(profiles)} cases  |  Segments: {n_total} coded ({n_classified} classified)")

    results: list[dict] = []

    print("\n=== Chi-square & Fisher tests ===")
    fig1_habermas_by_bloc(segments, results)
    fig2_habermas_by_period(segments, results)
    fig3_fisher_pairwise(segments, results)
    fig4_adjusted_residuals(segments, results)
    fig5_strategic_trend(segments, results)

    # Save summary
    pd.DataFrame([r for r in results if "chi2" in r]).to_csv(
        TABLES_OUT / "chi2_summary.csv", index=False
    )

    print("\n=== Done ===")
    print(f"Tables  : {TABLES_OUT}/")
    print(f"Figures : {FIGURES_OUT}/")
    print("\nFigures produced:")
    print("  fig1 — Habermas types × bloc (stacked bar + chi-square)")
    print("  fig2 — Habermas types × period (stacked bar + chi-square)")
    print("  fig3 — Pairwise bloc comparisons (Fisher's exact heatmap)")
    print("  fig4 — Adjusted residuals heatmap: roles × blocs")
    print("  fig5 — Strategic action trend across periods")


if __name__ == "__main__":
    main()
