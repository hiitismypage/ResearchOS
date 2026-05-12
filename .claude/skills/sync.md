---
name: sync
description: Push and pull changes to/from remote repo. Use during sessions to checkpoint progress.
model: haiku
---

Управляет синхронизацией с удалённым репозиторием. Три режима:

## Режимы запуска

- `/sync` — стандартный: добавить всё, закоммитить, запушить
- `/sync pull` — только получить изменения из remote
- `/sync checkpoint` — быстрый коммит без пуша (сохранить прогресс в сессии)

---

## /sync (стандартный)

1. Запусти `git status` — посмотри что изменилось
2. Запусти `git diff --stat` — краткая сводка изменений
3. Сформируй commit message по Conventional Commits (англ.):
   - `feat:` — новый файл, скилл, шаблон
   - `docs:` — обновление CLAUDE.md, README, шаблонов
   - `chore:` — настройки, .gitignore, скрипты
   - `content:` — контент подпроектов (chapters, notes, outlines)
   - `fix:` — исправление ошибок
   - Формат: `<type>(<scope>): <short description>`
   - Примеры:
     - `feat(skills): add process-source and find-quote skills`
     - `docs(readme): add full project setup guide`
     - `content(example-project): update outline and add source notes`
     - `chore(scripts): add export.sh and create_reference_doc.py`
4. Выполни:
   ```
   git add -A
   git commit -m "<message>"
   git push origin main
   ```
5. Сообщи: сколько файлов, что запушено, хэш коммита

---

## /sync pull

1. `git fetch origin`
2. Покажи что изменилось на remote: `git log HEAD..origin/main --oneline`
3. Если есть изменения — спроси подтверждение
4. `git pull origin main`
5. Сообщи что обновлено

---

## /sync checkpoint

Быстрый коммит без интерактивности — для сохранения прогресса в середине сессии.

1. `git add -A`
2. `git commit -m "wip: checkpoint [<краткое описание что делалось>]"`
   Например: `wip: checkpoint writing chapter 2 intro`
3. НЕ пушить (только локальный коммит)
4. Одна строка ответа: `✓ Checkpoint saved: <хэш>`

---

## Правила

- Никогда не делать `git push --force`
- Никогда не делать `git reset --hard` без явного запроса
- Если есть конфликты при pull — сообщить и остановиться, не разрешать автоматически
- Коммит message всегда на английском
- Scope в скобках — название модуля/папки: `skills`, `templates`, `readme`,
  `scripts`, `memory`, `projects`, `example-project` или конкретный slug проекта

---

## Рекомендации по частоте

В длинной рабочей сессии делай `/sync checkpoint` каждые 30-45 минут или после
завершения логического блока (написал раздел, обработал несколько источников).
Финальный `/sync` — в конце сессии.
