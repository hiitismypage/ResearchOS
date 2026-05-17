#!/usr/bin/env python3
"""
OCR сканированных PDF через Apple Vision framework.
Использует PyMuPDF для рендеринга страниц и VNRecognizeTextRequest для распознавания.

Использование:
    python3 .claude/scripts/ocr_pdf.py <путь_к_pdf> [--pages 1-5] [--lang ru-RU]

Примеры:
    python3 .claude/scripts/ocr_pdf.py sources/files/book.pdf --pages 1-3
    python3 .claude/scripts/ocr_pdf.py sources/files/book.pdf --pages 1,5,10 --lang ru-RU
"""

import sys
import argparse
import fitz  # PyMuPDF
import tempfile
import os
from pathlib import Path


def ocr_image_apple_vision(image_path: str, languages: list[str]) -> str:
    """OCR одного изображения через Apple Vision VNRecognizeTextRequest."""
    import Vision
    import Quartz
    import objc

    image_url = Quartz.CFURLCreateFromFileSystemRepresentation(
        None, image_path.encode(), len(image_path.encode()), False
    )
    image_source = Quartz.CGImageSourceCreateWithURL(image_url, None)
    if image_source is None:
        return ""
    cg_image = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)
    if cg_image is None:
        return ""

    results = []

    def completion_handler(request, error):
        if error:
            return
        for obs in request.results():
            candidate = obs.topCandidates_(1)
            if candidate:
                results.append(candidate[0].string())

    request = Vision.VNRecognizeTextRequest.alloc().initWithCompletionHandler_(completion_handler)
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    if languages:
        request.setRecognitionLanguages_(languages)

    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, {})
    handler.performRequests_error_([request], objc.nil)

    return "\n".join(results)


def parse_pages(pages_arg: str, total: int) -> list[int]:
    """Разбор аргумента --pages: '1-5', '1,3,5', '1-3,7' → список 0-based индексов."""
    indices = []
    for part in pages_arg.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            indices.extend(range(int(start) - 1, int(end)))
        else:
            indices.append(int(part) - 1)
    return [i for i in indices if 0 <= i < total]


def main():
    parser = argparse.ArgumentParser(description="OCR PDF через Apple Vision")
    parser.add_argument("pdf", help="Путь к PDF-файлу")
    parser.add_argument("--pages", default="1-5",
                        help="Страницы для OCR: '1-5', '1,2,3', '1-3,10' (по умолчанию: 1-5)")
    parser.add_argument("--lang", default="ru-RU,en-US",
                        help="Языки OCR через запятую (по умолчанию: ru-RU,en-US)")
    parser.add_argument("--dpi", type=int, default=300,
                        help="DPI рендеринга страниц (по умолчанию: 300)")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Файл не найден: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    languages = [lang.strip() for lang in args.lang.split(",")]

    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    page_indices = parse_pages(args.pages, total_pages)

    print(f"PDF: {pdf_path.name} ({total_pages} стр.)")
    print(f"Распознаю страницы: {[i+1 for i in page_indices]}")
    print(f"Языки: {languages}")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        for idx in page_indices:
            page = doc[idx]
            mat = fitz.Matrix(args.dpi / 72, args.dpi / 72)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img_path = os.path.join(tmpdir, f"page_{idx+1:04d}.png")
            pix.save(img_path)

            print(f"\n--- Страница {idx+1} ---")
            text = ocr_image_apple_vision(img_path, languages)
            if text.strip():
                print(text)
            else:
                print("[Текст не распознан]")

    doc.close()


if __name__ == "__main__":
    main()
