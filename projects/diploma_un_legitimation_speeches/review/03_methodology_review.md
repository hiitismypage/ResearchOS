# Ревью раздела: 3. Methodology
Дата: 2026-05-13

---

## Общая оценка

Глава методологически корректна и хорошо структурирована: логика от дизайна к данным к выборке к кодированию к претензиям выстроена без провалов. Главная слабость — Sub-question 2 (эволюция стратегий во времени) нигде не заземлена в аналитической процедуре: читатель видит temporal distribution в выборке, но не понимает, как именно методология отвечает на вопрос «как стратегии менялись». Второй момент: глава заканчивается ограничениями, а не синтезом — финал обрывается.

---

## Сильные стороны

- **3.1 — связь с gap**: новый абзац про «horizontal vs. vertical borings» прямо обосновывает выбор метода через пробел в литературе — это сильный ход, нетипичный для бакалаврских работ.
- **3.3 — sampling logic**: двухшаговая идентификация кейсов (контекстуальная документация → проверка в корпусе) конкретна и воспроизводима. Явное разграничение «контекстуальный индикатор ≠ доказательство нарушения» — методологически честно и важно.
- **3.4 — decision rules**: три правила для пограничных случаев (co-occurrence, denial/sovereignty, historical framing) — редкость для такого уровня работы. Кодбук с такими правилами реально работает.
- **3.5 — scope of claims**: раздел явно разграничивает, что изучается и что нет. Особенно важна формулировка про adjudicative claims.
- Python-скрипты вписаны органично — без технического перегруза.

---

## Проблемы и рекомендации

### Критические (нужно исправить)

**1. Sub-question 2 не отражён в аналитической процедуре**

Второй подвопрос («как стратегии эволюционировали?») упоминается только в sampling (temporal distribution) и вскользь в 3.1. Но в 3.4 (coding procedure) и 3.5 (scope of claims) ничего не сказано о том, как именно эволюция будет зафиксирована методологически. Является ли период коды отдельной переменной? Как сравниваются периоды?

> Предложение: добавить в 3.4 или 3.3 одно предложение вида: "In addition to the two primary coding dimensions, each coded segment is tagged with the historical sub-period of delivery (Cold War; post-1990 normative expansion; post-9/11 security turn; post-2014 fragmentation), enabling the temporal comparison that addresses Sub-question 2."

---

**2. Финал главы обрывается на ограничениях**

3.5 заканчивается второй оговоркой про перевод. Это уместно как последнее содержательное замечание, но не как финал раздела. Читатель, завершив методологическую главу, должен понимать, что дальше идёт эмпирика — и почему предложенная процедура это обеспечивает.

> Предложение: добавить один закрывающий абзац или предложение, например: "Subject to these constraints, the methodology is designed to produce a systematic, transparent, and theoretically grounded account of legitimation strategies in UNGA General Debate addresses — a foundation for the empirical analysis that follows in Chapter 4."

---

### Значимые (стоит исправить)

**3. "The study" как субъект — трижды в одном абзаце (3.5)**

STYLE.md запрещает "this study" как оборот. "The study makes claims... It claims... It claims... it makes no adjudicative claims" — четыре раза субъект "the study / it" в одном абзаце. Конструкция механическая.

> Оригинал: "The study makes claims that are appropriately bounded... It claims to identify... It claims to trace... it makes no adjudicative claims"
> Предложение: переформулировать часть через пассив или другой субъект: "Claims are appropriately bounded... The analysis identifies... No adjudicative judgments are made..."

---

**4. "does not replace" — повтор конструкции в 3.1 и 3.2**

Один и тот же риторический ход использован дважды подряд:
- 3.1: "does not replace case-study depth"
- 3.2: "do not replace the qualitative reading and coding procedure"

> Предложение: в 3.2 заменить: "These scripts are preparatory rather than analytical: every speech in the final sample is read and coded manually."

---

**5. Python-скрипты: keyword filters не конкретизированы**

"applying keyword-based filters to flag addresses likely to contain legitimation-relevant content" — неясно, что именно ищут скрипты. Это важно для воспроизводимости.

> Предложение: "applying keyword searches associated with the five violation type categories (e.g., terms related to self-defense, sovereignty, use of force, humanitarian intervention) to flag addresses likely to contain legitimation-relevant content"

---

### Мелкие (по желанию)

**6. "in principle reproducible" — слабый хедж**

> Оригинал: "making the analytical procedure transparent and in principle reproducible"
> Предложение: "making the analytical procedure transparent and reproducible"
Если процедура задокументирована — она воспроизводима, без «in principle».

**7. Абзац с decision rules (3.4) — самый длинный в главе**

Три правила описаны в одном абзаце без разбивки. Для документа, где воспроизводимость важна, лучше три отдельных коротких абзаца или маркированный список. Сейчас трудно быстро найти нужное правило.

**8. "approximately" × 4 в 3.3 и 3.5**

"approximately 50 to 80 speeches", "approximately 10–15 speeches", "approximately 20% of speeches", "approximately 10,000 speeches" — все в одной главе. Вариация: "roughly", "around", или просто числа без квалификатора там, где он не нужен (для корпуса в 10 000 он необязателен).

---

## Чеклист

### Логика и аргументация
- ✅ Центральная логика раздела ясна
- ✅ Каждый подраздел — одна тема
- ⚠️ Sub-Q2 не заземлён в процедуре
- ✅ Переходы между подразделами работают (заголовки + логический порядок)
- ❌ Финал обрывается — нет синтезирующего закрытия

### Связь с исследовательским вопросом
- ✅ Sub-Q1 (какие стратегии?) — полностью покрыт
- ❌ Sub-Q2 (эволюция?) — покрыт частично, не в аналитической процедуре
- ✅ Scope of claims явно ограничивает претензии
- ✅ Нет лишнего материала

### Работа с источниками
- ✅ Флаги [SOURCE NEEDED] расставлены корректно
- ✅ Единственная прямая цитата (Baturo et al., p. 3) введена с атрибуцией и страницей
- ⚠️ Decision rules в 3.4 не имеют ни источника, ни явного обоснования как стандартной практики

### Соответствие STYLE.md
- ⚠️ "The study... It claims... It claims..." — механический повтор, близко к запрещённому "this study"
- ✅ Пассивный залог в методологических контекстах уместен
- ✅ Запрещённых слов (robust, nuanced, leverage и др.) не обнаружено
- ✅ Смешанная длина предложений

### Техника письма
- ⚠️ "does not replace" — повтор конструкции
- ⚠️ "approximately" × 4
- ✅ Bullet-point список в 3.3 оправдан (критерии — не проза)
- ⚠️ Абзац с decision rules перегружен — лучше разбить

---

## Следующий шаг

1. Внести критические правки (#1 и #2) — они влияют на логическую полноту главы
2. Внести значимые правки (#3–#5) — улучшают читаемость и воспроизводимость
3. После правок: `/sync checkpoint` для сохранения
4. Следующий шаг по работе: `/write-section 4. Empirical Analysis` или `/find-sources` для закрытия [SOURCE NEEDED] флагов (Hsieh & Shannon, Krippendorff, Cohen's kappa)
