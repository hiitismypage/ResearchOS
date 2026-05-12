---
name: import-files
description: Moves files from any location into the correct subfolder of an active subproject based on file type
model: haiku
---

Перемещает файлы в правильное место внутри подпроекта.

## Аргумент

Путь к файлу (или несколько через пробел) + опционально slug подпроекта:
- `/import-files /path/to/article.pdf`
- `/import-files /path/to/data.xlsx projects/diploma_math_modeling`
- `/import-files /path/to/chapter.docx /path/to/source.pdf`

Если подпроект не указан — спроси у пользователя или определи по контексту сессии.

## Логика распределения по папкам

| Тип файла | Куда |
|-----------|------|
| `.pdf` — научная статья, книга, автореферат | `sources/files/` |
| `.docx`, `.doc` — глава диплома, раздел | `chapters/` |
| `.docx`, `.doc` — полный черновик / итоговый файл | `drafts/` |
| `.py` — скрипт модели, калибровки, симуляции | `scripts/` |
| `.xlsx`, `.csv`, `.json` — данные, таблицы | `data/` |
| `.png`, `.jpg`, `.svg` — графики, рисунки | `results/figures/` (создать если нет) |
| Неясный тип | Спросить пользователя |

## Как определить тип DOCX

Если файл `.docx` — спроси: это глава (→ `chapters/`) или итоговый файл диплома (→ `drafts/`)?
Или определи по имени файла: если содержит "glava", "chapter", "глава" → `chapters/`;
если содержит "диплом", "thesis", "итог", "final" → `drafts/`.

## Шаги

1. Определи подпроект (из аргумента или спроси)
2. Для каждого файла определи целевую папку по таблице выше
3. Создай папку если не существует: `mkdir -p <путь>`
4. Выполни перемещение: `mv "<источник>" "<цель>/"`
5. Выведи итог:
   ```
   ✓ article.pdf → projects/diploma_math_modeling/sources/files/
   ✓ chapter3.docx → projects/diploma_math_modeling/chapters/
   ✗ unknown.zip → не знаю куда, укажи папку вручную
   ```

## Правила

- Не перезаписывать файл если в целевой папке уже есть файл с таким именем —
  сообщить и спросить: перезаписать / переименовать / пропустить
- Не удалять оригинал если перемещение не удалось
- При перемещении PDF в `sources/files/` — напомнить что они в `.gitignore`
  и не будут версионированы
