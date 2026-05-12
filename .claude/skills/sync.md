---
name: sync
description: Push and pull changes to/from remote repo. Auto-pulls main at session start. Use checkpoint to save progress mid-session.
model: haiku
---

Управляет синхронизацией с удалённым репозиторием.

## Режимы запуска

- `/sync` — закоммитить всё и запушить в текущую ветку
- `/sync pull` — подтянуть изменения из remote (текущая ветка + merge из main)
- `/sync checkpoint` — быстрый локальный коммит без пуша
- `/sync start` — старт сессии: pull из main + merge в текущую ветку

---

## /sync start — запускать в начале каждой сессии

Цель: убедиться что локальный проект актуален перед началом работы.

1. Определи текущую ветку: `git branch --show-current`
2. `git fetch origin`
3. Покажи что изменилось на main с момента последней синхронизации:
   `git log HEAD..origin/main --oneline`
4. Если изменений нет — одна строка: `✓ Up to date with main`
5. Если есть изменения:
   - Если текущая ветка `main`: `git pull origin main`
   - Если текущая ветка НЕ `main` (например `aram`):
     - `git pull origin <текущая_ветка>` — сначала подтянуть свою ветку
     - `git merge origin/main` — затем влить обновления из main
     - При конфликтах — сообщить и остановиться, не разрешать автоматически
6. Итог одной строкой: `✓ Session started: branch <ветка>, merged X commits from main`

---

## /sync (стандартный)

1. `git status` + `git diff --stat` — посмотри что изменилось
2. Сформируй commit message по Conventional Commits (англ.):
   - `feat:` — новый файл, скилл, шаблон
   - `docs:` — обновление CLAUDE.md, README, шаблонов
   - `chore:` — настройки, .gitignore, скрипты
   - `content:` — контент подпроектов (chapters, notes, outlines)
   - `fix:` — исправление ошибок
   - Формат: `<type>(<scope>): <short description>`
   - Примеры:
     - `feat(skills): add process-source and find-quote skills`
     - `docs(readme): add full project setup guide`
     - `content(diploma-aram): update outline v2 and source notes`
     - `chore(scripts): add export.sh and create_reference_doc.py`
3. Определи текущую ветку: `git branch --show-current`
4. Выполни:
   ```
   git add -A
   git commit -m "<message>"
   git push origin <текущая_ветка>
   ```
5. Сообщи: ветка, количество файлов, хэш коммита

---

## /sync pull

1. `git fetch origin`
2. Определи текущую ветку
3. Покажи изменения: `git log HEAD..origin/<ветка> --oneline`
4. Если текущая ветка НЕ main — также покажи новое в main: `git log HEAD..origin/main --oneline`
5. При наличии изменений — выполни pull + merge (как в /sync start)
6. Сообщи что обновлено

---

## /sync checkpoint

Быстрый локальный коммит без пуша — сохранить прогресс в середине сессии.

1. `git add -A`
2. `git commit -m "wip: checkpoint <краткое описание>"`
   Например: `wip: checkpoint writing chapter 2 intro`
3. НЕ пушить
4. Одна строка ответа: `✓ Checkpoint: <хэш>`

---

## Правила

- Никогда `git push --force`
- Никогда `git reset --hard` без явного запроса
- При конфликтах при merge — сообщить и остановиться, не разрешать автоматически
- Commit message всегда на английском
- Пушить всегда в текущую ветку, никогда не пушить в чужую ветку без запроса

---

## Рекомендации по частоте

- **Начало сессии** → `/sync start` (всегда)
- **Каждые 30-45 минут** или после логического блока → `/sync checkpoint`
- **Конец сессии** → `/sync`
