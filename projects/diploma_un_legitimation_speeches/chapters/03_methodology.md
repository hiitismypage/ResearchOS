# 3. Methodology

## 3.1. Research Design: A Two-Level Analytical Strategy

The analytical approach adopted in this study combines two complementary levels of analysis, each designed to answer a distinct set of research questions and together enabling both breadth and interpretive depth that neither level could achieve alone.

The **first level** is a corpus-level keyword signal analysis, applied to a broad sample of speeches drawn from the full Harvard UN General Debate Corpus (UNGDC). This level is designed to address the macro-questions motivating the study: When does the frequency of particular legitimation-related linguistic signals increase or decrease across time? Are these changes associated with geopolitical bloc membership, historical period, or the profile of actors involved in the discourse? The corpus-level analysis does not code individual arguments; it tracks the normalized keyword density of seven thematic signals — counter-terrorism and securitization framing, self-defense appeals, sovereignty invocations, humanitarian discourse, procedural-legal references, historical framing, and whataboutism — across over 11,000 speeches, disaggregated by Cold War bloc membership and nine sub-periods from 1946 to 2023. This level is the primary evidentiary basis for testing H1 (convergence) and provides contextual grounding for the temporal patterns examined in H3.

The **second level** is a directed qualitative content analysis of 33 case-years identified through the criterion-based sampling procedure described in Section 3.3. This level engages the 102 coded argumentative segments from those cases and classifies each according to Habermas's (1984) four-type taxonomy of social action. This level is the primary evidentiary basis for testing H2, H3, and H4, and generates the comparative case analysis in Chapter 4.

The rationale for this two-level design is directly tied to the gap identified in Chapter 1. Existing research consists predominantly of case studies that yield analytic depth but cannot speak to patterns across actors, periods, and violation types (Bjola, 2005; Rapp, 2022). What the literature lacks is a horizontal account: which strategies are deployed, with what frequency, in what combinations, and how the distribution has shifted over time. The corpus-level analysis provides the horizontal account at scale; the case-level analysis provides the interpretive depth necessary to understand the rhetorical logic of individual legitimation moves. The two levels are designed to be mutually illuminating rather than redundant.

Within the second level, the analytical procedure unfolds in two stages. The first stage is *descriptive mapping*: classifying all segments in the sample against the Habermas typology, calculating frequencies and co-occurrence patterns, and generating the quantitative findings reported in Sections 4.3–4.6. The second stage is *comparative qualitative interpretation*: examining in closer detail how specific legitimation strategies are realized in representative cases — which rhetorical resources are deployed, which legal and normative frameworks are invoked, and how the framing responds to the specific allegation addressed. As Hsieh and Shannon (2005) argue in their account of directed content analysis, this combination of deductive category-driven coding with qualitative interpretation allows a study to move between the pattern level and the meaning level in a principled way. [SOURCE NEEDED: Hsieh & Shannon, 2005 — page reference for directed vs. conventional content analysis]

The unit of analysis is the argumentative segment — a sentence or sequence of sentences constituting a rhetorically complete justificatory move. [SOURCE NEEDED: Krippendorff — unit of analysis in content analysis] A single speech may contain multiple coded segments, each classified independently, which reflects the empirical reality that states defending contested conduct typically assemble composite justifications rather than relying on a single argument.

---

## 3.2. Data: The Harvard UN General Debate Corpus

The primary data source is the UN General Debate Corpus (UNGDC). The original corpus was compiled from UN official records and published on Harvard Dataverse by Baturo, Dasandi, and Mikhaylov (2017), who made available the full texts of speeches delivered during the General Debate of the United Nations General Assembly for sessions spanning 1970 to 2014, as a structured text-as-data resource. The extended version used in this study was developed by Jankin, Baturo, and Dasandi (2025), who expanded coverage backward to the inaugural General Assembly session in 1946 and forward through 2023. As employed in the present study, the corpus encompasses 11,127 speeches from 198 countries across nearly eight decades of General Debate sessions.

The corpus offers several properties that make it suitable for both levels of the analysis. Speeches are available as plain-text files, machine-readable and standardized in format, with consistent metadata on the year of delivery, country, and session number. The General Debate format is highly uniform across time: each member state receives a designated speaking slot, delivers an address on topics of its choosing before a plenary audience that includes the full UN membership. As Baturo et al. (2017, p. 3) observe, this genre stability — combined with the fact that "member states present themselves exclusively in the guise in which they wish to be known" — makes the corpus particularly well-suited to the systematic analysis of strategic legitimation discourse. Rather than treating strategic self-presentation as a distortion to be corrected, this study takes it as its primary analytical object.

