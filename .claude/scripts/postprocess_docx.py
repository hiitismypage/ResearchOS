#!/usr/bin/env python3
"""
postprocess_docx.py — Постобработка pandoc-DOCX для МГТУ Баумана.

Использование:
    python3 postprocess_docx.py <input.docx> <output.docx> [draft.docx]

draft.docx — черновик с титульным листом, который вставляется в начало без изменений.
"""
import re
import sys
from copy import deepcopy

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Emu, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsmap
from docx.oxml import OxmlElement
from lxml import etree

# ─── Константы ────────────────────────────────────────────────────────────────

BLACK = RGBColor(0, 0, 0)
MAX_IMG_WIDTH = Cm(16)          # максимальная ширина рисунка (текстовое поле ~17 см)
MAX_IMG_HEIGHT = Cm(20)         # максимальная высота рисунка
INDENT_FIRST = Cm(1.25)         # отступ первой строки
LIST_LEFT   = Cm(1.75)          # левый отступ пунктов списка
LIST_HANG   = Cm(0.50)          # выступ маркера

STRUCTURAL_HEADINGS = {
    'ВВЕДЕНИЕ', 'ЗАКЛЮЧЕНИЕ', 'СОДЕРЖАНИЕ', 'РЕФЕРАТ', 'АННОТАЦИЯ',
    'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ', 'СПИСОК ИСПОЛЬЗОВАННОЙ ЛИТЕРАТУРЫ',
    'ОПРЕДЕЛЕНИЯ', 'ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ',
}

FORMULA_RE = re.compile(r'#?\((\d+\.\d+[a-zA-Zа-яА-Я]?)\)\s*$')

# ─── Вспомогательные ──────────────────────────────────────────────────────────

def para_text(p):
    return p.text.strip()

def is_structural(p):
    txt = para_text(p)
    return txt in STRUCTURAL_HEADINGS or (txt.isupper() and len(txt) > 3 and not txt[0].isdigit())

def has_omml(p):
    return '{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath' in \
           etree.tostring(p._element, encoding='unicode')

def set_black(run):
    run.font.color.rgb = BLACK
    # Убираем тему цвета (themeColor) если есть
    rPr = run._r.get_or_add_rPr()
    for tag in ('w:color', 'w:rStyle'):
        el = rPr.find(qn(tag))
        if el is not None:
            theme = el.get(qn('w:themeColor'))
            if theme:
                el.attrib.pop(qn('w:themeColor'), None)
                el.attrib.pop(qn('w:themeShade'), None)
                el.attrib.pop(qn('w:themeTint'), None)
            if tag == 'w:color':
                el.set(qn('w:val'), '000000')

# ─── 1. Чёрный цвет везде ─────────────────────────────────────────────────────

def fix_all_colors(doc):
    def fix_para(p):
        for run in p.runs:
            set_black(run)
        # Также выставляем цвет на уровне rPr параграфа, если нет ранов
        pPr = p._element.find(qn('w:pPr'))
        if pPr is not None:
            rPr = pPr.find(qn('w:rPr'))
            if rPr is not None:
                color = rPr.find(qn('w:color'))
                if color is not None:
                    color.set(qn('w:val'), '000000')
                    for attr in (qn('w:themeColor'), qn('w:themeShade'), qn('w:themeTint')):
                        color.attrib.pop(attr, None)

    for p in doc.paragraphs:
        fix_para(p)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    fix_para(p)

# ─── 2. Разрывы страниц перед главами ─────────────────────────────────────────

def add_page_breaks(doc):
    """Вставляет разрыв страницы перед каждым Heading 1 и структурным заголовком."""
    for p in doc.paragraphs:
        sn = p.style.name if p.style else ''
        txt = para_text(p)
        needs_break = (
            sn.startswith('Heading 1')
            or (sn == 'Normal' and is_structural(p))
        )
        if needs_break:
            pPr = p._element.get_or_add_pPr()
            pb = OxmlElement('w:pageBreakBefore')
            pb.set(qn('w:val'), '1')
            # Удалим старый элемент если есть
            old = pPr.find(qn('w:pageBreakBefore'))
            if old is not None:
                pPr.remove(old)
            pPr.append(pb)

