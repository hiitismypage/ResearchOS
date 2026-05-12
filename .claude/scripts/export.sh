#!/bin/bash
# Экспорт подпроекта в DOCX через Pandoc
# Использование: bash export.sh <папка_подпроекта> [имя_файла]
set -e

PROJECT_DIR="$1"
OUTPUT_NAME="${2:-thesis}"
DATE=$(date +%Y-%m-%d)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -z "$PROJECT_DIR" ]; then
  echo "Ошибка: укажи папку подпроекта"
  echo "Использование: bash export.sh projects/my_thesis"
  exit 1
fi

FORMAT_FILE="$PROJECT_DIR/FORMAT.md"
REFERENCE_DOC="$PROJECT_DIR/reference.docx"
OUTPUT_DIR="$PROJECT_DIR/output"
CHAPTERS_DIR="$PROJECT_DIR/chapters"
BIB_FILE="$PROJECT_DIR/sources/bibliography.bib"

mkdir -p "$OUTPUT_DIR"

# Генерируем reference.docx если есть FORMAT.md и python-docx установлен
if [ -f "$FORMAT_FILE" ]; then
  echo "Генерирую reference.docx из FORMAT.md..."
  python3 "$SCRIPT_DIR/create_reference_doc.py" "$FORMAT_FILE" "$REFERENCE_DOC" || {
    echo "Предупреждение: не удалось создать reference.docx, используется шаблон по умолчанию"
    REFERENCE_DOC="$ROOT_DIR/templates/reference.docx"
  }
fi

# Определяем язык из FORMAT.md
LANG="ru"
if [ -f "$FORMAT_FILE" ]; then
  LANG=$(grep "^language:" "$FORMAT_FILE" | head -1 | cut -d: -f2 | cut -d# -f1 | tr -d ' ')
  [ -z "$LANG" ] && LANG="ru"
fi

# Собираем список глав в правильном порядке
CHAPTERS=$(ls -v "$CHAPTERS_DIR"/*.md 2>/dev/null | sort -V)
if [ -z "$CHAPTERS" ]; then
  echo "Ошибка: нет .md файлов в $CHAPTERS_DIR"
  exit 1
fi

echo "Главы для экспорта:"
ls -v "$CHAPTERS_DIR"/*.md | sort -V | while read f; do echo "  - $(basename $f)"; done

# Параметры pandoc
PANDOC_ARGS=(
  --from markdown
  --to docx
  --toc
  --toc-depth=3
  --lang="$LANG"
  --output="$OUTPUT_DIR/${OUTPUT_NAME}_${DATE}.docx"
)

[ -f "$REFERENCE_DOC" ] && PANDOC_ARGS+=(--reference-doc="$REFERENCE_DOC")
[ -f "$BIB_FILE" ] && PANDOC_ARGS+=(--bibliography="$BIB_FILE" --citeproc)

# Запускаем pandoc
pandoc "${PANDOC_ARGS[@]}" $CHAPTERS

echo ""
echo "Готово: $OUTPUT_DIR/${OUTPUT_NAME}_${DATE}.docx"
du -h "$OUTPUT_DIR/${OUTPUT_NAME}_${DATE}.docx"
