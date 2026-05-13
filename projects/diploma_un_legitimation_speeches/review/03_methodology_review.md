# Ревью раздела: 3. Methodology
Дата: 2026-05-13 (обновлено после правок outline и 3.3)

---

## Общая оценка

Глава методологически корректна и хорошо структурирована: логика от дизайна к данным к выборке к кодированию к ограничениям выстроена без провалов. Два основных вопроса: (1) после сегодняшней правки 3.3 возникло логическое противоречие между заголовком («Purposive Sampling») и формулировкой «all speeches» — это нужно разрешить принципиально; (2) Sub-Q2 (эволюция стратегий) нигде не заземлён в аналитической процедуре.

---

## Сильные стороны

- **3.1 — связь с gap**: обоснование выбора метода через пробел в литературе («horizontal account») — сильный и нетипичный для бакалаврской работы ход.
- **3.3 — двухшаговая идентификация**: явное разграничение «контекстуальный индикатор ≠ доказательство нарушения» — методологически честно и важно для комиссии.
- **3.4 — decision rules**: три правила для пограничных случаев (co-occurrence, denial/sovereignty, historical framing) — редкость для такого уровня работы.
- **3.5 — scope of claims**: явное разграничение adjudicative vs. analytical claims — принципиально важно для работы по теме нарушений МП.
- Python-скрипты вписаны органично, без технического перегруза.

---

## Проблемы и рекомендации

### Критические (нужно исправить)

**1. Внутреннее противоречие в 3.3: «purposive» vs. «all speeches»**

После сегодняшней правки section 3.3 говорит два несовместимых вещи одновременно:
- Заголовок и первый абзац: *"Purposive and Theory-Driven"* — выборка целенаправленная, не репрезентативная
- Новая формулировка: *"The sample comprises all speeches in which legitimation of alleged violations is identifiable"*

«Purposive» — это отбор подмножества по теоретическому критерию (вы ищете случаи, где есть стимул оправдываться). «All» — это исчерпывающая идентификация всех речей, отвечающих критерию. Это разные вещи.

Нужно решить принципиально: выборка исчерпывающая или ограниченная? Если исчерпывающая — нужно переформулировать заголовок и первый абзац. Если ограниченная (purposive) — вернуть примерный N и объяснить логику ограничения.

> Вариант A (исчерпывающая): изменить заголовок на *"3.3. Sampling Strategy: Exhaustive Identification Within Criterion"*, первый абзац — переписать без слова "purposive"
> Вариант B (ограниченная): вернуть примерный N как TBD: *"The initial target is to identify all state-years meeting the selection criterion; the final N will be determined after systematic identification [VERIFY]."*

---

**2. Sub-Q2 не отражён в аналитической процедуре**

Второй подвопрос («как стратегии эволюционировали?») упоминается в 3.3 (temporal distribution) и вскользь в 3.1, но в 3.4 (coding procedure) нет ни слова о том, как временна́я эволюция будет зафиксирована. Является ли период коды отдельной переменной?

> Предложение: добавить в 3.4 одно предложение:
> *"In addition to the two primary coding dimensions, each coded segment is tagged with the historical sub-period of delivery (Cold War, 1946–1989; post-Cold War normative expansion, 1990–2001; post-9/11 security turn, 2001–2013; sovereignty-revisionist fragmentation, 2014–2023), enabling the temporal comparison that addresses Sub-question 2."*

---

**3. Глава заканчивается ограничениями, а не синтезом**

3.5 закрывается второй оговоркой про перевод — методологически уместно, но слабый финал для раздела, который должен передать читателя в эмпирику.

> Предложение: добавить один закрывающий абзац:
> *"Subject to these constraints, the methodology is designed to produce a systematic, transparent, and theoretically grounded account of legitimation strategies in UNGA General Debate addresses — a foundation for the empirical analysis that follows in Chapter 4."*

---

### Значимые (стоит исправить)

**4. «This study» в 3.2 — запрещённый оборот**

> Оригинал: *"For this study, that characteristic is not a distortion to be corrected but the primary object of analysis"*
> Предложение: *"In this analysis, that characteristic is not a distortion to be corrected but the primary object of study"* или *"Rather than treating strategic self-presentation as a distortion, the present analysis takes it as its primary object."*

---

**5. «The study... It claims... It claims...» — механический повтор в 3.5**

Четыре раза подряд субъект «the study / it» в одном абзаце. Близко к запрещённому «this study», и монотонно.