The corpus-level analysis draws on the full UNGDC for signal frequency computation. The case-level analysis draws on 33 state-years identified through the criterion-based procedure described below. Python scripts serve three preparatory functions: extracting speeches for identified state-years; applying the keyword-based role classifier to all segments; and generating the corpus-level keyword signal scores used for ANOVA and temporal trend analysis.

Two limitations of the corpus require acknowledgment. First, speeches originally delivered in languages other than English are represented through official UN translations. The translation process introduces the possibility that strategic nuances in the original are smoothed out or lost, which the qualitative interpretive stage notes where salient. Second, speeches prior to approximately 1992 were stored as scanned copies of printed records and required OCR processing, which may affect text quality for some early sessions [VERIFY: confirm OCR coverage for pre-1992 speeches per Baturo et al. documentation].

---

## 3.3. Case Identification and Geopolitical Classification

### Criterion-Based Case Selection

The analytical sample for the case-level analysis includes all speeches in the UNGDC that satisfy the study's inclusion criterion: the delivering state faced documented external criticism or allegation of legally or normatively contested conduct at the time of the relevant UNGA session, and the speech itself contains material — direct or indirect — addressing that contested conduct. No predetermined N constrains the sample; the inclusion criterion is applied systematically to the full corpus. The present study identifies 33 state-years meeting both conditions, spanning 18 states across all four analytical periods (Cold War: 8 cases; post-Cold War normative expansion: 9; post-9/11 security turn: 8; post-2014 normative fragmentation: 8).

Case identification proceeds in two steps. First, episodes of legally or normatively contested conduct are identified using contextual documentation: UN reporting (General Assembly and Security Council records, special rapporteur reports), NGO documentation (Amnesty International, Human Rights Watch annual reports), and academic secondary literature on specific conflicts. These sources establish that a state faced external criticism at the time of its UNGA address; they do not establish that a legal violation occurred, and no claim about the legality of the conduct is made. Second, identified state-years are checked against the UNGDC to confirm that the speech for that country and session is available and contains material relevant to the contested episode. Speeches that make no reference — direct or indirect — to the contested conduct are excluded.

### Cold War Bloc Classification

The geopolitical comparative dimension of the analysis is structured around three Cold War institutional blocs: the **Western bloc** (NATO member states and their formal allies), the **Soviet/Eastern bloc** (Warsaw Pact member states and Soviet-aligned governments), and the **Non-Aligned Movement** (NAM member states and formally uncommitted governments). The choice of this classification over alternative schemes — UN regional groups, regime type classifications, or contemporary alliance configurations — requires explicit justification.

The Cold War bloc classification is most appropriate for the temporal scope of this study for three interconnected reasons. First, the study covers 77 years of UN General Assembly discourse (1946–2023), the majority of which — roughly 44 years (1946–1989) — falls within the genuinely bipolar international system structured by the Cold War. During this period, bloc membership was not merely a diplomatic affiliation but a marker of shared normative contexts, overlapping legal frameworks, and distinctive vocabularies of legitimate international conduct. Western bloc states operated within a liberal internationalist normative framework emphasizing rule-based order and human rights conditionality; Soviet/Eastern bloc states prioritized formal sovereignty and non-interference as counterweights to Western interventionism; Non-Aligned states, shaped by the 1955 Bandung Conference and the Group of 77, constructed a third normative repertoire emphasizing anti-colonialism, legal equality, and sovereign self-determination [SOURCE NEEDED: academic reference on NAM normative repertoire, e.g. Wiener 2018 or Prashad]. If legitimation strategies are shaped by the normative standards that a speaker's core audience accepts as legitimate grounds — which the Habermasian framework would predict — then bloc membership is the analytically relevant dimension.

Second, the bloc structure displays high institutional stability across the full period, unlike post-Cold War alliance configurations or economic groupings which have shifted substantially. The core composition of the Western and Soviet/Eastern blocs remained stable from the early 1950s through 1991. The Non-Aligned Movement, while more heterogeneous, maintained a broadly consistent normative orientation from its founding. This stability allows meaningful temporal comparison across all four analytical periods without requiring recoding of states' positions.

