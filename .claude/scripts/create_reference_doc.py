#!/usr/bin/env python3
"""
Генерирует reference.docx для Pandoc на основе format.md подпроекта.
Использование: python3 create_reference_doc.py <путь_к_format.md> <путь_к_output.docx>
"""
import sys
from docx import Document
from docx.shared import Pt, Cm, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH


def parse_format(path):
    """Парсит format.md, возвращает dict настроек."""
    settings = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, _, value = line.partition(':')
                value = value.split('#')[0].strip()
                if value:
                    settings[key.strip()] = value.strip()
    return settings


def alignment_map(val):
    return {
        'justify': WD_ALIGN_PARAGRAPH.JUSTIFY,
        'left': WD_ALIGN_PARAGRAPH.LEFT,
        'center': WD_ALIGN_PARAGRAPH.CENTER,
        'right': WD_ALIGN_PARAGRAPH.RIGHT,
    }.get(val, WD_ALIGN_PARAGRAPH.JUSTIFY)


def apply_paragraph_format(para_format, s, is_body=False):
    """Применяет настройки из словаря к paragraph format объекту."""
    if is_body:
        indent_str = s.get('first_line_indent', '1.25cm').replace('cm', '')
        para_format.first_line_indent = Cm(float(indent_str))
        para_format.alignment = alignment_map(s.get('body_alignment', 'justify'))

    spacing_before = s.get('paragraph_spacing_before', '0pt').replace('pt', '')
    spacing_after = s.get('paragraph_spacing_after', '0pt').replace('pt', '')
    para_format.space_before = Pt(float(spacing_before) if spacing_before else 0)
    para_format.space_after = Pt(float(spacing_after) if spacing_after else 0)

    ls = float(s.get('line_spacing', '1.5'))
    para_format.line_spacing = Pt(ls * float(s.get('font_size', '14')))


def create_reference_doc(format_path, output_path):
    s = parse_format(format_path)
    doc = Document()

    # Поля страницы
    for section in doc.sections:
        section.top_margin = Mm(float(s.get('margin_top', '20')))
        section.bottom_margin = Mm(float(s.get('margin_bottom', '20')))
        section.left_margin = Mm(float(s.get('margin_left', '30')))
        section.right_margin = Mm(float(s.get('margin_right', '15')))

    # Стиль Normal
    normal = doc.styles['Normal']
    normal.font.name = s.get('font_family', 'Times New Roman')
    normal.font.size = Pt(float(s.get('font_size', '14')))
    apply_paragraph_format(normal.paragraph_format, s, is_body=True)

    # Заголовок 1
    h1 = doc.styles['Heading 1']
    h1.font.name = s.get('heading1_font', s.get('font_family', 'Times New Roman'))
    h1.font.size = Pt(float(s.get('heading1_size', s.get('font_size', '14'))))
    h1.font.bold = s.get('heading1_bold', 'true').lower() == 'true'
    h1.paragraph_format.alignment = alignment_map(s.get('heading1_alignment', 'center'))
    apply_paragraph_format(h1.paragraph_format, s)

    # Заголовок 2
    h2 = doc.styles['Heading 2']
    h2.font.name = s.get('heading2_font', s.get('font_family', 'Times New Roman'))
    h2.font.size = Pt(float(s.get('heading2_size', s.get('font_size', '14'))))
    h2.font.bold = s.get('heading2_bold', 'true').lower() == 'true'
    h2.paragraph_format.alignment = alignment_map(s.get('heading2_alignment', 'left'))
    apply_paragraph_format(h2.paragraph_format, s)

    # Заголовок 3
    h3 = doc.styles['Heading 3']
    h3.font.name = s.get('heading3_font', s.get('font_family', 'Times New Roman'))
    h3.font.size = Pt(float(s.get('heading3_size', s.get('font_size', '14'))))
    h3.font.bold = s.get('heading3_bold', 'false').lower() == 'true'
    h3.font.italic = s.get('heading3_italic', 'false').lower() == 'true'
    h3.paragraph_format.alignment = alignment_map(s.get('heading3_alignment', 'left'))
    apply_paragraph_format(h3.paragraph_format, s)

    doc.save(output_path)
    print(f"reference.docx создан: {output_path}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Использование: python3 create_reference_doc.py <format.md> <output.docx>")
        sys.exit(1)
    create_reference_doc(sys.argv[1], sys.argv[2])
