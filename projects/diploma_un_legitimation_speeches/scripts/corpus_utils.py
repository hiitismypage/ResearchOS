"""
Utilities for reading the Harvard UNGDC corpus from its .tar.gz archive.
Builds an in-memory index on first use; subsequent calls read from a pickle cache.
"""

from __future__ import annotations

import pickle
import re
import tarfile
from pathlib import Path
from typing import Optional

import pandas as pd

from config import (
    CORPUS_ARCHIVE,
    CORPUS_INDEX_CACHE,
    SPEAKERS_FILE,
)


def session_from_year(year: int) -> int:
    return year - 1945


def speech_path_in_archive(iso3: str, year: int) -> str:
    session = session_from_year(year)
    return f"TXT/Session {session:02d} - {year}/{iso3}_{session}_{year}.txt"


def build_corpus_index(force_rebuild: bool = False) -> dict[tuple[str, int], str]:
    """
    Returns a mapping {(iso3, year) -> archive_member_path} for every speech
    available in the UNGDC archive.  The result is cached to disk.
    """
    if not force_rebuild and CORPUS_INDEX_CACHE.exists():
        with open(CORPUS_INDEX_CACHE, "rb") as f:
            return pickle.load(f)

    print("Building corpus index (one-time operation)…")
    index: dict[tuple[str, int], str] = {}
    pattern = re.compile(r"TXT/Session \d+ - (\d+)/([A-Z]{3})_\d+_(\d+)\.txt$")

    with tarfile.open(CORPUS_ARCHIVE, "r:gz") as tf:
        for member in tf.getmembers():
            m = pattern.match(member.name)
            if m:
                year = int(m.group(1))
                iso3 = m.group(2)
                index[(iso3, year)] = member.name

    CORPUS_INDEX_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_INDEX_CACHE, "wb") as f:
        pickle.dump(index, f)

    print(f"Index built: {len(index):,} speeches indexed.")
    return index


def load_speech(iso3: str, year: int, index: dict[tuple[str, int], str]) -> Optional[str]:
    """
    Loads and returns the full text of a speech. Returns None if not available.
    Performs basic cleaning: strips BOM, normalises whitespace, rejoins hyphenated line-breaks.
    """
    key = (iso3, year)
    if key not in index:
        return None

    with tarfile.open(CORPUS_ARCHIVE, "r:gz") as tf:
        try:
            member = tf.extractfile(index[key])
            raw = member.read().decode("utf-8", errors="replace")
        except (KeyError, AttributeError):
            return None

    text = raw.lstrip("﻿")
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\n\d{1,3}\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_speakers_metadata() -> pd.DataFrame:
    """
    Loads the Speakers_by_session.xlsx file. Returns an empty DataFrame if unavailable.
    Columns expected: Country, Session, Year, Name, Post.
    """
    if not SPEAKERS_FILE.exists():
        print(f"Warning: speakers file not found at {SPEAKERS_FILE}")
        return pd.DataFrame()
    return pd.read_excel(SPEAKERS_FILE)


def load_sampled_cases(events_path: Path) -> pd.DataFrame:
    df = pd.read_csv(events_path)
    df["session"] = df["year"].apply(session_from_year)
    return df