Third, the only structural disruption — the entry of fourteen Eastern European states into NATO after 1991 — is handled through a period-aware transition rule (BLOC_TRANSITIONS): states retain their Soviet/Eastern bloc classification through their year of NATO accession, after which they are reclassified as Western bloc. The states affected by this rule (including Bulgaria, Czech Republic, Estonia, Hungary, Latvia, Lithuania, Poland, Romania, Slovakia, Slovenia — 2004; Albania, Croatia — 2009; Montenegro — 2017; North Macedonia — 2020) do not appear in the 33-case sample, so the transition rule does not affect the reported results. Its inclusion preserves conceptual integrity and relevance for any expanded analysis.

The supervisor's question — whether blocs can be shown to differ in their legitimation repertoires — is precisely what the statistical comparisons in Chapter 4 test. The bloc classification is not assumed to produce differences; it is a theoretically motivated hypothesis that the data either support or reject.

---

## 3.4. Coding Framework

### 3.4.1. Habermas's Typology as the Master Coding Architecture

The case-level analysis classifies each coded segment according to Habermas's (1984) four-type taxonomy of social action. The decision to apply this deductively derived framework rather than developing categories inductively from the corpus follows the logic of directed qualitative content analysis: when existing theory provides sufficiently specified categories, it is both methodologically more defensible and analytically more productive to test those categories against new data rather than reinventing a descriptive vocabulary (Hsieh & Shannon, 2005) [SOURCE NEEDED: page]. Prior IR scholarship confirms the applicability of Habermas's typology to multilateral diplomatic discourse. Risse (2000) demonstrates that the distinction between arguing and bargaining — which maps directly onto communicative versus strategic action in Habermas's framework — generates empirically testable predictions about actor behavior in international institutions. Müller (2004) extends this by showing that the distinction operates at the level of actor *orientation* (toward understanding vs. toward success) rather than at the level of specific speech acts, which means that the same argumentative form can be communicative or strategic depending on the speaker's underlying orientation toward the audience. Bjola (2005) applies the framework directly to UNGA-adjacent discourse, demonstrating its purchase on the analysis of how states construct deliberative legitimacy for contested uses of force.

The nine communicative roles employed in this study are derived deductively from the four Habermas types and operationalized as follows:

| Habermas type | Validity claim | Communicative roles covered |
|---|---|---|
| Communicative action (*Verständigung*) | Truth | Justification; dialogue appeal |
| Normative action (*Richtigkeit*) | Rightness | Legal-normative invocation; sovereignty norm |
| Dramaturgical action (*Wahrhaftigkeit*) | Sincerity | Historical context; victim narrative |
| Strategic action (success-oriented) | — | Denial; counter-accusation; delegitimation |

This four-part structure allows the analysis to ask not only *which* strategies appear, but *what kind of legitimation work* they perform: whether states construct shared reasons (communicative), invoke shared norms (normative), stage authentic self-presentation (dramaturgical), or attempt to foreclose the legitimation game entirely (strategic). As Rapp (2022) observes, in a deeply legalized international system, actors face strong pressure to construct legal justifications even when those justifications are tenuous — which implies that the mode of legitimation itself carries information about the normative constraints states perceive themselves to be operating under.

### 3.4.2. Keyword-Based Classification Procedure

Each identified argumentative segment is classified using a keyword density scoring procedure applied across nine role-specific lexicons. For each segment, the score for role *r* is computed as:

**score(r) = (number of keyword matches for role r in segment) / (total word count of segment) × 1,000**

yielding a hits-per-thousand-words metric that normalizes for segment length. The dominant role assigned to a segment is the role with the highest non-zero score across all nine lexicons. Segments that return a score of zero across all nine lexicons are designated *unclassified*; these are analyzed separately as a methodologically informative category rather than treated as missing data.

This procedure is not a substitute for the manual reading and interpretation of each speech. Rather, it operationalizes the theoretical categories in a reproducible, transparent, and consistently applied way across the full 33-case sample. Each lexicon was developed deductively from the theoretical definitions in Chapter 2, then refined through iterative engagement with a pilot subset of speeches to ensure that keyword patterns reliably track the corresponding argumentative moves. The full lexicons are documented in the study's analytical code (scripts/ml/communicative_roles.py).

