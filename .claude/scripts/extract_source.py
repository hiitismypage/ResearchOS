#!/usr/bin/env python3
"""
Извлекает текст из PDF/DOCX/TXT для анализа.
Использование: python3 extract_source.py <путь_к_файлу>
Выводит первые 3000 слов для анализа Клодом.
"""
import sys
import os


def extract_pdf(path):
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            text = []
            for page in pdf.pages[:15]:  # первые 15 страниц
                t = page.extract_text()
                if t:
                    text.append(t)
        return '\n'.join(text)
    except ImportError:
        return "Ошибка: установи pdfplumber — pip install pdfplumber"


def extract_docx(path):
    try:
        from docx import Document
        doc = Document(path)
        return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        return "Ошибка: установи python-docx — pip install python-docx"


def extract_txt(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def main():
    if len(sys.argv) < 2:
        print("Использование: python3 extract_source.py <файл>")
        sys.exit(1)

    path = sys.argv[1]
    ext = os.path.splitext(path)[1].lower()

    if ext == '.pdf':
        text = extract_pdf(path)
    elif ext in ('.docx', '.doc'):
        text = extract_docx(path)
    elif ext == '.txt':
        text = extract_txt(path)
    else:
        print(f"Неподдерживаемый формат: {ext}")
        sys.exit(1)

    # Лимит: первые 3000 слов (экономия токенов)
    words = text.split()
    if len(words) > 3000:
        text = ' '.join(words[:3000])
        text += '\n\n[... текст обрезан до 3000 слов для экономии токенов ...]'

    print(text)


if __name__ == '__main__':
    main()