# ─── 3. Списки → короткое тире (Word list) ────────────────────────────────────

def _ensure_dash_numbering(doc):
    """Добавляет в numbering.xml определение списка с тире и возвращает numId."""
    W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

    numbering_part = doc.part.numbering_part
    if numbering_part is None:
        # Создаём numbering part с нуля через XML
        from docx.opc.part import Part
        from docx.opc.packuri import PackURI
        from docx.opc.constants import RELATIONSHIP_TYPE as RT
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:numbering xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"'
            ' xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex"'
            ' xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '</w:numbering>'
        )
        # Fallback: просто вернём None
        return None

    num_root = numbering_part._element
    nsW = f'{{{W}}}'

    # Генерируем уникальный abstractNumId
    existing_abs = [
        int(el.get(f'{nsW}abstractNumId', 0))
        for el in num_root.findall(f'{nsW}abstractNum')
    ]
    abs_id = max(existing_abs, default=0) + 1

    existing_nums = [
        int(el.get(f'{nsW}numId', 0))
        for el in num_root.findall(f'{nsW}num')
    ]
    num_id = max(existing_nums, default=0) + 1

    # abstractNum — bullet со знаком тире (U+2013)
    abs_xml = f'''<w:abstractNum xmlns:w="{W}" w:abstractNumId="{abs_id}">
      <w:multiLevelType w:val="hybridMultilevel"/>
      <w:lvl w:ilvl="0">
        <w:start w:val="1"/>
        <w:numFmt w:val="bullet"/>
        <w:lvlText w:val="–"/>
        <w:lvlJc w:val="left"/>
        <w:pPr>
          <w:ind w:left="994" w:hanging="284"/>
        </w:pPr>
        <w:rPr>
          <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
          <w:sz w:val="28"/>
          <w:color w:val="000000"/>
        </w:rPr>
      </w:lvl>
    </w:abstractNum>'''

    num_xml = f'''<w:num xmlns:w="{W}" w:numId="{num_id}">
      <w:abstractNumId w:val="{abs_id}"/>
    </w:num>'''

    abs_el = etree.fromstring(abs_xml)
    num_el = etree.fromstring(num_xml)

    # Вставляем abstractNum перед первым <w:num>
    first_num = num_root.find(f'{nsW}num')
    if first_num is not None:
        num_root.insert(list(num_root).index(first_num), abs_el)
    else:
        num_root.append(abs_el)
    num_root.append(num_el)

    return num_id


def fix_lists(doc):
    """
    Находит:
    а) Pandoc-списки (numPr) → убирает старый маркер, применяет тире-список
    б) Параграфы начинающиеся с '– ' → применяет форматирование пункта списка
    """
    dash_num_id = _ensure_dash_numbering(doc)
    W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

    def apply_list_style(p, text_to_set=None):
        """Применяет стиль пункта списка с тире."""
        pf = p.paragraph_format
        pf.left_indent = LIST_LEFT
        pf.first_line_indent = -LIST_HANG   # hanging
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)

        # Убираем numPr если есть (заменяем своим маркером)
        pPr = p._element.find(qn('w:pPr'))
        if pPr is not None:
            numPr = pPr.find(qn('w:numPr'))
            if numPr is not None:
                pPr.remove(numPr)

        if dash_num_id is not None:
            # Добавляем ссылку на наш dash-список
            pPr = p._element.get_or_add_pPr()
            numPr_el = OxmlElement('w:numPr')
            ilvl_el = OxmlElement('w:ilvl')
            ilvl_el.set(qn('w:val'), '0')
            numId_el = OxmlElement('w:numId')
            numId_el.set(qn('w:val'), str(dash_num_id))
            numPr_el.append(ilvl_el)
            numPr_el.append(numId_el)
            # Вставляем numPr первым в pPr
            pPr.insert(0, numPr_el)

        if text_to_set is not None and p.runs:
            p.runs[0].text = text_to_set + (p.runs[0].text[len(text_to_set):] if p.runs[0].text.startswith(text_to_set) else p.runs[0].text)

    for p in doc.paragraphs:
        sn = p.style.name if p.style else ''
        txt = para_text(p)

        # А) Pandoc-список (Word list paragraph with numPr)
        pPr_el = p._element.find(qn('w:pPr'))
        has_numPr = pPr_el is not None and pPr_el.find(qn('w:numPr')) is not None
        is_word_list = has_numPr or 'List' in sn or 'Bullet' in sn

        if is_word_list:
            # Убираем старые маркеры «-- » если постпроцессор уже добавил их
            for run in p.runs:
                if run.text.startswith('-- '):
                    run.text = run.text[3:]
                elif run.text.startswith('–– ') or run.text.startswith('– – '):
                    run.text = run.text.replace('–– ', '', 1)
            apply_list_style(p)
            continue

        # Б) Параграф начинается с '– ' (en-dash)
        if txt.startswith('– ') or txt.startswith('– '):
            # Убираем '– ' из начала текста первого рана
            for run in p.runs:
                if run.text.strip():
                    if run.text.startswith('– ') or run.text.startswith('– '):
                        run.text = run.text[2:]
                    break
            apply_list_style(p)

