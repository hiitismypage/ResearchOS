---
name: run-analysis
description: Запускает или продолжает работу с pipeline анализа UNGDC-корпуса для diploma_un_legitimation_speeches. Устанавливает зависимости, запускает скрининг или анализ, объясняет текущее состояние.
---

Ты помогаешь с практической (кодовой) частью дипломной работы по анализу легитимационных стратегий в речах ООН.

## Контекст подпроекта

Подпроект: `projects/diploma_un_legitimation_speeches/`

Тема: анализ стратегий легитимации нарушений МП в выступлениях на ГА ООН (1946–2023).
Корпус: Harvard UNGDC (`data/UNGDC_1946-2025.tar.gz`), 11 127 речей.
Метод: направленный качественный контент-анализ (Hsieh & Shannon, 2005) — две аналитические размерности из гл. 2.3 диплома:
- Dimension 1 — тип предполагаемого нарушения (5 категорий)
- Dimension 2 — стратегия легитимации (8 категорий)

Выборка: 35 кейсов (state-year), куративно отобранных, в `scripts/cases/violation_events.csv`.

---

## Структура pipeline

```
scripts/
├── run_analysis.py        ← точка входа, запускается через: python3 run_analysis.py
├── config.py              ← все пути, пороги, метки категорий (менять здесь)
├── corpus_utils.py        ← чтение .tar.gz архива, построение индекса, загрузка речей
├── coding_utils.py        ← сегментация текста (по предложениям, ~120 слов/сегмент),
│                             keyword-scoring по нормализованной частоте
├── analysis_utils.py      ← частоты, матрица co-occurrence, тренды, 6 matplotlib-фигур
├── lexicons/
│   ├── strategies.json    ← 8 стратегий легитимации (keyword-листы)
│   └── violations.json    ← 5 типов нарушений (keyword-листы)
├── cases/
│   └── violation_events.csv  ← 35 кейсов, 1946–2023
└── requirements.txt
```

Выходные данные:
```
analysis_output/
├── screening/
│   └── passages_for_screening.csv   ← 931 сегментов, 136 флагировано (Stage 1)
├── coding/
│   └── manual_codes.csv             ← ЗАПОЛНЯЕТСЯ ВРУЧНУЮ (Stage 1→2)
├── tables/
│   ├── frequency_strategies.csv
│   ├── frequency_violations.csv
│   ├── cooccurrence_matrix.csv
│   └── temporal_trends.csv
└── figures/
    ├── fig1_strategy_frequencies.png
    ├── fig2_violation_frequencies.png
    ├── fig3_cooccurrence_heatmap.png
    ├── fig4_temporal_trends_line.png
    ├── fig5_temporal_trends_stacked.png
    └── fig6_regional_distribution.png
```

---

## Шаг 0 — проверить окружение и установить зависимости

### Определи текущее состояние

```bash
cd projects/diploma_un_legitimation_speeches/scripts
python3 -c "import pandas, matplotlib, seaborn, openpyxl, scipy; print('OK')"
```

Если `ModuleNotFoundError` — установи:

```bash
python3 -m pip install -r requirements.txt
```

Если `pip` не работает (или заблокирован в настройках Claude):
```bash
python3 -m ensurepip --upgrade
python3 -m pip install -r requirements.txt
```

Если используется miniforge/conda:
```bash
conda install -c conda-forge pandas matplotlib seaborn openpyxl scipy -y
```

### Проверь наличие данных

```bash
ls ../data/
# ожидается: UNGDC_1946-2025.tar.gz  Speakers_by_session.xlsx  README.txt
```

Если архив отсутствует — его нет в git (добавлен в .gitignore как крупный файл).
Данные нужно скачать с Harvard Dataverse: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/0TJX8Y

---

## Шаг 1 — Stage 1: скрининг корпуса (первый запуск на новом компьютере)

```bash
cd projects/diploma_un_legitimation_speeches/scripts
python3 run_analysis.py --stage screen
```

Что происходит:
1. Строится индекс корпуса (один раз, ~30 сек, кэшируется в `analysis_output/cache/`)
2. Для каждого из 35 кейсов загружается речь из архива
3. Текст разбивается на сегменты ~120 слов (предложение-based)
4. Каждый сегмент скорируется по keyword-лексиконам стратегий и нарушений
5. Экспортируется `analysis_output/screening/passages_for_screening.csv`

Ожидаемый результат: 931 сегментов, ~136 флагированных (14.6%).

Если индекс уже есть, но архив не обновлялся — пропусти `--rebuild-index`.
Если архив обновился (новая версия UNGDC) — добавь `--rebuild-index`.

