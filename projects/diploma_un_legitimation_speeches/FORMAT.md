# Настройки форматирования
# Источник требований: методичка_ВКР.pdf (п. 4.1–4.7)

## Язык работы
language: en

## Шрифт основного текста
font_family: Times New Roman
font_size: 12

## Заголовки
# Все заголовки — Times New Roman 12, bold. Слово "Chapter" не используется.
# Нумерация: 1. Introduction / 1.1 / 1.2 и т.д.
heading1_font: Times New Roman
heading1_size: 12
heading1_bold: true
heading1_uppercase: false
heading1_alignment: left

heading2_font: Times New Roman
heading2_size: 12
heading2_bold: true
heading2_uppercase: false
heading2_alignment: left

heading3_font: Times New Roman
heading3_size: 12
heading3_bold: false
heading3_italic: true
heading3_alignment: left

## Абзацы
line_spacing: 1.5
first_line_indent: 1.25cm
paragraph_spacing_before: 0pt
paragraph_spacing_after: 0pt
body_alignment: justify

## Поля страницы (мм) — по методичке_ВКР.pdf п. 4.1
margin_top: 20
margin_bottom: 20
margin_left: 25
margin_right: 10

## Страница
page_size: A4
page_numbers: top_center
page_numbers_start: 2
# Титульный лист — без номера; нумерация начинается со 2-й страницы

## Сноски (постраничные)
footnote_font_size: 10
footnote_alignment: justify
# Сноски размещаются внизу страницы, выравниваются по ширине

## Цитирование
citation_style: APA
citation_format: in-text
# Пример: (Bjola, 2005, p. 270)
# Постраничные сноски — для пояснительных комментариев, не для цитат

## Структурные требования (из методичка_ВКР.pdf п. 4.1–4.5)
custom_notes: |
  - Каждая глава, введение, заключение, список литературы, приложения
    начинаются с новой страницы
  - Разделы нумеруются: 1.1, 1.2, 1.3 (глава 1); 2.1, 2.2 (глава 2) и т.д.
  - Точка в конце заголовка не ставится
  - Все таблицы и схемы нумеруются и подписываются
  - Приложения: слово "Appendix" + номер — в правом верхнем углу над заголовком
  - Объём: ≥90 000 знаков с пробелами, без учёта приложений
  - После титульного листа: аннотации на русском и английском языках
    (125–175 слов каждая) для исследовательской ВКР
  - AI disclaimer обязателен (образец из Research_Proposal.pdf):
    "I used AI-based tools to find relevant academic articles and books,
    to improve punctuation and spelling, and to refine the formatting
    of the reference list in accordance with APA style."