# ─── 4. Изображения — масштаб до ширины текста ────────────────────────────────

def _has_drawing(para):
    """True если параграф содержит встроенное изображение."""
    NS_WP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
    return bool(para._element.findall(f'.//{{{NS_WP}}}inline'))


def _scale_inline(inl, max_w, max_h):
    """Масштабирует wp:inline + a:ext по ограничениям."""
    NS_WP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
    NS_A  = 'http://schemas.openxmlformats.org/drawingml/2006/main'

    wp_ext = inl.find(f'{{{NS_WP}}}extent')
    if wp_ext is None:
        return
    cx = int(wp_ext.get('cx', 0))
    cy = int(wp_ext.get('cy', 0))
    if cx == 0:
        return

    # Масштабируем
    if cx > max_w:
        cy = int(cy * max_w / cx)
        cx = int(max_w)
    if cy > max_h:
        cx = int(cx * max_h / cy)
        cy = int(max_h)

    # Пишем в wp:extent
    wp_ext.set('cx', str(cx))
    wp_ext.set('cy', str(cy))

    # Синхронизируем a:ext (reальный DrawingML-размер)
    a_ext = inl.find(f'.//{{{NS_A}}}xfrm/{{{NS_A}}}ext')
    if a_ext is not None:
        a_ext.set('cx', str(cx))
        a_ext.set('cy', str(cy))


def _clear_img_para(p):
    """
    Сбрасывает параграф с изображением: убирает стиль Body Text,
    устанавливает Normal + явные нулевые отступы + автоинтерлиньяж.
    """
    W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

    # Меняем стиль на Normal
    try:
        p.style = p.part.document.styles['Normal']
    except Exception:
        pass

    pPr = p._element.get_or_add_pPr()

    # Явно центрируем
    jc = pPr.find(f'{{{W}}}jc')
    if jc is None:
        jc = OxmlElement('w:jc')
        pPr.append(jc)
    jc.set(qn('w:val'), 'center')

    # Убираем ВСЕ отступы
    ind = pPr.find(f'{{{W}}}ind')
    if ind is None:
        ind = OxmlElement('w:ind')
        pPr.append(ind)
    for attr in ('w:firstLine', 'w:firstLineChars', 'w:left', 'w:leftChars',
                 'w:right', 'w:rightChars', 'w:hanging', 'w:hangingChars'):
        ind.attrib.pop(qn(attr), None)
    ind.set(qn('w:firstLine'), '0')
    ind.set(qn('w:left'), '0')

    # Межстрочный интервал — авто (не Exactly), без before/after
    spacing = pPr.find(f'{{{W}}}spacing')
    if spacing is None:
        spacing = OxmlElement('w:spacing')
        pPr.append(spacing)
    spacing.set(qn('w:before'), '60')
    spacing.set(qn('w:after'), '60')
    # Убираем lineRule=Exact если было
    for attr in (qn('w:lineRule'), qn('w:line')):
        spacing.attrib.pop(attr, None)

    # Убираем pStyle → Body Text
    pStyle = pPr.find(f'{{{W}}}pStyle')
    if pStyle is not None:
        val = pStyle.get(qn('w:val'), '')
        if 'Body' in val or 'Text' in val:
            pPr.remove(pStyle)


