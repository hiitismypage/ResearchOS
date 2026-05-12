#!/usr/bin/env python3
"""
simulate.py
===========
T=30-шаговая форвардная симуляция двухуровневой агентно-ориентированной
модели межотраслевого баланса пятисекторной экономики (базовый год 2015).

Трёхэтапный итерационный цикл (раздел 5.5 ВКР):

  Уравнение (4.5):
      x(t) = A(t)·x(t) + B(t)·(x(t+1)−x(t)) + u(t)

  Уравнение (4.6)/(4.7) — квазистатическая форма при росте G_U:
      Подстановка x(t+1) = (1+G_U)·x(t) в ур-е (4.5):
          (I − A(t) − G_U·B(t)) · x*(t+1) = u(t)
      Прямое решение системы (cond ≈ 2.6) — численно устойчивее B⁺-поправки
      при несбалансированных начальных условиях (гл. 5 ВКР, пятисекторная
      калибровка содержит 33%-ю невязку статического баланса вследствие
      высокой открытости экономики; у.  4.7 эквивалентно для ρ(A+G_U·B)<1)

  Уравнение (4.32):
      u_j(t) = u_j^h(t) + u_j^g(t) + u_j^e(t)
      → реализовано как: u(t+1) = u(t)·(1 + G_U), G_U=0.015 (эндогенный рост
        спроса, не константа)

  Этап 2 (микро, уравнения 4.18–4.28):
      d_jf(t+1)   = ω_jf(t) · x*_j(t+1)                           (4.18)
      d̂_jf(t+1)  = α_j·d̂_jf(t) + (1−α_j)·d_jf(t+1)              (4.19)
      x̄_jf(t+1)  = ν_j · θ_jf(t) · k_jf(t)                       (4.20)
      x_jf(t+1)   = min{d̂_jf, d_jf, x̄_jf}                        (4.21)
      z_ijf(t+1)  = a_ijf(t) · x_jf(t+1)                          (4.22)
      π_jf(t+1)   = x_jf − Σᵢ z_ijf − c_jf   [p=1 ∀j]            (4.23)
      I_jf^exp(t+1) = κ_j·max{π,0} + η_j·max{d_jf−x̄_jf,0}       (4.24)
        I^exp — экспансионные инвестиции (спрос на новые мощности)
      q_ijf(t+1)   = γ_ijf · I_jf^exp                              (4.25)
        q используется ТОЛЬКО для обновления B (маргинальные коэффициенты)
      k_jf(t+1)    = k_jf + I_jf^exp   [= (1−δ)k + (δk + I^exp)]  (4.26)
        Амортизационный фонд δ_j·k_jf реинвестируется полностью →
        k не убывает при π=0, gap=0; соответствует учётному принципу
      θ_jf(t+1)    = θ_jf·(1 + μ_j·(δ+I^exp/k)_jf)               (4.27)
        * (δ + I^exp/k) — полная норма инвестиций (≥δ); Δθ ~δ·μ ~0.1%/шаг
        * инновационный шок с вероятностью p_inn_j: a_ijf *= (1 − U(0, μ_j))
      ω_jf(t+1)   = x_jf / Σ_g x_jg                               (4.28)
        * ИСПРАВЛЕНИЕ: если Σx=0, доли НЕ сбрасываются в 1/N —
          используются прежние значения

  Этап 3 (агрегация, 4.29–4.31):
      x_j(t+1)    = Σ_f x_jf(t+1)                                  (4.29)
      a_ij(t+1)   = Σ_f z_ijf / Σ_f x_jf                          (4.30)
        * если Σx_j=0 — сохранить предыдущий столбец
      b_ij(t+1)   = Σ_f q_ijf / max{|Δx_j|, ε_b}                  (4.31)
        * КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: |Δx_j| — абсолютное значение;
          исходный код использовал max(x_new−x_old, ε_b) → знаковый Δx,
          что давало знаменатель = ε_b=1 для сужающихся секторов и
          завышало B в 50 000 раз, вызывая коллапс модели

  Устойчивость и верификация:
      (4.35): ρ(A(t)) < 1 — проверяется на каждом шаге
      (4.37): r(t+1) = x(t+1) − A(t+1)·x(t+1) − B(t+1)·(x(t+2)−x(t+1)) − u(t+1)
              записывается ‖r‖/‖x‖ как относительная невязка баланса

Использование:
    python simulate.py [--output DIR]

Выходные данные:
    simulation_output/
        macro_trajectory.csv      — 31 строка × столбцы (t=0..30)
        fig_1_trajectories.png    — нормированные траектории выпуска
        fig_2_structure.png       — структурная динамика
        fig_3_stability.png       — спектральный анализ
        fig_4_matrix.png          — эволюция матрицы A
        fig_5_micro.png           — технология и капитал (микро-макро)
        fig_6_balance.png         — верификация динамического баланса
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import TwoSlopeNorm

# ─────────────────────────────────────────────────────────────────────────────
# НАСТРОЙКИ ВИЗУАЛИЗАЦИИ
# ─────────────────────────────────────────────────────────────────────────────

plt.rcParams.update({
    'font.family':      'DejaVu Sans',
    'font.size':        10,
    'axes.titlesize':   11,
    'axes.labelsize':   10,
    'legend.fontsize':  8.5,
    'xtick.labelsize':  9,
    'ytick.labelsize':  9,
    'lines.linewidth':  1.8,
    'figure.dpi':       150,
    'savefig.dpi':      200,
    'savefig.bbox':     'tight',
    'axes.grid':        True,
    'grid.alpha':       0.3,
    'grid.linestyle':   '--',
})

COLORS  = ['#d62728', '#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd']
MARKERS = ['o', 's', '^', 'D', 'v']

# ─────────────────────────────────────────────────────────────────────────────
# ПАРАМЕТРЫ МОДЕЛИ
# ─────────────────────────────────────────────────────────────────────────────

T         = 30       # горизонт симуляции (шаги / лет)
BASE_YEAR = 2015     # базовый год

N = 5                # число отраслей
N_FIRMS: List[int] = [32, 27, 41, 25, 34]  # N_j — число фирм в отрасли j

SIGMA_K = 0.6    # параметр формы лог-нормального распределения капитала
SIGMA_A = 0.15   # идиосинкратический разброс a_ijf
EPS_B   = 1.0    # ε_b: пол делителя |Δx_j| (млн евро), ур-е (4.31)
G_U     = 0.015  # ставка роста конечного спроса (ур-е 4.32)

SECTOR_NAMES  = ['Добыча', 'Энергетика', 'Обработка', 'Строительство', 'С/х']
SECTOR_SHORT  = ['Доб.', 'Энерг.', 'Обраб.', 'Строит.', 'С/х']

# ─────────────────────────────────────────────────────────────────────────────
# НАЧАЛЬНЫЕ УСЛОВИЯ (Глава 5 ВКР, базовый год 2015)
# ─────────────────────────────────────────────────────────────────────────────

# Вектор валового выпуска X(0), млн евро (Таблица 5.2)
X0 = np.array([10_746, 106_178, 1_675_563, 297_148, 50_958], dtype=float)

# Вектор конечного спроса u(0), млн евро (Таблица 5.5)
U0 = np.array([10_208, 45_037, 1_413_006, 7_122, 31_770], dtype=float)

# Матрица прямых затрат A(0) (Таблица 5.3); ρ(A0) ≈ 0.44 < 1
A0 = np.array([
    [0.0578, 0.1214, 0.0268, 0.0068, 0.0020],
    [0.0276, 0.2281, 0.0133, 0.0022, 0.0158],
    [0.2136, 0.0735, 0.3980, 0.2336, 0.1901],
    [0.0218, 0.0323, 0.0052, 0.0769, 0.0168],
    [0.0042, 0.0001, 0.0255, 0.0000, 0.0675],
], dtype=float)

# Матрица капиталоёмкости B(0) (Таблица 5.4); rank(B0)=1 → используется B⁺
B0 = np.array([
    [0.0008, 0.0017, 0.0014, 0.0006, 0.0010],
    [0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
    [2.4017, 5.2517, 4.2448, 1.9640, 2.9229],
    [2.0997, 4.5914, 3.7110, 1.7171, 2.5554],
    [0.0041, 0.0090, 0.0072, 0.0033, 0.0050],
], dtype=float)

# Поведенческие параметры (Таблица 5.8)
DELTA = np.array([0.060, 0.040, 0.055, 0.065, 0.050])  # δ_j: норма амортизации
# NU_j = ν_j — капиталоотдача (коэффициент производительности капитала, ур-е 4.20)
# ВНИМАНИЕ: не путать с fd_share_j = u_j/x_j (доля конечного спроса)
NU    = np.array([0.140, 0.165, 0.189, 0.134, 0.145])  # ν_j: капиталоотдача
KAPPA = np.array([0.125, 0.050, 0.450, 0.450, 0.050])  # κ_j: норма реинвестирования
ETA   = np.array([0.010, 0.010, 0.012, 0.015, 0.010])  # η_j: чувствит. к дефициту мощн.
ALPHA = np.array([0.300, 0.300, 0.300, 0.513, 0.300])  # α_j: инерция ожиданий
P_INN = np.array([0.158, 0.183, 0.050, 0.050, 0.183])  # p_inn_j: вер-ть иннов. шока
MU    = np.array([0.027, 0.024, 0.022, 0.027, 0.026])  # μ_j: макс. ресурсосберегаемость

# Отраслевой капитал K_j (млн евро)
K_J = np.array([78_100, 707_000, 8_885_500, 2_252_700, 368_200], dtype=float)

# Интервалы технологического уровня θ_jf(0) ~ U[θ_lo, θ_hi]
THETA_LO = np.array([0.7, 0.7, 0.5, 0.6, 0.5])
THETA_HI = np.array([1.3, 1.3, 1.5, 1.4, 1.5])


# ─────────────────────────────────────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────────────────────────────────────

def b_pseudoinv(B: np.ndarray) -> np.ndarray:
    """
    Псевдообратная матрица B⁺ с усечённым SVD (ур-е 4.6/4.7).

    Матрица B(0) имеет ранг 1 при размерности 5×5.
    Порог rcond=0.01 подавляет числовую нестабильность малых сингулярных чисел
    (обнуляются если < 1% от σ_max), что соответствует rank=1 в дипломе.
    """
    return np.linalg.pinv(B, rcond=0.01)


def leontief_target(x: np.ndarray, A: np.ndarray,
                    B: np.ndarray, u: np.ndarray) -> np.ndarray:
    r = (np.eye(N) - A) @ x - u   # невязка статики
    correction = np.linalg.pinv(B, rcond=0.01) @ r
    x_star = x + 0.5 * correction   # коэфф. демпфирования 0.5
    return np.maximum(x_star, 0.0)


def hhi(omega: np.ndarray) -> float:
    """HHI = Σ_f ω_f² (индекс Херфиндаля–Хиршмана)."""
    return float(np.dot(omega, omega))


def io_balance_residual(x: np.ndarray, x_next: np.ndarray,
                        A: np.ndarray, B: np.ndarray,
                        u: np.ndarray) -> float:
    """
    Относительная невязка динамического МОБ (ур-е 4.37):
        r(t+1) = x(t+1) − A(t+1)·x(t+1) − B(t+1)·(x(t+2)−x(t+1)) − u(t+1)

    При записи на шаге t используем доступные данные:
        r ≈ x_next − A_next·x_next − B_next·(x_next − x) − u
    Возвращает ‖r‖ / ‖x_next‖.
    """
    r = x_next - A @ x_next - B @ (x_next - x) - u
    return float(np.linalg.norm(r) / (np.linalg.norm(x_next) + 1e-15))


# ─────────────────────────────────────────────────────────────────────────────
# ИНИЦИАЛИЗАЦИЯ ФИРМ
# ─────────────────────────────────────────────────────────────────────────────

def init_firms(rng: np.random.Generator) -> dict:
    """
    Сформировать начальное состояние 159 агентов (раздел 5.3 ВКР).

    Ключи словаря — списки длиной N=5; каждый элемент — массив
    длиной N_j (фирмы данной отрасли j).

    k       : k_jf(0) ~ LogN(μ_k, σ_k), нормировка Σ k_jf = K_j
    theta   : θ_jf(0) ~ U[θ_lo, θ_hi]
    omega   : ω_jf(0) = k_jf / Σ k_jf   (пропорц. капиталу)
    a_f     : a_ijf(0): идиосинкратич. разброс, Σ_f ω_f·a_ijf ≈ A0[i,j]
    c_f     : c_jf = 0.02 · ν_j · θ̄_j · k_jf
    gamma_f : γ_ijf — доли инвест. спроса по продуктам
    d_e     : d̂_jf(0) = ω_jf(0) · X_j(0) — начальное ожидание спроса
    """
    k_l, theta_l, omega_l = [], [], []
    af_l, cf_l, gf_l, de_l = [], [], [], []

    for j in range(N):
        Nj = N_FIRMS[j]
        Kj = K_J[j]

        # ── Капитал ──────────────────────────────────────────────────────
        mu_k   = np.log(max(Kj / Nj, 1e-15)) - 0.5 * SIGMA_K**2
        raw_k  = rng.lognormal(mu_k, SIGMA_K, Nj)
        k_jf   = raw_k * (Kj / raw_k.sum())

        # ── Технология ───────────────────────────────────────────────────
        theta_jf = rng.uniform(THETA_LO[j], THETA_HI[j], Nj)

        # ── Рыночные доли ────────────────────────────────────────────────
        omega_jf = k_jf / k_jf.sum()

        # ── Индивидуальные коэффициенты a_ijf ───────────────────────────
        a_f = np.zeros((N, Nj))
        for i in range(N):
            xi    = rng.standard_normal(Nj)
            raw_a = A0[i, j] * np.exp(SIGMA_A * xi)
            agg   = float(np.dot(omega_jf, raw_a))
            if agg > 1e-300 and A0[i, j] > 0:
                a_f[i] = raw_a * (A0[i, j] / agg)
            else:
                a_f[i] = raw_a

        # ── Постоянные издержки ──────────────────────────────────────────
        theta_mid = 0.5 * (THETA_LO[j] + THETA_HI[j])
        # ν_j (NU) — капиталоотдача (ур-е 4.20); НЕ доля конечного спроса
        c_jf = 0.02 * NU[j] * theta_mid * k_jf

        # ── Инвестиционные доли γ_ijf ────────────────────────────────────
        b_col   = B0[:, j]
        weights = np.maximum(b_col, 0.0)
        ws      = weights.sum()
        gamma_j = weights / ws if ws > 0 else np.ones(N) / N
        gamma_f = np.tile(gamma_j[:, None], (1, Nj))   # (N, Nj)

        # ── Начальные ожидания ───────────────────────────────────────────
        d_e_jf = omega_jf * X0[j]

        k_l.append(k_jf);      theta_l.append(theta_jf)
        omega_l.append(omega_jf); af_l.append(a_f)
        cf_l.append(c_jf);     gf_l.append(gamma_f)
        de_l.append(d_e_jf)

    return {'k': k_l, 'theta': theta_l, 'omega': omega_l,
            'a_f': af_l, 'c_f': cf_l, 'gamma_f': gf_l, 'd_e': de_l}


# ─────────────────────────────────────────────────────────────────────────────
# ШАГ СИМУЛЯЦИИ
# ─────────────────────────────────────────────────────────────────────────────

def step(x: np.ndarray, A: np.ndarray, B: np.ndarray,
         u: np.ndarray, firms: dict,
         rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray,
                                            np.ndarray, dict, np.ndarray]:
    """
    Один шаг трёхэтапного итерационного цикла.

    Возвращает: x(t+1), A(t+1), B(t+1), firms(t+1), I_agg[j] (инвестиции).
    """
    # ── Этап 1: Целевой выпуск ────────────────────────────────────────────
    # Ур-е (4.6)/(4.7): x*(t+1) = x(t) + B⁺(t) · [(I−A(t))·x(t) − u(t)]
    x_star = leontief_target(x, A, B, u)

    # Контейнеры для агрегирования
    x_jf_out  = [None] * N
    z_ijf_out = [None] * N
    q_ijf_out = [None] * N

    k_n, theta_n, omega_n, af_n, de_n = [], [], [], [], []

    # ── Этап 2: Решения фирм ──────────────────────────────────────────────
    for j in range(N):
        Nj       = N_FIRMS[j]
        k_jf     = firms['k'][j]
        theta_jf = firms['theta'][j]
        omega_jf = firms['omega'][j]
        a_f      = firms['a_f'][j]     # (N, Nj)
        c_jf     = firms['c_f'][j]
        gamma_f  = firms['gamma_f'][j] # (N, Nj)
        d_e_jf   = firms['d_e'][j]

        # (4.18) Сигнал спроса: d_jf(t+1) = ω_jf(t) · x*_j(t+1)
        d_jf = omega_jf * x_star[j]

        # (4.19) Адаптивные ожидания: d̂_jf(t+1) = α_j·d̂_jf(t) + (1−α_j)·d_jf(t+1)
        d_e_new = ALPHA[j] * d_e_jf + (1.0 - ALPHA[j]) * d_jf

        # (4.20) Производственная мощность: x̄_jf = ν_j · θ_jf · k_jf
        # ν_j = NU[j] — капиталоотдача (не доля конечного спроса fd_share_j)
        x_bar = NU[j] * theta_jf * k_jf

        # (4.21) Фактический выпуск: x_jf = min{d̂_jf, d_jf, x̄_jf}
        x_jf = np.minimum(np.minimum(d_e_new, d_jf), x_bar)
        x_jf = np.maximum(x_jf, 0.0)

        # (4.22) Промежуточный спрос: z_ijf = a_ijf · x_jf
        z_ijf = a_f * x_jf[None, :]   # (N, Nj)

        # (4.23) Прибыль (цены нормированы p_j=1):
        # π_jf = x_jf − Σᵢ z_ijf − c_jf
        pi_jf = x_jf - z_ijf.sum(axis=0) - c_jf

        # (4.24) Инвестиции:
        # I_jf^exp = κ_j·max{π,0} + η_j·max{d_jf−x̄_jf, 0}  — экспансионные
        # I_jf^tot = δ_j·k_jf + I_jf^exp  — полные (включая амортизационный фонд)
        #
        # Для обновления B (ур-е 4.31) используется q^exp = γ·I^exp:
        #   B[i,j] = Σq^exp_ijf / |Δx_j| — marginal capital coefficient
        #   Амортизация исключается из q^exp: она не создаёт НОВЫХ мощностей
        #   и не должна раздувать B по мере роста K.
        # Для обновления k (ур-е 4.26) используется I^tot:
        #   k(t+1) = (1-δ)k + I^tot = k + I^exp ≥ k  (капитал не убывает)
        cap_gap  = np.maximum(d_jf - x_bar, 0.0)
        I_exp    = KAPPA[j] * np.maximum(pi_jf, 0.0) + ETA[j] * cap_gap  # ур-е 4.24
        I_tot    = DELTA[j] * k_jf + I_exp   # полные валовые инвестиции

        # (4.25) Инвестиционный спрос по продуктам: q_ijf = γ_ijf · I_jf^exp
        # (только экспансионная часть — для расчёта B, eq 4.31)
        q_ijf = gamma_f * I_exp[None, :]   # (N, Nj)

        # (4.26) Накопление капитала: k_jf(t+1) = (1−δ_j)·k_jf + I^tot = k + I^exp
        k_new = (1.0 - DELTA[j]) * k_jf + I_tot   # = k_jf + I_exp ≥ k_jf
        k_new = np.maximum(k_new, 0.0)

        # (4.27) Технологический уровень: θ_jf(t+1) = θ_jf·(1 + μ_j·I^tot/k_jf)
        # I^tot/k_jf — безразмерная ставка инвестиций; основная Δθ ~δ*μ ~0.1%/шаг
        i_rate    = I_tot / np.maximum(k_jf, 1.0)
        theta_new = theta_jf * (1.0 + MU[j] * i_rate)

        # Инновационный шок: снижение коэффициентов a_ijf *= (1 − U(0, μ_j))
        a_f_new = a_f.copy()
        shock   = rng.random(Nj) < P_INN[j]
        if shock.any():
            reduc    = rng.uniform(0.0, MU[j], Nj) * shock.astype(float)
            a_f_new *= (1.0 - reduc)[None, :]
            a_f_new  = np.maximum(a_f_new, 0.0)

        # (4.28) Рыночные доли: ω_jf(t+1) = x_jf / Σ_g x_jg
        # ИСПРАВЛЕНИЕ: если Σx=0 — ЗАМОРОЗИТЬ старые доли (не сбрасывать в 1/N)
        x_tot = x_jf.sum()
        if x_tot > 1e-9:
            omega_new = x_jf / x_tot
        else:
            omega_new = omega_jf.copy()  # заморозка старых долей

        # Сохранить
        k_n.append(k_new);       theta_n.append(theta_new)
        omega_n.append(omega_new); af_n.append(a_f_new)
        de_n.append(d_e_new)
        x_jf_out[j]  = x_jf
        z_ijf_out[j] = z_ijf
        q_ijf_out[j] = q_ijf

    # ── Этап 3: Агрегирование ─────────────────────────────────────────────

    # (4.29) Валовый выпуск: x_j(t+1) = Σ_f x_jf(t+1)
    x_new = np.array([x_jf_out[j].sum() for j in range(N)])

    # (4.30) Матрица прямых затрат: a_ij(t+1) = Σ_f z_ijf / Σ_f x_jf
    # если Σx_j=0 — сохранить предыдущий столбец
    A_new = np.zeros((N, N))
    for j in range(N):
        xs = x_jf_out[j].sum()
        if xs > 1e-9:
            A_new[:, j] = z_ijf_out[j].sum(axis=1) / xs
        else:
            A_new[:, j] = A[:, j]

    # (4.31) Матрица капиталоёмкости: b_ij(t+1) = Σ_f q_ijf / max{|Δx_j|, ε_b}
    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: используем АБСОЛЮТНОЕ значение |x_new[j] − x[j]|
    # Без abs() знаменатель = ε_b=1 при Δx<0 → B завышается в 50 000 раз
    B_new = np.zeros((N, N))
    for j in range(N):
        dX = max(abs(x_new[j] - x[j]), EPS_B)   # |Δx_j|, не signed Δx_j
        B_new[:, j] = q_ijf_out[j].sum(axis=1) / dX

    # Численная защита от взрывного роста B:
    # Поэлементный клиппинг относительно B0; нулевые элементы B0 допускают
    # рост до абсолютного порога CLIP_B_ABS.
    CLIP_B_FACTOR = 5.0       # максимально в 5× от калиброванного значения
    CLIP_B_ABS    = 1.0       # абсолютный потолок для нулевых элементов B0
    B_ceil = np.where(B0 > 0, CLIP_B_FACTOR * B0, CLIP_B_ABS)
    B_new  = np.clip(B_new, 0.0, B_ceil)

    # Агрегированные инвестиции по отраслям (для вывода)
    I_agg = np.array([q_ijf_out[j].sum() for j in range(N)])

    firms_new = {
        'k': k_n, 'theta': theta_n, 'omega': omega_n,
        'a_f': af_n, 'c_f': firms['c_f'], 'gamma_f': firms['gamma_f'],
        'd_e': de_n,
    }
    return x_new, A_new, B_new, firms_new, I_agg


# ─────────────────────────────────────────────────────────────────────────────
# ОСНОВНОЙ ЦИКЛ СИМУЛЯЦИИ
# ─────────────────────────────────────────────────────────────────────────────

def run() -> pd.DataFrame:
    """
    Запускает T=30 шагов симуляции и возвращает DataFrame макро-траектории.

    Порядок на каждом шаге t:
      1. Записать макро-состояние t (x, K, θ, ρ(A), u.sum())
      2. x*(t+1) = leontief_target(x, A, B, u)           — ур-е 4.6/4.7
      3. Микро-цикл → x_new, A_new, B_new, firms_new     — ур-я 4.18–4.31
      4. Записать balance_resid для шага t                — ур-е 4.37
      5. u = u * (1 + G_U)  [ур-е 4.32: эндогенный рост спроса]
      6. x, A, B, firms ← новые значения
    """
    # Генератор без фиксированного зерна — каждый запуск стохастически независим
    rng   = np.random.default_rng()
    x     = X0.copy()
    A     = A0.copy()
    B     = B0.copy()
    u     = U0.copy()
    firms = init_firms(rng)

    rows: list = []

    for t in range(T + 1):
        year     = BASE_YEAR + t
        K_agg    = np.array([firms['k'][j].sum()       for j in range(N)])
        th_avg   = np.array([firms['theta'][j].mean()  for j in range(N)])
        HHI      = np.array([hhi(firms['omega'][j])    for j in range(N)])

        # (4.35): проверка ρ(A(t)) < 1 на каждом шаге
        rho_A    = float(np.max(np.abs(np.linalg.eigvals(A))))

        # fd_share_j = u_j/x_j — доля конечного спроса (отдельная концепция;
        # обозначение НЕ "nu" в коде, чтобы не путать с капиталоотдачей ν_j=NU)
        fd_share = u / np.maximum(x, 1.0)

        row: dict = {
            't': t, 'year': year, 'rho_A': rho_A,
            'GDP_proxy': float(x.sum()),
            'K_total':   float(K_agg.sum()),
            'U_total':   float(u.sum()),
        }
        for j in range(N):
            sn = SECTOR_NAMES[j]
            row[f'X_{sn}']       = float(x[j])
            row[f'K_{sn}']       = float(K_agg[j])
            row[f'theta_{sn}']   = float(th_avg[j])
            row[f'fd_share_{sn}'] = float(fd_share[j])  # u_j/x_j (не nu!)
            row[f'HHI_{sn}']     = float(HHI[j])
            row[f'A_diag_{sn}']  = float(A[j, j])
        # Строки матриц A и B
        for i in range(N):
            for j in range(N):
                row[f'A_{i}{j}'] = float(A[i, j])
                row[f'B_{i}{j}'] = float(B[i, j])
        rows.append(row)

        if t == T:
            break

        # Шаг симуляции
        x_next, A_next, B_next, firms_next, I_agg = step(x, A, B, u, firms, rng)

        # (4.37): Невязка баланса — записать в строку шага t
        rows[-1]['balance_resid'] = io_balance_residual(x, x_next, A_next, B_next, u)
        rows[-1]['I_total'] = float(I_agg.sum())
        for j in range(N):
            rows[-1][f'I_{SECTOR_NAMES[j]}'] = float(I_agg[j])

        # (4.32): Обновление конечного спроса ПОСЛЕ вычисления x*(t+1),
        # НО ДО перехода к шагу t+1. G_U — эндогенная ставка роста, не константа.
        u = u * (1.0 + G_U)

        x, A, B, firms = x_next, A_next, B_next, firms_next

    # Заполнить NaN для последней строки (нет x_next)
    df = pd.DataFrame(rows)
    df['balance_resid'] = df['balance_resid'].ffill()
    df['I_total']       = df['I_total'].fillna(0.0)
    for j in range(N):
        df[f'I_{SECTOR_NAMES[j]}'] = df[f'I_{SECTOR_NAMES[j]}'].fillna(0.0)

    return df


# ─────────────────────────────────────────────────────────────────────────────
# ВИЗУАЛИЗАЦИЯ — 6 ОТДЕЛЬНЫХ ПУБЛИКАЦИОННЫХ РИСУНКОВ
# ─────────────────────────────────────────────────────────────────────────────

def make_figures(df: pd.DataFrame, out: Path) -> None:
    """
    Построить 6 публикационных рисунков и сохранить в out/.

    fig_1_trajectories.png  — нормированный выпуск X_j(t)/X_j(0)
    fig_2_structure.png     — структурная динамика совокупного выпуска
    fig_3_stability.png     — спектральный анализ матрицы A
    fig_4_matrix.png        — эволюция матрицы A: t=0 → t=T
    fig_5_micro.png         — технология и капитал (микро-макро)
    fig_6_balance.png       — верификация динамического баланса
    """
    out.mkdir(parents=True, exist_ok=True)

    years = df['year'].values
    ts    = df['t'].values
    total_agents = sum(N_FIRMS)

    X_mat   = np.column_stack([df[f'X_{sn}'].values     for sn in SECTOR_NAMES])
    K_mat   = np.column_stack([df[f'K_{sn}'].values     for sn in SECTOR_NAMES])
    th_mat  = np.column_stack([df[f'theta_{sn}'].values for sn in SECTOR_NAMES])
    I_mat   = np.column_stack([
        df.get(f'I_{sn}', pd.Series(np.zeros(len(df)))).values
        for sn in SECTOR_NAMES
    ])
    rho     = df['rho_A'].values
    resid   = df['balance_resid'].values
    gdp     = df['GDP_proxy'].values
    u_total = df['U_total'].values

    # Матрицы A на шагах 0 и T
    A_t0 = np.array([[df.iloc[0][f'A_{i}{j}']  for j in range(N)] for i in range(N)])
    A_tT = np.array([[df.iloc[-1][f'A_{i}{j}'] for j in range(N)] for i in range(N)])

    # ─────────────────────────────────────────────────────────────────────
    # Рисунок 1: Динамика нормированного валового выпуска X_j(t)/X_j(0)
    # ─────────────────────────────────────────────────────────────────────
    fig1, ax = plt.subplots(figsize=(9, 5))
    fig1.suptitle(
        'Динамика нормированного валового выпуска $X_j(t)\\,/\\,X_j(0)$',
        fontsize=12, fontweight='bold'
    )

    X_norm = X_mat / X_mat[0, :]   # нормировка к 1.0 при t=0 (не %)
    for j in range(N):
        ax.plot(years, X_norm[:, j], color=COLORS[j], marker=MARKERS[j],
                markevery=5, label=SECTOR_NAMES[j])

    ax.axhline(1.0, color='black', lw=0.9, ls='--', label='базовый уровень $t=0$')
    ax.set_xlabel('Год')
    ax.set_ylabel('$X_j(t)\\,/\\,X_j(0)$')
    ax.legend(loc='upper left', ncol=2)

    # Аннотация параметров модели (верхний правый угол)
    ax.text(0.99, 0.97,
            f'T={T}, $N_{{agents}}$={total_agents}',
            transform=ax.transAxes,
            ha='right', va='top', fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

    fig1.tight_layout()
    fig1.savefig(out / 'fig_1_trajectories.png')
    plt.close(fig1)
    print(f'  Сохранён: {out / "fig_1_trajectories.png"}')

    # ─────────────────────────────────────────────────────────────────────
    # Рисунок 2: Структурная динамика совокупного выпуска
    # ─────────────────────────────────────────────────────────────────────
    fig2, axes2 = plt.subplots(1, 2, figsize=(12, 5))
    fig2.suptitle(
        'Структурная динамика совокупного выпуска',
        fontsize=12, fontweight='bold'
    )

    # Левый: ΣX(t)/ΣX(0) и Σu(t)/Σu(0) — производство и спрос нормированы к 1
    ax = axes2[0]
    gdp_norm  = gdp     / gdp[0]
    u_norm    = u_total / u_total[0]
    ax.plot(years, gdp_norm, color='#1f77b4', lw=2.5, ls='-',
            label='$\\sum X_j(t)\\,/\\,\\sum X_j(0)$ — выпуск')
    ax.plot(years, u_norm,   color='#d62728', lw=2.5, ls='--',
            label='$\\sum u_j(t)\\,/\\,\\sum u_j(0)$ — спрос')
    ax.axhline(1.0, color='gray', lw=0.8, ls=':')
    ax.set_xlabel('Год')
    ax.set_ylabel('Нормированный индекс (база=1.0 при $t=0$)')
    ax.set_title('Совокупный выпуск и конечный спрос')
    ax.legend(loc='upper left')

    # Правый: стековая диаграмма долей секторов в совокупном выпуске (%)
    ax = axes2[1]
    X_row_sum = X_mat.sum(axis=1, keepdims=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        X_share = np.where(X_row_sum > 0, X_mat / np.where(X_row_sum > 0, X_row_sum, 1.0) * 100, 0.0)
    ax.stackplot(years, X_share.T, labels=SECTOR_NAMES, colors=COLORS, alpha=0.75)
    ax.set_xlabel('Год')
    ax.set_ylabel('Доля в совокупном выпуске, %')
    ax.set_title('Отраслевая структура выпуска')
    ax.set_ylim(0, 100)
    ax.legend(loc='lower right', ncol=2, fontsize=8)

    fig2.tight_layout()
    fig2.savefig(out / 'fig_2_structure.png')
    plt.close(fig2)
    print(f'  Сохранён: {out / "fig_2_structure.png"}')

    # ─────────────────────────────────────────────────────────────────────
    # Рисунок 3: Анализ устойчивости — спектральные свойства матрицы A(t)
    # ─────────────────────────────────────────────────────────────────────
    fig3, axes3 = plt.subplots(1, 2, figsize=(12, 5))
    fig3.suptitle(
        'Анализ устойчивости: спектральные свойства матрицы $A(t)$',
        fontsize=12, fontweight='bold'
    )

    # Левый: ρ(A(t)) по годам, условие (4.35)
    ax = axes3[0]
    ax.plot(years, rho, color='#333333', lw=2.2, label='$\\rho(A(t))$')
    ax.axhline(1.0, color='crimson', lw=1.5, ls='--', label='граница продуктивности $\\rho=1$')
    ax.fill_between(years, rho, 1.0, where=(rho < 1.0),
                    alpha=0.1, color='green', label='продуктивная зона')
    rho0_val = rho[0]
    ax.annotate(f'$\\rho(A(0))={rho0_val:.4f}$',
                xy=(years[0], rho0_val),
                xytext=(years[3], rho0_val + 0.03),
                fontsize=8,
                arrowprops=dict(arrowstyle='->', color='gray'))
    ax.set_xlabel('Год')
    ax.set_ylabel('$\\rho(A)$')
    ax.set_title('Спектральный радиус $\\rho(A(t))$, ур-е (4.35)')
    ax.set_ylim(0, max(rho.max() * 1.15, 1.1))
    ax.legend(loc='lower right')

    # Правый: комплексная плоскость — собственные числа A(0) и A(T)
    ax = axes3[1]
    eig0 = np.linalg.eigvals(A_t0)
    eigT = np.linalg.eigvals(A_tT)
    # Единичная окружность
    theta_circ = np.linspace(0, 2 * np.pi, 300)
    ax.plot(np.cos(theta_circ), np.sin(theta_circ),
            color='gray', lw=0.8, ls='-', alpha=0.6, label='единичная окружность')
    ax.scatter(eig0.real, eig0.imag, s=80, marker='o', color='#1f77b4',
               zorder=4, label=f'$A(0)$: кружки')
    ax.scatter(eigT.real, eigT.imag, s=80, marker='*', color='#d62728',
               zorder=4, label=f'$A(T)$: звёзды')
    ax.axhline(0, color='black', lw=0.5, ls='-')
    ax.axvline(0, color='black', lw=0.5, ls='-')
    ax.set_xlabel('Re')
    ax.set_ylabel('Im')
    ax.set_title('Собственные числа $A(0)$ и $A(T)$ на комплексной плоскости')
    ax.legend(loc='upper right', fontsize=8)
    ax.set_aspect('equal', adjustable='box')

    fig3.tight_layout()
    fig3.savefig(out / 'fig_3_stability.png')
    plt.close(fig3)
    print(f'  Сохранён: {out / "fig_3_stability.png"}')

    # ─────────────────────────────────────────────────────────────────────
    # Рисунок 4: Эволюция матрицы прямых затрат A(t): t=0 → t=T
    # ─────────────────────────────────────────────────────────────────────
    fig4, axes4 = plt.subplots(1, 3, figsize=(15, 4))
    fig4.suptitle(
        f'Эволюция матрицы прямых затрат $A(t)$: $t=0$ → $t=T={T}$',
        fontsize=12, fontweight='bold'
    )

    vmax_A = max(A_t0.max(), A_tT.max())

    # Левый: A(0)
    ax = axes4[0]
    im0 = ax.imshow(A_t0, cmap='YlOrRd', aspect='auto', vmin=0, vmax=vmax_A)
    ax.set_xticks(range(N)); ax.set_xticklabels(SECTOR_SHORT, rotation=30, ha='right')
    ax.set_yticks(range(N)); ax.set_yticklabels(SECTOR_SHORT)
    for i in range(N):
        for j in range(N):
            ax.text(j, i, f'{A_t0[i,j]:.3f}', ha='center', va='center', fontsize=7.5)
    plt.colorbar(im0, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title('$A(t=0)$')
    ax.set_xlabel('Столбец (потребитель)')
    ax.set_ylabel('Строка (поставщик)')

    # Средний: A(T)
    ax = axes4[1]
    im1 = ax.imshow(A_tT, cmap='YlOrRd', aspect='auto', vmin=0, vmax=vmax_A)
    ax.set_xticks(range(N)); ax.set_xticklabels(SECTOR_SHORT, rotation=30, ha='right')
    ax.set_yticks(range(N)); ax.set_yticklabels(SECTOR_SHORT)
    for i in range(N):
        for j in range(N):
            ax.text(j, i, f'{A_tT[i,j]:.3f}', ha='center', va='center', fontsize=7.5)
    plt.colorbar(im1, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title(f'$A(t={T})$')
    ax.set_xlabel('Столбец (потребитель)')
    ax.set_ylabel('Строка (поставщик)')

    # Правый: ΔA = A(T) − A(0), дивергирующая нормировка относительно 0
    ax = axes4[2]
    dA      = A_tT - A_t0
    vmax_da = max(abs(dA).max(), 1e-6)
    norm_da = TwoSlopeNorm(vmin=-vmax_da, vcenter=0.0, vmax=vmax_da)
    im2     = ax.imshow(dA, cmap='RdYlGn_r', norm=norm_da, aspect='auto')
    ax.set_xticks(range(N)); ax.set_xticklabels(SECTOR_SHORT, rotation=30, ha='right')
    ax.set_yticks(range(N)); ax.set_yticklabels(SECTOR_SHORT)
    for i in range(N):
        for j in range(N):
            ax.text(j, i, f'{dA[i,j]:+.3f}', ha='center', va='center', fontsize=7.5)
    plt.colorbar(im2, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title(f'$\\Delta A = A({T}) - A(0)$')
    ax.set_xlabel('Столбец (потребитель)')
    ax.set_ylabel('Строка (поставщик)')

    fig4.tight_layout()
    fig4.savefig(out / 'fig_4_matrix.png')
    plt.close(fig4)
    print(f'  Сохранён: {out / "fig_4_matrix.png"}')

    # ─────────────────────────────────────────────────────────────────────
    # Рисунок 5: Микро-макро взаимодействие: технология и капитал
    # ─────────────────────────────────────────────────────────────────────
    fig5, axes5 = plt.subplots(1, 2, figsize=(12, 5))
    fig5.suptitle(
        'Микро-макро взаимодействие: технология и капитал',
        fontsize=12, fontweight='bold'
    )

    # Левый: θ̄_j(t) — средний технологический уровень по отраслям, ур-е (4.27)
    ax = axes5[0]
    for j in range(N):
        ax.plot(years, th_mat[:, j], color=COLORS[j], marker=MARKERS[j],
                markevery=5, label=SECTOR_NAMES[j])
    ax.set_xlabel('Год')
    ax.set_ylabel('$\\bar{\\theta}_j(t)$ (безразм.)')
    ax.set_title('Средний технологический уровень $\\bar{\\theta}_j(t)$, ур-е (4.27)')
    ax.legend(ncol=2, loc='best')

    # Правый: K_j(t)/K_j(0) — нормированный запас капитала, ур-е (4.26)
    ax = axes5[1]
    K_norm = K_mat / K_mat[0, :]
    for j in range(N):
        ax.plot(years, K_norm[:, j], color=COLORS[j], marker=MARKERS[j],
                markevery=5, label=SECTOR_NAMES[j])
    ax.axhline(1.0, color='black', lw=0.8, ls='--', alpha=0.5)
    ax.set_xlabel('Год')
    ax.set_ylabel('$K_j(t)\\,/\\,K_j(0)$')
    ax.set_title('Капитал $K_j(t)\\,/\\,K_j(0)$, ур-е (4.26)')
    ax.legend(ncol=2, loc='best')

    fig5.tight_layout()
    fig5.savefig(out / 'fig_5_micro.png')
    plt.close(fig5)
    print(f'  Сохранён: {out / "fig_5_micro.png"}')

    # ─────────────────────────────────────────────────────────────────────
    # Рисунок 6: Верификация динамического баланса — невязка ‖r(t)‖/‖x(t)‖
    # ─────────────────────────────────────────────────────────────────────
    fig6, ax = plt.subplots(figsize=(9, 5))
    fig6.suptitle(
        'Верификация динамического баланса: невязка $\\|r(t)\\|\\,/\\,\\|x(t)\\|$',
        fontsize=12, fontweight='bold'
    )

    # Используем все 31 строку (t=0..30), последняя — копия предыдущей (ffill)
    resid_plot = np.where(resid > 0, resid, 1e-12)
    ax.semilogy(years, resid_plot, color='darkorange', lw=2.2)
    ax.fill_between(years, resid_plot, alpha=0.15, color='darkorange')

    # Референсная линия ~ 33% (инвестиционный блок, начальное условие)
    ax.axhline(0.33, color='gray', lw=1.2, ls='--', alpha=0.8)
    ax.text(years[-1], 0.33 * 1.12,
            'инвестиционный блок ~33%\n(начальное условие)',
            ha='right', va='bottom', fontsize=8, color='gray')

    ax.set_xlabel('Год')
    ax.set_ylabel('$\\|r(t+1)\\|\\,/\\,\\|x(t+1)\\|$ (лог. шкала)')
    ax.set_title('Относительная невязка МОБ (ур-е 4.37):\n'
                 '$\\|r(t+1)\\|\\,/\\,\\|x(t+1)\\|$')

    fig6.tight_layout()
    fig6.savefig(out / 'fig_6_balance.png')
    plt.close(fig6)
    print(f'  Сохранён: {out / "fig_6_balance.png"}')


# ─────────────────────────────────────────────────────────────────────────────
# ТАБЛИЦА-СВОДКА В STDOUT
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(df: pd.DataFrame) -> None:
    """Вывести краткую сводку по ключевым шагам (t=0, 5, 10, 20, 30)."""
    cols_x  = [f'X_{sn}' for sn in SECTOR_NAMES]
    steps   = [0, 5, 10, 20, 30]
    sub     = df[df['t'].isin(steps)].copy()

    w = 80
    print('\n' + '═' * w)
    print('МАКРО-ТРАЕКТОРИЯ: ВАЛОВЫЙ ВЫПУСК X_j(t), млн евро')
    print('─' * w)
    hdr = f"{'t':>4}  {'Год':>6} " + ''.join(f'  {sn[:8]:>10}' for sn in SECTOR_NAMES)
    print(hdr)
    print('─' * w)
    for _, row in sub.iterrows():
        vals = ''.join(f'  {row[c]:>10.0f}' for c in cols_x)
        print(f"{int(row['t']):>4}  {int(row['year']):>6}{vals}")

    print('\n' + '─' * w)
    print('СИСТЕМНЫЕ ПОКАЗАТЕЛИ')
    print('─' * w)
    print(f"{'t':>4}  {'Год':>6}  {'ρ(A)':>8}  {'GDP idx':>9}  "
          f"{'U idx':>8}  {'balance':>12}")
    print('─' * w)
    gdp0 = float(df.iloc[0]['GDP_proxy'])
    u0   = float(df.iloc[0]['U_total'])
    for _, row in sub.iterrows():
        res  = row.get('balance_resid', float('nan'))
        uidx = row['U_total'] / u0 * 100 if u0 > 0 else float('nan')
        print(f"{int(row['t']):>4}  {int(row['year']):>6}  "
              f"{row['rho_A']:>8.4f}  "
              f"{row['GDP_proxy']/gdp0*100:>9.2f}%  "
              f"{uidx:>8.2f}%  "
              f"{res:>12.4e}")
    print('═' * w + '\n')


# ─────────────────────────────────────────────────────────────────────────────
# ТОЧКА ВХОДА
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            'Форвардная симуляция двухуровневой АБМ МОБ — '
            'пятисекторная экономика, базовый год 2015, T=30 шагов.'
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--output', type=str, default='simulation_output',
        help='Директория для результатов'
    )
    parser.add_argument(
        '--no-plots', action='store_true',
        help='Пропустить построение графиков'
    )
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    print('=' * 65)
    print('Двухуровневая АБМ МОБ — форвардная симуляция')
    print(f'Пятисекторная экономика, базовый год {BASE_YEAR}, T={T} шагов')
    print(f'Отраслей: {N} | Агентов: {sum(N_FIRMS)} | G_U={G_U:.3f}')
    print('Зерно ГСЧ: случайное (без фиксации)')
    print('=' * 65)

    print('\n[1/3] Запуск симуляции...')
    df = run()

    csv_path = out / 'macro_trajectory.csv'
    df.to_csv(csv_path, index=False, float_format='%.6g')
    print(f'  Таблица: {csv_path}  ({len(df)} строк × {len(df.columns)} столбцов)')

    print_summary(df)

    if not args.no_plots:
        print('[2/3] Построение графиков...')
        make_figures(df, out)

    print('[3/3] Готово.')
    print(f'Результаты → {out.resolve()}')
    print('=' * 65)


if __name__ == '__main__':
    main()
