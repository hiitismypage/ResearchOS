#!/usr/bin/env python3
"""
simulate.py — форвардная симуляция двухуровневой АБМ МОБ.

Загружает начальные условия из выхода calibrate.py:
    python calibrate.py data/estat_naio_10_cp1700.csv data/Балашова_Германия.xlsx \\
        --country DE --year 2015 --output results/calibration

Запуск симуляции:
    python simulate.py --calibration-dir results/calibration [--output results/simulation] [--seed 42]

Трёхэтапный итерационный цикл (раздел 5.5 ВКР):

  Этап 1 — квазистатическая цель (ур-е 4.6/4.7):
      (I − A(t) − G_U·B(t)) · x*(t+1) = u(t)

  Этап 2 — решения фирм (ур-я 4.18–4.28):
      d_jf       = ω_jf · x*_j                          (4.18)
      d̂_jf      = α·d̂_jf + (1−α)·d_jf                 (4.19)
      x̄_jf      = ν_j · θ_jf · k_jf                    (4.20)
      x_jf       = min{d̂_jf, d_jf, x̄_jf}               (4.21)
      z_ijf      = a_ijf · x_jf                          (4.22)
      π_jf       = x_jf − Σz_ijf − c_jf                 (4.23)
      I_jf       = κ·max{π,0} + η·max{d−x̄,0}            (4.24)
      q_ijf      = γ_ijf · I_jf                          (4.25)
      k_jf(t+1)  = max{(1−δ)·k_jf + I_jf, k_min}       (4.26) ← точно по уравнению
      θ_jf(t+1)  = θ_jf·(1 + μ·I_jf/k_jf)              (4.27) ← точно по уравнению
        + инновационный шок с вер-ю p_inn: a_ijf *= (1−U(0,μ))
      ω_jf(t+1)  = x_jf / Σx_jg                         (4.28)

  Этап 3 — агрегирование (ур-я 4.29–4.31):
      x_j = Σ x_jf         (4.29)
      a_ij = Σz_ijf/Σx_jf  (4.30)
      b_ij = Σq_ijf/|Δx_j| (4.31)

  Примечание по k_min:
      Нижняя граница k_min предотвращает деление на нуль в (4.27) при
      крайне убыточных фирмах и обеспечивает численную устойчивость.
      k_min = 1e-4 М€ (100 евро) — экономически незначимо, технически необходимо.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

# ─────────────────────────────────────────────────────────────────────────────
# УПРАВЛЯЮЩИЕ ПАРАМЕТРЫ СИМУЛЯЦИИ (не калибруются, задаются здесь)
# ─────────────────────────────────────────────────────────────────────────────

T       = 30       # горизонт симуляции, шагов
G_U     = 0.015    # детерминированный тренд роста конечного спроса (ур-е 4.33)
SIGMA_U = 0.020    # σ_u: стд. стохастического шока спроса ε_j(t) ~ N(0, σ_u²) (ур-е 4.33)
EPS_B   = 1.0      # ε_b: пол |Δx_j| в знаменателе B (ур-е 4.31), млн евро
CLIP_B_FACTOR = 5.0  # B(t) ≤ 5·B(0) для ненулевых элементов
CLIP_B_ABS    = 1.0  # потолок для нулевых элементов B(0)
K_MIN   = 1e-4     # нижняя граница капитала фирмы, млн евро (100 евро)

# ─────────────────────────────────────────────────────────────────────────────
# ВИЗУАЛИЗАЦИЯ
# ─────────────────────────────────────────────────────────────────────────────

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 10,
    'axes.titlesize': 11, 'axes.labelsize': 10,
    'legend.fontsize': 8.5, 'lines.linewidth': 1.8,
    'figure.dpi': 150, 'savefig.dpi': 200,
    'savefig.bbox': 'tight', 'axes.grid': True,
    'grid.alpha': 0.3, 'grid.linestyle': '--',
})

COLORS  = ['#d62728', '#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd']
MARKERS = ['o', 's', '^', 'D', 'v']

# Русские названия секторов для отображения на графиках
# Ключ — английское имя из calibration output, значение — русское для подписей
RU_NAMES = {
    "Extraction":    "Добыча",
    "Energy":        "Энергетика",
    "Manufacturing": "Обработка",
    "Construction":  "Строительство",
    "Agriculture":   "С/х",
}

def _ru(name: str) -> str:
    """Вернуть русское название сектора (или само имя если нет в словаре)."""
    return RU_NAMES.get(name, name)


# ─────────────────────────────────────────────────────────────────────────────
# ЗАГРУЗКА КАЛИБРОВОЧНЫХ ДАННЫХ
# ─────────────────────────────────────────────────────────────────────────────

def load_calibration(cal_dir: str) -> dict:
    """
    Загрузить все начальные условия из выхода calibrate.py.

    Ожидаемая структура cal_dir/:
        csv/A0.csv, B0.csv, u0_X0.csv, sector_params.csv
        csv/firms_{sector_name_lower}.csv  — по одному на сектор

    Возвращает словарь с ключами:
        A0, B0, X0, U0      — матрицы и векторы (np.ndarray)
        N, N_FIRMS           — число секторов и фирм по секторам
        SECTOR_NAMES         — список строк
        DELTA, NU, KAPPA,   — отраслевые поведенческие параметры
        ETA, ALPHA, P_INN, MU  (np.ndarray длиной N)
        firms_raw            — dict {sector_name: pd.DataFrame} с данными фирм
    """
    p = Path(cal_dir) / "csv"

    sp = pd.read_csv(p / "sector_params.csv", index_col=0)
    sector_names: List[str] = list(sp.index)
    n = len(sector_names)

    def _arr(col: str) -> np.ndarray:
        return sp[col].values.astype(float)

    def _mat(name: str) -> np.ndarray:
        return pd.read_csv(p / f"{name}.csv", index_col=0).values.astype(float)

    ux   = pd.read_csv(p / "u0_X0.csv", index_col=0)
    X0   = ux["X0_M_EUR"].values.astype(float)
    U0   = ux["u0_M_EUR"].values.astype(float)
    A0   = _mat("A0")
    B0   = _mat("B0")

    firms_raw: dict = {}
    for sn in sector_names:
        fname = p / f"firms_{sn.lower()}.csv"
        if not fname.exists():
            raise FileNotFoundError(
                f"Файл фирм не найден: {fname}\n"
                f"Запустите calibrate.py с флагом --output {cal_dir}"
            )
        firms_raw[sn] = pd.read_csv(fname, index_col=0)

    n_firms = [len(firms_raw[sn]) for sn in sector_names]

    return {
        "A0": A0, "B0": B0, "X0": X0, "U0": U0,
        "N": n,
        "N_FIRMS": n_firms,
        "SECTOR_NAMES": sector_names,
        "DELTA":  _arr("delta"),
        "NU":     _arr("nu"),
        "KAPPA":  _arr("kappa"),
        "ETA":    _arr("eta"),
        "ALPHA":  _arr("alpha"),
        "P_INN":  _arr("p_inn"),
        "MU":     _arr("mu"),
        "firms_raw": firms_raw,
    }


def init_firms(cal: dict) -> dict:
    """
    Собрать начальное состояние агентов из сохранённых калибровочных CSV.

    Ключи возвращаемого словаря — списки длиной N, элемент j — массив для отрасли j:
        k       : k_jf(0), млн евро
        theta   : θ_jf(0)
        omega   : ω_jf(0)
        a_f     : (N, N_j) — индивидуальные технологические коэффициенты
        c_f     : постоянные издержки
        gamma_f : (N, N_j) — доли инвестиционного спроса
        d_e     : ожидаемый спрос = ω·X0_j
    """
    sector_names = cal["SECTOR_NAMES"]
    n = cal["N"]
    X0 = cal["X0"]

    k_l, theta_l, omega_l, af_l, cf_l, gf_l, de_l = [], [], [], [], [], [], []

    for j, sn in enumerate(sector_names):
        df   = cal["firms_raw"][sn]
        N_j  = len(df)

        k_jf     = df["k0"].values.astype(float)
        theta_jf = df["theta0"].values.astype(float)
        omega_jf = df["omega0"].values.astype(float)
        c_jf     = df["c_f"].values.astype(float)

        a_f = np.zeros((n, N_j))
        for i, sn_i in enumerate(sector_names):
            col = f"a_{sn_i}"
            if col in df.columns:
                a_f[i] = df[col].values.astype(float)

        gamma_f = np.zeros((n, N_j))
        for i, sn_i in enumerate(sector_names):
            col = f"gamma_{sn_i}"
            if col in df.columns:
                gamma_f[i] = df[col].values.astype(float)

        d_e_jf = omega_jf * X0[j]

        k_l.append(k_jf);      theta_l.append(theta_jf)
        omega_l.append(omega_jf); af_l.append(a_f)
        cf_l.append(c_jf);     gf_l.append(gamma_f)
        de_l.append(d_e_jf)

    return {
        'k': k_l, 'theta': theta_l, 'omega': omega_l,
        'a_f': af_l, 'c_f': cf_l, 'gamma_f': gf_l, 'd_e': de_l,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────────────────────────────────────

def leontief_target(x: np.ndarray, A: np.ndarray,
                    B: np.ndarray, u: np.ndarray) -> np.ndarray:
    """
    Квазистатическая цель (ур-е 4.7):
        (I − A(t) − G_U·B(t)) · x*(t+1) = u(t)
    """
    n = len(x)
    M = np.eye(n) - A - G_U * B
    try:
        x_star = np.linalg.solve(M, u)
    except np.linalg.LinAlgError:
        x_star, _, _, _ = np.linalg.lstsq(M, u, rcond=None)
    return np.maximum(x_star, 0.0)


def hhi(omega: np.ndarray) -> float:
    return float(np.dot(omega, omega))


def io_balance_residual(x: np.ndarray, x_next: np.ndarray,
                        A_next: np.ndarray, B_next: np.ndarray,
                        u: np.ndarray) -> float:
    """Относительная невязка ур-я (4.37): ‖r‖/‖x‖."""
    r = x_next - A_next @ x_next - B_next @ (x_next - x) - u
    return float(np.linalg.norm(r) / (np.linalg.norm(x_next) + 1e-15))


# ─────────────────────────────────────────────────────────────────────────────
# ШАГ СИМУЛЯЦИИ
# ─────────────────────────────────────────────────────────────────────────────

def step(x: np.ndarray, A: np.ndarray, B: np.ndarray,
         u: np.ndarray, firms: dict, rng: np.random.Generator,
         cal: dict):
    """
    Один шаг трёхэтапного цикла.
    Возвращает: x(t+1), A(t+1), B(t+1), firms(t+1), I_agg[j].
    """
    n          = cal["N"]
    N_FIRMS    = cal["N_FIRMS"]
    DELTA      = cal["DELTA"]
    NU         = cal["NU"]
    KAPPA      = cal["KAPPA"]
    ETA        = cal["ETA"]
    ALPHA_arr  = cal["ALPHA"]
    P_INN      = cal["P_INN"]
    MU         = cal["MU"]
    B0         = cal["B0"]

    # ── Этап 1: целевой выпуск ────────────────────────────────────────────
    x_star = leontief_target(x, A, B, u)    # ур-е (4.7)

    x_jf_out  = [None] * n
    z_ijf_out = [None] * n
    q_ijf_out = [None] * n
    k_n, theta_n, omega_n, af_n, de_n = [], [], [], [], []

    # ── Этап 2: решения фирм ──────────────────────────────────────────────
    for j in range(n):
        k_jf     = firms['k'][j]
        theta_jf = firms['theta'][j]
        omega_jf = firms['omega'][j]
        a_f      = firms['a_f'][j]      # (n, N_j)
        c_jf     = firms['c_f'][j]
        gamma_f  = firms['gamma_f'][j]  # (n, N_j)
        d_e_jf   = firms['d_e'][j]

        # (4.18) Спросовый сигнал
        d_jf = omega_jf * x_star[j]

        # (4.19) Адаптивные ожидания
        d_e_new = ALPHA_arr[j] * d_e_jf + (1.0 - ALPHA_arr[j]) * d_jf

        # (4.20) Производственная мощность
        x_bar = NU[j] * theta_jf * k_jf

        # (4.21) Фактический выпуск
        x_jf = np.minimum(np.minimum(d_e_new, d_jf), x_bar)
        x_jf = np.maximum(x_jf, 0.0)

        # (4.22) Промежуточный спрос
        z_ijf = a_f * x_jf[None, :]

        # (4.23) Прибыль (нормированные цены p_j = 1)
        pi_jf = x_jf - z_ijf.sum(axis=0) - c_jf

        # (4.24) Экспансионные инвестиции I_exp: из прибыли и дефицита мощностей
        cap_gap = np.maximum(d_jf - x_bar, 0.0)
        I_exp   = KAPPA[j] * np.maximum(pi_jf, 0.0) + ETA[j] * cap_gap

        # (4.25) Инвестиционный спрос по продуктам (для обновления B).
        # Используются только I_exp — маргинальные затраты на новые мощности.
        q_ijf = gamma_f * I_exp[None, :]

        # (4.26) Накопление капитала.
        # I_jf в ур-е (4.26) — полные валовые инвестиции I_tot = δ·k + I_exp:
        #   амортизационный фонд δ·k реинвестируется автоматически как
        #   обязательное обслуживание капитала (покрывается из валовой выручки),
        #   I_exp — только экспансионная часть, определяемая правилом (4.24).
        # Следствие: k_new = (1-δ)·k + δ·k + I_exp = k + I_exp ≥ k.
        k_new = np.maximum(k_jf + I_exp, K_MIN)

        # (4.27) Технологический уровень: θ растёт пропорционально I_exp/k.
        # Используются только экспансионные инвестиции — технологии улучшаются
        # при освоении новых мощностей, не при простом воспроизводстве старых.
        theta_new = theta_jf * (1.0 + MU[j] * I_exp / np.maximum(k_jf, K_MIN))

        # Инновационный шок (описан в §4.5): снижает a_ijf независимо от θ
        a_f_new = a_f.copy()
        N_j     = N_FIRMS[j]
        shock   = rng.random(N_j) < P_INN[j]
        if shock.any():
            reduc    = rng.uniform(0.0, MU[j], N_j) * shock.astype(float)
            a_f_new *= (1.0 - reduc)[None, :]
            a_f_new  = np.maximum(a_f_new, 0.0)

        # (4.28) Рыночные доли
        x_tot = x_jf.sum()
        omega_new = x_jf / x_tot if x_tot > 1e-9 else omega_jf.copy()

        k_n.append(k_new);       theta_n.append(theta_new)
        omega_n.append(omega_new); af_n.append(a_f_new)
        de_n.append(d_e_new)
        x_jf_out[j]  = x_jf
        z_ijf_out[j] = z_ijf
        q_ijf_out[j] = q_ijf

    # ── Этап 3: агрегирование ─────────────────────────────────────────────

    # (4.29)
    x_new = np.array([x_jf_out[j].sum() for j in range(n)])

    # (4.30)
    A_new = np.zeros((n, n))
    for j in range(n):
        xs = x_jf_out[j].sum()
        A_new[:, j] = (z_ijf_out[j].sum(axis=1) / xs
                       if xs > 1e-9 else A[:, j])

    # (4.31) — абсолютное значение |Δx_j|
    B_new = np.zeros((n, n))
    for j in range(n):
        dX = max(abs(x_new[j] - x[j]), EPS_B)
        B_new[:, j] = q_ijf_out[j].sum(axis=1) / dX

    B_ceil = np.where(B0 > 0, CLIP_B_FACTOR * B0, CLIP_B_ABS)
    B_new  = np.clip(B_new, 0.0, B_ceil)

    I_agg = np.array([q_ijf_out[j].sum() for j in range(n)])

    firms_new = {
        'k': k_n, 'theta': theta_n, 'omega': omega_n,
        'a_f': af_n, 'c_f': firms['c_f'], 'gamma_f': firms['gamma_f'],
        'd_e': de_n,
    }
    return x_new, A_new, B_new, firms_new, I_agg


# ─────────────────────────────────────────────────────────────────────────────
# ОСНОВНОЙ ЦИКЛ
# ─────────────────────────────────────────────────────────────────────────────

BASE_YEAR = 2015


def run(cal_dir: str, seed: int = 42) -> tuple:
    cal   = load_calibration(cal_dir)
    rng   = np.random.default_rng(seed)
    n     = cal["N"]
    sn    = cal["SECTOR_NAMES"]

    x     = cal["X0"].copy()
    A     = cal["A0"].copy()
    B     = cal["B0"].copy()

    # u0 = max((I - A0)·X0, ε) — формула (5.9) диплома.
    # Леонтьевски-согласованный конечный спрос гарантирует статический баланс
    # X = AX + u при t=0. Статистический C+G+NX из calibrate.py не включает
    # GFCF (P51G), поэтому для строительства и смежных секторов даёт заниженные
    # значения, несовместимые с начальным вектором выпуска.
    n     = cal["N"]
    u     = np.maximum((np.eye(n) - A) @ x, 1e-2)

    firms = init_firms(cal)

    rows: list = []
    firm_snapshots: dict = {}

    for t in range(T + 1):
        year   = BASE_YEAR + t
        K_agg  = np.array([firms['k'][j].sum()      for j in range(n)])

        if t in (0, T // 2, T):
            firm_snapshots[t] = {
                'k':     [arr.copy() for arr in firms['k']],
                'omega': [arr.copy() for arr in firms['omega']],
                'theta': [arr.copy() for arr in firms['theta']],
            }
        th_avg = np.array([firms['theta'][j].mean() for j in range(n)])
        HHI    = np.array([hhi(firms['omega'][j])   for j in range(n)])
        rho_A  = float(np.max(np.abs(np.linalg.eigvals(A))))
        fd_share = u / np.maximum(x, 1.0)

        row: dict = {
            't': t, 'year': year, 'rho_A': rho_A,
            'GDP_proxy': float(x.sum()),
            'K_total':   float(K_agg.sum()),
            'U_total':   float(u.sum()),
        }
        for j in range(n):
            row[f'X_{sn[j]}']       = float(x[j])
            row[f'K_{sn[j]}']       = float(K_agg[j])
            row[f'theta_{sn[j]}']   = float(th_avg[j])
            row[f'fd_share_{sn[j]}'] = float(fd_share[j])
            row[f'HHI_{sn[j]}']     = float(HHI[j])
            row[f'A_diag_{sn[j]}']  = float(A[j, j])
        for i in range(n):
            for jj in range(n):
                row[f'A_{i}{jj}'] = float(A[i, jj])
                row[f'B_{i}{jj}'] = float(B[i, jj])
        rows.append(row)

        if t == T:
            break

        x_next, A_next, B_next, firms_next, I_agg = step(x, A, B, u, firms, rng, cal)

        rows[-1]['balance_resid'] = io_balance_residual(x, x_next, A_next, B_next, u)
        rows[-1]['I_total'] = float(I_agg.sum())
        for j in range(n):
            rows[-1][f'I_{sn[j]}'] = float(I_agg[j])

        # (4.33): u_j(t+1) = u_j(t) * (1 + G_U + ε_j(t)),  ε_j ~ N(0, σ_u²)
        eps = rng.normal(0.0, SIGMA_U, size=n)
        u = np.maximum(u * (1.0 + G_U + eps), 1e-3)
        x, A, B, firms = x_next, A_next, B_next, firms_next

    df = pd.DataFrame(rows)
    df['balance_resid'] = df['balance_resid'].ffill()
    df['I_total'] = df['I_total'].fillna(0.0)
    for j in range(n):
        df[f'I_{sn[j]}'] = df[f'I_{sn[j]}'].fillna(0.0)
    return df, firm_snapshots


# ─────────────────────────────────────────────────────────────────────────────
# ВИЗУАЛИЗАЦИЯ
# ─────────────────────────────────────────────────────────────────────────────

def _smooth(arr: np.ndarray, w: int = 5) -> np.ndarray:
    kernel = np.ones(w) / w
    pad    = w // 2
    padded = np.pad(arr, pad, mode='edge')
    return np.convolve(padded, kernel, mode='valid')[:len(arr)]


def make_agent_figures(firm_snapshots: dict, out: Path, sn: List[str]) -> None:
    """
    Агентные графики — по одному рисунку на сектор для читаемости на листе.

    Рис. 9_1..9_5 : Распределение капитала k_jf (t=0 vs t=T)
    Рис. 10_1..10_5: Рыночные доли лидер/медиана/аутсайдер (ур-е 4.28)
    Рис. 11_1..11_5: Кривые Лоренца рыночных долей (t=0, t_mid, t=T)
    """
    n = len(sn)
    ru = [_ru(s) for s in sn]
    T_vals = sorted(firm_snapshots.keys())
    t0, t_mid, tT = T_vals[0], T_vals[1], T_vals[2]
    years = {t0: BASE_YEAR + t0, t_mid: BASE_YEAR + t_mid, tT: BASE_YEAR + tT}
    snap_years = [years[t0], years[t_mid], years[tT]]

    def lorenz(shares):
        s = np.sort(shares)
        cs = np.cumsum(s)
        cs = np.insert(cs, 0, 0)
        return np.linspace(0, 1, len(s) + 1), cs / cs[-1]

    def gini(shares):
        s = np.sort(shares)
        N = len(s)
        return float(np.sum((2 * np.arange(1, N + 1) - N - 1) * s) / (N * s.sum()))

    sector_labels = [s.lower().replace('/', '_') for s in [_ru(x) for x in sn]]

    for j in range(n):
        label   = sector_labels[j]
        ru_name = ru[j]

        # ── Рис. 9: распределение капитала ───────────────────────────────
        k0 = firm_snapshots[t0]['k'][j]
        kT = firm_snapshots[tT]['k'][j]
        fig, ax = plt.subplots(figsize=(7, 5))
        bins = np.linspace(0, max(kT.max(), k0.max()) * 1.05, 20)
        ax.hist(k0, bins=bins, alpha=0.60, color='steelblue',
                label=f'{years[t0]}', density=True)
        ax.hist(kT, bins=bins, alpha=0.60, color='tomato',
                label=f'{years[tT]}', density=True)
        ax.set_title(f'Распределение капитала фирм — {ru_name}', fontsize=11)
        ax.set_xlabel('$k_{jf}$, млн евро', fontsize=10)
        ax.set_ylabel('Плотность', fontsize=10)
        ax.legend(fontsize=9)
        plt.tight_layout()
        fig.savefig(out / f'fig_9_{j+1}_{label}.png')
        plt.close(fig)

        # ── Рис. 10: лидер / медиана / аутсайдер ─────────────────────────
        top_sh, med_sh, bot_sh = [], [], []
        for t_key in [t0, t_mid, tT]:
            om = firm_snapshots[t_key]['omega'][j]
            top_sh.append(float(np.max(om)))
            med_sh.append(float(np.median(om)))
            bot_sh.append(float(np.min(om)))
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(snap_years, top_sh, 'o-',  color='#d62728', lw=2.0, ms=7, label='Лидер')
        ax.plot(snap_years, med_sh, 's--', color='#2ca02c', lw=1.8, ms=6, label='Медиана')
        ax.plot(snap_years, bot_sh, 'v:',  color='#1f77b4', lw=1.5, ms=6, label='Аутсайдер')
        ax.set_title(f'Рыночные доли $\\omega_{{jf}}$ — {ru_name} (ур-е 4.28)', fontsize=11)
        ax.set_xlabel('Год', fontsize=10)
        ax.set_ylabel('$\\omega_{jf}$', fontsize=10)
        ax.legend(fontsize=9)
        ax.set_xticks(snap_years)
        plt.tight_layout()
        fig.savefig(out / f'fig_10_{j+1}_{label}.png')
        plt.close(fig)

        # ── Рис. 11: кривые Лоренца ───────────────────────────────────────
        colors_lc = ['steelblue', 'darkorange', 'tomato']
        fig, ax = plt.subplots(figsize=(7, 5))
        for t_key, col in zip([t0, t_mid, tT], colors_lc):
            om = firm_snapshots[t_key]['omega'][j]
            xs, ys = lorenz(om)
            g = gini(om)
            ax.plot(xs, ys, color=col, lw=2.0,
                    label=f'{years[t_key]}  (G = {g:.3f})')
        ax.plot([0, 1], [0, 1], 'k--', lw=0.9, alpha=0.5, label='Равенство')
        ax.set_title(f'Кривая Лоренца $\\omega_{{jf}}$ — {ru_name}', fontsize=11)
        ax.set_xlabel('Доля фирм', fontsize=10)
        ax.set_ylabel('Доля выпуска', fontsize=10)
        ax.legend(fontsize=9)
        plt.tight_layout()
        fig.savefig(out / f'fig_11_{j+1}_{label}.png')
        plt.close(fig)

    print(f'  Агентные рисунки (9–11) → {out}  [{n*3} файлов]')


def make_figures(df: pd.DataFrame, out: Path, sn: List[str], firm_snapshots: dict = None) -> None:
    """
    Построить 8 публикационных рисунков.
    Все текстовые подписи — русские; математические обозначения переменных — в оригинале.
    """
    out.mkdir(parents=True, exist_ok=True)
    years  = df['year'].values
    n      = len(sn)
    ru     = [_ru(s) for s in sn]           # русские названия для легенд
    ru_sh  = [_ru(s)[:4] for s in sn]       # сокращения для матричных тепловых карт

    X_mat  = np.column_stack([df[f'X_{s}'].values      for s in sn])
    K_mat  = np.column_stack([df[f'K_{s}'].values      for s in sn])
    th_mat = np.column_stack([df[f'theta_{s}'].values  for s in sn])
    I_mat  = np.column_stack([
        df.get(f'I_{s}', pd.Series(np.zeros(len(df)))).values for s in sn
    ])
    rho    = df['rho_A'].values
    resid  = df['balance_resid'].values
    gdp    = df['GDP_proxy'].values
    u_tot  = df['U_total'].values

    A_t0 = np.array([[df.iloc[0][f'A_{i}{j}']  for j in range(n)] for i in range(n)])
    A_tT = np.array([[df.iloc[-1][f'A_{i}{j}'] for j in range(n)] for i in range(n)])

    # ── Рисунок 1: нормированные траектории выпуска ──────────────────────
    fig1, ax = plt.subplots(figsize=(9, 5))
    fig1.suptitle('Динамика нормированного валового выпуска $X_j(t)/X_j(0)$',
                  fontsize=12, fontweight='bold')
    X_norm = X_mat / X_mat[0, :]
    for j in range(n):
        ax.plot(years, X_norm[:, j], color=COLORS[j], lw=0.8, alpha=0.25)
        ax.plot(years, _smooth(X_norm[:, j]), color=COLORS[j], lw=2.0,
                marker=MARKERS[j], markevery=5, label=ru[j])
    ax.axhline(1.0, color='black', lw=0.9, ls='--', label='базовый уровень $t=0$')
    ax.set_xlabel('Год')
    ax.set_ylabel('$X_j(t)\\ /\\ X_j(0)$')
    ax.legend(loc='upper left', ncol=2)
    fig1.tight_layout()
    fig1.savefig(out / 'fig_1_trajectories.png')
    plt.close(fig1)

    # ── Рисунок 2: структурная динамика ──────────────────────────────────
    fig2, axes2 = plt.subplots(1, 2, figsize=(12, 5))
    fig2.suptitle('Структурная динамика совокупного выпуска',
                  fontsize=12, fontweight='bold')
    ax = axes2[0]
    ax.plot(years, _smooth(gdp / gdp[0]), color='#1f77b4', lw=2.5,
            label='$\\sum X_j(t)/\\sum X_j(0)$ — выпуск')
    ax.plot(years, u_tot / u_tot[0], color='#d62728', lw=2.5, ls='--',
            label='$\\sum u_j(t)/\\sum u_j(0)$ — конечный спрос')
    ax.axhline(1.0, color='gray', lw=0.8, ls=':')
    ax.set_xlabel('Год')
    ax.set_ylabel('Нормированный индекс (база $t=0$, ед.)')
    ax.set_title('Совокупный выпуск и конечный спрос')
    ax.legend(loc='upper left')
    ax = axes2[1]
    X_share = X_mat / X_mat.sum(axis=1, keepdims=True) * 100
    for j in range(n):
        ax.plot(years, _smooth(X_share[:, j]), color=COLORS[j], lw=2.0,
                marker=MARKERS[j], markevery=5, label=ru[j])
    ax.set_xlabel('Год')
    ax.set_ylabel('Доля в совокупном выпуске, %')
    ax.set_title('Структурные сдвиги: доли секторов')
    ax.legend(ncol=1, fontsize=8)
    fig2.tight_layout()
    fig2.savefig(out / 'fig_2_structure.png')
    plt.close(fig2)

    # ── Рисунок 3: устойчивость матрицы A ────────────────────────────────
    fig3, axes3 = plt.subplots(1, 2, figsize=(12, 5))
    fig3.suptitle('Анализ устойчивости: спектральные свойства матрицы $A(t)$',
                  fontsize=12, fontweight='bold')
    ax = axes3[0]
    ax.plot(years, rho, color='#333333', lw=2.2, label='$\\rho(A(t))$')
    ax.axhline(1.0, color='crimson', lw=1.5, ls='--',
               label='граница продуктивности $\\rho=1$')
    ax.fill_between(years, rho, 1.0, where=(rho < 1.0),
                    alpha=0.1, color='green', label='продуктивная зона')
    ax.set_xlabel('Год')
    ax.set_ylabel('$\\rho(A(t))$')
    ax.set_title('Спектральный радиус $\\rho(A(t))$, ур-е (4.35)')
    ax.set_ylim(0, max(rho.max() * 1.15, 1.1))
    ax.legend(loc='upper right')
    ax = axes3[1]
    for j in range(n):
        a_d = df[f'A_diag_{sn[j]}'].values
        ax.plot(years, _smooth(a_d), color=COLORS[j], lw=2.0,
                marker=MARKERS[j], markevery=5, label=ru[j])
    ax.set_xlabel('Год')
    ax.set_ylabel('$a_{jj}(t)$')
    ax.set_title('Внутриотраслевые самозатраты $a_{jj}(t)$')
    ax.legend(fontsize=8, ncol=2)
    fig3.tight_layout()
    fig3.savefig(out / 'fig_3_stability.png')
    plt.close(fig3)

    # ── Рисунок 4: тепловые карты матрицы A ──────────────────────────────
    fig4, axes4 = plt.subplots(1, 3, figsize=(15, 4))
    fig4.suptitle(f'Эволюция матрицы прямых затрат $A(t)$: $t=0$ → $t=T={T}$',
                  fontsize=12, fontweight='bold')
    vmax_A = max(A_t0.max(), A_tT.max())
    for ax_i, (mat, title) in enumerate([(A_t0, '$A(t=0)$'), (A_tT, f'$A(t={T})$')]):
        ax = axes4[ax_i]
        im = ax.imshow(mat, cmap='YlOrRd', vmin=0, vmax=vmax_A)
        ax.set_xticks(range(n)); ax.set_xticklabels(ru_sh, rotation=30, ha='right')
        ax.set_yticks(range(n)); ax.set_yticklabels(ru_sh)
        for i in range(n):
            for j in range(n):
                ax.text(j, i, f'{mat[i,j]:.3f}',
                        ha='center', va='center', fontsize=7.5)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        ax.set_title(title)
        ax.set_xlabel('Сектор-потребитель')
        ax.set_ylabel('Сектор-поставщик')
    ax = axes4[2]
    dA = A_tT - A_t0
    vd = max(abs(dA).max(), 1e-4)
    dA_min, dA_max = dA.min(), dA.max()
    if dA_min < -1e-8 and dA_max > 1e-8:
        im2 = ax.imshow(dA, cmap='RdYlGn_r',
                        norm=TwoSlopeNorm(vmin=-vd, vcenter=0.0, vmax=vd))
    else:
        im2 = ax.imshow(dA, cmap='RdYlGn_r', vmin=-vd, vmax=vd)
    ax.set_xticks(range(n)); ax.set_xticklabels(ru_sh, rotation=30, ha='right')
    ax.set_yticks(range(n)); ax.set_yticklabels(ru_sh)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f'{dA[i,j]:+.3f}',
                    ha='center', va='center', fontsize=7.5)
    plt.colorbar(im2, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title(f'$\\Delta A = A(T={T}) - A(0)$')
    ax.set_xlabel('Сектор-потребитель')
    ax.set_ylabel('Сектор-поставщик')
    fig4.tight_layout()
    fig4.savefig(out / 'fig_4_matrix.png')
    plt.close(fig4)

    # ── Рисунок 5: технология и капитал ──────────────────────────────────
    fig5, axes5 = plt.subplots(1, 2, figsize=(12, 5))
    fig5.suptitle('Микро-макро взаимодействие: технологический уровень и капитал',
                  fontsize=12, fontweight='bold')
    ax = axes5[0]
    for j in range(n):
        ax.plot(years, th_mat[:, j], color=COLORS[j], marker=MARKERS[j],
                markevery=5, label=ru[j])
    ax.set_xlabel('Год')
    ax.set_ylabel('$\\bar{\\theta}_j(t)$, ед.')
    ax.set_title('Средний технологический уровень $\\bar{\\theta}_j(t)$, ур-е (4.27)')
    ax.legend(ncol=2, loc='best')
    ax = axes5[1]
    K_norm = K_mat / K_mat[0, :]
    for j in range(n):
        ax.plot(years, K_norm[:, j], color=COLORS[j], marker=MARKERS[j],
                markevery=5, label=ru[j])
    ax.axhline(1.0, color='black', lw=0.8, ls='--', alpha=0.5,
               label='базовый уровень')
    ax.set_xlabel('Год')
    ax.set_ylabel('$K_j(t)\\ /\\ K_j(0)$')
    ax.set_title('Нормированный запас капитала $K_j(t)/K_j(0)$, ур-е (4.26)')
    ax.legend(ncol=2, loc='best')
    fig5.tight_layout()
    fig5.savefig(out / 'fig_5_micro.png')
    plt.close(fig5)

    # ── Рисунок 6: верификация динамического баланса ─────────────────────
    fig6, ax = plt.subplots(figsize=(9, 5))
    fig6.suptitle(
        'Верификация динамического баланса: невязка $\\|r(t)\\|/\\|x(t)\\|$',
        fontsize=12, fontweight='bold')
    resid_plot = np.where(resid > 0, resid, 1e-12)
    ax.semilogy(years, resid_plot, color='darkorange', lw=2.2)
    ax.fill_between(years, resid_plot, alpha=0.15, color='darkorange')
    ax.axhline(0.33, color='gray', lw=1.2, ls='--', alpha=0.8)
    ax.text(years[-1], 0.33 * 1.12,
            'инвестиционный блок ~33%\n(начальное условие)',
            ha='right', va='bottom', fontsize=8, color='gray')
    ax.set_xlabel('Год')
    ax.set_ylabel('$\\|r(t+1)\\|\\ /\\ \\|x(t+1)\\|$ (лог. шкала)')
    ax.set_title('Относительная невязка МОБ, ур-е (4.37)')
    fig6.tight_layout()
    fig6.savefig(out / 'fig_6_balance.png')
    plt.close(fig6)

    # ── Рисунок 7: инвестиционные волны ──────────────────────────────────
    fig7, axes7 = plt.subplots(1, 2, figsize=(12, 5))
    fig7.suptitle('Инвестиционная динамика: объём и структура',
                  fontsize=12, fontweight='bold')
    mask    = df['I_total'].values > 0
    years_I = years[mask]
    I_mat_I = I_mat[mask, :]
    ax = axes7[0]
    ax.bar(years_I, df['I_total'].values[mask] / 1e3,
           color='#1f77b4', alpha=0.65, label='$I_{total}(t)$')
    ax2 = ax.twinx()
    ax2.plot(years_I, gdp[mask] / 1e6, color='#d62728', lw=2.2,
             marker='o', markevery=3, label='ВВП (прав. ось)')
    ax.set_xlabel('Год')
    ax.set_ylabel('Совокупные инвестиции, млрд евро')
    ax2.set_ylabel('Совокупный выпуск, трлн евро', color='#d62728')
    ax2.tick_params(axis='y', labelcolor='#d62728')
    ax.set_title('Совокупные инвестиции и валовый выпуск')
    lines1, lab1 = ax.get_legend_handles_labels()
    lines2, lab2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, lab1 + lab2, loc='upper left', fontsize=8)
    ax = axes7[1]
    I_base = np.where(I_mat_I[0, :] > 0, I_mat_I[0, :], 1.0)
    for j in range(n):
        ax.plot(years_I, _smooth(I_mat_I[:, j] / I_base[j]),
                color=COLORS[j], lw=2.0, marker=MARKERS[j],
                markevery=5, label=ru[j])
    ax.axhline(1.0, color='black', lw=0.8, ls='--', alpha=0.5,
               label='базовый уровень')
    ax.set_xlabel('Год')
    ax.set_ylabel('$I_j(t)\\ /\\ I_j(0)$')
    ax.set_title('Нормированные инвестиции по секторам')
    ax.legend(ncol=2, loc='upper left', fontsize=8)
    fig7.tight_layout()
    fig7.savefig(out / 'fig_7_investment.png')
    plt.close(fig7)

    # ── Рисунок 8: концентрация рынков (HHI) ─────────────────────────────
    fig8, ax = plt.subplots(figsize=(9, 5))
    fig8.suptitle(
        'Динамика концентрации рынков: индекс Херфиндаля--Хиршмана $HHI_j(t)$',
        fontsize=12, fontweight='bold')
    HHI_mat = np.column_stack([df[f'HHI_{s}'].values for s in sn])
    N_FIRMS  = [None] * n   # нет прямого доступа здесь — подпись без N_j
    for j in range(n):
        ax.plot(years, _smooth(HHI_mat[:, j]), color=COLORS[j], lw=2.0,
                marker=MARKERS[j], markevery=5, label=ru[j])
    ax.set_xlabel('Год')
    ax.set_ylabel('$HHI_j = \\sum_f \\omega_{jf}^2$')
    ax.set_title('$HHI_j(t)$ по отраслям (ур-е 4.28)')
    ax.legend(ncol=2, loc='upper right')
    fig8.tight_layout()
    fig8.savefig(out / 'fig_8_hhi.png')
    plt.close(fig8)

    if firm_snapshots is not None:
        make_agent_figures(firm_snapshots, out, sn)

    print(f'  Рисунки сохранены: {out}/')


# ─────────────────────────────────────────────────────────────────────────────
# СВОДКА В STDOUT
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(df: pd.DataFrame, sn: List[str]) -> None:
    steps = [0, 5, 10, 20, 30]
    sub   = df[df['t'].isin(steps)]
    w     = 80
    print('\n' + '═' * w)
    print('МАКРО-ТРАЕКТОРИЯ: ВАЛОВЫЙ ВЫПУСК X_j(t), млн евро')
    print('─' * w)
    hdr = f"{'t':>4}  {'Год':>6}" + ''.join(f'  {s[:8]:>10}' for s in sn)
    print(hdr); print('─' * w)
    for _, row in sub.iterrows():
        vals = ''.join(f'  {row[f"X_{s}"]:>10.0f}' for s in sn)
        print(f"{int(row['t']):>4}  {int(row['year']):>6}{vals}")
    print('\n─' * 1 + '─' * (w - 1))
    print('СИСТЕМНЫЕ ПОКАЗАТЕЛИ')
    print('─' * w)
    gdp0 = float(df.iloc[0]['GDP_proxy'])
    u0   = float(df.iloc[0]['U_total'])
    print(f"{'t':>4}  {'Год':>6}  {'ρ(A)':>8}  {'GDP idx':>9}  {'balance':>12}")
    print('─' * w)
    for _, row in sub.iterrows():
        res = row.get('balance_resid', float('nan'))
        print(f"{int(row['t']):>4}  {int(row['year']):>6}  "
              f"{row['rho_A']:>8.4f}  "
              f"{row['GDP_proxy']/gdp0*100:>9.2f}%  "
              f"{res:>12.4e}")
    print('═' * w + '\n')


# ─────────────────────────────────────────────────────────────────────────────
# ТОЧКА ВХОДА
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            'Форвардная симуляция двухуровневой АБМ МОБ. '
            'Загружает начальные условия из выхода calibrate.py.'
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--calibration-dir', default='results/calibration',
        help='Директория с выходом calibrate.py (содержит папку csv/)'
    )
    parser.add_argument(
        '--output', default='results/simulation',
        help='Директория для результатов симуляции'
    )
    parser.add_argument('--seed', type=int, default=42, help='Зерно ГСЧ')
    parser.add_argument('--no-plots', action='store_true',
                        help='Пропустить построение графиков')
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    print('=' * 65)
    print('Двухуровневая АБМ МОБ — форвардная симуляция')
    print(f'Базовый год {BASE_YEAR}, T={T} шагов, G_U={G_U:.3f}')
    print(f'Калибровка: {args.calibration_dir}')
    print(f'Зерно ГСЧ: {args.seed}')
    print('=' * 65)

    print('\n[1/3] Загрузка калибровки...')
    cal = load_calibration(args.calibration_dir)
    sn  = cal["SECTOR_NAMES"]
    total_agents = sum(cal["N_FIRMS"])
    print(f'  Секторов: {cal["N"]}  |  Агентов: {total_agents}  |  {sn}')

    print('\n[2/3] Запуск симуляции...')
    df, firm_snapshots = run(args.calibration_dir, seed=args.seed)

    csv_path = out / 'macro_trajectory.csv'
    df.to_csv(csv_path, index=False, float_format='%.6g')
    print(f'  Таблица: {csv_path}  ({len(df)} строк × {len(df.columns)} столбцов)')

    print_summary(df, sn)

    if not args.no_plots:
        print('[3/3] Построение графиков...')
        make_figures(df, out, sn, firm_snapshots=firm_snapshots)

    print(f'\nРезультаты → {out.resolve()}')
    print('=' * 65)


if __name__ == '__main__':
    main()
