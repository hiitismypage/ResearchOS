"""
Communicative role classification for the UNGDC legitimation study.

Operationalizes Habermas's full four-part typology of social action
(Theory of Communicative Action, 1981):

  1. Communicative action  — oriented toward mutual understanding (Verständigung)
  2. Normative action      — oriented toward shared normative expectations
  3. Dramaturgical action  — oriented toward self-presentation to an audience
  4. Strategic action      — oriented toward success, using others as means

Each coded segment from the 35-case purposive sample is classified by its
dominant communicative role. Case-level profiles aggregate these into a
communicative situation map across blocs and historical periods.

Run from scripts/:
    python3 ml/communicative_roles.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

sys.path.insert(0, str(Path(__file__).parents[1]))
from config import (
    VIOLATION_EVENTS,
    CODING_DIR,
    TABLES_DIR,
    FIGURES_DIR,
    FIGURE_DPI,
    FIGURE_STYLE,
)

# ---------------------------------------------------------------------------
# Habermas four-type taxonomy
# ---------------------------------------------------------------------------

ROLES: dict[str, dict] = {
    # ── Communicative action (Kommunikatives Handeln) ──────────────────────
    # Oriented toward Verständigung: raising validity claims open to rational
    # evaluation by all parties.
    "justification": {
        "habermas_type": "communicative",
        "description": "Provides reasons for action open to rational evaluation",
        "keywords": [
            "because", "in order to", "for the purpose of", "necessary",
            "compelled", "had no choice", "forced to", "required to",
            "aimed at", "in response to", "to prevent", "justified by",
            "proportionate", "imminent", "acts of terrorism", "terrorist threat",
            "terrorist attack", "necessary measures", "right to respond",
            "compelled to act", "no alternative", "had to act",
            "terrorist", "terrorism", "extremism", "extremist", "radicalism",
            "weapons of mass destruction", "chemical weapons", "biological weapons",
            "threat posed", "defeat terrorism", "fight terrorism", "combat terrorism",
            "eliminate the threat", "protect our citizens", "defend our",
        ],
    },
    "dialogue_appeal": {
        "habermas_type": "communicative",
        "description": "Invites the other side to rational discourse or negotiation",
        "keywords": [
            "call upon", "invite", "urge all parties", "we propose",
            "negotiate", "peaceful resolution", "open to dialogue",
            "political solution", "we are ready", "constructive engagement",
        ],
    },

    # ── Normative action (Normreguliertes Handeln) ──────────────────────────
    # Oriented toward fulfilling shared normative expectations (Richtigkeit).
    # Validity claim: normative rightness.
    "legal_normative": {
        "habermas_type": "normative",
        "description": "Appeals to shared legal norms and treaty obligations",
        "keywords": [
            "article 51", "united nations charter", "in accordance with",
            "international law", "treaty obligation", "resolution",
            "lawful", "legal right", "legal basis", "binding obligation",
            "under international law", "consistent with",
            "authorized", "mandate", "pursuant to", "in conformity with",
            "permissible", "in compliance with", "sanctioned by",
            "resolution 1373", "resolution 1368", "right of self-defense",
            "chapter vii", "enforcement action", "inherent right",
            "armed attack", "necessary and proportionate", "collective security",
        ],
    },
    "sovereignty_norm": {
        "habermas_type": "normative",
        "description": "Invokes sovereignty and non-interference as shared norms",
        "keywords": [
            "sovereignty", "non-interference", "territorial integrity",
            "internal affairs", "inviolability", "equal rights of states",
            "sovereign right", "domestic jurisdiction", "principle of",
        ],
    },

    # ── Dramaturgical action (Dramaturgisches Handeln) ──────────────────────
    # Oriented toward self-presentation to an audience.
    # Validity claim: sincerity / authenticity (Wahrhaftigkeit).
    "historical_context": {
        "habermas_type": "dramaturgical",
        "description": "Constructs historical framing to contextualise action",
        "keywords": [
            "historical", "for decades", "colonial", "legacy",
            "long-standing", "ancestral", "since independence",
            "roots of the conflict", "for centuries", "background",
        ],
    },
    "victim_narrative": {
        "habermas_type": "dramaturgical",
        "description": "Presents the state as victim or peace-seeking actor",
        "keywords": [
            "suffered", "victim of", "aggression against", "provocation",
            "we were attacked", "endured", "peaceful people", "our suffering",
            "targeted", "subjected to", "in self-defence", "unprovoked",
            "rocket fire", "rocket attacks", "missile attacks", "shelling",
            "attacks on our", "under attack", "bombardment", "civilians targeted",
            "self-defense", "act of aggression", "right to defend",
        ],
    },

    # ── Strategic action (Strategisches Handeln) ────────────────────────────
    # Oriented toward success; uses discourse to avoid accountability or
    # undermine the accusation rather than seeking understanding.
    "denial": {
        "habermas_type": "strategic",
        "description": "Explicitly rejects the allegation without substantive justification",
        "keywords": [
            "deny", "reject", "refute", "false accusation", "unfounded",
            "baseless", "fabricated", "did not", "have not", "never committed",
            "categorically reject", "groundless", "disinformation",
        ],
    },
    "counter_accusation": {
        "habermas_type": "strategic",
        "description": "Deflects by redirecting criticism to the accuser (tu quoque)",
        "keywords": [
            "double standards", "those who accuse", "hypocrisy", "selective",
            "accusers themselves", "who are they to", "same logic",
            "applies equally", "look at their own", "while at the same time",
        ],
    },
    "delegitimation": {
        "habermas_type": "strategic",
        "description": "Challenges the legitimacy of the accusation or the accuser",
        "keywords": [
            "no right", "political motives", "biased", "politicized",
            "not entitled to", "ulterior motives", "politically motivated",
            "lacks standing", "has no mandate", "interference in",
        ],
    },
}

# Habermas types — display order matters for stacked charts
HABERMAS_TYPES: list[str] = ["communicative", "normative", "dramaturgical", "strategic"]

HABERMAS_TYPE_COLORS: dict[str, str] = {
    "communicative": "#1a9850",
    "normative":     "#2166ac",
    "dramaturgical": "#c2a5cf",
    "strategic":     "#d73027",
}

ROLE_COLORS: dict[str, str] = {
    "justification":     "#1a9850",
    "dialogue_appeal":   "#66bd63",
    "legal_normative":   "#2166ac",
    "sovereignty_norm":  "#74add1",
    "historical_context":"#c2a5cf",
    "victim_narrative":  "#e8b4d8",
    "denial":            "#d73027",
    "counter_accusation":"#f46d43",
    "delegitimation":    "#fdae61",
}

GROUP_PALETTE: dict[str, str] = {
    "Western bloc":        "#2166ac",
    "Soviet/Eastern bloc": "#d6604d",
    "Non-Aligned Movement":"#4dac26",
}

STATE_GROUPS: dict[str, set[str]] = {
    "Western bloc": {
        "USA","GBR","FRA","BEL","NLD","LUX","CAN","DNK","NOR","ISL",
        "ITA","PRT","GRC","TUR","DEU","ESP","AUS","NZL","JPN",
        "SWE","FIN","AUT","IRL","ISR","AND","CHE","CIV","LIE","MCO","SMR","VAT",
    },
    "Soviet/Eastern bloc": {
        "RUS","BLR","UKR","MNG","CUB","PRK","VNM","YMD",
        "ARM","KAZ","KGZ","TJK","TKM","UZB","AZE","MDA","CSK","DDR","GEO",
    },
    "Non-Aligned Movement": {
        "IND","CHN","IDN","PAK","BGD","LKA","NPL","MMR","MYS","PHL",
        "THA","KHM","LAO","SGP","BRN","BTN","MDV","TLS",
        "EGY","SYR","IRQ","IRN","JOR","LBN","LBY","DZA","MAR","TUN",
        "SAU","ARE","BHR","KWT","OMN","QAT","YEM","SDN","DJI","PSE","CYP",
        "NGA","GHA","ETH","TZA","KEN","UGA","ZAF","ZMB","ZWE","SEN",
        "CMR","COD","COG","GAB","MDG","MLI","BFA","NER","TCD","CAF",
        "SLE","GIN","GMB","LBR","BEN","TGO","MRT","BDI","RWA","SOM",
        "ERI","MOZ","AGO","NAM","BWA","LSO","SWZ","MUS","SYC","COM",
        "CPV","STP","GNB","GNQ","SSD","MWI",
        "BRA","MEX","ARG","COL","PER","VEN","CHL","BOL","ECU","URY",
        "PRY","PAN","GTM","HND","SLV","NIC","CRI","DOM","HTI","JAM",
        "TTO","BRB","GUY","SUR","BLZ","BHS","ATG","DMA","GRD","VCT","LCA","KNA",
        "FJI","PNG","VUT","WSM","KIR","TON","TUV","NRU","SLB","FSM","MHL","PLW",
        "AFG","BIH","YUG","SRB","MLT","KOR",
    },
}

BLOC_TRANSITIONS: dict[str, tuple[int, str]] = {
    "POL": (1999, "Western bloc"), "CZE": (1999, "Western bloc"),
    "HUN": (1999, "Western bloc"), "BGR": (2004, "Western bloc"),
    "ROU": (2004, "Western bloc"), "SVK": (2004, "Western bloc"),
    "SVN": (2004, "Western bloc"), "EST": (2004, "Western bloc"),
    "LVA": (2004, "Western bloc"), "LTU": (2004, "Western bloc"),
    "HRV": (2009, "Western bloc"), "ALB": (2009, "Western bloc"),
    "MNE": (2017, "Western bloc"), "MKD": (2020, "Western bloc"),
}

PERIOD_ORDER: list[str] = [
    "Cold War (1946–1989)",
    "Post–Cold War (1990–2001)",
    "Post-9/11 Security Turn (2002–2013)",
    "Post-2014 Normative Fragmentation",
]


# ---------------------------------------------------------------------------
# Core classification
# ---------------------------------------------------------------------------

def score_role(text: str, role: str) -> float:
    text_lower = text.lower()
    words = max(len(text_lower.split()), 1)
    hits = sum(text_lower.count(kw) for kw in ROLES[role]["keywords"])
    return hits / words * 1000


def classify_segment(text: str) -> dict[str, float]:
    return {role: score_role(text, role) for role in ROLES}


def dominant_role(scores: dict[str, float]) -> str:
    nonzero = {r: s for r, s in scores.items() if s > 0}
    return max(nonzero, key=lambda r: nonzero[r]) if nonzero else "unclassified"


def resolve_group(iso3: str, year: int) -> str:
    if iso3 in BLOC_TRANSITIONS:
        ty, ng = BLOC_TRANSITIONS[iso3]
        return ng if year >= ty else "Soviet/Eastern bloc"
    for group, members in STATE_GROUPS.items():
        if iso3 in members:
            return group
    return "Unclassified"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_coded_segments() -> pd.DataFrame:
    path = CODING_DIR / "manual_codes.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Manual codes not found: {path}\n"
            "Run: python3 run_analysis.py --stage screen  then fill manual codes."
        )
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["manual_strategy_code"] = df["manual_strategy_code"].fillna("")
    coded = df[df["manual_strategy_code"] != ""].copy()
    print(f"  Loaded {len(coded)} coded segments ({len(df)} total).")
    return coded


def load_cases() -> pd.DataFrame:
    return pd.read_csv(VIOLATION_EVENTS, encoding="utf-8-sig")


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def classify_all_segments(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    role_scores = df["paragraph_text"].apply(
        lambda t: classify_segment(str(t)) if pd.notna(t) else {r: 0.0 for r in ROLES}
    )
    for role in ROLES:
        df[f"role_score_{role}"] = role_scores.apply(lambda s: s[role])
    df["dominant_role"]   = role_scores.apply(dominant_role)
    df["habermas_type"]   = df["dominant_role"].apply(
        lambda r: ROLES[r]["habermas_type"] if r in ROLES else "unclassified"
    )
    return df


def build_case_profiles(df: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, case in cases.iterrows():
        iso3   = case["country_iso3"]
        year   = int(case["year"])
        period = case["period"]
        group  = resolve_group(iso3, year)
        sub    = df[(df["country_iso3"] == iso3) & (df["year"] == year)]
        if sub.empty:
            continue
        classified = sub[sub["habermas_type"] != "unclassified"]
        role_counts = classified["dominant_role"].value_counts()
        type_counts = classified["habermas_type"].value_counts()
        total = len(sub)
        n_classified = len(classified)
        denom = n_classified if n_classified > 0 else 1
        row: dict = {
            "country_iso3":   iso3,
            "year":           year,
            "period":         period,
            "bloc":           group,
            "allegation":     case.get("allegation_description", ""),
            "n_segments":     total,
            "n_classified":   n_classified,
            "pct_unclassified": round((total - n_classified) / total * 100, 1),
        }
        for role in ROLES:
            row[f"pct_{role}"] = round(role_counts.get(role, 0) / denom * 100, 1)
        for ht in HABERMAS_TYPES:
            row[f"pct_{ht}"] = round(type_counts.get(ht, 0) / denom * 100, 1)
        records.append(row)
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def plot_roles_heatmap(profiles: pd.DataFrame, output_path: Path) -> None:
    role_cols = [f"pct_{r}" for r in ROLES]
    col_labels = [r.replace("_", "\n") for r in ROLES]

    pivot = profiles.set_index("country_iso3")[role_cols].copy()
    pivot.columns = col_labels

    # Annotate row labels with bloc
    row_labels = [
        f"{iso} ({profiles.loc[profiles['country_iso3']==iso,'bloc'].values[0][:3]})"
        for iso in pivot.index
    ]
    pivot.index = row_labels

    plt.style.use(FIGURE_STYLE)
    fig, ax = plt.subplots(figsize=(15, max(6, len(pivot) * 0.38)))
    sns.heatmap(
        pivot, ax=ax, cmap="YlOrRd", annot=True, fmt=".0f",
        linewidths=0.3, linecolor="#dddddd",
        cbar_kws={"label": "% of coded segments"},
    )
    ax.set_title(
        "Communicative Role Distribution per Case\n"
        "(% of classified segments; Habermas four-type typology)",
        fontsize=12, pad=10,
    )
    ax.set_xlabel("Role (Habermas type)", fontsize=10)
    ax.set_ylabel("Accused state (bloc)", fontsize=10)
    plt.xticks(fontsize=8)
    plt.yticks(rotation=0, fontsize=8)

    # Add type-coloured header band
    for i, role in enumerate(ROLES):
        ht = ROLES[role]["habermas_type"]
        color = HABERMAS_TYPE_COLORS[ht]
        ax.add_patch(plt.Rectangle((i, -0.6), 1, 0.45,
                     color=color, clip_on=False, transform=ax.transData))

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path.name}")


def plot_habermas_types_by_bloc(profiles: pd.DataFrame, output_path: Path) -> None:
    plt.style.use(FIGURE_STYLE)
    group_order = list(STATE_GROUPS.keys())
    x = np.arange(len(group_order))
    width = 0.18

    fig, ax = plt.subplots(figsize=(11, 5))
    for i, ht in enumerate(HABERMAS_TYPES):
        col = f"pct_{ht}"
        vals = [profiles[profiles["bloc"] == g][col].mean() for g in group_order]
        sems = [profiles[profiles["bloc"] == g][col].sem() for g in group_order]
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, vals, width,
                      label=ht.capitalize(), color=HABERMAS_TYPE_COLORS[ht],
                      yerr=sems, capsize=3, edgecolor="white", alpha=0.9)
        for bar, val in zip(bars, vals):
            if not np.isnan(val) and val > 3:
                ax.text(bar.get_x() + bar.get_width() / 2, val + 1,
                        f"{val:.0f}%", ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels([g.replace(" ", "\n") for g in group_order], fontsize=9)
    ax.set_ylabel("Mean % of segments per case", fontsize=10)
    ax.set_ylim(0, 80)
    ax.legend(title="Habermas type", fontsize=9, title_fontsize=9)
    ax.set_title(
        "Four Types of Action (Habermas, TCA 1981) by Cold War Bloc\n"
        "(accused states; % of classified segments)",
        fontsize=11,
    )
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path.name}")


def plot_roles_by_period(df_segments: pd.DataFrame, output_path: Path) -> None:
    plt.style.use(FIGURE_STYLE)
    available = [p for p in PERIOD_ORDER if p in df_segments["period"].values]
    role_list  = list(ROLES.keys())

    counts = (
        df_segments.groupby(["period", "dominant_role"])
        .size().unstack(fill_value=0)
        .reindex(available)
        .reindex(columns=role_list, fill_value=0)
    )
    pcts = counts.div(counts.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(12, 5))
    bottom = np.zeros(len(pcts))
    for role in role_list:
        vals = pcts[role].values if role in pcts.columns else np.zeros(len(pcts))
        bars = ax.bar(pcts.index, vals, bottom=bottom,
                      color=ROLE_COLORS[role],
                      label=f"{role.replace('_',' ')} [{ROLES[role]['habermas_type'][:4]}]",
                      edgecolor="white", linewidth=0.4)
        for bar, val in zip(bars, vals):
            if val > 7:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.0f}%", ha="center", va="center",
                    fontsize=7, color="white", fontweight="bold",
                )
        bottom += vals

    ax.set_ylabel("% of coded segments", fontsize=10)
    ax.set_ylim(0, 108)
    ax.set_xticks(range(len(pcts.index)))
    ax.set_xticklabels(
        [p.replace(" (", "\n(") for p in pcts.index], rotation=0, fontsize=8,
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12),
              ncol=3, fontsize=7, frameon=False)
    ax.set_title(
        "Communicative Role Distribution by Historical Period\n"
        "(Habermas typology in brackets: comm / norm / dram / stra)",
        fontsize=11,
    )
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path.name}")


def plot_habermas_types_by_period(df_segments: pd.DataFrame, output_path: Path) -> None:
    plt.style.use(FIGURE_STYLE)
    available = [p for p in PERIOD_ORDER if p in df_segments["period"].values]

    counts = (
        df_segments.groupby(["period", "habermas_type"])
        .size().unstack(fill_value=0)
        .reindex(available)
        .reindex(columns=HABERMAS_TYPES, fill_value=0)
    )
    pcts = counts.div(counts.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(11, 5))
    bottom = np.zeros(len(pcts))
    for ht in HABERMAS_TYPES:
        vals = pcts[ht].values if ht in pcts.columns else np.zeros(len(pcts))
        bars = ax.bar(pcts.index, vals, bottom=bottom,
                      color=HABERMAS_TYPE_COLORS[ht],
                      label=ht.capitalize(),
                      edgecolor="white", linewidth=0.5)
        for bar, val in zip(bars, vals):
            if val > 8:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.0f}%", ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold",
                )
        bottom += vals

    ax.set_ylabel("% of coded segments", fontsize=10)
    ax.set_ylim(0, 108)
    ax.set_xticks(range(len(pcts.index)))
    ax.set_xticklabels(
        [p.replace(" (", "\n(") for p in pcts.index], rotation=0, fontsize=8,
    )
    ax.legend(title="Habermas type", fontsize=9, title_fontsize=9)
    ax.set_title(
        "Habermas Action Types by Historical Period\n"
        "(% of classified segments — accused states only)",
        fontsize=11,
    )
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path.name}")


def plot_roles_by_group(df_segments: pd.DataFrame, output_path: Path) -> None:
    plt.style.use(FIGURE_STYLE)
    group_order = list(STATE_GROUPS.keys())
    role_list   = list(ROLES.keys())

    fig, axes = plt.subplots(1, len(group_order), figsize=(16, 6), sharey=True)

    for ax, group in zip(axes, group_order):
        sub = df_segments[df_segments["bloc"] == group]
        if sub.empty:
            ax.set_title(group.replace(" ", "\n"), fontsize=9)
            continue
        counts = sub["dominant_role"].value_counts().reindex(role_list, fill_value=0)
        total  = counts.sum()
        pcts   = counts / total * 100
        colors = [ROLE_COLORS[r] for r in role_list]

        bars = ax.barh(
            [r.replace("_", " ") for r in role_list],
            pcts.values, color=colors, edgecolor="white",
        )
        for bar, val, role in zip(bars, pcts.values, role_list):
            ht_label = ROLES[role]["habermas_type"][:4]
            if val > 2:
                ax.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
                        f"{val:.0f}% [{ht_label}]", va="center", fontsize=7)

        ax.set_title(group.replace(" ", "\n"), fontsize=9, pad=6)
        ax.set_xlim(0, pcts.max() * 1.5 + 5)
        ax.tick_params(axis="y", labelsize=8)

    axes[0].set_xlabel("% of segments", fontsize=9)
    fig.suptitle(
        "Communicative Role Profile by Cold War Bloc\n"
        "(Habermas type in brackets; accused states only)",
        fontsize=11,
    )
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading data…")
    cases = load_cases()
    coded = load_coded_segments()

    print("\n=== 1. Classifying communicative roles (Habermas four-type) ===")
    df = classify_all_segments(coded)

    cases_lookup = cases.set_index(["country_iso3", "year"])
    df["period"] = df.apply(
        lambda r: cases_lookup.at[(r["country_iso3"], r["year"]), "period"]
        if (r["country_iso3"], r["year"]) in cases_lookup.index else "Unknown",
        axis=1,
    )
    df["bloc"] = df.apply(lambda r: resolve_group(r["country_iso3"], r["year"]), axis=1)

    fig_dir = FIGURES_DIR / "roles"
    fig_dir.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    role_score_cols = [f"role_score_{r}" for r in ROLES]
    export_cols = [
        "country_iso3", "year", "period", "bloc",
        "paragraph_id", "manual_strategy_code",
        "dominant_role", "habermas_type",
    ] + role_score_cols
    df[[c for c in export_cols if c in df.columns]].to_csv(
        TABLES_DIR / "communicative_roles.csv", index=False
    )

    print("\n=== 2. Building case profiles ===")
    profiles = build_case_profiles(df, cases)
    profiles.to_csv(TABLES_DIR / "communicative_situation_profiles.csv", index=False)

    print("\nClassification coverage by bloc (% of segments matched by keyword classifier):")
    cov = profiles.groupby("bloc")[["n_segments", "n_classified", "pct_unclassified"]].mean().round(1)
    print(cov.to_string())

    print("\nHabermas type distribution by bloc (% of CLASSIFIED segments):")
    type_cols = [f"pct_{ht}" for ht in HABERMAS_TYPES]
    summary = profiles.groupby("bloc")[type_cols].mean().round(1)
    summary.columns = HABERMAS_TYPES
    print(summary.to_string())

    print("\nRole distribution by bloc:")
    role_cols = [f"pct_{r}" for r in ROLES]
    role_summary = profiles.groupby("bloc")[role_cols].mean().round(1)
    role_summary.columns = list(ROLES.keys())
    print(role_summary.to_string())

    print("\n=== 3. Figures ===")
    if not profiles.empty:
        plot_roles_heatmap(profiles,          fig_dir / "fig1_roles_heatmap.png")
        plot_habermas_types_by_bloc(profiles,  fig_dir / "fig2_habermas_types_by_bloc.png")
    plot_roles_by_period(df,                   fig_dir / "fig3_roles_by_period.png")
    plot_habermas_types_by_period(df,          fig_dir / "fig4_habermas_types_by_period.png")
    plot_roles_by_group(df,                    fig_dir / "fig5_roles_by_group.png")

    print("\n=== Done ===")
    print(f"Tables : {TABLES_DIR}/")
    print(f"Figures: {fig_dir}/")
    print()
    print("Figures produced:")
    print("  fig1 — Role heatmap per case (colour band = Habermas type)")
    print("  fig2 — Four Habermas types by Cold War bloc (bar chart)")
    print("  fig3 — Role distribution by historical period (stacked bars)")
    print("  fig4 — Habermas types by period (stacked bars)")
    print("  fig5 — Role profile per bloc (horizontal bars)")


if __name__ == "__main__":
    main()
