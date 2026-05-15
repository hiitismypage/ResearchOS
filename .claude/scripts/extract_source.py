#!/usr/bin/env python3
"""
Извлекает текст из PDF/DOCX/TXT для анализа.
Использование: python3 extract_source.py <путь_к_файлу>
Выводит первые 3000 слов для анализа Клодом.
"""
import sys
import os


def extract_pdf(path):
    # 1. pdfplumber (лучшее качество)
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            text = []
            for page in pdf.pages[:15]:
                t = page.extract_text()
                if t:
                    text.append(t)
        result = '\n'.join(text)
        if result.strip():
            return result
    except ImportError:
        pass
    except Exception:
        pass

    # 2. pdftotext из poppler (miniforge или системный)
    import subprocess
    import shutil
    pdftotext = shutil.which('pdftotext') or '/Users/kbalashova/miniforge3/bin/pdftotext'
    try:
        result = subprocess.run(
            [pdftotext, '-layout', path, '-'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 3. PyPDF2 (последний вариант)
    try:
        import PyPDF2
        text = []
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages[:15]:
                t = page.extract_text()
                if t:
                    text.append(t)
        result = '\n'.join(text)
        if result.strip():
            return result
    except ImportError:
        pass
    except Exception:
        pass

    return "Ошибка: не удалось извлечь текст. Установи poppler (brew install poppler) или pdfplumber (pip install pdfplumber)."


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