def fix_images(doc):
    """Масштабирует встроенные изображения и сбрасывает форматирование параграфа."""
    NS_WP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'

    max_w = int(MAX_IMG_WIDTH)
    max_h = int(MAX_IMG_HEIGHT)

    for p in doc.paragraphs:
        inlines = p._element.findall(f'.//{{{NS_WP}}}inline')
        if not inlines:
            continue

        for inl in inlines:
            _scale_inline(inl, max_w, max_h)

        _clear_img_para(p)

# ─── 5. Таблицы — рамки + жирная шапка ───────────────────────────────────────

def _cell_border(val='single', sz='4', color='000000'):
    def make(tag):
        el = OxmlElement(f'w:{tag}')
        el.set(qn('w:val'),   val)
        el.set(qn('w:sz'),    sz)
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), color)
        return el
    return make

def set_cell_borders(cell):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    borders_el = tcPr.find(qn('w:tcBorders'))
    if borders_el is None:
        borders_el = OxmlElement('w:tcBorders')
        tcPr.append(borders_el)
    else:
        # Очищаем старые
        for child in list(borders_el):
            borders_el.remove(child)
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        borders_el.append(_cell_border()(side))

def fix_tables(doc):
    for tbl in doc.tables:
        for i, row in enumerate(tbl.rows):
            is_header = (i == 0)
            for cell in row.cells:
                set_cell_borders(cell)
                # Убираем цветной фон
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                shd = tcPr.find(qn('w:shd'))
                if shd is not None:
                    shd.set(qn('w:val'),   'clear')
                    shd.set(qn('w:color'), 'auto')
                    shd.set(qn('w:fill'),  'FFFFFF')
                # Жирный + чёрный в шапке
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.font.color.rgb = BLACK
                        if is_header:
                            run.bold = True

# ─── 6. Формулы — центр + номер справа через таб-стоп ────────────────────────

def fix_formulas(doc):
    """
    Параграфы с формулами форматирует:
    - центрирование параграфа
    - пустая строка сверху/снизу
    Номер (N.M) при необходимости помечается.
    """
    for p in doc.paragraphs:
        txt = para_text(p)
        is_formula = bool(FORMULA_RE.search(txt)) and has_omml(p)
        is_display_eq = has_omml(p) and not is_formula  # дисплейное уравнение без явного номера

        if is_formula or is_display_eq:
            pf = p.paragraph_format
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf.first_line_indent = Cm(0)
            pf.left_indent = Cm(0)
            pf.space_before = Pt(6)
            pf.space_after = Pt(6)

# ─── 7. Блоки «где» ───────────────────────────────────────────────────────────

def fix_gde(doc):
    for p in doc.paragraphs:
        txt = para_text(p)
        if txt.startswith('где ') or txt.startswith('где\xa0') or txt == 'где':
            pf = p.paragraph_format
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.first_line_indent = Cm(0)
            pf.left_indent = Cm(0)

# ─── 8. Заголовки ─────────────────────────────────────────────────────────────

def fix_headings(doc):
    for p in doc.paragraphs:
        sn = p.style.name if p.style else ''
        if not sn.startswith('Heading'):
            continue

        structural = is_structural(p)
        pf = p.paragraph_format

        if structural:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf.first_line_indent = Cm(0)
            pf.left_indent = Cm(0)
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.first_line_indent = Cm(0)
            pf.left_indent = Cm(0)

        for run in p.runs:
            run.bold = True
            run.font.size = Pt(14)
            run.font.name = 'Times New Roman'
            run.font.italic = False
            run.font.color.rgb = BLACK

# ─── 9. Титульный лист из черновика ───────────────────────────────────────────

