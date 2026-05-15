#!/usr/bin/env python3
"""
Revised calibration script for the two-level agent-based input-output model.

Main revisions relative to the original version:
1. Sectoral capital K_j is estimated by a perpetual-inventory-style proxy K_j ~ GFCF_j / delta_j,
   then normalized to the aggregate capital stock.
2. Final demand for the simulation uses a partially balanced vector u0_model that soft-corrects
   the initial static residual without overwriting the raw Eurostat-based u0_raw.
3. Construction-sector eta is damped to avoid spurious oscillations in forward simulation.
4. Rich machine-readable outputs are written to params.json and matrices.npz so simulate_revised.py
   can consume calibration results directly.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

import calibrate as base

SECTOR_MAP = base.SECTOR_MAP


def _ser(v):
    if isinstance(v, dict):
        return {str(k): _ser(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_ser(x) for x in v]
    if isinstance(v, np.ndarray):
        return [_ser(x) for x in v.tolist()]
    if isinstance(v, pd.Series):
        return {str(k): _ser(vv) for k, vv in v.items()}
    if isinstance(v, pd.DataFrame):
        return {
            str(col): [_ser(x) for x in v[col].tolist()]
            for col in v.columns
        }
    if isinstance(v, (np.floating, float)):
        val = float(v)
        return None if (np.isnan(val) or np.isinf(val)) else val
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if pd.isna(v):
        return None
    return v


def calibrate_sector_params_revised(
    io_df: pd.DataFrame,
    macro: dict,
    sector_map: Dict,
    year_range: Tuple[int, int],
    io_csv_path: Optional[str] = None,
    country_iso: Optional[str] = None,
) -> dict:
    """Revised sector calibration with capital estimated from GFCF/delta."""
    n = len(sector_map)
    c2s = base._code_to_sector(sector_map)
    cpa_set = set(c2s.keys())
    yr0, yr1 = year_range
    years = list(range(yr0, yr1 + 1))

    if io_csv_path and country_iso:
        dfs = base._parse_io_multi(io_csv_path, country_iso, years)
    else:
        dfs = {yr: io_df for yr in years}

    def _sector_col(df: pd.DataFrame, prd_ava_code: str) -> np.ndarray:
        vec = np.zeros(n)
        sub = df[(df["prd_ava"] == prd_ava_code) & df["prd_use"].isin(cpa_set)].dropna(subset=["value"])
        for row in sub.itertuples(index=False):
            vec[c2s[row.prd_use] - 1] += row.value
        return vec

    def _sector_row(df: pd.DataFrame, prd_use_code: str) -> np.ndarray:
        vec = np.zeros(n)
        sub = df[(df["prd_use"] == prd_use_code) & df["prd_ava"].isin(cpa_set)].dropna(subset=["value"])
        for row in sub.itertuples(index=False):
            vec[c2s[row.prd_ava] - 1] += row.value
        return vec

    ny = len(years)
    GVA_ts = np.zeros((ny, n))
    D1_ts = np.zeros((ny, n))
    GFCF_ts = np.zeros((ny, n))
    X_ts = np.zeros((ny, n))

    for t_i, yr in enumerate(years):
        df_yr = dfs.get(yr, io_df)
        GVA_ts[t_i] = _sector_col(df_yr, "B1G")
        D1_ts[t_i] = _sector_col(df_yr, "D1")
        GFCF_ts[t_i] = _sector_row(df_yr, "P51G")
        X_ts[t_i] = base.build_X_vector(df_yr, sector_map)

    GVA_avg = np.nanmean(GVA_ts, axis=0)
    D1_avg = np.nanmean(D1_ts, axis=0)
    GFCF_avg = np.nanmean(GFCF_ts, axis=0)
    X_avg = np.nanmean(X_ts, axis=0)

    for j_idx, sid in enumerate(sorted(sector_map.keys())):
        macro["GVA_series"][sid] = pd.Series({yr: GVA_ts[t_i, j_idx] for t_i, yr in enumerate(years)}, dtype=float)

    Am = float(macro["Am"])
    delta_j = np.array([Am * sector_map[sid]["delta_mult"] for sid in sorted(sector_map)], dtype=float)

    K_series = macro["K_series"]
    k_years = [yr for yr in years if yr in K_series.index and not np.isnan(K_series[yr])]
    K_total = float(np.mean([K_series[yr] for yr in k_years])) if k_years else 0.0

    # Revised capital proxy: K_j ~ GFCF_j / delta_j, then normalized to K_total.
    delta_safe = np.where(delta_j > 1e-6, delta_j, 1e-6)
    K_proxy = GFCF_avg / delta_safe
    if np.all(K_proxy <= 0):
        gva_total = float(GVA_avg.sum())
        gva_shares = GVA_avg / gva_total if gva_total > 0 else np.ones(n) / n
        K_j = gva_shares * K_total
        capital_method = "fallback_gva_share"
    else:
        K_proxy = np.maximum(K_proxy, 1.0)
        if K_total > 0:
            K_j = K_proxy * (K_total / K_proxy.sum())
        else:
            K_j = K_proxy
        capital_method = "pim_proxy_gfcf_over_delta"

    X_safe = np.where(X_avg > 0, X_avg, 1.0)
    nu_j = X_avg / np.where(K_j > 0, K_j, 1.0)

    pi_j = GVA_avg - D1_avg
    eps_pi = 1e-3 * max(float(np.nanmean(X_avg[X_avg > 0])), 1.0) if (X_avg > 0).any() else 1e-3
    kappa_j = np.clip(GFCF_avg / np.maximum(pi_j, eps_pi), 0.05, 0.45)

    # Dampened eta, especially for construction.
    eta_j = np.clip(0.10 * GFCF_avg / X_safe, 0.01, 0.20)
    eta_cap = np.array([0.015, 0.015, 0.020, 0.015, 0.015])
    eta_j = np.minimum(eta_j, eta_cap)

    X_growth = np.diff(X_ts, axis=0) / np.where(X_ts[:-1] > 0, X_ts[:-1], 1.0)
    vol_j = np.nanstd(X_growth, axis=0)
    mean_vol = float(np.nanmean(vol_j))
    alpha_j = np.clip(1.0 - vol_j / (mean_vol if mean_vol > 0 else 1e-6), 0.30, 0.90)

    kappa_max = float(kappa_j.max()) if kappa_j.max() > 0 else 1.0
    p_inn_j = 0.05 + 0.15 * (1.0 - kappa_j / kappa_max)

    mu_j = np.clip(0.01 + 0.04 * (GVA_avg / X_safe), 0.01, 0.05)

    return {
        "delta_j": delta_j,
        "nu_j": nu_j,
        "kappa_j": kappa_j,
        "eta_j": eta_j,
        "alpha_j": alpha_j,
        "p_inn_j": p_inn_j,
        "mu_j": mu_j,
        "_K_j": K_j,
        "_K_method": capital_method,
        "_GVA_avg": GVA_avg,
        "_X_avg": X_avg,
        "_GFCF_avg": GFCF_avg,
        "_D1_avg": D1_avg,
        "_X_ts": X_ts,
    }


def build_params_payload(
    A: np.ndarray,
    B: np.ndarray,
    B_plus: np.ndarray,
    X0: np.ndarray,
    u0_raw: np.ndarray,
    u0_model: np.ndarray,
    sector_params: dict,
    firm_dist: dict,
    sim_params: dict,
    macro: dict,
    validation: dict,
    sector_map: Dict,
    n_firms: List[int],
    year: int,
    country_iso: str,
) -> dict:
    sids = sorted(sector_map.keys())
    return {
        "model_meta": {
            "country_iso": country_iso,
            "base_year": int(year),
            "n_sectors": len(sids),
            "n_firms": n_firms,
            "sector_names": [sector_map[sid]["name"] for sid in sids],
            "sector_names_short": ["Ext", "Energy", "Mfg", "Constr", "Agr"],
        },
        "A0": _ser(A),
        "B0": _ser(B),
        "B_plus": _ser(B_plus),
        "X0": _ser(X0),
        "u0_raw": _ser(u0_raw),
        "u0_model": _ser(u0_model),
        "macro": {k: _ser(v) for k, v in macro.items() if k not in ("GVA_series",)},
        "sector_params": {k: _ser(v) for k, v in sector_params.items()},
        "firm_dist": {k: _ser(v) for k, v in firm_dist.items()},
        "sim_params": sim_params,
        "validation": {k: [bool(v[0]), float(v[1])] for k, v in validation.items()},
    }


def save_enhanced_outputs(
    output_dir: str,
    payload: dict,
    A: np.ndarray,
    B: np.ndarray,
    B_plus: np.ndarray,
    X0: np.ndarray,
    u0_raw: np.ndarray,
    u0_model: np.ndarray,
) -> None:
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "params.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    np.savez_compressed(
        os.path.join(output_dir, "matrices.npz"),
        A0=A,
        B0=B,
        B_plus=B_plus,
        X0=X0,
        u0_raw=u0_raw,
        u0_model=u0_model,
    )


def main(
    io_csv: str,
    macro_xlsx: str,
    country_iso: str,
    year: int,
    output_dir: str,
    balance_lambda: float = 0.5,
) -> None:
    sim_params = {
        "T": 30,
        "dt": 1,
        "epsilon_b": 1.0,
        "epsilon_r": 1e-6,
        "seed": 42,
        "growth_u": 0.015,
        "leontief_damping": 0.5,
        "B_smoothing_lambda": 0.7,
        "dynamic_fixed_costs": True,
    }
    n_firms = [32, 27, 41, 25, 34]
    year_range = (2010, 2019)

    base._ts("=" * 60)
    base._ts(f"Revised two-level ABM calibration — country={country_iso} year={year}")
    base._ts("=" * 60)

    base._ts("Parsing IO table (reference year)...")
    io_df = base.parse_io_table(io_csv, country_iso, year)
    base._ts(f"  {len(io_df)} records loaded for {country_iso} {year}")

    base._ts("Loading IO table time series 2010-2019 for dX estimation...")
    ts_years = list(range(year_range[0], year_range[1] + 1))
    dfs_ts = base._parse_io_multi(io_csv, country_iso, ts_years)
    X_ts_b1 = np.array([base.build_X_vector(dfs_ts.get(yr, io_df), SECTOR_MAP) for yr in ts_years])
    X_mean_all = float(np.nanmean(X_ts_b1[X_ts_b1 > 0])) if (X_ts_b1 > 0).any() else 1.0
    eps_dX = 1e-3 * X_mean_all
    dX = np.nanmean(np.diff(X_ts_b1, axis=0), axis=0)
    dX = np.where(np.abs(dX) < eps_dX, np.where(dX >= 0, eps_dX, -eps_dX), dX)

    base._ts("Building Z, X, u, Q, A, B matrices...")
    Z = base.build_Z_matrix(io_df, SECTOR_MAP)
    X0 = base.build_X_vector(io_df, SECTOR_MAP)
    u0_raw = base.build_u_vector(io_df, SECTOR_MAP)
    Q = base.build_Q_matrix(io_df, SECTOR_MAP, X0)
    A0 = base.compute_A(Z, X0)
    B0, B_plus = base.compute_B(Q, dX, sim_params["epsilon_b"])

    residual_raw = X0 - (A0 @ X0 + u0_raw)
    u0_model = u0_raw + balance_lambda * np.maximum(residual_raw, 0.0)
    u0_model = np.minimum(u0_model, 0.98 * X0)

    rho_A = float(np.max(np.abs(np.linalg.eigvals(A0))))
    rel_raw = float(np.linalg.norm(residual_raw) / (np.linalg.norm(X0) + 1e-12))
    rel_model = float(np.linalg.norm(X0 - (A0 @ X0 + u0_model)) / (np.linalg.norm(X0) + 1e-12))
    base._ts(f"  ρ(A0) = {rho_A:.6f}  {'✓ < 1' if rho_A < 1 else '✗ WARNING ≥ 1'}")
    base._ts(f"  raw static residual   = {rel_raw:.4%}")
    base._ts(f"  model static residual = {rel_model:.4%}")
    base._ts(f"  rank(B0) = {np.linalg.matrix_rank(B0)}/{B0.shape[0]}")

    base._ts("Loading macro parameters...")
    macro = base.load_macro_params(macro_xlsx)
    base._ts(f"  Am={macro['Am']:.4f}  α={macro['alpha']:.4f}  MPS={macro['MPS']:.6f}  g={macro['g']:.5f}")

    base._ts("Calibrating sector parameters (revised, averages 2010-2019)...")
    sector_params = calibrate_sector_params_revised(
        io_df=io_df,
        macro=macro,
        sector_map=SECTOR_MAP,
        year_range=year_range,
        io_csv_path=io_csv,
        country_iso=country_iso,
    )
    for j, sid in enumerate(sorted(SECTOR_MAP.keys())):
        sn = SECTOR_MAP[sid]["name"]
        base._ts(
            f"  {sn:<16} δ={sector_params['delta_j'][j]:.4f}"
            f" ν={sector_params['nu_j'][j]:.4f}"
            f" κ={sector_params['kappa_j'][j]:.4f}"
            f" η={sector_params['eta_j'][j]:.4f}"
        )

    base._ts("Generating firm-level distributions...")
    firm_dist = base.generate_firm_distributions(
        sector_params=sector_params,
        macro=macro,
        N_firms=n_firms,
        A0=A0,
        B0=B0,
        sector_map=SECTOR_MAP,
        seed=sim_params["seed"],
    )
    base._ts(f"  Total firms: {sum(n_firms)} per sector: {n_firms}")

    base._ts("Running validation checks against model demand u0_model...")
    validation = base.validate_model(A0, B0, B_plus, u0_model, X0, sector_params, firm_dist)
    validation["raw_static_balance"] = [False if rel_raw >= 1e-6 else True, rel_raw]
    validation["model_static_balance"] = [False if rel_model >= 1e-6 else True, rel_model]
    n_fail = sum(1 for ok, _ in validation.values() if not ok)
    base._ts(f"  {len(validation) - n_fail}/{len(validation)} checks passed" + (f" ({n_fail} FAILED)" if n_fail else ""))

    # Reuse the original rich XLSX/CSV/report export, but with simulation demand.
    base._ts(f"Saving base outputs to '{output_dir}'...")
    base.save_parameters(
        output_dir=output_dir,
        A=A0,
        B=B0,
        B_plus=B_plus,
        u=u0_model,
        X=X0,
        sector_params=sector_params,
        firm_dist=firm_dist,
        sim_params=sim_params,
        macro=macro,
        sector_map=SECTOR_MAP,
        io_df=io_df,
        validation=validation,
    )

    payload = build_params_payload(
        A=A0,
        B=B0,
        B_plus=B_plus,
        X0=X0,
        u0_raw=u0_raw,
        u0_model=u0_model,
        sector_params=sector_params,
        firm_dist=firm_dist,
        sim_params=sim_params,
        macro=macro,
        validation=validation,
        sector_map=SECTOR_MAP,
        n_firms=n_firms,
        year=year,
        country_iso=country_iso,
    )
    save_enhanced_outputs(output_dir, payload, A0, B0, B_plus, X0, u0_raw, u0_model)

    # Write an extra balance note.
    note_path = Path(output_dir) / "balance_note.txt"
    note_path.write_text(
        (
            f"Raw relative static residual:   {rel_raw:.6f}\n"
            f"Model relative static residual: {rel_model:.6f}\n"
            f"balance_lambda: {balance_lambda:.3f}\n"
            "u0_model = u0_raw + λ * max(X0 - A0 X0 - u0_raw, 0) with sector-wise cap at 0.98*X0.\n"
        ),
        encoding="utf-8",
    )
    base._ts(f"Enhanced files written: {Path(output_dir) / 'params.json'} and matrices.npz")
    base._ts("DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Revised calibration for the two-level agent-based IO model.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("io_csv", help="Path to Eurostat IO table CSV (estat_naio_10_cp1700)")
    parser.add_argument("macro_xlsx", help="Path to macro time-series Excel workbook")
    parser.add_argument("--country", default="DE", metavar="ISO", help="Two-letter ISO country code")
    parser.add_argument("--year", type=int, default=2015, help="Reference year for IO matrices")
    parser.add_argument("--output", default="calibration_output_revised", metavar="DIR", help="Output directory")
    parser.add_argument("--balance-lambda", type=float, default=0.5, help="Soft balance correction weight for u0_model")
    args = parser.parse_args()
    main(
        io_csv=args.io_csv,
        macro_xlsx=args.macro_xlsx,
        country_iso=args.country,
        year=args.year,
        output_dir=args.output,
        balance_lambda=args.balance_lambda,
    )
