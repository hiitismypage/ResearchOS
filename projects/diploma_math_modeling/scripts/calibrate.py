#!/usr/bin/env python3
"""
Calibration and parameterisation script for a two-level agent-based
input-output model of a five-sector economy.

Usage:
    python calibrate.py estat_naio_10_cp1700.csv Балашова_Германия.xlsx \
        --country DE --year 2015 --output calibration_output
"""

import argparse
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import openpyxl
import numpy as np
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# SECTOR DEFINITIONS  — only place where sector metadata lives
# ─────────────────────────────────────────────────────────────────────────────

SECTOR_MAP: Dict[int, Dict] = {
    1: {
        "name": "Extraction",
        "codes": ["CPA_B"],
        "delta_mult": 1.2,
        "theta_lo": 0.7,
        "theta_hi": 1.3,
    },
    2: {
        "name": "Energy",
        "codes": ["CPA_D"],
        "delta_mult": 0.8,
        "theta_lo": 0.7,
        "theta_hi": 1.3,
    },
    3: {
        "name": "Manufacturing",
        "codes": [
            "CPA_C10-12", "CPA_C13-15", "CPA_C16", "CPA_C17", "CPA_C18",
            "CPA_C19", "CPA_C20", "CPA_C21", "CPA_C22", "CPA_C23", "CPA_C24",
            "CPA_C25", "CPA_C26", "CPA_C27", "CPA_C28", "CPA_C29", "CPA_C30",
            "CPA_C31_32", "CPA_C33",
        ],
        "delta_mult": 1.1,
        "theta_lo": 0.5,
        "theta_hi": 1.5,
    },
    4: {
        "name": "Construction",
        "codes": ["CPA_F"],
        "delta_mult": 1.3,
        "theta_lo": 0.6,
        "theta_hi": 1.4,
    },
    5: {
        "name": "Agriculture",
        "codes": ["CPA_A01", "CPA_A02", "CPA_A03"],
        "delta_mult": 1.0,
        "theta_lo": 0.5,
        "theta_hi": 1.5,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────


def _ts(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def _code_to_sector(sector_map: Dict) -> Dict[str, int]:
    """Return {CPA_code: sector_id (1-indexed)}."""
    mapping: Dict[str, int] = {}
    for sid, info in sector_map.items():
        for code in info["codes"]:
            mapping[code] = sid
    return mapping


# ─────────────────────────────────────────────────────────────────────────────
# IO TABLE PARSING
# ─────────────────────────────────────────────────────────────────────────────


def parse_io_table(
    csv_path: str,
    country_iso: str,
    year: int,
    stk_flow: str = "TOTAL",
) -> pd.DataFrame:
    """
    Parse Eurostat symmetric IO table CSV for one country and year.
    CSV format: comma-delimited metadata (freq,unit,stk_flow,prd_use,prd_ava),
    then a tab-delimited block starting with geo code followed by annual values.
    stk_flow: 'DOM' (domestic), 'IMP' (imported), or 'TOTAL' (default).
    Returns long-format DataFrame with columns [prd_use, prd_ava, value].
    """
    with open(csv_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    # Parse year positions from header
    header_tab = lines[0].rstrip("\n").split(",", 5)[5]
    year_fields = header_tab.split("\t")[1:]  # skip "geo\TIME_PERIOD"
    available_years: List[int] = []
    for yf in year_fields:
        try:
            available_years.append(int(yf.strip()))
        except ValueError:
            pass

    if year not in available_years:
        raise ValueError(
            f"Year {year} not in IO table. Available: {available_years}"
        )
    year_tab_idx = available_years.index(year) + 1  # +1: tab[0] is geo

    seen: set = set()  # deduplicate (prd_use, prd_ava) within a stk_flow filter
    records = []
    for line in lines[1:]:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split(",", 5)
        if len(parts) < 6:
            continue
        if parts[2].strip() != stk_flow:
            continue
        prd_use = parts[3].strip()
        prd_ava = parts[4].strip()
        tab_fields = parts[5].split("\t")
        if tab_fields[0].strip() != country_iso:
            continue
        key = (prd_use, prd_ava)
        if key in seen:
            continue
        seen.add(key)
        if year_tab_idx >= len(tab_fields):
            value = np.nan
        else:
            raw = tab_fields[year_tab_idx].strip()
            if not raw or raw.startswith(":"):
                value = np.nan
            else:
                try:
                    value = float(raw.split()[0])
                except (ValueError, IndexError):
                    value = np.nan
        records.append({"prd_use": prd_use, "prd_ava": prd_ava, "value": value})

    return pd.DataFrame(records, columns=["prd_use", "prd_ava", "value"])


def _parse_io_multi(
    csv_path: str,
    country_iso: str,
    years: List[int],
    stk_flow: str = "TOTAL",
) -> Dict[int, pd.DataFrame]:
    """
    Parse IO table for multiple years in a single file pass.
    Filters to stk_flow (default 'TOTAL') and deduplicates (prd_use, prd_ava).
    Returns {year: DataFrame[prd_use, prd_ava, value]}.
    """
    with open(csv_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    header_tab = lines[0].rstrip("\n").split(",", 5)[5]
    year_fields = header_tab.split("\t")[1:]
    all_years: List[int] = []
    for yf in year_fields:
        try:
            all_years.append(int(yf.strip()))
        except ValueError:
            pass

    year_tab_idx = {yr: all_years.index(yr) + 1 for yr in years if yr in all_years}
    records: Dict[int, List[Dict]] = {yr: [] for yr in year_tab_idx}
    seen: set = set()

    for line in lines[1:]:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split(",", 5)
        if len(parts) < 6:
            continue
        if parts[2].strip() != stk_flow:
            continue
        prd_use = parts[3].strip()
        prd_ava = parts[4].strip()
        tab_fields = parts[5].split("\t")
        if tab_fields[0].strip() != country_iso:
            continue
        key = (prd_use, prd_ava)
        if key in seen:
            continue
        seen.add(key)
        for yr, ti in year_tab_idx.items():
            if ti >= len(tab_fields):
                value = np.nan
            else:
                raw = tab_fields[ti].strip()
                if not raw or raw.startswith(":"):
                    value = np.nan
                else:
                    try:
                        value = float(raw.split()[0])
                    except (ValueError, IndexError):
                        value = np.nan
            records[yr].append({"prd_use": prd_use, "prd_ava": prd_ava, "value": value})

    return {
        yr: pd.DataFrame(recs, columns=["prd_use", "prd_ava", "value"])
        for yr, recs in records.items()
    }


# ─────────────────────────────────────────────────────────────────────────────
# MATRIX CONSTRUCTORS
# ─────────────────────────────────────────────────────────────────────────────


def build_Z_matrix(df: pd.DataFrame, sector_map: Dict) -> np.ndarray:
    """
    5×5 intermediate flow matrix.
    In Eurostat layout: prd_ava=row (supplied product i), prd_use=column (production sector j).
    Z[i,j] = supply of product i used by sector j; a_{ij} = Z[i,j]/X[j].
    """
    n = len(sector_map)
    Z = np.zeros((n, n))
    c2s = _code_to_sector(sector_map)
    cpa_set = set(c2s.keys())

    sub = df[df["prd_use"].isin(cpa_set) & df["prd_ava"].isin(cpa_set)].dropna(
        subset=["value"]
    )
    for row in sub.itertuples(index=False):
        i = c2s[row.prd_ava] - 1   # row = supplied product (prd_ava)
        j = c2s[row.prd_use] - 1   # col = production sector (prd_use)
        Z[i, j] += row.value
    return Z


def build_X_vector(df: pd.DataFrame, sector_map: Dict) -> np.ndarray:
    """Gross output vector X of length 5 from prd_ava='P1' rows."""
    n = len(sector_map)
    X = np.zeros(n)
    c2s = _code_to_sector(sector_map)

    sub = df[(df["prd_ava"] == "P1") & df["prd_use"].isin(c2s)].dropna(
        subset=["value"]
    )
    for row in sub.itertuples(index=False):
        j = c2s[row.prd_use] - 1
        X[j] += row.value
    return X


def build_u_vector(df: pd.DataFrame, sector_map: Dict) -> np.ndarray:
    """
    Final demand vector u = C + G + NX of length 5.
    C=P3_S14, G=P3_S13, NX=P6−P7; all indexed by prd_ava=CPA code.
    """
    n = len(sector_map)
    c2s = _code_to_sector(sector_map)
    cpa_set = set(c2s.keys())

    C = np.zeros(n)
    G = np.zeros(n)
    Ex = np.zeros(n)
    Im = np.zeros(n)

    fd_arrays = {"P3_S14": C, "P3_S13": G, "P6": Ex, "P7": Im}
    sub = df[df["prd_ava"].isin(cpa_set) & df["prd_use"].isin(fd_arrays)].dropna(
        subset=["value"]
    )
    for row in sub.itertuples(index=False):
        j = c2s[row.prd_ava] - 1
        fd_arrays[row.prd_use][j] += row.value

    return C + G + (Ex - Im)


def build_Q_matrix(
    df: pd.DataFrame, sector_map: Dict, X: np.ndarray
) -> np.ndarray:
    """
    5×5 capital requirement matrix.
    GFCF by product i (P51G rows, prd_ava=CPA code) distributed to sectors j
    proportional to gross output shares: Q[i,j] = GFCF_i * (X_j / sum X).
    """
    n = len(sector_map)
    c2s = _code_to_sector(sector_map)
    cpa_set = set(c2s.keys())

    gfcf = np.zeros(n)
    sub = df[(df["prd_use"] == "P51G") & df["prd_ava"].isin(cpa_set)].dropna(
        subset=["value"]
    )
    for row in sub.itertuples(index=False):
        i = c2s[row.prd_ava] - 1
        gfcf[i] += row.value

    X_total = X.sum()
    w = X / X_total if X_total > 0 else np.ones(n) / n
    return np.outer(gfcf, w)


def compute_A(Z: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Direct requirements matrix: A[i,j] = Z[i,j] / X[j]."""
    X_safe = np.where(X > 0, X, 1.0)
    return Z / X_safe[np.newaxis, :]


def compute_B(
    Q: np.ndarray,
    dX: np.ndarray,
    epsilon: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Capital requirements matrix B[i,j] = Q[i,j] / |dX[j]|.
    Uses absolute value of dX to guarantee B >= 0 (sectors with declining output
    still require capital investment; the sign of growth is irrelevant for
    capital requirements).  Near-zero |dX[j]| floored at epsilon.
    Returns (B, B_plus) where B_plus is the Moore-Penrose pseudoinverse.
    B_plus equals inv(B) when B is full-rank; pseudoinverse otherwise.
    """
    dX_abs  = np.abs(dX)
    dX_safe = np.where(dX_abs > epsilon, dX_abs, epsilon)
    B = Q / dX_safe[np.newaxis, :]

    rank = np.linalg.matrix_rank(B)
    if rank < B.shape[0]:
        B_plus = np.linalg.pinv(B)
    else:
        try:
            B_plus = np.linalg.inv(B)
        except np.linalg.LinAlgError:
            B_plus = np.linalg.pinv(B)

    return B, B_plus


# ─────────────────────────────────────────────────────────────────────────────
# MACRO PARAMETER LOADING
# ─────────────────────────────────────────────────────────────────────────────


def load_macro_params(xlsx_path: str) -> dict:
    """
    Load calibration scalars and time series from Excel workbook.
    Returns dict with keys: Am, alpha, beta, TFP_growth, MPS, g, m,
    K_series, Y_series, I_series (pd.Series indexed by year),
    GVA_series (empty dict — populated by calibrate_sector_params).
    """
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["Эконом рост"]
    sg = list(ws.iter_rows(values_only=True))

    def _scalar(row_1idx: int, col_1idx: int = 2) -> float:
        val = sg[row_1idx - 1][col_1idx - 1]
        return float(val) if isinstance(val, (int, float)) and val is not None else np.nan

    TFP_growth = _scalar(7)   # delta_a  row 7  col B
    alpha      = _scalar(8)   # α        row 8
    beta       = _scalar(9)   # β        row 9
    m_import   = _scalar(12)  # m        row 12
    Am         = _scalar(16)  # Am (δ)   row 16
    MPS        = _scalar(17)  # MPS      row 17
    g          = _scalar(25)  # g        row 25

    # Build year → column-index map from header row 1
    header = sg[0]
    year_col: Dict[int, int] = {}
    for ci, val in enumerate(header):
        if isinstance(val, (int, float)) and val is not None and 1990 <= val <= 2100:
            year_col[int(val)] = ci

    def _series(row_1idx: int) -> pd.Series:
        row = sg[row_1idx - 1]
        data: Dict[int, float] = {}
        for yr, ci in year_col.items():
            if ci < len(row):
                v = row[ci]
                data[yr] = float(v) if isinstance(v, (int, float)) and v is not None else np.nan
        return pd.Series(data, dtype=float).sort_index()

    K_series = _series(5)   # capital stock
    Y_series = _series(2)   # real GDP
    I_series = _series(11)  # real investment

    wb.close()
    return {
        "TFP_growth": TFP_growth,
        "alpha":      alpha,
        "beta":       beta,
        "m":          m_import,
        "Am":         Am,
        "MPS":        MPS,
        "g":          g,
        "K_series":   K_series,
        "Y_series":   Y_series,
        "I_series":   I_series,
        "GVA_series": {},
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTOR PARAMETER CALIBRATION
# ─────────────────────────────────────────────────────────────────────────────


def calibrate_sector_params(
    io_df: pd.DataFrame,
    macro: dict,
    sector_map: Dict,
    year_range: Tuple[int, int],
    io_csv_path: Optional[str] = None,
    country_iso: Optional[str] = None,
) -> dict:
    """
    Calibrate sector-level behavioural parameters as averages over year_range.
    Populates macro['GVA_series'] as a side-effect.
    Returns dict of length-5 arrays: delta_j, nu_j, kappa_j, eta_j,
    alpha_j, p_inn_j, mu_j, plus internal _* keys used downstream.
    """
    n = len(sector_map)
    c2s = _code_to_sector(sector_map)
    cpa_set = set(c2s.keys())
    yr0, yr1 = year_range
    years = list(range(yr0, yr1 + 1))

    # Load multi-year IO data
    if io_csv_path and country_iso:
        dfs = _parse_io_multi(io_csv_path, country_iso, years)
    else:
        dfs = {yr: io_df for yr in years}

    def _sector_col(df: pd.DataFrame, prd_ava_code: str) -> np.ndarray:
        """Sum values by sector: prd_ava == code, prd_use in CPA."""
        vec = np.zeros(n)
        sub = df[
            (df["prd_ava"] == prd_ava_code) & df["prd_use"].isin(cpa_set)
        ].dropna(subset=["value"])
        for row in sub.itertuples(index=False):
            vec[c2s[row.prd_use] - 1] += row.value
        return vec

    def _sector_row(df: pd.DataFrame, prd_use_code: str) -> np.ndarray:
        """Sum values by sector: prd_use == code, prd_ava in CPA."""
        vec = np.zeros(n)
        sub = df[
            (df["prd_use"] == prd_use_code) & df["prd_ava"].isin(cpa_set)
        ].dropna(subset=["value"])
        for row in sub.itertuples(index=False):
            vec[c2s[row.prd_ava] - 1] += row.value
        return vec

    ny = len(years)
    GVA_ts  = np.zeros((ny, n))
    D1_ts   = np.zeros((ny, n))
    GFCF_ts = np.zeros((ny, n))
    X_ts    = np.zeros((ny, n))

    for t_i, yr in enumerate(years):
        df_yr = dfs.get(yr, io_df)
        GVA_ts[t_i]  = _sector_col(df_yr, "B1G")
        D1_ts[t_i]   = _sector_col(df_yr, "D1")
        GFCF_ts[t_i] = _sector_row(df_yr, "P51G")
        X_ts[t_i]    = build_X_vector(df_yr, sector_map)

    GVA_avg  = np.nanmean(GVA_ts,  axis=0)
    D1_avg   = np.nanmean(D1_ts,   axis=0)
    GFCF_avg = np.nanmean(GFCF_ts, axis=0)
    X_avg    = np.nanmean(X_ts,    axis=0)

    # Populate GVA_series in macro dict
    for j_idx, sid in enumerate(sorted(sector_map.keys())):
        macro["GVA_series"][sid] = pd.Series(
            {yr: GVA_ts[t_i, j_idx] for t_i, yr in enumerate(years)}, dtype=float
        )

    # delta_j
    Am = macro["Am"]
    delta_j = np.array([Am * sector_map[sid]["delta_mult"] for sid in sorted(sector_map)])

    # nu_j = X_j / K_j;  K_j distributed by GVA share
    K_series = macro["K_series"]
    k_years = [yr for yr in years if yr in K_series.index and not np.isnan(K_series[yr])]
    K_total = float(np.mean([K_series[yr] for yr in k_years])) if k_years else 0.0
    gva_total = float(GVA_avg.sum())
    gva_shares = GVA_avg / gva_total if gva_total > 0 else np.ones(n) / n
    K_j = gva_shares * K_total
    nu_j = X_avg / np.where(K_j > 0, K_j, 1.0)

    # kappa_j = I_j / max(π_j, ε), clipped [0.05, 0.45]
    pi_j = GVA_avg - D1_avg
    eps_pi = 1e-3 * max(float(np.nanmean(X_avg[X_avg > 0])), 1.0) if (X_avg > 0).any() else 1e-3
    kappa_j = np.clip(GFCF_avg / np.maximum(pi_j, eps_pi), 0.05, 0.45)

    # eta_j: η_j * mean(X_j) ≈ 0.10 * I_j, clipped [0.01, 0.25]
    X_safe = np.where(X_avg > 0, X_avg, 1.0)
    eta_j = np.clip(0.10 * GFCF_avg / X_safe, 0.01, 0.25)

    # alpha_j = 1 − vol_j / mean_vol, clipped [0.3, 0.9]
    X_growth = np.diff(X_ts, axis=0) / np.where(X_ts[:-1] > 0, X_ts[:-1], 1.0)
    vol_j = np.nanstd(X_growth, axis=0)
    mean_vol = float(np.nanmean(vol_j))
    alpha_j = np.clip(1.0 - vol_j / (mean_vol if mean_vol > 0 else 1e-6), 0.3, 0.9)

    # p_inn_j
    kappa_max = float(kappa_j.max()) if kappa_j.max() > 0 else 1.0
    p_inn_j = 0.05 + 0.15 * (1.0 - kappa_j / kappa_max)

    # mu_j = 0.01 + 0.04 * (GVA_j / X_j), clipped [0.01, 0.05]
    mu_j = np.clip(0.01 + 0.04 * (GVA_avg / X_safe), 0.01, 0.05)

    return {
        "delta_j": delta_j,
        "nu_j":    nu_j,
        "kappa_j": kappa_j,
        "eta_j":   eta_j,
        "alpha_j": alpha_j,
        "p_inn_j": p_inn_j,
        "mu_j":    mu_j,
        "_K_j":      K_j,
        "_GVA_avg":  GVA_avg,
        "_X_avg":    X_avg,
        "_GFCF_avg": GFCF_avg,
        "_D1_avg":   D1_avg,
        "_X_ts":     X_ts,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FIRM-LEVEL DISTRIBUTIONS
# ─────────────────────────────────────────────────────────────────────────────


def generate_firm_distributions(
    sector_params: dict,
    macro: dict,
    N_firms: List[int],
    A0: np.ndarray,
    B0: np.ndarray,
    sector_map: Dict,
    seed: int = 42,
) -> dict:
    """
    Draw initial firm-level distributions for each sector.
    Returns dict: k0, theta0, omega0, a_f0, c_f, gamma_f
    — each a list of N_j arrays (one per sector).
    """
    rng = np.random.default_rng(seed)
    n = len(sector_map)
    sigma_a = 0.15
    sigma_k = 0.6

    K_j  = sector_params["_K_j"]
    nu_j = sector_params["nu_j"]

    k0_list:      List[np.ndarray] = []
    theta0_list:  List[np.ndarray] = []
    omega0_list:  List[np.ndarray] = []
    a_f0_list:    List[np.ndarray] = []
    c_f_list:     List[np.ndarray] = []
    gamma_f_list: List[np.ndarray] = []

    for j_idx, sid in enumerate(sorted(sector_map.keys())):
        N_j   = N_firms[j_idx]
        K_val = float(K_j[j_idx])
        info  = sector_map[sid]
        lo, hi = info["theta_lo"], info["theta_hi"]

        # k_{jf} ~ LogNormal, renormalised to sum == K_j
        mu_k  = np.log(max(K_val / N_j, 1e-12)) - 0.5 * sigma_k ** 2
        raw_k = rng.lognormal(mu_k, sigma_k, N_j)
        k_jf  = raw_k * (K_val / raw_k.sum()) if raw_k.sum() > 0 else raw_k

        # θ ~ Uniform(lo, hi)
        theta_jf = rng.uniform(lo, hi, N_j)

        # ω: market shares proportional to capital
        omega_jf = k_jf / (k_jf.sum() + 1e-300)

        # a_{ij}^(f): idiosyncratic spread, renormalised so
        # Σ_f omega_f * a_{ij}^(f) = A0[i,j]  (output-weighted aggregate)
        a_f = np.zeros((n, N_j))
        for i_idx in range(n):
            xi = rng.standard_normal(N_j)
            a_f[i_idx] = A0[i_idx, j_idx] * np.exp(sigma_a * xi)

        for i_idx in range(n):
            agg = float(np.dot(omega_jf, a_f[i_idx]))
            if agg > 1e-300:
                a_f[i_idx] *= A0[i_idx, j_idx] / agg
            # if A0[i,j] == 0, leave at zero (no flow)

        # c_{jf} = 0.02 * p_j * x̄_{jf};  p_j = 1 (normalised)
        theta_mean = (lo + hi) / 2.0
        x_bar_jf   = nu_j[j_idx] * theta_mean * k_jf
        c_jf       = 0.02 * x_bar_jf

        # γ_{ij}^(f): investment allocation; same for all firms in sector j
        b_col = B0[:, j_idx]
        a_col = A0[:, j_idx]
        weights = np.maximum(b_col, 0.0) if b_col.sum() > 0 else np.maximum(a_col, 0.0)
        w_sum   = weights.sum()
        gamma_j = weights / w_sum if w_sum > 0 else np.ones(n) / n
        gamma_f_j = np.tile(gamma_j[:, np.newaxis], (1, N_j))  # (n, N_j)

        k0_list.append(k_jf)
        theta0_list.append(theta_jf)
        omega0_list.append(omega_jf)
        a_f0_list.append(a_f)
        c_f_list.append(c_jf)
        gamma_f_list.append(gamma_f_j)

    return {
        "k0":      k0_list,
        "theta0":  theta0_list,
        "omega0":  omega0_list,
        "a_f0":    a_f0_list,
        "c_f":     c_f_list,
        "gamma_f": gamma_f_list,
    }


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────────────────────


def validate_model(
    A: np.ndarray,
    B: np.ndarray,
    B_plus: np.ndarray,
    u: np.ndarray,
    X: np.ndarray,
    sector_params: dict,
    firm_dist: dict,
) -> dict:
    """
    Consistency checks. Returns {check_name: (pass:bool, magnitude:float)}.
    Prints WARNING for every failed check.
    """
    eps = 1e-6
    results: Dict[str, Tuple[bool, float]] = {}

    # 1. ρ(A) < 1
    rho_A = float(np.max(np.abs(np.linalg.eigvals(A))))
    ok1 = rho_A < 1.0
    results["rho_A_lt_1"] = (ok1, rho_A)
    if not ok1:
        print(f"WARNING: [rho_A_lt_1] ρ(A) = {rho_A:.6f} ≥ 1. Leontief inverse may not exist.")

    # 2. Static balance  X ≈ A·X + u
    resid_X = np.linalg.norm(X - (A @ X + u))
    X_norm  = max(np.linalg.norm(X), 1e-12)
    rel_bal = resid_X / X_norm
    ok2 = rel_bal < eps
    results["static_balance"] = (ok2, rel_bal)
    if not ok2:
        print(f"WARNING: [static_balance] relative residual = {rel_bal:.4e}")

    # 3. Market shares sum to 1
    max_omega_err = max(abs(float(omega.sum()) - 1.0) for omega in firm_dist["omega0"])
    ok3 = max_omega_err < eps
    results["omega_sum_1"] = (ok3, max_omega_err)
    if not ok3:
        print(f"WARNING: [omega_sum_1] max |Σω − 1| = {max_omega_err:.4e}")

    # 4. B_plus · B · B_plus ≈ B_plus  (pseudoinverse property)
    B_norm = np.linalg.norm(B_plus) + 1e-12
    bpbp_err = np.linalg.norm(B_plus @ B @ B_plus - B_plus) / B_norm
    ok4 = bpbp_err < 1e-6
    results["B_plus_consistent"] = (ok4, bpbp_err)
    if not ok4:
        print(f"WARNING: [B_plus_consistent] ‖B⁺BB⁺ − B⁺‖/‖B⁺‖ = {bpbp_err:.4e}")

    # 5. Parameter range checks
    sp = sector_params
    range_checks = {
        "kappa_j_range": (sp["kappa_j"], 0.05, 0.45),
        "eta_j_range":   (sp["eta_j"],   0.01, 0.25),
        "alpha_j_range": (sp["alpha_j"], 0.30, 0.90),
        "mu_j_range":    (sp["mu_j"],    0.01, 0.05),
        "nu_j_positive": (sp["nu_j"],    0.0,  np.inf),
        "delta_j_range": (sp["delta_j"], 0.0,  0.30),
    }
    for name, (arr, lo, hi) in range_checks.items():
        lo_viol = float(np.maximum(lo - arr, 0.0).max())
        hi_viol = 0.0 if np.isinf(hi) else float(np.maximum(arr - hi, 0.0).max())
        violation = max(lo_viol, hi_viol)
        ok_r = violation < eps
        results[name] = (ok_r, violation)
        if not ok_r:
            print(f"WARNING: [{name}] out-of-range violation = {violation:.4e}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT SAVING
# ─────────────────────────────────────────────────────────────────────────────


def _df_matrix(mat: np.ndarray, snames: List[str]) -> pd.DataFrame:
    """Wrap 5×5 numpy array in a labelled DataFrame."""
    return pd.DataFrame(mat, index=snames, columns=snames)


def save_parameters(
    output_dir: str,
    A: np.ndarray,
    B: np.ndarray,
    B_plus: np.ndarray,
    u: np.ndarray,
    X: np.ndarray,
    sector_params: dict,
    firm_dist: dict,
    sim_params: dict,
    macro: dict,
    sector_map: Dict,
    io_df: pd.DataFrame,
    validation: dict,
) -> None:
    """
    Write calibration outputs to output_dir:
      parameters.xlsx  — human-readable multi-sheet workbook
      CSV files        — A0, B0, B_plus, sector_params, firms_sX
      params.json      — machine-readable full parameter set
      calibration_report.txt
    """
    os.makedirs(output_dir, exist_ok=True)
    sids   = sorted(sector_map.keys())
    snames = [sector_map[s]["name"] for s in sids]
    n = len(sids)

    # ── params.json ──────────────────────────────────────────────────────────
    def _ser(v):
        if isinstance(v, np.ndarray):
            return v.tolist()
        if isinstance(v, pd.Series):
            return {str(k): (float(vv) if not pd.isna(vv) else None)
                    for k, vv in v.items()}
        return v

    params_out = {
        "macro": {k: _ser(v) for k, v in macro.items() if k not in ("GVA_series",)},
        "sector_params": {k: _ser(v) for k, v in sector_params.items()
                          if not k.startswith("_")},
        "sim_params": sim_params,
        "sector_names": {str(sid): sector_map[sid]["name"] for sid in sids},
    }
    with open(os.path.join(output_dir, "params.json"), "w", encoding="utf-8") as fh:
        json.dump(params_out, fh, indent=2, default=str)

    # ── CSV: plain matrices ───────────────────────────────────────────────────
    csv_dir = os.path.join(output_dir, "csv")
    os.makedirs(csv_dir, exist_ok=True)
    for name, mat in [("A0", A), ("B0", B), ("B_plus", B_plus)]:
        _df_matrix(mat, snames).round(6).to_csv(
            os.path.join(csv_dir, f"{name}.csv")
        )
    pd.DataFrame({"u0_M_EUR": u, "X0_M_EUR": X}, index=snames).round(2).to_csv(
        os.path.join(csv_dir, "u0_X0.csv")
    )
    sp = sector_params
    pd.DataFrame({
        "delta":  sp["delta_j"],
        "nu":     sp["nu_j"],
        "kappa":  sp["kappa_j"],
        "eta":    sp["eta_j"],
        "alpha":  sp["alpha_j"],
        "p_inn":  sp["p_inn_j"],
        "mu":     sp["mu_j"],
    }, index=snames).round(6).to_csv(os.path.join(csv_dir, "sector_params.csv"))

    for j_i, sid in enumerate(sids):
        sn = sector_map[sid]["name"]
        N_j = len(firm_dist["k0"][j_i])
        a_f  = firm_dist["a_f0"][j_i]   # (5, N_j)
        gf   = firm_dist["gamma_f"][j_i]  # (5, N_j)
        firm_df = pd.DataFrame({
            "k0":       firm_dist["k0"][j_i],
            "theta0":   firm_dist["theta0"][j_i],
            "omega0":   firm_dist["omega0"][j_i],
            "c_f":      firm_dist["c_f"][j_i],
            **{f"a_{r}": a_f[r_i] for r_i, r in enumerate(snames)},
            **{f"gamma_{r}": gf[r_i] for r_i, r in enumerate(snames)},
        })
        firm_df.index.name = "firm_id"
        firm_df.round(6).to_csv(os.path.join(csv_dir, f"firms_{sn.lower()}.csv"))

    # ── Excel workbook: parameters.xlsx ──────────────────────────────────────
    xlsx_path = os.path.join(output_dir, "parameters.xlsx")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:

        # Sheet 1: A0
        df_A = _df_matrix(A, snames).round(6)
        df_A.to_excel(writer, sheet_name="A0_direct_requirements")

        # Sheet 2: B0
        df_B = _df_matrix(B, snames).round(4)
        df_B.to_excel(writer, sheet_name="B0_capital_requirements")

        # Sheet 3: B_plus
        _df_matrix(B_plus, snames).round(6).to_excel(
            writer, sheet_name="B_plus_pseudoinverse"
        )

        # Sheet 4: u0 and X0 with component breakdown
        c2s     = _code_to_sector(sector_map)
        cpa_set = set(c2s.keys())
        C_v = np.zeros(n); G_v = np.zeros(n)
        Ex_v = np.zeros(n); Im_v = np.zeros(n)
        fd_m = {"P3_S14": C_v, "P3_S13": G_v, "P6": Ex_v, "P7": Im_v}
        for row in io_df.itertuples(index=False):
            if row.prd_ava in cpa_set and row.prd_use in fd_m and not pd.isna(row.value):
                fd_m[row.prd_use][c2s[row.prd_ava] - 1] += row.value
        pd.DataFrame({
            "C_household_M_EUR":    C_v.round(1),
            "G_government_M_EUR":   G_v.round(1),
            "Exports_M_EUR":        Ex_v.round(1),
            "Imports_M_EUR":        Im_v.round(1),
            "NX_M_EUR":             (Ex_v - Im_v).round(1),
            "u0_final_demand_M_EUR": u.round(1),
            "X0_gross_output_M_EUR": X.round(1),
            "u0_pct_of_X0":         (u / np.where(X > 0, X, 1) * 100).round(2),
        }, index=snames).to_excel(writer, sheet_name="u0_X0_final_demand")

        # Sheet 5: Sector behavioural parameters
        pd.DataFrame({
            "delta_depreciation":   sp["delta_j"].round(4),
            "nu_capital_product":   sp["nu_j"].round(4),
            "kappa_reinvest_rate":  sp["kappa_j"].round(4),
            "eta_capacity_sensit":  sp["eta_j"].round(4),
            "alpha_expect_inertia": sp["alpha_j"].round(4),
            "p_inn_innovation":     sp["p_inn_j"].round(4),
            "mu_max_resource_sav":  sp["mu_j"].round(4),
            "K_j_M_EUR":            sp["_K_j"].round(0),
            "GVA_avg_M_EUR":        sp["_GVA_avg"].round(0),
            "X_avg_M_EUR":          sp["_X_avg"].round(0),
        }, index=snames).to_excel(writer, sheet_name="sector_params")

        # Sheet 6: Macro parameters
        macro_rows = {
            "alpha_capital_share":    macro["alpha"],
            "beta_labour_share":      macro["beta"],
            "TFP_growth_rate":        macro["TFP_growth"],
            "Am_depreciation_rate":   macro["Am"],
            "MPS_marginal_prop_save": macro["MPS"],
            "g_labour_force_growth":  macro["g"],
            "m_import_propensity":    macro["m"],
        }
        pd.DataFrame.from_dict(
            macro_rows, orient="index", columns=["value"]
        ).round(6).to_excel(writer, sheet_name="macro_params")

        # Sheet 7: Simulation control
        pd.DataFrame.from_dict(
            sim_params, orient="index", columns=["value"]
        ).to_excel(writer, sheet_name="sim_params")

        # Sheets 8+: Firm distributions per sector (summary stats + raw)
        for j_i, sid in enumerate(sids):
            sn  = sector_map[sid]["name"]
            N_j = len(firm_dist["k0"][j_i])
            a_f = firm_dist["a_f0"][j_i]
            gf  = firm_dist["gamma_f"][j_i]
            firm_df = pd.DataFrame({
                "k0_capital_M_EUR": firm_dist["k0"][j_i].round(2),
                "theta0_technology": firm_dist["theta0"][j_i].round(4),
                "omega0_mktshare":  firm_dist["omega0"][j_i].round(6),
                "c_f_fixed_cost":   firm_dist["c_f"][j_i].round(2),
                **{f"a_from_{r}": a_f[r_i].round(6) for r_i, r in enumerate(snames)},
                **{f"gamma_{r}": gf[r_i].round(6) for r_i, r in enumerate(snames)},
            })
            firm_df.index.name = "firm_id"
            sheet_nm = f"firms_{sn[:11]}"  # Excel 31-char limit
            firm_df.to_excel(writer, sheet_name=sheet_nm)

    # ── calibration_report.txt ───────────────────────────────────────────────
    # C_v, G_v, Ex_v, Im_v already computed above for the Excel sheet

    rho_A  = float(np.max(np.abs(np.linalg.eigvals(A))))
    B_rank = int(np.linalg.matrix_rank(B))
    eigs   = np.linalg.eigvals(A)
    dom_e  = eigs[np.argmax(np.abs(eigs))]
    W = 80
    SEP = "─" * W

    def _hdr(title: str) -> str:
        return f"\n{SEP}\n{title.center(W)}\n{SEP}"

    lines: List[str] = [
        "CALIBRATION REPORT — Two-Level Agent-Based IO Model",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    # Section 1
    lines.append(_hdr("SECTION 1: Macro Aggregate Parameters"))
    lines.append(f"{'Parameter':<22} {'Value':>14}   Source")
    lines.append("─" * 60)
    s1 = [
        ("alpha (K share)",   macro["alpha"],      "Эконом рост row 8  col B"),
        ("beta (L share)",    macro["beta"],       "Эконом рост row 9  col B"),
        ("TFP growth δ_a",    macro["TFP_growth"], "Эконом рост row 7  col B"),
        ("Depreciation Am",   macro["Am"],         "Эконом рост row 16 col B"),
        ("MPS",               macro["MPS"],        "Эконом рост row 17 col B"),
        ("g (LF growth)",     macro["g"],          "Эконом рост row 25 col B"),
        ("m (import prop.)",  macro["m"],          "Эконом рост row 12 col B"),
    ]
    for pname, val, src in s1:
        fval = f"{val:.6f}" if not (isinstance(val, float) and np.isnan(val)) else "N/A"
        lines.append(f"  {pname:<20} {fval:>14}   {src}")

    # Section 2
    lines.append(_hdr("SECTION 2: A(0) — Direct Requirements Matrix"))
    col_hdr = f"{'':>16}" + "".join(f"{s:>14}" for s in snames)
    lines.append(col_hdr)
    for i, sn in enumerate(snames):
        lines.append(f"  {sn:<14}" + "".join(f"{A[i, j]:>14.6f}" for j in range(n)))

    # Section 3
    lines.append(_hdr(f"SECTION 3: B(0) — Capital Requirements Matrix  [rank={B_rank}/{n}]"))
    lines.append(col_hdr)
    for i, sn in enumerate(snames):
        lines.append(f"  {sn:<14}" + "".join(f"{B[i, j]:>14.4f}" for j in range(n)))
    if B_rank < n:
        lines.append("\n  B is rank-deficient. Moore-Penrose pseudoinverse B+:")
        lines.append(col_hdr)
        for i, sn in enumerate(snames):
            lines.append(f"  {sn:<14}" + "".join(f"{B_plus[i, j]:>14.6f}" for j in range(n)))

    # Section 4
    lines.append(_hdr("SECTION 4: u(0) Final Demand and X(0) Gross Output  [M EUR]"))
    lines.append(f"  {'Sector':<16} {'C':>12} {'G':>12} {'NX':>12} {'u(0)':>12} {'X(0)':>14}")
    lines.append("  " + "─" * 72)
    for j, sn in enumerate(snames):
        nx = Ex_v[j] - Im_v[j]
        uj = C_v[j] + G_v[j] + nx
        lines.append(
            f"  {sn:<16} {C_v[j]:>12.1f} {G_v[j]:>12.1f} {nx:>12.1f} {uj:>12.1f} {X[j]:>14.1f}"
        )
    lines.append(
        f"  {'TOTAL':<16} {C_v.sum():>12.1f} {G_v.sum():>12.1f} "
        f"{(Ex_v-Im_v).sum():>12.1f} {u.sum():>12.1f} {X.sum():>14.1f}"
    )

    # Section 5
    sp = sector_params
    lines.append(_hdr("SECTION 5: Sector-Level Behavioural Parameters"))
    lines.append(
        f"  {'Sector':<16} {'δ':>8} {'ν':>12} {'κ':>8} {'η':>8} {'α':>8} {'p_inn':>8} {'μ':>8}"
    )
    lines.append("  " + "─" * 80)
    for j, sn in enumerate(snames):
        lines.append(
            f"  {sn:<16} "
            f"{sp['delta_j'][j]:>8.4f} "
            f"{sp['nu_j'][j]:>12.4f} "
            f"{sp['kappa_j'][j]:>8.4f} "
            f"{sp['eta_j'][j]:>8.4f} "
            f"{sp['alpha_j'][j]:>8.4f} "
            f"{sp['p_inn_j'][j]:>8.4f} "
            f"{sp['mu_j'][j]:>8.4f}"
        )

    # Section 6
    lines.append(_hdr("SECTION 6: Firm Distribution Summary"))
    lines.append(
        f"  {'Sector':<16} {'N':>5} "
        f"{'k mean':>12} {'k std':>12} {'k min':>12} {'k max':>12}  "
        f"{'θ mean':>8} {'θ std':>8}"
    )
    lines.append("  " + "─" * 90)
    for j, sn in enumerate(snames):
        kv = firm_dist["k0"][j]
        tv = firm_dist["theta0"][j]
        lines.append(
            f"  {sn:<16} {len(kv):>5} "
            f"{kv.mean():>12.2f} {kv.std():>12.2f} {kv.min():>12.2f} {kv.max():>12.2f}  "
            f"{tv.mean():>8.4f} {tv.std():>8.4f}"
        )

    # Section 7
    lines.append(_hdr("SECTION 7: Validation Results"))
    for check, (ok, val) in validation.items():
        status = "PASS" if ok else "FAIL"
        lines.append(f"  [{status}]  {check:<30}  value/residual = {val:.4e}")

    # Section 8
    lines.append(_hdr("SECTION 8: Spectral Radius and Convergence"))
    conv = "YES — Leontief inverse exists" if rho_A < 1.0 else "NO — model may diverge"
    lines.append(f"  Spectral radius  ρ(A)      = {rho_A:.8f}")
    lines.append(f"  Dominant eigenvalue        = {dom_e:.6f} (complex part: {dom_e.imag:+.4e})" if isinstance(dom_e, complex) else f"  Dominant eigenvalue        = {dom_e:.6f}")
    lines.append(f"  Convergence status         : {conv}")
    lines.append(f"\n{SEP}")

    report_path = os.path.join(output_dir, "calibration_report.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    _ts(f"Report  → {report_path}")
    _ts(f"Excel   → {xlsx_path}")
    _ts(f"CSV dir → {csv_dir}/")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────


def main(
    io_csv: str,
    macro_xlsx: str,
    country_iso: str,
    year: int,
    output_dir: str,
) -> None:
    """Orchestrate full calibration pipeline."""
    sim_params = {"T": 30, "dt": 1, "epsilon_b": 1e-3, "epsilon_r": 1e-6, "seed": 42}
    N_firms    = [32, 27, 41, 25, 34]
    year_range = (2010, 2019)

    _ts("=" * 60)
    _ts(f"Two-Level ABM Calibration — country={country_iso}  year={year}")
    _ts("=" * 60)

    # ── Block 1: IO matrices (reference year) ─────────────────────────────────
    _ts("Parsing IO table (reference year)...")
    io_df = parse_io_table(io_csv, country_iso, year)
    _ts(f"  {len(io_df)} records loaded for {country_iso} {year}")

    _ts("Loading IO table time series 2010-2019 for dX estimation...")
    ts_years = list(range(year_range[0], year_range[1] + 1))
    dfs_ts   = _parse_io_multi(io_csv, country_iso, ts_years)
    X_ts_b1  = np.array([build_X_vector(dfs_ts.get(yr, io_df), SECTOR_MAP)
                          for yr in ts_years])  # (10, 5)

    X_mean_all = float(np.nanmean(X_ts_b1[X_ts_b1 > 0])) if (X_ts_b1 > 0).any() else 1.0
    eps_dX = 1e-3 * X_mean_all
    dX = np.nanmean(np.diff(X_ts_b1, axis=0), axis=0)  # mean annual increment
    dX = np.where(np.abs(dX) < eps_dX, np.where(dX >= 0, eps_dX, -eps_dX), dX)

    _ts("Building Z, X, u, Q, A, B matrices...")
    Z  = build_Z_matrix(io_df, SECTOR_MAP)
    X0 = build_X_vector(io_df, SECTOR_MAP)
    u0_raw = build_u_vector(io_df, SECTOR_MAP)
    # Cap u0 at 95 % of X0 per sector — prevents negative target output on t=1
    u0 = np.minimum(u0_raw, 0.95 * X0)
    capped = np.where(u0_raw > u0)[0]
    if len(capped):
        snames_all = [SECTOR_MAP[s]["name"] for s in sorted(SECTOR_MAP)]
        for ci in capped:
            _ts(f"  NOTE: u0[{snames_all[ci]}] capped {u0_raw[ci]:.0f} → {u0[ci]:.0f}")
    Q  = build_Q_matrix(io_df, SECTOR_MAP, X0)
    A0 = compute_A(Z, X0)
    B0, B_plus = compute_B(Q, dX, sim_params["epsilon_b"])

    rho_A = float(np.max(np.abs(np.linalg.eigvals(A0))))
    _ts(f"  ρ(A0) = {rho_A:.6f}  {'✓ < 1' if rho_A < 1 else '✗ WARNING ≥ 1'}")
    if rho_A >= 1.0:
        print(f"WARNING: [spectral_radius] ρ(A) = {rho_A:.6f} ≥ 1. Check IO data.")
    _ts(f"  rank(B0) = {np.linalg.matrix_rank(B0)}/{B0.shape[0]}")

    # ── Macro scalars ─────────────────────────────────────────────────────────
    _ts("Loading macro parameters...")
    macro = load_macro_params(macro_xlsx)
    _ts(f"  Am={macro['Am']:.4f}  α={macro['alpha']:.4f}  MPS={macro['MPS']:.6f}  g={macro['g']:.5f}")

    # ── Block 2: Sector calibration ───────────────────────────────────────────
    _ts("Calibrating sector parameters (averages 2010-2019)...")
    sector_params = calibrate_sector_params(
        io_df=io_df,
        macro=macro,
        sector_map=SECTOR_MAP,
        year_range=year_range,
        io_csv_path=io_csv,
        country_iso=country_iso,
    )
    for j, sid in enumerate(sorted(SECTOR_MAP.keys())):
        sn = SECTOR_MAP[sid]["name"]
        _ts(
            f"  {sn:<16}  δ={sector_params['delta_j'][j]:.4f}"
            f"  ν={sector_params['nu_j'][j]:.4f}"
            f"  κ={sector_params['kappa_j'][j]:.4f}"
            f"  η={sector_params['eta_j'][j]:.4f}"
        )

    # ── Block 3: Firm distributions ───────────────────────────────────────────
    _ts("Generating firm-level distributions...")
    firm_dist = generate_firm_distributions(
        sector_params=sector_params,
        macro=macro,
        N_firms=N_firms,
        A0=A0,
        B0=B0,
        sector_map=SECTOR_MAP,
        seed=sim_params["seed"],
    )
    _ts(f"  Total firms: {sum(N_firms)}  per sector: {N_firms}")

    # ── Validation ────────────────────────────────────────────────────────────
    _ts("Running validation checks...")
    validation = validate_model(A0, B0, B_plus, u0, X0, sector_params, firm_dist)
    n_fail = sum(1 for ok, _ in validation.values() if not ok)
    _ts(f"  {len(validation) - n_fail}/{len(validation)} checks passed"
        + (f"  ({n_fail} FAILED)" if n_fail else ""))

    # ── Save ──────────────────────────────────────────────────────────────────
    _ts(f"Saving outputs to '{output_dir}'...")
    save_parameters(
        output_dir=output_dir,
        A=A0, B=B0, B_plus=B_plus, u=u0, X=X0,
        sector_params=sector_params,
        firm_dist=firm_dist,
        sim_params=sim_params,
        macro=macro,
        sector_map=SECTOR_MAP,
        io_df=io_df,
        validation=validation,
    )
    _ts("Outputs written: params.json  matrices.npz  calibration_report.txt")
    _ts("=" * 60)
    _ts("DONE")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calibrate two-level agent-based IO model (five-sector economy).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("io_csv",     help="Path to Eurostat IO table CSV (estat_naio_10_cp1700)")
    parser.add_argument("macro_xlsx", help="Path to macro time-series Excel workbook")
    parser.add_argument("--country",  default="DE", metavar="ISO",
                        help="Two-letter ISO country code")
    parser.add_argument("--year",     type=int, default=2015,
                        help="Reference year for IO matrices")
    parser.add_argument("--output",   default="calibration_output", metavar="DIR",
                        help="Output directory for saved parameters")
    args = parser.parse_args()

    main(
        io_csv=args.io_csv,
        macro_xlsx=args.macro_xlsx,
        country_iso=args.country,
        year=args.year,
        output_dir=args.output,
    )
