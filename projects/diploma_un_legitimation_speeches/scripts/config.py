"""
Configuration for the UNGDC legitimation analysis pipeline.
All paths and analytical constants are defined here.
"""

from pathlib import Path

PROJECT_DIR = Path(__file__).parents[1]
DATA_DIR = PROJECT_DIR / "data"
SCRIPTS_DIR = PROJECT_DIR / "scripts"
OUTPUT_DIR = PROJECT_DIR / "analysis_output"

CORPUS_ARCHIVE = DATA_DIR / "UNGDC_1946-2025.tar.gz"
SPEAKERS_FILE = DATA_DIR / "Speakers_by_session.xlsx"
CORPUS_INDEX_CACHE = OUTPUT_DIR / "cache" / "corpus_index.pkl"

STRATEGIES_LEXICON = SCRIPTS_DIR / "lexicons" / "strategies.json"
VIOLATIONS_LEXICON = SCRIPTS_DIR / "lexicons" / "violations.json"
VIOLATION_EVENTS = SCRIPTS_DIR / "cases" / "violation_events.csv"

SCREENING_DIR = OUTPUT_DIR / "screening"
CODING_DIR = OUTPUT_DIR / "coding"
TABLES_DIR = OUTPUT_DIR / "tables"
FIGURES_DIR = OUTPUT_DIR / "figures"

# Temporal periods used in trend analysis (Chapter 4)
PERIODS: dict[str, tuple[int, int]] = {
    "Cold War (1946–1989)":            (1946, 1989),
    "Post–Cold War (1990–2001)":       (1990, 2001),
    "Post-9/11 Security Turn (2002–2013)": (2002, 2013),
    "Post-2014 Normative Fragmentation": (2014, 2023),
}

# Violation type labels (Dimension 1, Section 2.3)
VIOLATION_LABELS: dict[str, str] = {
    "use_of_force":         "Use of Force (jus ad bellum)",
    "ihl_violations":       "IHL Violations",
    "human_rights":         "Human Rights Allegations",
    "territorial_integrity":"Territorial Integrity / Sovereignty",
    "treaty_noncompliance": "Treaty / UNSC Non-Compliance",
}

# Legitimation strategy labels (Dimension 2, Section 2.3)
STRATEGY_LABELS: dict[str, str] = {
    "self_defense":         "Self-Defense & Necessity",
    "sovereignty":          "Sovereignty & Non-Interference",
    "denial":               "Denial & Reinterpretation",
    "humanitarian":         "Moral & Humanitarian Framing",
    "counterterrorism":     "Counter-Terrorism & Securitization",
    "whataboutism":         "Whataboutism & Tu Quoque",
    "procedural_legal":     "Procedural-Legal Claims",
    "historical":           "Historical & Existential Narratives",
}

# UN regional groups — restricted to states in the purposive sample
REGIONAL_GROUPS: dict[str, set[str]] = {
    "WEOG":         {"USA", "GBR", "FRA", "ISR", "YUG"},
    "EEG":          {"RUS", "UKR"},
    "ASIA-PACIFIC": {"CHN", "IDN", "VNM", "PRK", "MMR"},
    "ARAB/ME":      {"IRQ", "SAU", "SYR", "IRN"},
    "AFRICA":       {"ZAF", "ETH"},
    "OTHER":        {"TUR", "AZE", "GEO"},
}

# Scoring thresholds
MIN_PARAGRAPH_WORDS = 20
STRATEGY_FLAG_THRESHOLD = 0.013
VIOLATION_FLAG_THRESHOLD = 0.013

# Publication-quality figure settings
FIGURE_DPI = 300
FIGURE_STYLE = "seaborn-v0_8-whitegrid"
FIGURE_PALETTE = "Blues_d"
FIGURE_WIDTH = 10
FIGURE_HEIGHT = 6
