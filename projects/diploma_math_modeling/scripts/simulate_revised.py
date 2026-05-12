#!/usr/bin/env python3
"""
Revised forward simulation for the two-level agent-based input-output model.

Main revisions relative to the original version:
1. The Leontief target follows the damped pseudoinverse version of (4.7):
      x*(t+1) = x(t) + λ B⁺(t)[(I-A(t))x(t) - u(t)]
2. The script reads calibration outputs from params.json or matrices.npz.
3. B(t) is updated with exponential smoothing.
4. Exact balance residuals are computed ex post using x(t+2), in line with (4.37).
5. Final figures emphasize dynamic decomposition and diagnostic thresholds.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

# -----------------------------------------------------------------------------
# Defaults used only when no calibration file is provided
# -----------------------------------------------------------------------------

DEFAULTS = {
    "model_meta": {
        "country_iso": "DE",
        "base_year": 2015,
        "n_sectors": 5,
        "n_firms": [32, 27, 41, 25, 34],
        "sector_names": ["Добыча", "Энергетика", "Обработка", "Строительство", "С/х"],
        "sector_names_short": ["Доб.", "Энерг.", "Обраб.", "Строит.", "С/х"],
    },
    "A0": [
        [0.0578, 0.1214, 0.0268, 0.0068, 0.0020],
        [0.0276, 0.2281, 0.0133, 0.0022, 0.0158],
        [0.2136, 0.0735, 0.3980, 0.2336, 0.1901],
        [0.0218, 0.0323, 0.0052, 0.0769, 0.0168],
        [0.0042, 0.0001, 0.0255, 0.0000, 0.0675],
    ],
    "B0": [
        [0.0008, 0.0017, 0.0014, 0.0006, 0.0010],
        [0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
        [2.4017, 5.2517, 4.2448, 1.9640, 2.9229],
        [2.0997, 4.5914, 3.7110, 1.7171, 2.5554],
        [0.0041, 0.0090, 0.0072, 0.0033, 0.0050],
    ],
    "B_plus": None,
    "X0": [10746.0, 106178.0, 1675563.0, 297148.0, 50958.0],
    "u0_raw": [10208.0, 45037.0, 1413006.0, 7122.0, 31770.0],
    "u0_model": [10208.0, 45037.0, 1413006.0, 7122.0, 31770.0],
    "sector_params": {
        "delta_j": [0.060, 0.040, 0.055, 0.065, 0.050],
        "nu_j": [0.140, 0.165, 0.189, 0.134, 0.145],
        "kappa_j": [0.125, 0.050, 0.450, 0.450, 0.050],
        "eta_j": [0.010, 0.010, 0.012, 0.015, 0.010],
        "alpha_j": [0.300, 0.300, 0.300, 0.513, 0.300],
        "p_inn_j": [0.158, 0.183, 0.050, 0.050, 0.183],
        "mu_j": [0.027, 0.024, 0.022, 0.027, 0.026],
        "_K_j": [78100.0, 707000.0, 8885500.0, 2252700.0, 368200.0],
    },
    "firm_dist": None,
    "sim_params": {
        "T": 30,
        "dt": 1,
        "epsilon_b": 1.0,
        "epsilon_r": 1e-6,
        "seed": 42,
        "growth_u": 0.015,
        "leontief_damping": 0.5,
        "B_smoothing_lambda": 0.7,
        "dynamic_fixed_costs": True,
    },
}

COLORS = ["#d62728", "#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd"]
MARKERS = ["o", "s", "^", "D", "v"]
SIGMA_K = 0.6
SIGMA_A = 0.15

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 8.5,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "lines.linewidth": 1.8,
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})


def _to_np(v):
    return np.array(v, dtype=float)


def load_payload(params_path: Path | None) -> dict:
    if params_path is None:
        payload = json.loads(json.dumps(DEFAULTS))
        B0 = _to_np(payload["B0"])
        payload["B_plus"] = np.linalg.pinv(B0, rcond=0.01).tolist()
        return payload
    with open(params_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def init_firms_from_payload(payload: dict, rng: np.random.Generator) -> dict:
    meta = payload["model_meta"]
    n_firms = meta["n_firms"]
    sector_params = payload["sector_params"]
    A0 = _to_np(payload["A0"])
    B0 = _to_np(payload["B0"])
    sector_names = meta["sector_names"]
    n = len(sector_names)

    if payload.get("firm_dist"):
        fd = payload["firm_dist"]
        firms = {
            "k": [_to_np(arr) for arr in fd["k0"]],
            "theta": [_to_np(arr) for arr in fd["theta0"]],
            "omega": [_to_np(arr) for arr in fd["omega0"]],
            "a_f": [_to_np(arr) for arr in fd["a_f0"]],
            "c_f": [_to_np(arr) for arr in fd["c_f"]],
            "gamma_f": [_to_np(arr) for arr in fd["gamma_f"]],
        }
    else:
        K_j = _to_np(sector_params["_K_j"])
        nu_j = _to_np(sector_params["nu_j"])
        theta_lo = np.array([0.7, 0.7, 0.5, 0.6, 0.5], dtype=float)
        theta_hi = np.array([1.3, 1.3, 1.5, 1.4, 1.5], dtype=float)
        firms = {"k": [], "theta": [], "omega": [], "a_f": [], "c_f": [], "gamma_f": []}
        for j in range(n):
            Nj = n_firms[j]
            Kj = K_j[j]
            mu_k = np.log(max(Kj / Nj, 1e-15)) - 0.5 * SIGMA_K**2
            raw_k = rng.lognormal(mu_k, SIGMA_K, Nj)
            k_jf = raw_k * (Kj / raw_k.sum())
            theta_jf = rng.uniform(theta_lo[j], theta_hi[j], Nj)
            omega_jf = k_jf / max(k_jf.sum(), 1e-15)
            a_f = np.zeros((n, Nj), dtype=float)
            for i in range(n):
                raw_a = A0[i, j] * np.exp(SIGMA_A * rng.standard_normal(Nj))
                agg = float(np.dot(omega_jf, raw_a))
                a_f[i] = raw_a * (A0[i, j] / agg) if agg > 1e-300 and A0[i, j] > 0 else raw_a
            c_rate = 0.02 * nu_j[j]
            c_f = c_rate * k_jf
            b_col = B0[:, j]
            weights = np.maximum(b_col, 0.0)
            gamma_j = weights / weights.sum() if weights.sum() > 0 else np.ones(n) / n
            gamma_f = np.tile(gamma_j[:, None], (1, Nj))
            firms["k"].append(k_jf)
            firms["theta"].append(theta_jf)
            firms["omega"].append(omega_jf)
            firms["a_f"].append(a_f)
            firms["c_f"].append(c_f)
            firms["gamma_f"].append(gamma_f)

    d_e = []
    X0 = _to_np(payload["X0"])
    c_f_rate = []
    for j in range(len(n_firms)):
        d_e.append(firms["omega"][j] * X0[j])
        c_f_rate.append(firms["c_f"][j] / np.maximum(firms["k"][j], 1.0))
    firms["d_e"] = d_e
    firms["c_f_rate"] = c_f_rate
    return firms


def hhi(omega: np.ndarray) -> float:
    return float(np.dot(omega, omega))


def leontief_target(x: np.ndarray, A: np.ndarray, B: np.ndarray, u: np.ndarray, damping: float, max_rel_step: float = 0.15) -> np.ndarray:
    """
    Damped version of (4.7): x* = x + λ B⁺[(I-A)x-u].
    The correction is additionally clipped component-wise to avoid spurious
    one-step collapses under large initial imbalance.
    """
    B_plus = np.linalg.pinv(B, rcond=0.01)
    r = (np.eye(len(x)) - A) @ x - u
    correction = B_plus @ r
    step = damping * correction
    clip = max_rel_step * np.maximum(x, 1.0)
    step = np.clip(step, -clip, clip)
    x_star = x + step
    return np.maximum(x_star, 0.0)


def step(x: np.ndarray, A: np.ndarray, B: np.ndarray, u: np.ndarray, firms: dict, params: dict, rng: np.random.Generator, B0_ref: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, dict, dict]:
    n = len(x)
    sector_params = params["sector_params"]
    DELTA = _to_np(sector_params["delta_j"])
    NU = _to_np(sector_params["nu_j"])
    KAPPA = _to_np(sector_params["kappa_j"])
    ETA = _to_np(sector_params["eta_j"])
    ALPHA = _to_np(sector_params["alpha_j"])
    P_INN = _to_np(sector_params["p_inn_j"])
    MU = _to_np(sector_params["mu_j"])
    eps_b = float(params["sim_params"]["epsilon_b"])
    damping = float(params["sim_params"]["leontief_damping"])
    lambda_B = float(params["sim_params"]["B_smoothing_lambda"])
    dynamic_fixed_costs = bool(params["sim_params"].get("dynamic_fixed_costs", True))

    x_star = leontief_target(x, A, B, u, damping=damping)

    x_jf_out, z_ijf_out, q_ijf_out = [None] * n, [None] * n, [None] * n
    k_n, theta_n, omega_n, af_n, de_n, cf_n = [], [], [], [], [], []
    cap_gap_sector = np.zeros(n)
    xbar_sector = np.zeros(n)

    for j in range(n):
        k_jf = firms["k"][j]
        theta_jf = firms["theta"][j]
        omega_jf = firms["omega"][j]
        a_f = firms["a_f"][j]
        c_jf = firms["c_f"][j]
        c_rate = firms["c_f_rate"][j]
        gamma_f = firms["gamma_f"][j]
        d_e_jf = firms["d_e"][j]

        d_jf = omega_jf * x_star[j]
        d_e_new = ALPHA[j] * d_e_jf + (1.0 - ALPHA[j]) * d_jf
        x_bar = NU[j] * theta_jf * k_jf
        x_jf = np.maximum(np.minimum(np.minimum(d_e_new, d_jf), x_bar), 0.0)
        z_ijf = a_f * x_jf[None, :]
        pi_jf = x_jf - z_ijf.sum(axis=0) - c_jf
        cap_gap = np.maximum(d_jf - x_bar, 0.0)
        I_exp = KAPPA[j] * np.maximum(pi_jf, 0.0) + ETA[j] * cap_gap
        q_ijf = gamma_f * I_exp[None, :]

        # Capital law with depreciation, consistent with Solow-style stock accumulation.
        k_new = np.maximum((1.0 - DELTA[j]) * k_jf + I_exp, 0.0)
        i_rate = I_exp / np.maximum(k_jf, 1.0)
        theta_new = theta_jf * (1.0 + MU[j] * i_rate)

        a_f_new = a_f.copy()
        shock = rng.random(len(k_jf)) < P_INN[j]
        if shock.any():
            reduc = rng.uniform(0.0, MU[j], len(k_jf)) * shock.astype(float)
            a_f_new *= (1.0 - reduc)[None, :]
            a_f_new = np.maximum(a_f_new, 0.0)

        x_tot = x_jf.sum()
        omega_new = x_jf / x_tot if x_tot > 1e-9 else omega_jf.copy()

        if dynamic_fixed_costs:
            c_new = c_rate * k_new
        else:
            c_new = c_jf.copy()

        k_n.append(k_new)
        theta_n.append(theta_new)
        omega_n.append(omega_new)
        af_n.append(a_f_new)
        de_n.append(d_e_new)
        cf_n.append(c_new)
        x_jf_out[j] = x_jf
        z_ijf_out[j] = z_ijf
        q_ijf_out[j] = q_ijf
        cap_gap_sector[j] = cap_gap.sum()
        xbar_sector[j] = x_bar.sum()

    x_new = np.array([arr.sum() for arr in x_jf_out], dtype=float)
    A_raw = np.zeros_like(A)
    B_raw = np.zeros_like(B)
    for j in range(n):
        xs = x_jf_out[j].sum()
        if xs > 1e-9:
            A_raw[:, j] = z_ijf_out[j].sum(axis=1) / xs
        else:
            A_raw[:, j] = A[:, j]
        dX = max(abs(x_new[j] - x[j]), eps_b)
        B_raw[:, j] = q_ijf_out[j].sum(axis=1) / dX

    A_new = A_raw
    B_new = lambda_B * B + (1.0 - lambda_B) * B_raw
    B_ceil = np.where(B0_ref > 0, 5.0 * B0_ref, 1.0)
    B_new = np.clip(B_new, 0.0, B_ceil)

    firms_new = {
        "k": k_n,
        "theta": theta_n,
        "omega": omega_n,
        "a_f": af_n,
        "c_f": cf_n,
        "gamma_f": firms["gamma_f"],
        "d_e": de_n,
        "c_f_rate": firms["c_f_rate"],
    }

    diag = {
        "I_agg": np.array([q_ijf_out[j].sum() for j in range(n)], dtype=float),
        "I_exp_sector": np.array([q_ijf_out[j].sum() for j in range(n)], dtype=float),
        "cap_gap_sector": cap_gap_sector,
        "xbar_sector": xbar_sector,
        "x_star": x_star,
        "A_raw": A_raw,
        "B_raw": B_raw,
    }
    return x_new, A_new, B_new, firms_new, diag


def run_simulation(payload: dict, seed_override: int | None = None) -> Tuple[pd.DataFrame, dict]:
    meta = payload["model_meta"]
    base_year = int(meta["base_year"])
    sector_names = meta["sector_names"]
    sector_short = meta.get("sector_names_short", sector_names)
    n = len(sector_names)
    params = payload
    sim_params = payload["sim_params"]
    T = int(sim_params["T"])
    growth_u = float(sim_params.get("growth_u", 0.015))
    seed = int(seed_override if seed_override is not None else sim_params.get("seed", 42))
    rng = np.random.default_rng(seed)

    x = _to_np(payload["X0"])
    A = _to_np(payload["A0"])
    B = _to_np(payload["B0"])
    B0_ref = B.copy()
    u = _to_np(payload.get("u0_model", payload.get("u0_raw")))
    firms = init_firms_from_payload(payload, rng)

    history = {"x": [x.copy()], "A": [A.copy()], "B": [B.copy()], "u": [u.copy()], "firms": [firms], "diag": []}
    rows: List[dict] = []

    for t in range(T + 1):
        year = base_year + t
        K_agg = np.array([firms["k"][j].sum() for j in range(n)], dtype=float)
        th_avg = np.array([firms["theta"][j].mean() for j in range(n)], dtype=float)
        HHI = np.array([hhi(firms["omega"][j]) for j in range(n)], dtype=float)
        rho_A = float(np.max(np.abs(np.linalg.eigvals(A))))
        intermediate = A @ x
        row = {
            "t": t,
            "year": year,
            "rho_A": rho_A,
            "gross_output_total": float(x.sum()),
            "final_demand_total": float(u.sum()),
            "intermediate_total": float(intermediate.sum()),
            "value_added_proxy_total": float(x.sum() - intermediate.sum()),
            "K_total": float(K_agg.sum()),
        }
        for j in range(n):
            sn = sector_names[j]
            row[f"X_{sn}"] = float(x[j])
            row[f"K_{sn}"] = float(K_agg[j])
            row[f"theta_{sn}"] = float(th_avg[j])
            row[f"fd_share_{sn}"] = float(u[j] / max(x[j], 1.0))
            row[f"HHI_{sn}"] = float(HHI[j])
            row[f"A_diag_{sn}"] = float(A[j, j])
        for i in range(n):
            for j in range(n):
                row[f"A_{i}{j}"] = float(A[i, j])
                row[f"B_{i}{j}"] = float(B[i, j])
        rows.append(row)

        if t == T:
            break

        x_next, A_next, B_next, firms_next, diag = step(x, A, B, u, firms, params, rng, B0_ref)
        rows[-1]["I_total"] = float(diag["I_agg"].sum())
        rows[-1]["capital_block_total"] = float((B_next @ (x_next - x)).sum())
        for j in range(n):
            rows[-1][f"I_{sector_names[j]}"] = float(diag["I_agg"][j])
            rows[-1][f"cap_gap_{sector_names[j]}"] = float(diag["cap_gap_sector"][j])
            rows[-1][f"xbar_{sector_names[j]}"] = float(diag["xbar_sector"][j])
            rows[-1][f"xstar_{sector_names[j]}"] = float(diag["x_star"][j])

        u = u * (1.0 + growth_u)
        x, A, B, firms = x_next, A_next, B_next, firms_next
        history["x"].append(x.copy())
        history["A"].append(A.copy())
        history["B"].append(B.copy())
        history["u"].append(u.copy())
        history["firms"].append(firms)
        history["diag"].append(diag)

    # Exact residuals using x(t+2) where available.
    df = pd.DataFrame(rows)
    resid = np.full(len(df), np.nan, dtype=float)
    cap_block_exact = np.full(len(df), np.nan, dtype=float)
    for t in range(len(df) - 2):
        x_t1 = history["x"][t + 1]
        x_t2 = history["x"][t + 2]
        A_t1 = history["A"][t + 1]
        B_t1 = history["B"][t + 1]
        u_t1 = history["u"][t + 1]
        r = x_t1 - A_t1 @ x_t1 - B_t1 @ (x_t2 - x_t1) - u_t1
        resid[t] = float(np.linalg.norm(r) / (np.linalg.norm(x_t1) + 1e-15))
        cap_block_exact[t] = float((B_t1 @ (x_t2 - x_t1)).sum())
    if len(df) >= 2:
        resid[-2:] = resid[len(df) - 3] if len(df) >= 3 and np.isfinite(resid[len(df) - 3]) else np.nan
        cap_block_exact[-2:] = cap_block_exact[len(df) - 3] if len(df) >= 3 else np.nan
    df["balance_resid"] = resid
    df["capital_block_exact_total"] = cap_block_exact
    df["gross_output_index"] = df["gross_output_total"] / max(float(df.loc[0, "gross_output_total"]), 1e-12)
    df["final_demand_index"] = df["final_demand_total"] / max(float(df.loc[0, "final_demand_total"]), 1e-12)
    df["value_added_index"] = df["value_added_proxy_total"] / max(float(df.loc[0, "value_added_proxy_total"]), 1e-12)
    return df, {"sector_names": sector_names, "sector_short": sector_short, "T": T, "seed": seed, "n_firms": meta["n_firms"]}


def make_figures(df: pd.DataFrame, out: Path, sector_names: List[str], sector_short: List[str], T: int, n_firms: List[int]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    years = df["year"].values
    n = len(sector_names)
    X_mat = np.column_stack([df[f"X_{sn}"].values for sn in sector_names])
    K_mat = np.column_stack([df[f"K_{sn}"].values for sn in sector_names])
    th_mat = np.column_stack([df[f"theta_{sn}"].values for sn in sector_names])
    rho = df["rho_A"].values
    resid = df["balance_resid"].values
    total_agents = sum(n_firms)
    A_t0 = np.array([[df.iloc[0][f"A_{i}{j}"] for j in range(n)] for i in range(n)])
    A_tT = np.array([[df.iloc[-1][f"A_{i}{j}"] for j in range(n)] for i in range(n)])
    B_t0 = np.array([[df.iloc[0][f"B_{i}{j}"] for j in range(n)] for i in range(n)])
    B_tT = np.array([[df.iloc[-1][f"B_{i}{j}"] for j in range(n)] for i in range(n)])

    # Fig 1
    fig1, ax = plt.subplots(figsize=(9, 5))
    fig1.suptitle("Динамика нормированного валового выпуска $X_j(t)/X_j(0)$", fontsize=12, fontweight="bold")
    X_norm = X_mat / X_mat[0, :]
    for j in range(n):
        ax.plot(years, X_norm[:, j], color=COLORS[j], marker=MARKERS[j], markevery=5, label=sector_names[j])
    ax.axhline(1.0, color="black", lw=0.9, ls="--", label="базовый уровень $t=0$")
    ax.set_xlabel("Год")
    ax.set_ylabel("$X_j(t)/X_j(0)$")
    ax.legend(loc="upper left", ncol=2)
    ax.text(0.99, 0.97, f"T={T}, $N_{{agents}}$={total_agents}", transform=ax.transAxes, ha="right", va="top", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
    fig1.tight_layout(); fig1.savefig(out / "fig_1_trajectories.png"); plt.close(fig1)

    # Fig 2
    fig2, axes2 = plt.subplots(1, 2, figsize=(12, 5))
    fig2.suptitle("Структурная динамика совокупного выпуска", fontsize=12, fontweight="bold")
    ax = axes2[0]
    ax.plot(years, df["gross_output_index"].values, color="#1f77b4", lw=2.4, label="$\\sum X_j$ — валовой выпуск")
    ax.plot(years, df["value_added_index"].values, color="#2ca02c", lw=2.2, ls="-.", label="value-added proxy")
    ax.plot(years, df["final_demand_index"].values, color="#d62728", lw=2.4, ls="--", label="$\\sum u_j$ — конечный спрос")
    ax.axhline(1.0, color="gray", lw=0.8, ls=":")
    ax.set_xlabel("Год")
    ax.set_ylabel("Нормированный индекс (база = 1)")
    ax.set_title("Выпуск, value added proxy и конечный спрос")
    ax.legend(loc="upper left")
    ax = axes2[1]
    X_row_sum = X_mat.sum(axis=1, keepdims=True)
    X_share = np.where(X_row_sum > 0, X_mat / X_row_sum * 100.0, 0.0)
    ax.stackplot(years, X_share.T, labels=sector_names, colors=COLORS, alpha=0.75)
    ax.set_xlabel("Год")
    ax.set_ylabel("Доля в совокупном выпуске, %")
    ax.set_title("Отраслевая структура выпуска")
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right", ncol=2, fontsize=8)
    fig2.tight_layout(); fig2.savefig(out / "fig_2_structure.png"); plt.close(fig2)

    # Fig 3
    fig3, axes3 = plt.subplots(1, 2, figsize=(12, 5))
    fig3.suptitle("Анализ устойчивости: спектральные свойства матрицы $A(t)$", fontsize=12, fontweight="bold")
    ax = axes3[0]
    ax.plot(years, rho, color="#333333", lw=2.2, label="$\\rho(A(t))$")
    ax.axhline(1.0, color="crimson", lw=1.5, ls="--", label="граница продуктивности $\\rho=1$")
    ax.fill_between(years, rho, 1.0, where=(rho < 1.0), alpha=0.1, color="green", label="продуктивная зона")
    ax.annotate(f"$\\rho(A(0))={rho[0]:.4f}$", xy=(years[0], rho[0]), xytext=(years[3], rho[0] + 0.03), fontsize=8,
                arrowprops=dict(arrowstyle="->", color="gray"))
    ax.set_xlabel("Год"); ax.set_ylabel("$\\rho(A)$"); ax.set_title("Спектральный радиус $\\rho(A(t))$"); ax.legend(loc="lower right")
    ax = axes3[1]
    eig0 = np.linalg.eigvals(A_t0); eigT = np.linalg.eigvals(A_tT)
    theta_c = np.linspace(0, 2 * np.pi, 300)
    ax.plot(np.cos(theta_c), np.sin(theta_c), color="gray", lw=0.8, alpha=0.6, label="единичная окружность")
    ax.scatter(eig0.real, eig0.imag, s=80, marker="o", color="#1f77b4", zorder=4, label="$A(0)$")
    ax.scatter(eigT.real, eigT.imag, s=80, marker="*", color="#d62728", zorder=4, label="$A(T)$")
    ax.axhline(0, color="black", lw=0.5); ax.axvline(0, color="black", lw=0.5)
    ax.set_xlabel("Re"); ax.set_ylabel("Im"); ax.set_title("Собственные числа $A(0)$ и $A(T)$")
    ax.legend(loc="upper right", fontsize=8); ax.set_aspect("equal", adjustable="box")
    fig3.tight_layout(); fig3.savefig(out / "fig_3_stability.png"); plt.close(fig3)

    # Fig 4: show both A and B evolution.
    fig4, axes4 = plt.subplots(2, 3, figsize=(15, 8))
    fig4.suptitle(
        f"Эволюция матриц $A(t)$ и $B(t)$: t=0 → T={T}",
        fontsize=12,
        fontweight="bold",
    )
    for row_id, (M0, MT, label, cmap) in enumerate([(A_t0, A_tT, "A", "YlOrRd"), (B_t0, B_tT, "B", "YlGnBu")]):
        vmax = max(M0.max(), MT.max()) if max(M0.max(), MT.max()) > 0 else 1.0
        dM = MT - M0
        vmax_d = max(abs(dM).max(), 1e-6)
        norm_d = TwoSlopeNorm(vmin=-vmax_d, vcenter=0.0, vmax=vmax_d)
        for col, M, ttl in [(0, M0, f"{label}(0)"), (1, MT, f"{label}(T)"), (2, dM, f"Δ{label} = {label}(T)-{label}(0)")]:
            ax = axes4[row_id, col]
            if col < 2:
                im = ax.imshow(M, cmap=cmap, aspect="auto", vmin=0, vmax=vmax)
            else:
                im = ax.imshow(M, cmap="RdYlGn_r", norm=norm_d, aspect="auto")
            ax.set_xticks(range(n)); ax.set_xticklabels(sector_short, rotation=30, ha="right")
            ax.set_yticks(range(n)); ax.set_yticklabels(sector_short)
            for i in range(n):
                for j in range(n):
                    text = f"{M[i, j]:+.3f}" if col == 2 else f"{M[i, j]:.3f}"
                    ax.text(j, i, text, ha="center", va="center", fontsize=7)
            ax.set_title(ttl)
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig4.tight_layout(); fig4.savefig(out / "fig_4_matrix.png"); plt.close(fig4)

    # Fig 5
    fig5, axes5 = plt.subplots(1, 2, figsize=(12, 5))
    fig5.suptitle("Микро-макро взаимодействие: технология и капитал", fontsize=12, fontweight="bold")
    ax = axes5[0]
    for j in range(n):
        ax.plot(years, th_mat[:, j], color=COLORS[j], marker=MARKERS[j], markevery=5, label=sector_names[j])
    ax.set_xlabel("Год"); ax.set_ylabel("$\\bar{\\theta}_j(t)$"); ax.set_title("Средний технологический уровень")
    ax.legend(ncol=2, loc="best")
    ax = axes5[1]
    K_norm = K_mat / K_mat[0, :]
    for j in range(n):
        ax.plot(years, K_norm[:, j], color=COLORS[j], marker=MARKERS[j], markevery=5, label=sector_names[j])
    ax.axhline(1.0, color="black", lw=0.8, ls="--", alpha=0.5)
    ax.set_xlabel("Год"); ax.set_ylabel("$K_j(t)/K_j(0)$"); ax.set_title("Нормированный капитал")
    ax.legend(ncol=2, loc="best")
    fig5.tight_layout(); fig5.savefig(out / "fig_5_micro.png"); plt.close(fig5)

    # Fig 6
    fig6, ax = plt.subplots(figsize=(9, 5))
    fig6.suptitle("Верификация динамического баланса: невязка $\\|r(t)\\|/\\|x(t)\\|$", fontsize=12, fontweight="bold")
    resid_plot = np.where(np.isfinite(resid) & (resid > 0), resid, np.nan)
    ax.semilogy(years, resid_plot, color="darkorange", lw=2.2, label="точечная невязка")
    valid = pd.Series(resid_plot).interpolate(limit_direction="both")
    resid_ma = valid.rolling(3, center=True, min_periods=1).mean().values
    ax.semilogy(years, resid_ma, color="black", lw=1.5, alpha=0.6, label="МА(3)")
    ax.axhline(0.10, color="green", lw=1.0, ls=":", alpha=0.7, label="порог 10%")
    ax.axhline(0.05, color="blue", lw=1.0, ls=":", alpha=0.7, label="порог 5%")
    ax.set_xlabel("Год"); ax.set_ylabel("$\\|r(t+1)\\|/\\|x(t+1)\\|$ (лог. шкала)")
    ax.set_title("Относительная невязка МОБ по точной формуле (4.37)")
    ax.legend(loc="best")
    fig6.tight_layout(); fig6.savefig(out / "fig_6_balance.png"); plt.close(fig6)


def print_summary(df: pd.DataFrame, sector_names: List[str]) -> None:
    cols_x = [f"X_{sn}" for sn in sector_names]
    steps = [0, 5, 10, 20, 30]
    sub = df[df["t"].isin(steps)].copy()
    w = 92
    print("\n" + "═" * w)
    print("МАКРО-ТРАЕКТОРИЯ: ВАЛОВЫЙ ВЫПУСК X_j(t), млн евро")
    print("─" * w)
    hdr = f"{'t':>4}  {'Год':>6} " + "".join(f"  {sn[:10]:>11}" for sn in sector_names)
    print(hdr)
    print("─" * w)
    for _, row in sub.iterrows():
        vals = "".join(f"  {row[c]:>11.0f}" for c in cols_x)
        print(f"{int(row['t']):>4}  {int(row['year']):>6}{vals}")
    print("\n" + "─" * w)
    print("СИСТЕМНЫЕ ПОКАЗАТЕЛИ")
    print("─" * w)
    print(f"{'t':>4}  {'Год':>6}  {'ρ(A)':>8}  {'X idx':>9}  {'u idx':>9}  {'VA idx':>9}  {'balance':>12}")
    print("─" * w)
    for _, row in sub.iterrows():
        print(f"{int(row['t']):>4}  {int(row['year']):>6}  {row['rho_A']:>8.4f}  {row['gross_output_index']*100:>8.2f}%  {row['final_demand_index']*100:>8.2f}%  {row['value_added_index']*100:>8.2f}%  {row['balance_resid']:>12.4e}")
    print("═" * w + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Revised forward simulation for the two-level ABM input-output model.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--params", type=str, default=None, help="Path to calibration params.json")
    parser.add_argument("--output", type=str, default="simulation_output_revised", help="Output directory")
    parser.add_argument("--seed", type=int, default=None, help="Override RNG seed")
    parser.add_argument("--no-plots", action="store_true", help="Skip plots")
    args = parser.parse_args()

    payload = load_payload(Path(args.params) if args.params else None)
    df, meta = run_simulation(payload, seed_override=args.seed)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "macro_trajectory.csv"
    df.to_csv(csv_path, index=False, float_format="%.6g")

    print("=" * 72)
    print("Двухуровневая АБМ МОБ — revised forward simulation")
    print(f"Базовый год {payload['model_meta']['base_year']} | T={meta['T']} | seed={meta['seed']}")
    print(f"Результаты → {out.resolve()}")
    print("=" * 72)
    print_summary(df, meta["sector_names"])

    if not args.no_plots:
        make_figures(df, out, meta["sector_names"], meta["sector_short"], meta["T"], meta["n_firms"])
        print(f"Графики сохранены в {out.resolve()}")


if __name__ == "__main__":
    main()
