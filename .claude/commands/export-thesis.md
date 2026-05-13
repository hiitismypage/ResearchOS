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
    # или скачай установщик: https://pandoc.org/installing.html
```

**Windows:**
```
⚠️  Pandoc не установлен. Установи одним из способов:

    Вариант 1 — через winget (встроен в Windows 10/11):
        winget install --id JohnMacFarlane.Pandoc

    Вариант 2 — через Scoop:
        scoop install pandoc

    Вариант 3 — через conda/miniforge:
        conda install -c conda-forge pandoc

    Вариант 4 — скачать .msi установщик:
        https://pandoc.org/installing.html
        (выбрать Windows installer)

    После установки перезапусти терминал и снова запусти /export-thesis.
```

**Linux:**
```
⚠️  Pandoc не установлен. Установи:

    sudo apt-get install pandoc   # Debian/Ubuntu
    sudo dnf install pandoc       # Fedora
    conda install -c conda-forge pandoc
```

Не продолжай выполнение скилла, пока Pandoc не установлен.

### Учёт Windows при запуске скрипта

На Windows `bash` может быть недоступен. Используй Git Bash, WSL, или адаптируй команду:

- **Git Bash / WSL:** `bash .claude/scripts/export.sh projects/<slug> <name>` — работает как на macOS
- **PowerShell без bash:** запусти Pandoc напрямую (см. шаг 4 ниже)

### python-docx (для генерации reference.docx)

```bash
python3 -c "import docx; print('ok')" 2>/dev/null || echo "not found"
```

Если не найден — сообщи:

```
⚠️  python-docx не установлен. Установи:

    pip install python-docx

reference.docx будет использован шаблон по умолчанию (форматирование может отличаться от FORMAT.md).
```

---

## Шаг 3 — проверить наличие глав

```bash
ls projects/<slug>/chapters/*.md 2>/dev/null | sort -V
```

Если список пустой — сообщи что нечего экспортировать.

Если главы есть — **покажи их список** в порядке сортировки (именно в таком порядке они войдут в документ):

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

**Windows (PowerShell, если bash недоступен)** — собери Pandoc-команду вручную:
```powershell
# Определи переменные
$PROJECT = "projects/<slug>"
$DATE = Get-Date -Format "yyyy-MM-dd"
$OUTPUT = "$PROJECT/output/thesis_$DATE.docx"

# Создай папку output если нет
New-Item -ItemType Directory -Force -Path "$PROJECT/output"

# Сгенерируй reference.docx (если python-docx установлен)
python .claude/scripts/create_reference_doc.py "$PROJECT/FORMAT.md" "$PROJECT/reference.docx"

# Запусти Pandoc
$chapters = Get-ChildItem "$PROJECT/chapters/*.md" | Sort-Object Name
pandoc $chapters --from markdown --to docx --toc --toc-depth=3 `
  --reference-doc="$PROJECT/reference.docx" `
  --output="$OUTPUT"

Write-Host "Готово: $OUTPUT"
```

Скрипт автоматически (bash-версия):
- Генерирует `reference.docx` из `FORMAT.md` (Times New Roman 12pt, поля 25/10/20/20мм, межстрочный 1.5, отступ 1.25см)
- Собирает все `chapters/*.md` в порядке имён файлов
- Добавляет автоматическое оглавление (`--toc`, глубина 3)
- Применяет язык из `FORMAT.md`
- Подключает `bibliography.bib` если файл существует
- Сохраняет в `projects/<slug>/output/<output_name>_YYYY-MM-DD.docx`

---

## Шаг 5 — проверить результат

После успешного запуска:

```bash
du -h projects/<slug>/output/*.docx | tail -1
```

Сообщи пользователю:
- Полный путь к файлу
- Размер файла
- Список вошедших глав
- Предупреждения если были (например: нет reference.docx, нет bibliography.bib)

---

## Требования к форматированию (из методичка_ВКР.pdf)

Эти требования уже заложены в `FORMAT.md` и автоматически применяются через `reference.docx`:

| Параметр | Значение |
|----------|---------|
| Шрифт | Times New Roman 12pt |
| Межстрочный интервал | 1.5 |
| Отступ первой строки | 1.25 см |
| Поля (лев/пр/верх/низу) | 25 / 10 / 20 / 20 мм |
| Выравнивание текста | По ширине |
| Нумерация страниц | Вверху по центру, с 2-й страницы |
| Сноски | Times New Roman 10pt, по ширине |

**Структурные требования** (необходимо проверить вручную после экспорта):
- Каждая глава начинается с новой страницы ✓ (Pandoc делает автоматически для H1)
- Заголовки нумеруются: Introduction / 1. Literature Review / 1.1 / 1.2 и т.д.
- Точка в конце заголовка не ставится
- Аннотации на рус. и англ. (125–175 слов каждая) — добавляются вручную на титульном листе
- AI disclaimer обязателен (добавить вручную в финальный документ)

---

## Частые проблемы

| Проблема | Решение |
|---------|---------|
| `pandoc: command not found` (macOS) | `brew install pandoc` |
| `pandoc: command not found` (Windows) | `winget install JohnMacFarlane.Pandoc` или скачать .msi с pandoc.org |
| `bash: command not found` (Windows) | Использовать Git Bash, WSL, или PowerShell-вариант команды из шага 4 |
| `python-docx not found` | `pip install python-docx` |
| Неправильный порядок глав | Переименовать файлы: `00_`, `01_`, `02_`… |
| Нет оглавления | Убедись что заголовки в `.md` используют `#`, `##`, `###` |
| Кривое форматирование | Запустить `/create-reference-doc` и повторить экспорт |
| Путь с пробелами не работает (Windows) | Обернуть путь в кавычки: `"projects/my thesis"` |

---

## После экспорта — напомни пользователю

1. Открыть DOCX и проверить форматирование вручную (особенно поля и шрифт)
2. Добавить титульный лист вручную в Word
3. Добавить аннотации (рус. + англ.) после титульного листа
4. Вставить AI disclaimer в конец работы
5. Проверить оглавление (обновить поля Word: правая кнопка → «Обновить поле»)
