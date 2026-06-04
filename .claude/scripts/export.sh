#!/bin/bash
# Экспорт подпроекта в DOCX через Pandoc + постобработка (МГТУ Баумана)
# Использование: bash export.sh <папка_подпроекта> [имя_файла]
set -e

PROJECT_DIR="$1"
OUTPUT_NAME="${2:-thesis}"
DATE=$(date +%Y-%m-%d)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Путь к pandoc (не в системном PATH)
PANDOC="${PANDOC_BIN:-/Users/kbalashova/Applications/pandoc/pandoc}"
if [ ! -f "$PANDOC" ]; then
  PANDOC="$(which pandoc 2>/dev/null || true)"
fi
if [ -z "$PANDOC" ]; then
  echo "Ошибка: pandoc не найден. Установи или укажи PANDOC_BIN=/путь/к/pandoc"
  exit 1
fi

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
RAW_DOCX="$OUTPUT_DIR/${OUTPUT_NAME}_raw_${DATE}.docx"
FINAL_DOCX="$OUTPUT_DIR/${OUTPUT_NAME}_${DATE}.docx"

mkdir -p "$OUTPUT_DIR"

# Генерируем reference.docx из FORMAT.md
if [ -f "$FORMAT_FILE" ]; then
  echo "Генерирую reference.docx из FORMAT.md..."
  python3 "$SCRIPT_DIR/create_reference_doc.py" "$FORMAT_FILE" "$REFERENCE_DOC" || {
    echo "Предупреждение: не удалось создать reference.docx, используется шаблон по умолчанию"
    REFERENCE_DOC="$ROOT_DIR/templates/reference.docx"
  }
fi

# Собираем главы
CHAPTERS_LIST=()
while IFS= read -r f; do
  CHAPTERS_LIST+=("$f")
done < <(ls -v "$CHAPTERS_DIR"/*.md 2>/dev/null | sort -V)

if [ ${#CHAPTERS_LIST[@]} -eq 0 ]; then
  echo "Ошибка: нет .md файлов в $CHAPTERS_DIR"
  exit 1
fi

echo "Главы для экспорта:"
for f in "${CHAPTERS_LIST[@]}"; do echo "  - $(basename "$f")"; done

# Аргументы pandoc
PANDOC_ARGS=(
  --from "markdown+tex_math_dollars+raw_tex"
  --to docx
  --toc
  --toc-depth=3
  -V lang=ru
  --resource-path="$CHAPTERS_DIR"
  --output="$RAW_DOCX"
)

[ -f "$REFERENCE_DOC" ] && PANDOC_ARGS+=(--reference-doc="$REFERENCE_DOC")
[ -f "$BIB_FILE" ]      && PANDOC_ARGS+=(--bibliography="$BIB_FILE" --citeproc)

echo ""
echo "Запускаю pandoc..."
"$PANDOC" "${PANDOC_ARGS[@]}" "${CHAPTERS_LIST[@]}"

DRAFT_DOCX="$PROJECT_DIR/drafts/диплом_итог.docx"

echo ""
echo "Постобработка (МГТУ: заголовки, списки, формулы, рисунки, таблицы, титульник)..."
if [ -f "$DRAFT_DOCX" ]; then
  python3 "$SCRIPT_DIR/postprocess_docx.py" "$RAW_DOCX" "$FINAL_DOCX" "$DRAFT_DOCX"
else
  echo "  (черновик не найден — титульный лист пропущен)"
  python3 "$SCRIPT_DIR/postprocess_docx.py" "$RAW_DOCX" "$FINAL_DOCX"
fi

# Убираем промежуточный файл
rm -f "$RAW_DOCX"

echo ""
echo "Готово: $FINAL_DOCX"
du -h "$FINAL_DOCX"