---

## Шаг 2 — ручное кодирование (делается в Excel/Numbers)

Открой `analysis_output/screening/passages_for_screening.csv`.

Для каждой строки где `flagged_for_review = True` (и по желанию других строк):
1. Прочитай `paragraph_text`
2. Заполни `manual_violation_code` — один из:
   - `use_of_force`, `ihl_violations`, `human_rights`, `territorial_integrity`, `treaty_noncompliance`
3. Заполни `manual_strategy_code` — один из:
   - `self_defense`, `sovereignty`, `denial`, `humanitarian`, `counterterrorism`, `whataboutism`, `procedural_legal`, `historical`
4. Опционально заполни `coder_notes`

Сохрани заполненный файл как:
```
analysis_output/coding/manual_codes.csv
```

Колонки `suggested_violation` и `suggested_strategy` — подсказки от системы (не обязательны для принятия).

---

## Шаг 3 — Stage 2: статистика и графики

```bash
python3 run_analysis.py --stage analyze
```

Что генерируется:
- `tables/` — 4 CSV-таблицы: частоты стратегий/нарушений, матрица co-occurrence, тренды по периодам
- `figures/` — 6 PNG-графиков (300 dpi, готовы для вставки в диплом)

---

## Автозапуск (auto-detect)

```bash
python3 run_analysis.py
```

Если `manual_codes.csv` **существует** → запускает Stage 2 (analyze).
Если **не существует** → запускает Stage 1 (screen).

---

## Изменение параметров

Все настройки — в `config.py`:

| Параметр | Значение | Описание |
|----------|---------|----------|
| `MIN_PARAGRAPH_WORDS` | 20 | Минимум слов в сегменте |
| `STRATEGY_FLAG_THRESHOLD` | 0.013 | Порог флагирования (~1–2 keyword matches / 120 слов) |
| `VIOLATION_FLAG_THRESHOLD` | 0.013 | То же для типов нарушений |
| `FIGURE_DPI` | 300 | DPI для графиков |

Чтобы добавить кейсы в выборку — редактируй `cases/violation_events.csv`.
Чтобы уточнить keyword-листы — редактируй `lexicons/strategies.json` или `lexicons/violations.json`.

---

## Связь с методологической главой

| Файл | Раздел диплома |
|------|---------------|
| `cases/violation_events.csv` | гл. 3.3 (sampling strategy) |
| `lexicons/strategies.json` | гл. 2.3 (8 legitimation strategy types) |
| `lexicons/violations.json` | гл. 2.3 (5 violation type categories) |
| `coding_utils.py` → `segment_speech` | гл. 3.1 (unit of analysis = argumentative segment) |
| `coding_utils.py` → `score_paragraph` | гл. 3.2 (keyword-based pre-screening) |
| `analysis_utils.py` → `build_cooccurrence_matrix` | гл. 4 (descriptive mapping) |
| `analysis_utils.py` → `build_temporal_trends` | гл. 4 (longitudinal analysis, 4 periods) |

---

## Если что-то пошло не так

| Проблема | Решение |
|---------|---------|
| `ModuleNotFoundError: pandas` | `python3 -m pip install -r requirements.txt` |
| `FileNotFoundError: UNGDC_1946-2025.tar.gz` | Скачать архив с Harvard Dataverse, положить в `data/` |
| Индекс устарел после обновления архива | `python3 run_analysis.py --stage screen --rebuild-index` |
| `manual_codes.csv not found` | Stage 2 требует ручного кодирования — сначала Stage 1 |
| Речь отсутствует в корпусе | `[MISSING]` в выводе — норма для ранних сессий или спорных государств |
| Мало флагированных сегментов | Снизить `STRATEGY_FLAG_THRESHOLD` в `config.py` |

---

## Описание кейсов (35 state-year)

Кейсы охватывают 4 исторических периода из гл. 2.4:
- Cold War (1946–1989): 10 кейсов — Suez, Hungary, Czechoslovakia, Afghanistan, Grenada, South Africa (apartheid), Vietnam/Cambodia
- Post-Cold War (1990–2001): 9 кейсов — Kuwait, East Timor, Chechnya, Kosovo/NATO, Yugoslavia
- Post-9/11 (2002–2013): 8 кейсов — Iraq invasion, Abu Ghraib, Lebanon, Gaza (Cast Lead), Georgia, Iran nuclear, Syria CW
- Post-2014 (2014–2023): 8 кейсов — Crimea/Donbas, Yemen, SCS, Rohingya, Syria operation, NK-Karabakh, Tigray, Ukraine

Все 5 UN региональных групп представлены.
