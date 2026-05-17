#!/usr/bin/env python3
"""
web_app.py — Flask-сервер для интерактивного дашборда модели МОБ.

Установка зависимостей:
    pip install flask

Запуск из папки scripts/:
    python web_app.py

Интерфейс: http://127.0.0.1:5000
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, str(Path(__file__).parent))
import simulate as sim

app = Flask(__name__)
_sim_lock = threading.Lock()

DASHBOARD_DIR = Path(__file__).parent / 'dashboard'


@app.route('/')
def index():
    return send_from_directory(str(DASHBOARD_DIR), 'Dashboard.html')


@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    data    = request.get_json(force=True)
    params  = data.get('params', {})
    sectors = data.get('sectors', [])

    # Имена секторов из фронтенда (до 5; остальные — из модели)
    frontend_names = [s['name'] for s in sectors[:5]]
    while len(frontend_names) < 5:
        frontend_names.append(sim.SECTOR_NAMES[len(frontend_names)])

    def _get(lst, idx, default):
        try:
            return lst[idx]
        except (IndexError, TypeError):
            return default

    T_req      = max(5, min(50,  int(params.get('T',      30))))
    gU_req     = max(0.001, min(0.10, float(params.get('gU',    0.015))))
    sigmaK_req = max(0.05,  min(2.0,  float(params.get('sigmaK', 0.6))))
    bClip_req  = max(1.0,   min(20.0, float(params.get('bClip',  5.0))))

    kappa_in = params.get('kappa', [])
    eta_in   = params.get('eta',   [])
    pInn_in  = params.get('pInn',  [])
    mu_in    = params.get('mu',    [])
    Nj_in    = params.get('Nj',    [])

    with _sim_lock:
        # Сохранить оригинальные глобалы
        orig = dict(
            T=sim.T, G_U=sim.G_U, SIGMA_K=sim.SIGMA_K,
            CLIP_B_FACTOR=sim.CLIP_B_FACTOR,
            KAPPA=sim.KAPPA.copy(), ETA=sim.ETA.copy(),
            P_INN=sim.P_INN.copy(), MU=sim.MU.copy(),
            N_FIRMS=list(sim.N_FIRMS),
        )
        try:
            sim.T             = T_req
            sim.G_U           = gU_req
            sim.SIGMA_K       = sigmaK_req
            sim.CLIP_B_FACTOR = bClip_req

            for j in range(5):
                sim.KAPPA[j]   = float(_get(kappa_in, j, orig['KAPPA'][j]))
                sim.ETA[j]     = float(_get(eta_in,   j, orig['ETA'][j]))
                sim.P_INN[j]   = float(_get(pInn_in,  j, orig['P_INN'][j]))
                sim.MU[j]      = float(_get(mu_in,    j, orig['MU'][j]))
                sim.N_FIRMS[j] = max(5, min(100, int(_get(Nj_in, j, orig['N_FIRMS'][j]))))

            df = sim.run(seed=42)
        finally:
            sim.T             = orig['T']
            sim.G_U           = orig['G_U']
            sim.SIGMA_K       = orig['SIGMA_K']
            sim.CLIP_B_FACTOR = orig['CLIP_B_FACTOR']
            sim.KAPPA[:]  = orig['KAPPA']
            sim.ETA[:]    = orig['ETA']
            sim.P_INN[:]  = orig['P_INN']
            sim.MU[:]     = orig['MU']
            for j in range(5):
                sim.N_FIRMS[j] = orig['N_FIRMS'][j]

    T_actual = len(df) - 1
    years    = df['year'].tolist()

    output, investment, hhi_out = [], [], []
    for j in range(5):
        sn    = sim.SECTOR_NAMES[j]
        x_vec = df[f'X_{sn}'].tolist()
        x0    = x_vec[0] if x_vec[0] else 1.0

        output.append([v / x0 for v in x_vec])

        i_col = f'I_{sn}'
        if i_col in df.columns:
            inv = [i / max(x, 1.0) for i, x in zip(df[i_col].tolist(), x_vec)]
        else:
            inv = [0.0] * len(years)
        investment.append(inv)

        h_col = f'HHI_{sn}'
        hhi_out.append(df[h_col].tolist() if h_col in df.columns else [0.0] * len(years))

    rho = df['rho_A'].tolist()

    # KPI
    g0     = df['GDP_proxy'].iloc[0]
    g_end  = df['GDP_proxy'].iloc[-1]
    cagr   = ((g_end / g0) ** (1.0 / T_actual) - 1) * 100 if T_actual > 0 else 0.0
    gdp_tr = g_end / 1_000_000  # млн → трлн евро

    # Инвестиционные пульсы: локальные максимумы I_total > 1.3× среднего
    pulses = 0
    if 'I_total' in df.columns:
        ia = df['I_total'].fillna(0).values
        mu_i = ia.mean()
        for t in range(2, len(ia) - 2):
            if (ia[t] > ia[t-1] and ia[t] > ia[t+1]
                    and ia[t] > ia[t-2] and ia[t] > ia[t+2]
                    and ia[t] > mu_i * 1.3):
                pulses += 1

    return jsonify({
        'years':      years,
        'output':     output,
        'rho':        rho,
        'investment': investment,
        'hhi':        hhi_out,
        'kpi': {
            'cagr':     round(cagr, 2),
            'finalGDP': round(gdp_tr, 3),
            'pulses':   pulses,
            'stable':   bool(all(r < 1.0 for r in rho)),
        },
    })


if __name__ == '__main__':
    print(f'\n  Дашборд: http://127.0.0.1:5000')
    print('  Остановить: Ctrl+C\n')
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=False)