> Оригинал: *"The study makes claims... It claims to identify... It claims to trace... it makes no adjudicative claims"*
> Предложение: переформулировать часть через пассив или другой субъект:
> *"Claims are appropriately bounded by the study's design... The analysis identifies and describes... No adjudicative judgments are made..."*

---

**6. Перекрытие ограничения по переводу между 3.2 и 3.5**

3.2 уже обсуждает translation limitation (UN translations, strategic nuances lost). 3.5 повторяет тот же тезис. Небольшое дублирование.

> Предложение: в 3.5 сократить до одного предложения-ссылки: *"The translation constraint, addressed in Section 3.2, is particularly salient for qualitative interpretation of speeches from non-Anglophone states."*

---

**7. Python keyword filters не конкретизированы**

*"applying keyword-based filters to flag addresses likely to contain legitimation-relevant content"* — неясно, что именно ищут скрипты. Для воспроизводимости нужна хотя бы одна строка.

> Предложение: *"applying keyword searches associated with the five violation type categories (e.g., terms related to self-defense, use of force, sovereignty, humanitarian intervention) to flag addresses likely to contain legitimation-relevant content"*

---

### Мелкие (по желанию)

**8. «does not replace» — повтор конструкции в 3.1 и 3.2**

- 3.1: *"does not replace interpretive depth"*
- 3.2: *"do not replace the qualitative reading"*

> Предложение для 3.2: *"These scripts are preparatory rather than analytical: every speech in the final sample is read and coded manually."*

---

**9. «approximately» × 3 в одной главе**

После исправления 3.3: *"approximately 10–15 speeches"* (pilot), *"approximately 20%"* (reliability), *"approximately 10,000"* (corpus). Вариация: "roughly", "around", или числа без квалификатора где он не нужен.

---

**10. Self-review секция в конце главы**

Строка в self-review: *"Ожидаемый N ~50-80 — нужно финализировать"* — устарела после сегодняшних правок. Также сама секция self-review не является частью академического текста — удалить перед сдачей.

---

**11. Абзац с decision rules (3.4) — перегружен**

Три правила в одном абзаце. Для документа, где воспроизводимость важна, лучше разбить на три коротких абзаца или маркированный список.

---

## Чеклист

### Логика и аргументация
- ✅ Центральная логика раздела ясна (дизайн → данные → выборка → кодирование → ограничения)
- ✅ Каждый подраздел — одна тема
- ❌ Sub-Q2 не заземлён в аналитической процедуре
- ✅ Переходы между подразделами работают
- ❌ Финал обрывается — нет синтезирующего закрытия

### Связь с исследовательским вопросом
- ✅ Sub-Q1 (какие стратегии?) — полностью покрыт
- ❌ Sub-Q2 (эволюция?) — покрыт частично, не в 3.4
- ✅ Scope of claims явно ограничивает претензии
- ✅ Лишнего материала нет

### Работа с источниками
- ✅ Флаги [SOURCE NEEDED] и [VERIFY] расставлены корректно
- ✅ Единственная прямая цитата (Baturo et al., p. 3) введена с атрибуцией
- ⚠️ Decision rules в 3.4 не имеют источника или обоснования как стандартной практики CA

### Соответствие STYLE.md
- ❌ «This study» в 3.2 — запрещённый оборот
- ⚠️ «The study / It» × 4 подряд в 3.5 — механический повтор
- ✅ Пассивный залог в методологических контекстах уместен
- ✅ Запрещённых слов (robust, nuanced, leverage и др.) не обнаружено
- ✅ Смешанная длина предложений

### Техника письма
- ⚠️ «does not replace» — повтор конструкции в 3.1 и 3.2
- ⚠️ «approximately» × 3 в одной главе
- ✅ Bullet-point список в 3.3 оправдан (критерии разнообразия)
- ⚠️ Абзац с decision rules перегружен — стоит разбить

---

## Следующий шаг

1. **Принципиальное решение по 3.3** (#1): purposive или exhaustive? — от этого зависит формулировка всей секции
2. **Критические правки** #2 и #3 — добавить temporal tagging в 3.4, закрыть главу синтезом
3. **Значимые правки** #4–#7 — стиль и воспроизводимость
4. После правок: `/sync checkpoint`
5. Следующий шаг: `/find-sources` для закрытия [SOURCE NEEDED] (Hsieh & Shannon, Krippendorff, Cohen's kappa)
