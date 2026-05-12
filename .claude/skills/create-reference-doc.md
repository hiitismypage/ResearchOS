---
name: create-reference-doc
description: Генерирует reference.docx для подпроекта на основе FORMAT.md
model: haiku
---

Аргумент: название или путь к подпроекту. Например:
- `/create-reference-doc projects/my_thesis`

Шаги:
1. Проверь что файл `<проект>/FORMAT.md` существует. Если нет — сообщи и предложи
   скопировать из `templates/format.md`.
2. Запусти:
   ```
   python3 .claude/scripts/create_reference_doc.py <проект>/FORMAT.md <проект>/reference.docx
   ```
3. Сообщи результат.

Если python-docx не установлен — сообщи об ошибке и предложи:
```
pip install python-docx
```
или через uv (если проект использует uv):
```
uv add python-docx
```

Если всё прошло успешно — напомни что reference.docx используется автоматически
при запуске `bash .claude/scripts/export.sh`.
