# Ревью раздела: Chapter 5. Discussion — проверка на непротиворечие
Дата: 2026-05-14

Фокус: согласованность Ch. 5 с Ch. 4, Ch. 1, CONTEXT.md и outline.
Все статистические значения проверены против Ch. 4.

---

## Общая оценка

Статистика в Ch. 5 воспроизведена точно: все числа (F, p, χ², Cramér's V, проценты) совпадают с Ch. 4. Гипотезы H1–H4 сформулированы в Ch. 5 последовательно с CONTEXT.md и outline. Однако выявлены три проблемы: одна критическая (Iraq 2003 почти дословно повторён из 4.6 в 5.2), одна значимая (терминологическое расхождение Bjola между главами), и одна фоновая — внутреннее противоречие в Ch. 4 (счёт классифицированных сегментов по Western bloc), которая проявляется в Ch. 5 опосредованно.

---

## Статистика: статус ✅

| Утверждение Ch. 5 | Значение | Источник в Ch. 4 | Совпадение |
|---|---|---|---|
| ANOVA pre-2001 | F = 0.39, p = .678 | Ch. 4, 4.5 | ✅ |
| ANOVA post-2001 | F = 1.29, p = .288 | Ch. 4, 4.5 | ✅ |
| χ² по периодам | 21.06, p = .0018, V = .33 | Ch. 4, 4.5 | ✅ |
| Cold War normative | 63.6% | Ch. 4, 4.5 | ✅ |
| Post-9/11 communicative | 71.0% | Ch. 4, 4.5 | ✅ |
| Post-2014 normative | 25.9% / рост с 16.1% | Ch. 4, 4.5 | ✅ |
| Fisher's exact Western/EEG | p = .023 | Ch. 4, 4.6 | ✅ |
| Fisher's exact Western/NAM | p = .003 | Ch. 4, 4.6 | ✅ |
| CA inertia Dim 1 | 82.5% | Ch. 4, 4.6 | ✅ |
| Communicative action | 51.5% | Ch. 4, 4.3 | ✅ |
| Normative action | 36.1% | Ch. 4, 4.3 | ✅ |
| Article 51, n=1 | n = 1 | Ch. 4, 4.3 + 4.4.1 | ✅ |
| 33 case-years, 102 сегмента | — | Ch. 4, 4.1 | ✅ |

---

## Проблемы и рекомендации

### Критические (нужно исправить)

**1. Iraq 2003 — почти дословное повторение между Ch. 4 (4.6) и Ch. 5 (5.2)**

Один и тот же аргумент про Iraq 2003 сформулирован практически одинаково в обоих местах:

> Ch. 4, 4.6: *"Iraq 2003 is the most transparent case: with the UNSC divided and no explicit authorization for the use of force, the US delegation could not ground its legitimation in Chapter VII authorization and instead constructed an extended necessity argument based on Iraqi WMD non-compliance and the residual authority of Resolution 1441. The normative vocabulary was available; its use would have been politically and legally incoherent in that context."*

> Ch. 5, 5.2: *"Iraq 2003 is the most transparent case: with the UNSC divided and no explicit Chapter VII authorization, the American delegation was pushed toward a necessity argument grounded in Iraqi WMD non-compliance rather than toward the normative-legal idiom that the Charter architecture would otherwise provide."*

Это не просто тематическое повторение — это структурно и лексически идентичные абзацы. Для Антиплагиата это самоцитирование, которое снижает оригинальность; для читателя — ощущение, что Ch. 5 не добавляет ничего нового к Ch. 4.

**Рекомендации (на выбор):**
- В Ch. 5 заменить пересказ кейса прямой отсылкой: *«As the Iraq 2003 case illustrates (Section 4.6), states operating outside formal UNSC authorization are structurally pushed toward necessity argumentation rather than Charter invocation.»*
- Либо развить аргумент в Ch. 5 за пределы того, что уже сказано в 4.6 — добавить теоретическое измерение (например, через Koskenniemi о quasi-legal necessity logic), которого в 4.6 нет.

---

### Значимые (стоит исправить)

**2. «Deliberative legitimation» vs. «deliberative legitimacy» — терминологическое расхождение между главами**

Bjola (2005) вводит понятие **deliberative legitimacy** — именно так оно атрибутировано в Ch. 1:
> *«His concept of deliberative legitimacy, defined as 'the non-coerced commitment of an actor to obey a norm…'»*

В Ch. 4 (4.3) и Ch. 5 (5.2) используется другой вариант — **deliberative legitimation**:
> Ch. 4: *«Bjola's (2005) observation that states frequently engage in 'deliberative legitimation'…»*
> Ch. 5: *«This is consistent with Bjola's (2005) concept of deliberative legitimation»*

Это разные слова с разными значениями: *legitimacy* — нормативный статус; *legitimation* — процесс его конструирования. Bjola's термин — *legitimacy*. Использование *legitimation* как его концепта создаёт неточность атрибуции.

**Предложение:** в Ch. 4 и Ch. 5 заменить на *deliberative legitimacy* в атрибутивном контексте. Говорить о процессе легитимации — допустимо, но отдельно от ссылки на Bjola's concept.

> Ch. 5 вариант: *«This is consistent with the logic of deliberative legitimacy that Bjola (2005) identifies: the construction of normative consensus through public argumentation operates as a constraint…»*

---

**3. Фоновое расхождение в Ch. 4: Western bloc classified segments — 23 или 24?**

Это внутренняя проблема Ch. 4, но она подпирает H4 в Ch. 5.

- Ch. 4, 4.2: *«Within the Western bloc, the rate is notably higher at 14.4 percent (approximately four segments from the nine Western cases)»* → 14.4% × 27 = 3.9 ≈ 4 unclassified → **23 classified**
- Ch. 4, 4.4.1: *«19 of 24 classified Western segments»* → **24 classified**
- Ch. 4, 4.4.2: *«only 3 of 24 Western classified segments»* → **24 classified**
- Ch. 4, 4.4.3: *«2 of 24 (8.3 percent) in the Western subcorpus»* → **24 classified**

Расхождение: 4.2 говорит о ≈4 неклассифицированных (→ 23 classified), все 4.4.x работают с 24 classified (→ 3 неклассифицированных, 11.1%, а не 14.4%).

Фактическое число классифицированных сегментов по блоку — ключевой параметр для Fisher's exact тестов, на которых строится H4. Если реальное число 24 (а не 23), то "14.4%" в 4.2 — ошибка округления; если 23 — все 4.4.x нужно пересмотреть.

**Что нужно:** сверить с данными пайплайна и исправить один из двух вариантов. Если фактических unclassified = 3, то 4.2 нужно изменить: *«approximately three segments»* и *«11.1 percent»*. Если 4, то все 4.4.x меняются с «24» на «23».

---

### Мелкие (по желанию)

**4. «Partial reversion» (Ch. 5) vs. «partially stabilizes» (Ch. 4) — незначительное расхождение формулировок**

> Ch. 4 (4.5): *«the pattern partially stabilizes»*
> Ch. 5 (5.1): *«post-2014 partial reversion toward normative framing»*

«Reversion» точнее — нормативный тип действительно вырос с 16.1% до 25.9%, то есть частично вернулся к прежним значениям. «Stabilizes» технически неточно. Ch. 5 правее, Ch. 4 стоит скорректировать.

---

## Чеклист согласованности

| Критерий | Статус |
|----------|--------|
| Все статистические значения совпадают с Ch. 4 | ✅ |
| H1–H4 формулировки согласованы с CONTEXT.md и outline | ✅ |
| n=1 (Article 51) согласован между главами | ✅ |
| Iraq 2003 не повторяется дословно | ✗ (5.2 = 4.6 почти verbatim) |
| Bjola's термин используется последовательно | ✗ (legitimacy в Ch. 1, legitimation в Ch. 4–5) |
| Western classified N согласован внутри Ch. 4 | ⚠ (23 vs. 24) |
| «Partial reversion» vs. «stabilizes» | ⚠ (Ch. 4 менее точен) |

---

## Следующий шаг

1. **Сначала:** исправить Iraq 2003 в Ch. 5 (5.2) — заменить пересказ на cross-reference или развить теоретически
2. **Затем:** унифицировать «deliberative legitimacy» во всех главах, где атрибутируется Bjola
3. **Параллельно:** сверить Western bloc classified count с данными пайплайна — 3 или 4 unclassified
4. **После правок:** писать Conclusion
