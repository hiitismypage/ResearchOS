#!/usr/bin/env python3
"""
Ретроспективная верификация модели (2016–2019).

Сравнивает нормированные траектории выпуска X_j(t)/X_j(0) из симуляции
с нормированными траекториями GVA_j(t)/GVA_j(0) из данных Eurostat.

Метод сравнения: темпы роста (индексы базового года), а не абсолютные
уровни — GVA и X в абсолютных единицах несопоставимы, но при стабильной
доле добавленной стоимости их темпы роста близки.

Выходные файлы (results/validation/):
  validation_table.csv   — числовая таблица для раздела 5.8
  fig_validation.png     — рисунок 5.9: модель vs реальность
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent

SIM_CSV  = ROOT / "results" / "simulation" / "macro_trajectory.csv"
GVA_CSV  = ROOT / "data" / "eurostat_validation" / "gva_by_sector.csv"
OUT_DIR  = ROOT / "results" / "validation"

# Соответствие: имя в симуляции → имя в Eurostat CSV
# Имена секторов из simulate.py (из calibration output) → Eurostat GVA CSV
SECTOR_MAP = {
    "Extraction":    "Extraction",
    "Energy":        "Energy",
    "Manufacturing": "Manufacturing",
    "Construction":  "Construction",
    "Agriculture":   "Agriculture",
}

VALIDATION_YEARS = [2015, 2016, 2017, 2018, 2019]   # до COVID, горизонт верификации
BASE_YEAR = 2015

COLORS  = ['#d62728', '#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd']
MARKERS = ['o', 's', '^', 'D', 'v']

# ─────────────────────────────────────────────────────────────────────────────

def load_simulation() -> pd.DataFrame:
    """Загрузить нормированные траектории выпуска из симуляции."""
    df = pd.read_csv(SIM_CSV)
    rows = df[df["year"].isin(VALIDATION_YEARS)].copy()
    result = pd.DataFrame({"year": VALIDATION_YEARS})
    for sim_name in SECTOR_MAP:
        col = f"X_{sim_name}"
        x = rows.set_index("year")[col]
        x0 = x.loc[BASE_YEAR]
        result[sim_name] = result["year"].map(x / x0)
    return result.set_index("year")


def load_actual() -> pd.DataFrame:
    """Загрузить нормированные траектории GVA из Eurostat."""
    gva = pd.read_csv(GVA_CSV, index_col="year")
    result = pd.DataFrame({"year": VALIDATION_YEARS}).set_index("year")
    for sim_name, euro_name in SECTOR_MAP.items():
        gva_sector = gva.loc[VALIDATION_YEARS, euro_name]
        gva0 = float(gva_sector.loc[BASE_YEAR])
        result[sim_name] = gva_sector / gva0
    return result


def compute_mape(sim: pd.DataFrame, actual: pd.DataFrame) -> dict[str, float]:
    """MAPE по каждому сектору (2016–2019)."""
    mape = {}
    check_years = [y for y in VALIDATION_YEARS if y != BASE_YEAR]
    for col in SECTOR_MAP:
        err = np.abs(sim.loc[check_years, col].values - actual.loc[check_years, col].values)
        mape[col] = float(np.mean(err / actual.loc[check_years, col].values) * 100)
    return mape


def save_table(sim: pd.DataFrame, actual: pd.DataFrame, mape: dict) -> None:
    """Таблица для раздела 5.8 диплома."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for yr in VALIDATION_YEARS:
        for sim_name, euro_name in SECTOR_MAP.items():
            rows.append({
                "Год":     yr,
                "Сектор":  euro_name,
                "Модель":  round(sim.loc[yr, sim_name], 4),
                "Факт":    round(actual.loc[yr, sim_name], 4),
                "Откл.,%": round((sim.loc[yr, sim_name] / actual.loc[yr, sim_name] - 1) * 100, 1)
                           if yr != BASE_YEAR else 0.0,
            })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT_DIR / "validation_table.csv", index=False, encoding="utf-8-sig")

    # Краткая сводка MAPE
    print("\nMAPE по секторам (2016–2019):")
    for sn, euro_name in SECTOR_MAP.items():
        print(f"  {euro_name:<16}  MAPE = {mape[sn]:.1f}%")
    total = np.mean(list(mape.values()))
    print(f"  {'Среднее':<16}  MAPE = {total:.1f}%")


def make_figure(sim: pd.DataFrame, actual: pd.DataFrame, mape: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        "Верификация модели: нормированный выпуск/ВДС, 2015–2019\n"
        "(сплошная — модель, пунктир — данные Eurostat)",
        fontsize=11, fontweight="bold"
    )

    sector_names_ru  = list(SECTOR_MAP.keys())
    sector_names_eng = list(SECTOR_MAP.values())
    years = VALIDATION_YEARS

    # Левый: все 5 секторов — модель vs факт
    ax = axes[0]
    for j, (sn_ru, sn_eng) in enumerate(zip(sector_names_ru, sector_names_eng)):
        ax.plot(years, sim[sn_ru].values,
                color=COLORS[j], lw=2.0, marker=MARKERS[j], markevery=1,
                label=f"{sn_eng} (модель)")
        ax.plot(years, actual[sn_ru].values,
                color=COLORS[j], lw=1.5, ls="--", alpha=0.7, marker=MARKERS[j],
                markersize=5, markevery=1)
    ax.axhline(1.0, color="black", lw=0.8, ls=":", alpha=0.5)
    ax.set_xlabel("Год")
    ax.set_ylabel("Индекс (2015 = 1,0)")
    ax.set_title("Нормированные траектории (база 2015)")
    ax.legend(fontsize=8, ncol=2)
    ax.set_xticks(years)

    # Правый: столбцы MAPE по секторам
    ax = axes[1]
    mape_values = [mape[sn] for sn in sector_names_ru]
    bars = ax.bar(sector_names_eng, mape_values, color=COLORS, alpha=0.75, edgecolor="white")
    ax.axhline(10.0, color="gray", lw=1.2, ls="--", alpha=0.7, label="порог 10%")
    for bar, val in zip(bars, mape_values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.3,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("MAPE, %")
    ax.set_title("Средняя абсолютная ошибка 2016–2019")
    ax.set_xticklabels(sector_names_eng, rotation=20, ha="right")
    ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_validation.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  Рисунок → {OUT_DIR / 'fig_validation.png'}")


def main():
    print("=" * 60)
    print("Верификация модели: симуляция vs Eurostat, 2016–2019")
    print("=" * 60)

    sim    = load_simulation()
    actual = load_actual()
    mape   = compute_mape(sim, actual)

    print("\nСравнение нормированных индексов (2015 = 1.00):")
    print(f"  {'Год':>4}  {'Сектор':<16}  {'Модель':>8}  {'Факт':>8}  {'Откл.':>8}")
    print("  " + "─" * 54)
    for yr in VALIDATION_YEARS:
        for sn_ru, sn_eng in SECTOR_MAP.items():
            s = sim.loc[yr, sn_ru]
            a = actual.loc[yr, sn_ru]
            d = (s/a - 1)*100 if yr != BASE_YEAR else 0.0
            flag = "  !" if abs(d) > 20 else ""
            print(f"  {yr:>4}  {sn_eng:<16}  {s:>8.3f}  {a:>8.3f}  {d:>+7.1f}%{flag}")

    save_table(sim, actual, mape)
    make_figure(sim, actual, mape)

    print(f"\n  Таблица → {OUT_DIR / 'validation_table.csv'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