The overall unclassified rate is 4.9 percent (5 of 102 segments). The slightly elevated rate for the Western bloc subcorpus (three segments) is itself analytically relevant: it reflects the more institutionally indirect and hedged argumentative style characteristic of US and Israeli diplomatic discourse in the sample periods, where justificatory arguments are often constructed through elaborate conditional framings rather than explicit keyword-dense assertions. This pattern is consistent with Rapp's (2022) observation that actors in highly legalized contexts invest significant resources in constructing *legally palatable* arguments rather than simply asserting positions directly.

In addition to the Habermas-type classification derived from keyword scoring, a complementary manual strategy coding layer records the dominant legitimation strategy for each segment from a set of eight theoretically derived strategy types (self-defense and necessity; sovereignty and non-interference; denial and reinterpretation; moral and humanitarian framing; counter-terrorism and securitization; whataboutism and tu quoque; procedural-legal claims; historical and existential narratives). This layer is consistent with the two analytical dimensions described in Section 2.3. The two coding layers — Habermas type from keyword classification; manual strategy type — capture different facets of the same speech act and are treated as complementary rather than redundant in the empirical analysis.

### 3.4.3. Historical Periodization

Each coded segment is additionally tagged with one of four historical sub-periods, defined by geopolitically significant inflection points rather than arbitrary temporal intervals:

- **Cold War (1946–1989):** the foundational decades of the postwar normative order, marked by superpower bipolarity and the ideological structuring of international legitimation discourse
- **Post–Cold War normative expansion (1990–2001):** the transition to liberal internationalism's ascendancy, emergence of humanitarian intervention as a contested norm, and UNSC activism
- **Post-9/11 Security Turn (2002–2013):** beginning with UNSC Resolution 1373 (2001), which established counter-terrorism as a universal security obligation and created a new legitimation resource broadly available to state actors
- **Post-2014 Normative Fragmentation (2014–2023):** beginning with Russia's incorporation of Crimea, which General Assembly resolution 68/262 characterized as a violation of territorial integrity, and the subsequent fragmentation of the post-Cold War normative consensus

This periodization allows the analysis to test H3 (temporal shift) and provides the temporal structure for the corpus-level H1 convergence analysis.

---

## 3.5. Statistical Methods

The quantitative dimension of the analysis employs a suite of statistical methods, selected to match the data structure (categorical, small-N, often with sparse cell frequencies) and the substantive questions being addressed.

**Chi-square tests of independence (χ²)** are used to assess whether the distribution of Habermas action types differs significantly across blocs (H4) and across historical periods (H3). The chi-square statistic measures the deviation of observed cell frequencies from what would be expected if the two categorical variables were independent [SOURCE NEEDED: standard statistics reference for chi-square]. Effect size is reported as Cramér's V, which normalizes chi-square for table dimensions and sample size [SOURCE NEEDED: Cramér 1946 or standard reference]. Given the small expected cell frequencies characteristic of the 33-case sample (many cells below the conventional threshold of 5), all chi-square results are accompanied by the percentage of cells with expected frequency below 5, and results with high proportions of such cells are interpreted with explicit caution.

**Fisher's exact test** is used for pairwise bloc comparisons, where the small sample sizes render chi-square approximations unreliable. Fisher's exact test computes the exact probability of observing the given contingency table or a more extreme one under the null hypothesis of independence, without relying on large-sample approximations [SOURCE NEEDED: Fisher 1934 or standard reference]. It is preferred over chi-square for 2×2 and small contingency tables with expected cell counts below 5 (Agresti, 2002) [SOURCE NEEDED: Agresti — verify edition and page].

**Adjusted standardized residuals** (Haberman, 1973) are used to identify which specific role-bloc combinations deviate most substantially from expected frequencies. Unlike raw residuals, adjusted residuals account for both the marginal totals of the row and column and the overall sample size, making comparisons across cells in the same table meaningful [SOURCE NEEDED: Haberman 1973 page]. Values exceeding ±2 are interpreted as indicating statistically notable over- or under-representation.

**Correspondence analysis (CA)** provides a geometric representation of the association structure in a contingency table. CA decomposes the chi-square distance between row and column profiles via singular value decomposition (SVD), producing principal coordinates for both rows (communicative roles) and columns (blocs or periods) in a low-dimensional space. The proportion of total inertia (analogous to variance) captured by each dimension is reported via scree plots; dimensions capturing cumulatively more than 80 percent of total inertia are treated as the substantively meaningful space. Greenacre (1984) provides the standard account of the method and its interpretation [SOURCE NEEDED: Greenacre 1984 — verify title and page]. CA was implemented via SVD in Python (numpy) without external dimensionality-reduction libraries, ensuring full procedural transparency.

