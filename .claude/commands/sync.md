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
- `/sync start` — старт сессии: актуализировать ветку относительно remote и main

---

## Вспомогательная процедура: безопасный pull с rebase

Используй эту процедуру везде, где нужно подтянуть remote. Она корректно обрабатывает расхождение веток.

```
# 1. Проверь состояние
git status
git log --oneline HEAD..origin/<ветка>   # что есть на remote, чего нет локально
git log --oneline origin/<ветка>..HEAD   # что есть локально, чего нет на remote

# 2. Если есть незакоммиченные изменения — спрячь их
git stash

# 3. Подтяни с rebase (работает и когда ветки разошлись)
git pull --rebase origin <ветка>

# 4. Верни спрятанные изменения (если делал stash)
git stash pop

# При конфликтах на любом шаге — остановись и сообщи пользователю.
# Никогда не разрешай конфликты автоматически.
```

---

## /sync start — запускать в начале каждой сессии

Цель: убедиться что локальный проект полностью актуален перед началом работы.

1. Определи текущую ветку: `git branch --show-current`
2. `git fetch origin`
3. Покажи состояние относительно remote и main:
   ```
   git log HEAD..origin/<ветка> --oneline   # новое на remote
   git log origin/<ветка>..HEAD --oneline   # локальные коммиты впереди
   git log HEAD..origin/main --oneline      # новое в main
   ```
4. Если текущая ветка `main`:
   - Применить процедуру безопасного pull с rebase для `main`
5. Если текущая ветка НЕ `main` (например `aram`):
   - Сначала: применить процедуру безопасного pull с rebase для текущей ветки
   - Затем: `git merge origin/main` — влить обновления из main
   - При конфликтах — сообщить и остановиться
6. Итог одной строкой: `✓ Session started: branch <ветка>, synced X commits`

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
     - `content(diploma-aram): update outline v2 and source notes`
     - `chore(settings): update project permissions`
3. Определи текущую ветку: `git branch --show-current`
4. Выполни staging:
   ```
   git add -A
   ```
5. **Коммит:** `git commit` требует подтверждения пользователя (в deny-листе).
   Покажи пользователю готовую команду и попроси запустить через `!`:
   ```
   ! git commit -m "<message>"
   ```
6. После коммита — запуши:
   ```
   git push origin <текущая_ветка>
   ```
7. Сообщи: ветка, количество файлов, хэш коммита

---

## /sync pull

1. `git fetch origin`
2. Определи текущую ветку
3. Покажи изменения:
   ```
   git log HEAD..origin/<ветка> --oneline   # новое на remote
   git log HEAD..origin/main --oneline      # новое в main (если ветка не main)
   ```
4. Применить процедуру безопасного pull с rebase для текущей ветки
5. Если ветка не main и в main есть новые коммиты: `git merge origin/main`
6. Сообщи что обновлено

---

## /sync checkpoint

Быстрый локальный коммит без пуша — сохранить прогресс в середине сессии.

1. `git add -A`
2. Покажи пользователю команду для запуска через `!`:
   ```
   ! git commit -m "wip: checkpoint <краткое описание>"
   ```
   Например: `wip: checkpoint writing chapter 2 intro`
3. НЕ пушить
4. Одна строка ответа: `✓ Checkpoint: <хэш>`

---

## Правила

- Никогда `git push --force`
- Никогда `git reset --hard` без явного запроса
- Всегда использовать `--rebase` при pull, чтобы избежать лишних merge-коммитов
- Перед `git pull --rebase` — проверить незакоммиченные изменения и при необходимости сделать `git stash`
- При конфликтах при merge или rebase — сообщить и остановиться, не разрешать автоматически
- Commit message всегда на английском
- Пушить всегда в текущую ветку, никогда не пушить в чужую ветку без запроса
- `git commit` требует ручного запуска пользователем (через `! git commit`)

---

## Рекомендации по частоте

- **Начало сессии** → `/sync start` (всегда)
- **Каждые 30-45 минут** или после логического блока → `/sync checkpoint`
- **Конец сессии** → `/sync`
