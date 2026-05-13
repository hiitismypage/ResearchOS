"""
Main entry point for the UNGDC legitimation analysis pipeline.

Usage:
    python run_analysis.py [--stage STAGE] [--rebuild-index]

Stages:
    screen   — load speeches, score paragraphs, export screening CSV  (default if no manual codes)
    analyze  — load manual codes, compute statistics, generate figures
    full     — run both stages sequentially

The pipeline implements the two-stage methodology described in Chapter 3:
  Stage 1 (screen): automated keyword screening to identify legitimation-relevant passages
  Stage 2 (analyze): statistics and figures from researcher-completed manual codes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    VIOLATION_EVENTS,
    STRATEGIES_LEXICON,
    VIOLATIONS_LEXICON,
    SCREENING_DIR,
    CODING_DIR,
    TABLES_DIR,
    FIGURES_DIR,
    STRATEGY_FLAG_THRESHOLD,
    VIOLATION_FLAG_THRESHOLD,
    MIN_PARAGRAPH_WORDS,
)
from corpus_utils import build_corpus_index, load_speech, load_sampled_cases
from coding_utils import load_lexicon, code_speech
from analysis_utils import (
    build_frequency_table,
    build_cooccurrence_matrix,
    build_temporal_trends,
    build_regional_distribution,
    plot_strategy_frequencies,
    plot_violation_frequencies,
    plot_cooccurrence_heatmap,
    plot_temporal_trends,
    plot_temporal_trends_stacked,
    plot_regional_distribution,
    export_tables,
)


MANUAL_CODES_PATH = CODING_DIR / "manual_codes.csv"
SCREENING_CSV = SCREENING_DIR / "passages_for_screening.csv"


def run_screening(cases: pd.DataFrame, rebuild_index: bool) -> None:
    print("\n=== Stage 1: Corpus screening ===\n")

    index = build_corpus_index(force_rebuild=rebuild_index)
    violation_lex = load_lexicon(VIOLATIONS_LEXICON)
    strategy_lex = load_lexicon(STRATEGIES_LEXICON)

    all_records = []
    missing = []

    for _, row in cases.iterrows():
        iso3 = row["country_iso3"]
        year = int(row["year"])

        text = load_speech(iso3, year, index)
        if text is None:
            missing.append(f"{iso3} {year}")
            print(f"  [MISSING] {iso3} {year} — no speech file in corpus")
            continue

        records = code_speech(
            text,
            violation_lex,
            strategy_lex,
            min_words=MIN_PARAGRAPH_WORDS,
            violation_threshold=VIOLATION_FLAG_THRESHOLD,
            strategy_threshold=STRATEGY_FLAG_THRESHOLD,
        )
        for r in records:
            r["country_iso3"] = iso3
            r["year"] = year
            r["period"] = row["period"]
            r["allegation"] = row["allegation_description"]
        all_records.extend(records)

        flagged = sum(1 for r in records if r["flagged_for_review"])
        print(f"  {iso3} {year}: {len(records)} paragraphs, {flagged} flagged")

    if not all_records:
        print("\nNo records produced. Check that the corpus archive is accessible.")
        return

    df = pd.DataFrame(all_records)
    col_order = [
        "country_iso3", "year", "period", "allegation", "paragraph_id",
        "word_count", "flagged_for_review",
        "suggested_violation", "violation_score", "violation_matches",
        "suggested_strategy", "strategy_score", "strategy_matches",
        "manual_violation_code", "manual_strategy_code", "coder_notes",
        "paragraph_text",
    ]
    df = df[[c for c in col_order if c in df.columns]]

    SCREENING_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(SCREENING_CSV, index=False, encoding="utf-8-sig")

    flagged_total = df["flagged_for_review"].sum()
    print(f"\n  Total paragraphs screened: {len(df):,}")
    print(f"  Flagged for manual review: {flagged_total:,} "
          f"({100 * flagged_total / max(len(df), 1):.1f}%)")
    print(f"\n  Screening output: {SCREENING_CSV}")

    if missing:
        print(f"\n  Missing speeches ({len(missing)}): {', '.join(missing)}")

    print("\n--- Next step (manual coding) ---")
    print(f"  Open {SCREENING_CSV} in Excel or any CSV editor.")
    print("  For each flagged row, fill in the columns:")
    print("    manual_violation_code  — one of:", list(violation_lex.keys()))
    print("    manual_strategy_code   — one of:", list(strategy_lex.keys()))
    print("    coder_notes            — optional free-text notes")
    print("  Save the file to:")
    print(f"    {MANUAL_CODES_PATH}")
    print("  Then run: python run_analysis.py --stage analyze")


def run_analysis() -> None:
    print("\n=== Stage 2: Statistical analysis ===\n")

    if not MANUAL_CODES_PATH.exists():
        print(f"Manual codes file not found: {MANUAL_CODES_PATH}")
        print("Complete Stage 1 (screening) and fill in manual codes first.")
        sys.exit(1)

    coded = pd.read_csv(MANUAL_CODES_PATH, encoding="utf-8-sig")
    coded["manual_violation_code"] = coded["manual_violation_code"].fillna("")
    coded["manual_strategy_code"] = coded["manual_strategy_code"].fillna("")

    cases = load_sampled_cases(VIOLATION_EVENTS)

    coded_subset = coded[
        (coded["manual_violation_code"] != "") | (coded["manual_strategy_code"] != "")
    ]

    if coded_subset.empty:
        print("No manually coded passages found. Fill in the manual_codes columns and retry.")
        sys.exit(1)

    print(f"  Loaded {len(coded):,} passages; {len(coded_subset):,} with manual codes.\n")

    print("Computing frequency tables…")
    freqs = build_frequency_table(coded_subset)
    print(f"  Strategies: {len(freqs['strategies'])} categories coded")
    print(f"  Violations: {len(freqs['violations'])} categories coded")

    print("\nComputing co-occurrence matrix…")
    matrix = build_cooccurrence_matrix(coded_subset)

    print("\nComputing temporal trends…")
    trends = build_temporal_trends(coded_subset, cases)

    print("\nComputing regional distribution…")
    regional = build_regional_distribution(coded_subset, cases)

    print("\nExporting tables…")
    export_tables(freqs, matrix, trends, TABLES_DIR)

    print("\nGenerating figures…")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    if not freqs["strategies"].empty:
        plot_strategy_frequencies(freqs["strategies"], FIGURES_DIR / "fig1_strategy_frequencies.png")

    if not freqs["violations"].empty:
        plot_violation_frequencies(freqs["violations"], FIGURES_DIR / "fig2_violation_frequencies.png")

    plot_cooccurrence_heatmap(matrix, FIGURES_DIR / "fig3_cooccurrence_heatmap.png")
    plot_temporal_trends(trends, FIGURES_DIR / "fig4_temporal_trends_line.png")
    plot_temporal_trends_stacked(trends, FIGURES_DIR / "fig5_temporal_trends_stacked.png")
    plot_regional_distribution(regional, FIGURES_DIR / "fig6_regional_distribution.png")

    print(f"\n  All outputs saved to: {FIGURES_DIR.parent}/")
    print("  Tables : tables/")
    print("  Figures: figures/  (fig1–fig6)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UNGDC legitimation analysis pipeline (Chapter 3–4 methodology)"
    )
    parser.add_argument(
        "--stage",
        choices=["screen", "analyze", "full"],
        default=None,
        help="Pipeline stage to run (default: auto-detect based on file state)",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Force rebuild of the corpus index cache",
    )
    args = parser.parse_args()

    cases = load_sampled_cases(VIOLATION_EVENTS)
    print(f"Purposive sample loaded: {len(cases)} state-year cases")

    stage = args.stage
    if stage is None:
        stage = "analyze" if MANUAL_CODES_PATH.exists() else "screen"
        print(f"Auto-detected stage: {stage}")

    if stage in ("screen", "full"):
        run_screening(cases, rebuild_index=args.rebuild_index)

    if stage in ("analyze", "full"):
        run_analysis()


if __name__ == "__main__":
    main()