def _para_index_of(doc, search_text):
    """Возвращает индекс первого параграфа, содержащего search_text."""
    for i, p in enumerate(doc.paragraphs):
        if search_text in p.text:
            return i
    return None

def prepend_title_page(target_doc, draft_path):
    """
    Копирует титульный лист из черновика в начало target_doc.
    Вставляет разрыв страницы после титульника.
    """
    try:
        draft = Document(draft_path)
    except Exception as e:
        print(f'  [предупреждение] не удалось открыть черновик: {e}')
        return

    # Найдём конец титульного листа: первый параграф «РЕФЕРАТ»
    title_end_idx = _para_index_of(draft, 'РЕФЕРАТ')
    if title_end_idx is None:
        print('  [предупреждение] РЕФЕРАТ не найден в черновике — титульник не вставлен')
        return

    # Собираем XML-элементы титульного листа из draft
    # (все дочерние элементы body ДО параграфа РЕФЕРАТ)
    draft_body = draft.element.body
    elements_to_copy = []
    para_seen = 0
    for child in draft_body:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'sectPr':
            continue
        elements_to_copy.append(deepcopy(child))
        if tag == 'p':
            para_seen += 1
            if para_seen >= title_end_idx:
                break  # копируем до РЕФЕРАТ (не включая)

    # Добавляем разрыв страницы после титульника
    br_xml = '<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:r><w:br w:type="page"/></w:r></w:p>'
    elements_to_copy.append(etree.fromstring(br_xml))

    # Вставляем в начало target_doc перед первым элементом body
    target_body = target_doc.element.body
    first_child = target_body[0] if len(target_body) else None

    if first_child is None:
        for el in elements_to_copy:
            target_body.append(el)
    else:
        insert_pos = 0
        for i, el in enumerate(elements_to_copy):
            target_body.insert(insert_pos + i, el)

    # Копируем стили из draft в target (шрифты, numbering)
    # Переносим шрифтовую таблицу если нужно
    try:
        _merge_fonts(draft, target_doc)
    except Exception:
        pass

    print(f'  Титульный лист вставлен ({len(elements_to_copy)-1} элементов из черновика)')


def _merge_fonts(src_doc, dst_doc):
    """Добавляет записи о шрифтах из src в dst если их там нет."""
    src_fonts = src_doc.element.body.getparent().find(
        '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fonts'
    )
    dst_fonts = dst_doc.element.body.getparent().find(
        '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fonts'
    )
    if src_fonts is None or dst_fonts is None:
        return
    W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    existing = {
        el.get(f'{{{W}}}name')
        for el in dst_fonts.findall(f'{{{W}}}font')
    }
    for font_el in src_fonts.findall(f'{{{W}}}font'):
        name = font_el.get(f'{{{W}}}name')
        if name not in existing:
            dst_fonts.append(deepcopy(font_el))

# ─── Основная функция ─────────────────────────────────────────────────────────

def postprocess(input_path, output_path, draft_path=None):
    doc = Document(input_path)

    print('  → Масштабирую изображения...')
    fix_images(doc)

    print('  → Чёрный цвет текста...')
    fix_all_colors(doc)

    print('  → Заголовки...')
    fix_headings(doc)

    print('  → Разрывы страниц перед главами...')
    add_page_breaks(doc)

    print('  → Списки (тире)...')
    fix_lists(doc)

    print('  → Формулы...')
    fix_formulas(doc)

    print('  → Блоки «где»...')
    fix_gde(doc)

    print('  → Таблицы (рамки, шапка)...')
    fix_tables(doc)

    if draft_path:
        print('  → Вставляю титульный лист из черновика...')
        prepend_title_page(doc, draft_path)

    doc.save(output_path)
    print(f'Постобработка завершена: {output_path}')


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        print('Использование: python3 postprocess_docx.py <input.docx> <output.docx> [draft.docx]')
        sys.exit(1)
    draft = sys.argv[3] if len(sys.argv) == 4 else None
    postprocess(sys.argv[1], sys.argv[2], draft)
