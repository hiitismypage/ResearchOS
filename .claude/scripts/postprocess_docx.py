#!/usr/bin/env python3
"""
postprocess_docx.py — Постобработка pandoc-DOCX для соответствия требованиям МГТУ Баумана.

Что делает:
  1. Заголовки: 14pt bold TNR, структурные (ВВЕДЕНИЕ/ЗАКЛЮЧЕНИЕ/...) — центр без отступа,
     нумерованные (1, 1.1, ...) — влево с отступом 1.25 см.
  2. Списки: bullet-маркер → «-- » (тире) с отступом 1.25 см.
  3. Формулы: параграфы вида «$math$ (n.m)» — центрирование, число (n.m) в правой колонке
     (реализовано через центрирование всего параграфа; для точного правого выравнивания
     числа используется Word-редактирование вручную).
  4. Блоки «где»: убирается отступ первой строки, выравнивание влево.

Использование:
    python3 postprocess_docx.py <input.docx> <output.docx>
"""
import re
import sys
from copy import deepcopy

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from lxml import etree

STRUCTURAL_HEADINGS = {
    'ВВЕДЕНИЕ', 'ЗАКЛЮЧЕНИЕ', 'СОДЕРЖАНИЕ', 'РЕФЕРАТ', 'АННОТАЦИЯ',
    'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ', 'СПИСОК ИСПОЛЬЗОВАННОЙ ЛИТЕРАТУРЫ',
    'ОПРЕДЕЛЕНИЯ', 'ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ', 'ПРИЛОЖЕНИЕ',
}

FORMULA_NUMBER_RE = re.compile(r'\(\d+\.\d+\)\s*$')


def para_text(para):
    return para.text.strip()


def is_structural_heading(para):
    txt = para_text(para)
    if txt in STRUCTURAL_HEADINGS:
        return True
    if txt.isupper() and len(txt) > 3 and not txt[0].isdigit():
        return True
    return False


def has_math(para):
    ns = 'm'
    el = para._element
    return (
        el.find(f'{{{qn("m:oMath").split("}")[0][1:]}}}oMath') is not None
        or '{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath' in etree.tostring(el, encoding='unicode')
    )


def is_formula_para(para):
    txt = para_text(para)
    return bool(FORMULA_NUMBER_RE.search(txt)) and ('$' in txt or has_math(para))


def is_gde_para(para):
    txt = para_text(para)
    return txt.startswith('где ') or txt.startswith('где$') or txt == 'где'


def is_list_para(para):
    sn = para.style.name if para.style else ''
    if 'List' in sn or 'Bullet' in sn:
        return True
    # pandoc may use Normal style with numPr element
    pPr = para._element.find(qn('w:pPr'))
    if pPr is not None and pPr.find(qn('w:numPr')) is not None:
        return True
    return False


def fix_heading(para, structural):
    pf = para.paragraph_format
    if structural:
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.first_line_indent = Cm(0)
        pf.left_indent = Cm(0)
    else:
        para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf.first_line_indent = Cm(1.25)
        pf.left_indent = Cm(0)
    for run in para.runs:
        run.bold = True
        run.font.size = Pt(14)
        run.font.name = 'Times New Roman'
        run.font.italic = False


def fix_list_para(para, doc):
    """Convert bullet list paragraph to dash paragraph."""
    pf = para.paragraph_format
    # Change to Normal style
    try:
        para.style = doc.styles['Normal']
    except KeyError:
        pass
    # Remove list numbering XML
    pPr = para._element.find(qn('w:pPr'))
    if pPr is not None:
        numPr = pPr.find(qn('w:numPr'))
        if numPr is not None:
            pPr.remove(numPr)
    # Set indent: hanging style — first line at 1.25cm, left at 1.75cm
    pf.left_indent = Cm(1.75)
    pf.first_line_indent = Cm(-0.5)  # hanging
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    # Prepend dash to first non-empty run
    prepended = False
    for run in para.runs:
        if run.text.strip():
            run.text = '-- ' + run.text.lstrip()
            prepended = True
            break
    if not prepended and para.runs:
        para.runs[0].text = '-- '


def fix_formula_para(para):
    pf = para.paragraph_format
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(0)
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)


def fix_gde_para(para):
    pf = para.paragraph_format
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(0)


def postprocess(input_path, output_path):
    doc = Document(input_path)

    for para in doc.paragraphs:
        sn = para.style.name if para.style else ''

        if sn.startswith('Heading 1'):
            fix_heading(para, is_structural_heading(para))

        elif sn.startswith('Heading 2') or sn.startswith('Heading 3'):
            fix_heading(para, False)

        elif is_list_para(para):
            fix_list_para(para, doc)

        elif is_formula_para(para):
            fix_formula_para(para)

        elif is_gde_para(para):
            fix_gde_para(para)

    doc.save(output_path)
    print(f'Постобработка завершена: {output_path}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Использование: python3 postprocess_docx.py <input.docx> <output.docx>')
        sys.exit(1)
    postprocess(sys.argv[1], sys.argv[2])