**One-way ANOVA** is used to test whether the mean corpus-level keyword signal score for the counter-terrorism dimension differs significantly across the three blocs in the pre-2001 and post-2001 periods separately. ANOVA tests the null hypothesis that group means are equal; a non-significant result (both pre- and post-2001) is the predicted outcome under H1, indicating that adoption of counter-terrorism framing did not cluster in a single bloc. [SOURCE NEEDED: standard ANOVA reference]

**Two-sample t-tests (independent samples)** are used to assess whether the mean counter-terrorism signal score differs significantly between the pre-2001 and post-2001 periods within each bloc. This tests whether the post-9/11 shift detected in the case-level analysis is also present at the corpus level, across all bloc members — not only those in the 33-case sample.

---

## 3.6. Reliability, Validity, and Scope of Claims

*Reliability* is addressed through double-coding: a subset of the sample (approximately 20 percent of speeches) is independently coded by a trained research assistant working from the same codebook. Inter-coder reliability is calculated using Cohen's kappa [SOURCE NEEDED: Cohen 1960 — standard reference], with a target threshold of κ ≥ 0.70 regarded as acceptable for this type of categorical coding [VERIFY: confirm standard threshold for qualitative content analysis in IR]. Disagreements are resolved through discussion and codebook refinement. All disagreements and resolutions are documented in an audit trail.

*Validity* in directed content analysis depends on whether the coding categories adequately capture the phenomenon of interest. Construct validity is grounded in the theoretical derivation of the categories from Habermas (1984), operationalized through the IR applications in Risse (2000), Müller (2004), and Bjola (2005). Face validity is assessed through the pilot phase: if trained coders systematically struggle to assign segments to categories, this signals that category definitions require refinement.

Claims are appropriately bounded by the study's design. The analysis identifies and describes the distribution of legitimation strategies *within the selected sample* of speeches from states facing allegations of contested conduct; it does not claim that this distribution is representative of all UNGA speeches. The temporal dimension captures distributional shifts across the sample; no causal mechanisms are established. No adjudicative claims are made: coding a segment as deploying self-defense framing is not a finding that the state's action was or was not lawful. The object of analysis is justificatory discourse — how states publicly account for their conduct — not the legal or factual merits of those accounts.

Two further constraints apply. The corpus covers only the UNGA General Debate; legitimation strategies operative in the Security Council, bilateral diplomatic communications, or domestic political discourse fall outside the scope of analysis. Translation from non-English originals introduces the risk of systematic distortion in cases where specific legal vocabulary is not fully preserved; the interpretive analysis flags this constraint where it is especially salient.

Subject to these constraints, the two-level analytical design produces a systematic, transparent, and theoretically grounded account — adequate for the empirical analysis reported in Chapter 4.

---

## Self-review

**Сильные стороны:**
- Два уровня анализа (корпусный + кейс-уровень) теперь явно описаны и связаны с гипотезами
- Обоснование блоков подробное, логически связанное с 77-летним охватом и биполярной системой
- Статистические методы описаны каждый отдельно, с обоснованием выбора и флагами для источников
- Keyword scoring представлен как основной классификационный метод, а не просто скрининг
- Источники: Habermas (1984), Risse (2000), Müller (2004), Bjola (2005), Rapp (2022), Baturo et al. (2017) использованы по делу

**Флаги:**
- `[SOURCE NEEDED]` × 8 — статистические методы (chi-square, Fisher, Cramér, adjusted residuals, CA, ANOVA, t-test, Cohen's kappa): стандартные ссылки нужны, но не в notes/
- `[SOURCE NEEDED]`: Hsieh & Shannon (2005) — страница для directed CA
- `[SOURCE NEEDED]`: Крэммер/Haberman — методологические источники для adjusted residuals и V
- `[SOURCE NEEDED]`: NAM normative repertoire — Wiener (2018) или Prashad
- `[SOURCE NEEDED]`: Agresti (2002) — Fisher's exact для малых выборок
- `[VERIFY]`: κ ≥ 0.70 порог — уточнить стандарт для IR qualitative content analysis
- `[VERIFY]`: OCR-качество для речей до 1992
