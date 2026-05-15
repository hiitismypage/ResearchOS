---
name: export-thesis
description: Экспортирует главы подпроекта из chapters/*.md в единый DOCX с оглавлением и форматированием по FORMAT.md
---

Собирает все отредактированные главы подпроекта в один DOCX-документ через Pandoc.

## Аргументы

- `/export-thesis` — экспорт активного подпроекта, имя файла по умолчанию `thesis`
- `/export-thesis <slug>` — явно указать подпроект: `/export-thesis diploma_un_legitimation_speeches`
- `/export-thesis <slug> <name>` — задать имя выходного файла: `/export-thesis diploma_un_legitimation_speeches final_draft`

---

## Шаг 0 — предэкспортная проверка соответствия методичке

Перед экспортом выполни следующие проверки и сообщи о результатах.

### Объём работы

```bash
cat projects/<slug>/chapters/*.md | wc -m
```

Требование: **≥ 90 000 знаков с пробелами** (без приложений). Markdown-разметка даёт ~10% накладных расходов — вычти при оценке.

### Количество источников в references

```bash
grep -c "^[A-Z]" projects/<slug>/chapters/07_references.md 2>/dev/null || \
grep -c "^[А-Я]" projects/<slug>/chapters/07_references.md 2>/dev/null
```

Требование: **≥ 45 академических источников** для исследовательской ВКР. Если меньше — предупреди:

```
⚠️  КРИТИЧНО: В references найдено X источников (требуется ≥ 45).
    Необходимо добавить источники в chapters/07_references.md и bibliography.md
    перед финальным экспортом.
```

### Структура глав

```bash
ls projects/<slug>/chapters/*.md | sort -V
```

Проверь что присутствуют: введение, обзор литературы, теор. рамка, методология, эмпирика, обсуждение, заключение, список источников.

---

## Шаг 1 — определить подпроект

Если подпроект не указан в аргументе — определи по контексту сессии (активный проект).
Путь: `projects/<slug>/`.
Если неясно — спроси.

---

## Шаг 2 — определить ОС и проверить зависимости

### Определи операционную систему

```bash
uname -s 2>/dev/null || echo "Windows"
```

- `Darwin` → macOS
- `Linux` → Linux
- Ошибка или `Windows` → Windows

### Pandoc

**macOS / Linux:**
```bash
which pandoc
```

**Windows (PowerShell / Git Bash):**
```powershell
where pandoc
```

Если не найден — **Pandoc нужно установить на компьютер.** Попробуй автоматически через conda (если miniforge установлен):

```bash
conda install -c conda-forge pandoc -y
```

Если conda недоступна или установка не удалась — сообщи пользователю инструкцию для его ОС:

**macOS:**
```
⚠️  Pandoc не установлен. Установи:

    brew install pandoc
    # или
    conda install -c conda-forge pandoc
```

**Windows:**
```
⚠️  Pandoc не установлен. Установи одним из способов:

    winget install --id JohnMacFarlane.Pandoc
    # или через conda: conda install -c conda-forge pandoc
    # или скачать .msi: https://pandoc.org/installing.html
```

**Linux:**
```
⚠️  Pandoc не установлен. Установи:

    sudo apt-get install pandoc   # Debian/Ubuntu
    sudo dnf install pandoc       # Fedora
```

Не продолжай выполнение скилла, пока Pandoc не установлен.

### python-docx (для генерации reference.docx)

```bash
python3 -c "import docx; print('ok')" 2>/dev/null || echo "not found"
```

Если не найден — предупреди что форматирование может отличаться от FORMAT.md, предложи `pip install python-docx`.

---

## Шаг 3 — проверить наличие глав

```bash
ls projects/<slug>/chapters/*.md 2>/dev/null | sort -V
```

Если список пустой — сообщи что нечего экспортировать.

Если главы есть — **покажи их список** в порядке сортировки:

```
Главы для сборки:
  1. 00_introduction.md
  2. 01_literature_review.md
  ...
```

Убедись что порядок файлов соответствует логической структуре работы из `outline/outline_v1.md`.
Если порядок не совпадает — предупреди пользователя.

---

## Шаг 4 — запустить экспорт

**macOS / Linux / Git Bash / WSL:**
```bash
bash .claude/scripts/export.sh projects/<slug> <output_name>
```

**Windows (PowerShell, если bash недоступен):**
```powershell
$PROJECT = "projects/<slug>"
$DATE = Get-Date -Format "yyyy-MM-dd"
$OUTPUT = "$PROJECT/output/thesis_$DATE.docx"
New-Item -ItemType Directory -Force -Path "$PROJECT/output"
python .claude/scripts/create_reference_doc.py "$PROJECT/FORMAT.md" "$PROJECT/reference.docx"
$chapters = Get-ChildItem "$PROJECT/chapters/*.md" | Sort-Object Name
pandoc $chapters --from markdown --to docx --toc --toc-depth=3 `
  --reference-doc="$PROJECT/reference.docx" `
  --output="$OUTPUT"
Write-Host "Готово: $OUTPUT"
```

Скрипт автоматически (bash-версия):
- Генерирует `reference.docx` из `FORMAT.md`
- Собирает все `chapters/*.md` в порядке имён файлов
- Добавляет автоматическое оглавление (`--toc`, глубина 3)
- Подключает `bibliography.bib` если файл существует
- Сохраняет в `projects/<slug>/output/<output_name>_YYYY-MM-DD.docx`

---

## Шаг 5 — проверить результат

```bash
du -h projects/<slug>/output/*.docx | tail -1
```

Сообщи пользователю: путь к файлу, размер, список вошедших глав, предупреждения.

---

## Требования к форматированию

**Приоритет при конфликтах: Методичка ВКР > APA Guide > умолчания Pandoc.**

| Параметр | Значение | Источник |
|----------|---------|---------|
| Шрифт | Times New Roman 12pt | Методичка + APA |
| Межстрочный интервал | **1.5** (не double, как в APA) | Методичка |
| Отступ первой строки | 1.25 см | Методичка |
| Поля (лев/пр/верх/низ) | **25 / 10 / 20 / 20 мм** | Методичка |
| Выравнивание текста | **По ширине** (не left, как в APA) | Методичка |
| Нумерация страниц | Вверху по центру, с 2-й страницы | Методичка |
| Сноски | Times New Roman 10pt, по ширине, внизу страницы | Методичка |
| Список источников | Hanging indent (первая строка у поля, продолжение с отступом ~1.25 см) | APA 7th ed. |
| Цитирование в тексте | APA in-text: (Автор, год, p. X) | Методичка + APA |

### Форматирование списка источников (APA 7th ed.)

Список References оформляется **в алфавитном порядке** с hanging indent:

```
Bjola, C. (2005). Legitimating the use of force in international politics:
    A communicative action perspective. European Journal of International
    Relations, 11(2), 266–303. https://doi.org/...
```

- Первая строка каждой записи — у левого поля
- Все последующие строки — отступ ~1.25 см (hanging indent)
- Курсив: названия книг и журналов (не статей)
- DOI/URL в конце, без точки после ссылки
- Работа начинается с новой страницы

### Заголовки (Методичка ВКР — приоритет над APA)

| Уровень | Формат | Пример |
|---------|--------|--------|
| Глава (H1) | Times New Roman 12pt, **жирный**, с новой страницы | `1. Literature Review` |
| Раздел (H2) | Times New Roman 12pt, **жирный** | `1.1 Legitimacy in IR Theory` |
| Подраздел (H3) | Times New Roman 12pt, *курсив* | `1.1.1 Early approaches` |

Нумерация: глава `1.`, раздел `1.1`, подраздел `1.1.1`. Слово «Глава» не используется. Точка в конце заголовка не ставится.

### Таблицы и рисунки (APA 7th ed. для тезисов)

- Встраиваются в текст (не выносятся за References)
- Нумеруются последовательно: Table 1, Table 2 / Figure 1, Figure 2
- Название — над таблицей, жирным
- Примечание — под таблицей, обычный шрифт

---

## Структурные требования (проверить вручную после экспорта)

- [ ] Каждая глава начинается с новой страницы (Pandoc делает автоматически для H1)
- [ ] Введение, заключение, список источников — с новой страницы
- [ ] Заголовки нумеруются: `Introduction` / `1. Literature Review` / `1.1` / `1.2` и т.д.
- [ ] Точка в конце заголовка не ставится
- [ ] В оглавлении указаны номера страниц (обновить в Word: ПКМ → «Обновить поле»)
- [ ] Список источников — hanging indent, алфавитный порядок
- [ ] Таблицы и схемы пронумерованы и подписаны
- [ ] ≥ 45 академических источников в References

---

## После экспорта — напомни пользователю

1. Открыть DOCX и проверить форматирование вручную (поля, шрифт, интервал)
2. Добавить **титульный лист** вручную в Word
3. Добавить **аннотации** (рус. + англ., 125–175 слов каждая) после титульного листа — вручную
4. Вставить **AI disclaimer** в конец работы (перед приложениями):
   > *"I used AI-based tools to find relevant academic articles and books, to improve punctuation and spelling, and to refine the formatting of the reference list in accordance with APA style."*
5. Обновить оглавление в Word (ПКМ → «Обновить поле»)
6. Проверить hanging indent в списке источников
7. Проверить нумерацию таблиц и рисунков

---

## Частые проблемы

| Проблема | Решение |
|---------|---------|
| `pandoc: command not found` (macOS) | `brew install pandoc` |
| `pandoc: command not found` (Windows) | `winget install JohnMacFarlane.Pandoc` |
| `python-docx not found` | `pip install python-docx` |
| Неправильный порядок глав | Переименовать файлы: `00_`, `01_`, `02_`… |
| Нет оглавления | Убедись что заголовки используют `#`, `##`, `###` |
| Нет hanging indent в References | Настроить стиль абзаца в Word вручную или через reference.docx |
| Кривое форматирование | Запустить `/create-reference-doc` и повторить экспорт |
