#!/usr/bin/env python3
"""
Добавляет запись в bibliography.bib.
Использование: python3 add_to_bib.py <bib_file> "<bibtex_entry>"
Или через stdin: echo "@article{...}" | python3 add_to_bib.py <bib_file>
"""
import sys


def main():
    if len(sys.argv) < 2:
        print("Использование: python3 add_to_bib.py <bib_file> [bibtex_entry]")
        sys.exit(1)

    bib_file = sys.argv[1]
    entry = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read()

    if not entry.strip():
        print("Ошибка: пустая BibTeX запись")
        sys.exit(1)

    with open(bib_file, 'a', encoding='utf-8') as f:
        f.write('\n' + entry.strip() + '\n')
    print(f"Добавлено в {bib_file}")


if __name__ == '__main__':
    main()
