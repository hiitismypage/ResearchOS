---
name: process-source
description: Обрабатывает файл литературы из sources/files/ — извлекает тезисы, создаёт карточку источника
model: sonnet
---

Аргумент: путь к файлу в sources/files/ активного подпроекта. Например:
- `/process-source projects/my_thesis/sources/files/goffman_1959.pdf`

## Шаги

1. **Определи активный подпроект** из аргумента или спроси если неясно.

2. **Извлеки текст:**
   ```
   python3 .claude/scripts/extract_source.py <путь_к_файлу>
   ```
   Получишь первые 3000 слов.

3. **Прочитай CONTEXT.md** подпроекта — пойми тему и исследовательский вопрос.

4. **Создай карточку источника** по шаблону `projects/<проект>/sources/notes/_template.md`:
   - Заполни все поля на основе извлечённого текста
   - Раздел "Связь с моей работой" заполни относительно CONTEXT.md
   - Имя файла карточки: `<фамилия_год_ключевое_слово>.md` (латиница, нижний регистр)
     Например: `goffman_1959_presentation.md`

5. **Сохрани карточку** в `projects/<проект>/sources/notes/<имя_файла>.md`

6. **Добавь строку** в `projects/<проект>/sources/bibliography.md`:
   ```
   - [Автор, Год] Название. Журнал/Издательство. → notes/<имя_файла>.md
   ```

7. **Предложи BibTeX-запись** в формате:
   ```bibtex
   @article{goffman1959presentation,
     author  = {Goffman, Erving},
     title   = {The Presentation of Self in Everyday Life},
     year    = {1959},
     ...
   }
   ```
   Спроси: добавить в `bibliography.bib`?
   Если да:
   ```
   python3 .claude/scripts/add_to_bib.py <проект>/sources/bibliography.bib "<bibtex>"
   ```

## Правила

- Если текст не позволяет точно определить авторов или год — ставь `[UNKNOWN]`, не выдумывай
- Не повторяй извлечённый текст в своём ответе — только карточку
- Если файл не читается (зашифрован, сканированный PDF) — сообщи об этом явно
