"""
Paragraph segmentation and keyword-based scoring for the two-dimensional coding framework.

Scoring is normalized: score(category, paragraph) = matched_phrase_count / paragraph_word_count.
This rewards specificity over length and makes scores comparable across paragraphs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_lexicon(path: Path) -> dict[str, list[str]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def segment_speech(
    text: str,
    min_words: int = 20,
    target_words: int = 120,
) -> list[str]:
    """
    Segments speech text into analysis units of approximately target_words each.

    UNGDC texts use single newlines for line-wrapping (not paragraph breaks),
    so we do not rely on blank lines.  Instead the text is joined into one string,
    split into sentences at terminal punctuation, then grouped into ~120-word
    chunks that serve as the "argumentative segments" described in Chapter 3.
    """
    # Join soft line-wraps; remove stray page-number lines
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r" {2,}", " ", text)

    # Sentence boundary: terminal punct followed by whitespace + capital letter
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)

    segments: list[str] = []
    current: list[str] = []

    for sent in sentences:
        words = sent.split()
        current.extend(words)
        if len(current) >= target_words:
            segments.append(" ".join(current))
            current = []

    if len(current) >= min_words:
        segments.append(" ".join(current))

    return segments


def _count_phrase_matches(text: str, phrases: list[str]) -> tuple[int, list[str]]:
    text_lower = text.lower()
    matched: list[str] = []
    for phrase in phrases:
        if phrase.lower() in text_lower:
            matched.append(phrase)
    return len(matched), matched


def score_paragraph(
    paragraph: str,
    lexicon: dict[str, list[str]],
) -> dict[str, Any]:
    """
    Returns a dict with keys = category names; values = dicts with
    'score' (float), 'count' (int), 'matches' (list[str]).
    """
    word_count = max(len(paragraph.split()), 1)
    results: dict[str, Any] = {}

    for category, phrases in lexicon.items():
        count, matches = _count_phrase_matches(paragraph, phrases)
        score = count / word_count
        results[category] = {
            "score": round(score, 6),
            "count": count,
            "matches": matches,
        }

    return results


def top_category(scores: dict[str, Any]) -> tuple[str, float]:
    """Returns the category with the highest score and its score value."""
    best = max(scores.items(), key=lambda kv: kv[1]["score"])
    return best[0], best[1]["score"]


def code_speech(
    text: str,
    violation_lexicon: dict[str, list[str]],
    strategy_lexicon: dict[str, list[str]],
    min_words: int = 20,
    violation_threshold: float = 0.04,
    strategy_threshold: float = 0.04,
) -> list[dict[str, Any]]:
    """
    Segments a speech and scores each paragraph against both lexicons.
    Returns a list of paragraph-level records ready for CSV export.
    """
    paragraphs = segment_speech(text, min_words=min_words)
    records: list[dict[str, Any]] = []

    for idx, para in enumerate(paragraphs):
        v_scores = score_paragraph(para, violation_lexicon)
        s_scores = score_paragraph(para, strategy_lexicon)

        top_v, top_v_score = top_category(v_scores)
        top_s, top_s_score = top_category(s_scores)

        flagged = (top_v_score >= violation_threshold) or (top_s_score >= strategy_threshold)

        records.append({
            "paragraph_id": idx,
            "paragraph_text": para,
            "word_count": len(para.split()),
            "suggested_violation": top_v if top_v_score >= violation_threshold else "",
            "violation_score": top_v_score,
            "violation_matches": "; ".join(v_scores[top_v]["matches"]) if top_v_score > 0 else "",
            "suggested_strategy": top_s if top_s_score >= strategy_threshold else "",
            "strategy_score": top_s_score,
            "strategy_matches": "; ".join(s_scores[top_s]["matches"]) if top_s_score > 0 else "",
            "flagged_for_review": flagged,
            "manual_violation_code": "",
            "manual_strategy_code": "",
            "coder_notes": "",
        })

    return records
