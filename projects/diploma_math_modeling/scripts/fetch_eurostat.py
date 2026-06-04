#!/usr/bin/env python3
"""
Загрузка данных из Eurostat API для верификации модели.

Источники:
  nama_10_a64  — GVA (B1G), GFCF (P51G), D1 по детальным отраслям NACE, Германия, 2010-2022
  naio_10_cp1700 — симметричная IO-таблица (уже есть в data/)

Выходные файлы (data/eurostat_validation/):
  gva_by_sector.csv   — GVA (B1G) по 5 секторам, 2010-2022
  gfcf_by_sector.csv  — GFCF (P51G) по 5 секторам, 2010-2022
  d1_by_sector.csv    — Оплата труда (D1) по 5 секторам, 2010-2022
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "eurostat_validation")

# Соответствие: наш сектор → NACE-коды в nama_10_a64
SECTOR_NACE = {
    "Extraction":     ["B"],
    "Energy":         ["D35"],
    "Manufacturing":  ["C"],
    "Construction":   ["F"],
    "Agriculture":    ["A01", "A02", "A03"],
}

YEARS = list(range(2010, 2023))

API_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"


# ─────────────────────────────────────────────────────────────────────────────

def fetch_json(dataset: str, na_item: str, year: int) -> dict:
    """Загрузить один год из Eurostat JSON API."""
    params = urllib.parse.urlencode({
        "na_item": na_item,
        "geo":     "DE",
        "unit":    "CP_MEUR",
        "time":    str(year),
        "lang":    "EN",
    })
    url = f"{API_BASE}/{dataset}?{params}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def extract_nace_value(data: dict, nace_code: str) -> float | None:
    """
    Извлечь значение для конкретного NACE-кода из JSON-ответа Eurostat.

    Eurostat JSON stat format:
      data['size']       = [dim1_size, dim2_size, ...]
      data['dimension']  = {dim_name: {category: {index: {code: pos}}}}
      data['value']      = {str(flat_idx): value}

    Порядок измерений в 'id':
      ['freq', 'unit', 'nace_r2', 'na_item', 'geo', 'time']
    """
    ids    = data["id"]       # список имён измерений по порядку
    sizes  = data["size"]     # размер каждого измерения
    dims   = data["dimension"]
    values = data["value"]

    # Позиция NACE-кода в измерении nace_r2
    nace_dim_idx = ids.index("nace_r2")
    nace_pos_map = dims["nace_r2"]["category"]["index"]
    if nace_code not in nace_pos_map:
        return None
    nace_pos = nace_pos_map[nace_code]

    # Все остальные измерения — размер 1 (фильтрованы до единственного значения)
    # Flat index = nace_pos * (stride for nace dimension)
    # stride = product of sizes of all dimensions AFTER nace_r2
    stride = 1
    for k in range(nace_dim_idx + 1, len(sizes)):
        stride *= sizes[k]

    flat_idx = nace_pos * stride
    val = values.get(str(flat_idx))
    return float(val) if val is not None else None


def fetch_indicator(dataset: str, na_item: str) -> dict[int, dict[str, float]]:
    """
    Загрузить показатель na_item для всех лет и всех наших секторов.
    Возвращает {year: {sector_name: value_M_EUR}}.
    """
    result: dict[int, dict[str, float]] = {}

    for year in YEARS:
        print(f"  [{na_item}] {year}...", end=" ", flush=True)
        try:
            data = fetch_json(dataset, na_item, year)
        except Exception as e:
            print(f"ERROR: {e}")
            result[year] = {}
            continue

        row: dict[str, float] = {}
        for sector, nace_codes in SECTOR_NACE.items():
            total = 0.0
            found = False
            for code in nace_codes:
                val = extract_nace_value(data, code)
                if val is not None:
                    total += val
                    found = True
            row[sector] = round(total, 1) if found else None
        result[year] = row
        print("OK")

    return result


def save_csv(result: dict[int, dict[str, float]], filename: str) -> None:
    sectors = list(SECTOR_NACE.keys())
    lines = ["year," + ",".join(sectors)]
    for year in sorted(result.keys()):
        row = result[year]
        vals = [str(row.get(s, "")) for s in sectors]
        lines.append(f"{year}," + ",".join(vals))
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  Сохранено: {path}")


def main():
    print("=" * 60)
    print(f"Eurostat API fetch — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Dataset: nama_10_a64  |  Страна: DE  |  Годы: {YEARS[0]}–{YEARS[-1]}")
    print("=" * 60)

    print("\n[1/3] GVA (B1G)...")
    gva = fetch_indicator("nama_10_a64", "B1G")
    save_csv(gva, "gva_by_sector.csv")

    print("\n[2/3] GFCF (P51G)...")
    gfcf = fetch_indicator("nama_10_a64", "P51G")
    save_csv(gfcf, "gfcf_by_sector.csv")

    print("\n[3/3] Compensation of employees (D1)...")
    d1 = fetch_indicator("nama_10_a64", "D1")
    save_csv(d1, "d1_by_sector.csv")

    print("\n" + "=" * 60)
    print("Готово. Данные в data/eurostat_validation/")
    print("=" * 60)


if __name__ == "__main__":
    main()
