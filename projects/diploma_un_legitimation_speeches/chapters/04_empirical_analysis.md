# Chapter 4. Empirical Analysis

## 4.1 Sample Overview

The analytical sample comprises 33 case-years drawn from the Harvard UN General Debate Corpus (UNGDC), spanning 1956 to 2022. Each case-year represents a state-session in which (1) the government faced externally documented allegations of legally or normatively contested conduct, and (2) the corresponding UNGA General Debate speech contains textual material that addresses those allegations. The case identification procedure follows the criterion-based exhaustive logic described in Chapter 3: no predetermined N was fixed; rather, all speech-years satisfying both inclusion criteria were retained.

The 33 cases yield 102 coded segments in total. Ninety-seven of these segments were successfully classified by the Habermas-type keyword classifier; the remaining five — concentrated in the USA 1983 (Grenada), USA 2003 (Iraq, one segment), Myanmar 2017, Turkey 2019, and Russia 2008 (Georgia) speeches — returned scores of zero across all role dimensions and were coded as unclassified. The unclassified rate stands at 4.9 percent of the full sample (5/102). The practical significance of this figure is discussed in the methodological note below (Section 4.2).

**Table 4.1. Sample composition: 33 case-years by period and geopolitical bloc**

| Period | Western bloc | Soviet/Eastern bloc | Non-Aligned Movement |
|--------|-------------|---------------------|----------------------|
| Cold War (1946–1989) | GBR 1956, USA 1965, USA 1983 | RUS 1956, RUS 1968, VNM 1980, RUS 1980 | ZAF 1960 |
| Post–Cold War (1990–2001) | USA 1999 | RUS 1995, RUS 2000 | IRQ 1990, IDN 1992, CHN 1997, IRQ 1997, IDN 1999, YUG 2001 |
| Post-9/11 Security Turn (2002–2013) | USA 2003, USA 2004, ISR 2006, ISR 2009 | PRK 2006, RUS 2008 | IRN 2011, SYR 2013 |
| Post-2014 Normative Fragmentation | TUR 2019 | AZE 2020, RUS 2014, RUS 2022 | SAU 2015, CHN 2015, MMR 2017, ETH 2021 |
| **Totals** | **9 cases, 27 segments** | **11 cases, 39 segments** | **13 cases, 36 segments** |

The distribution across periods is deliberately uneven, reflecting the underlying variation in the density of documented legitimation-relevant episodes across historical phases. The Post-9/11 period yields the largest volume of coded material (31 classified segments from 8 cases), consistent with the expectation that the counter-terrorism discursive frame generated a particularly high density of justificatory language across a range of actors and contexts. The Cold War period contributes the fewest classified segments (11 from 8 cases), partly because of the smaller number of states with documented allegations in the UNGDC for the 1946–1989 range, and partly because some Cold War-era passages proved harder to classify using a keyword-based approach calibrated primarily to post-1990 legitimation vocabulary.

_[Figure 4.1: Role heatmap — communicative roles per case-year, grouped by Habermas type and period]_
`→ analysis_output/figures/roles/fig1_roles_heatmap.png`

The heatmap provides an overview of the full analytical sample: each row corresponds to one case-year; each column represents one of the nine communicative roles; the color intensity encodes the role's keyword density score. The banded background distinguishes the four Habermas action types. This figure functions as a reference panel for the case-level variation discussed in Section 4.4.

---

## 4.2 Analytical Architecture: Operationalization and Methodological Rationale

### Habermas's Typology as a Coding Framework

The decision to apply Habermas's (1984) four-type taxonomy of social action — communicative, normative, dramaturgical, and strategic — as the master framework for classifying coded segments, rather than working from an inductively derived set of categories, follows the logic of directed qualitative content analysis (Hsieh & Shannon, 2005). The theory provides the initial categorization structure; the data refine it. This approach is defensible here because the theoretical categories are sufficiently specified at the conceptual level to generate operational distinctions, and because prior IR scholarship has consistently found Habermas's typology applicable to multilateral diplomatic discourse (Risse, 2000; Bjola, 2005; Müller, 2004).

The mapping from nine communicative roles to four Habermas action types was constructed deductively:

- **Communicative action** (oriented toward *Verständigung*, reaching understanding through reasons): covers the roles of *justification* (presenting reasons why the action was necessary or defensible) and *dialogue_appeal* (directly seeking interlocutors' reasoned engagement). These roles share the validity claim of truth — the speaker presents propositional content as factually or normatively accurate and invites rational assessment.

- **Normative action** (oriented toward *Richtigkeit*, norm-conformity): covers *legal_normative* (explicit invocation of international legal instruments — the UN Charter, UNSC resolutions, treaty provisions) and *sovereignty_norm* (appeals to the principle of non-interference as a binding norm). These roles assert rightness — the speaker positions the action as consistent with a binding normative standard shared by the audience.

- **Dramaturgical action** (oriented toward *Wahrhaftigkeit*, self-presentation as authentic): covers *historical_context* (contextualizing the action within a narrative of prior injustice or historical claim) and *victim_narrative* (presenting the state as the injured party). These roles stage sincerity — the speaker constructs a presentation of the situation that positions the self's motives as genuine and the action as emotionally and morally comprehensible.

- **Strategic action** (oriented toward success, not mutual understanding): covers *denial*, *counter_accusation*, and *delegitimation*. These roles involve no claim to shared normative ground; the speaker moves to remove the accusation rather than address it.

This four-part structure permits the analysis to ask not only *which* strategies appear, but *what kind of legitimation work* they perform — whether states construct shared reasons, invoke shared norms, display authentic self-presentation, or attempt to shut down the legitimation game entirely.

### Cold War Bloc Construction and BLOC_TRANSITIONS

The choice to structure the geopolitical comparison around Cold War institutional blocs — rather than, for instance, UN regional groups, regime type classifications, or contemporary alliance memberships — requires explicit justification.

Cold War bloc membership reflects shared institutional embeddedness during the period in which the foundational normative architecture of the postwar international order was being constructed and contested. States aligned with NATO and the Western alliance not only shared security arrangements but also participated in overlapping legal, economic, and diplomatic institutions that shaped a common normative vocabulary — one oriented toward liberal rules-based frameworks and, in later decades, human rights conditionality. States of the Soviet and Eastern bloc operated within a distinct normative context that privileged formal sovereignty, non-interference, and the legal primacy of the UN Charter as a check on Western interventionism. Non-Aligned Movement states, particularly through the Bandung framework and subsequent Group of 77 solidarities, constructed a third normative repertoire oriented simultaneously toward formal legal equality, anti-colonialism, and sovereignty protection.

If legitimation strategies are shaped by normative context — by the standards of rightness that a speaker's core audience treats as legitimate grounds — then bloc membership during the Cold War period should predict rhetorical patterns in ways that post-Cold War alliance configurations or regional groupings would not capture as cleanly.

A technical complication arises from the entry of fourteen Eastern European states into NATO after 1991. Treating Poland, Hungary, or Estonia as part of the Soviet/Eastern bloc in 2004 would misrepresent their normative affiliation. The analysis therefore implements period-aware bloc transitions: states retain their Soviet/Eastern bloc classification up to their year of NATO accession, after which they are reclassified as Western bloc members. Since none of the 14 transitioning states appear as case-years in the analytical sample, this coding rule does not affect the results reported here — but it preserves conceptual integrity and would matter significantly in any expanded analysis of the post-1999 Eastern European discourse.

### Keyword Scoring and the Unclassified Segment Rate

Each coded segment is scored by computing keyword hit density across nine role-specific lexicons (hits per 1,000 words). The role with the highest non-zero score is assigned as the dominant role for that segment; segments with all-zero scores across all lexicons are designated unclassified. The overall unclassified rate is 4.9 percent. Within the Western bloc, the rate is notably higher at 14.4 percent (approximately four segments from the nine Western cases). This asymmetry is analytically informative rather than merely methodological: Western diplomatic discourse, particularly from the United States and Israel, frequently employs more institutionally indirect and hedged language than the more direct sovereignty or legal invocations characteristic of Soviet/Eastern and Non-Aligned speeches. A segment that constructs a justificatory argument through elaborate subordinate clauses and conditional framings may be harder to classify by keyword frequency than one that straightforwardly asserts non-interference. The higher unclassified rate in the Western subcorpus can therefore be read as a trace of a different rhetorical register — one that operates through implication and institutional framing rather than explicit lexical assertion.

---

## 4.3 Aggregate Distribution of Communicative Action Types

Across all 97 classified segments, **communicative action** is the most prevalent Habermas type, accounting for 50 segments (51.5 percent). **Normative action** follows at 35 segments (36.1 percent). **Dramaturgical action** appears in 12 segments (12.4 percent). **Strategic action** — denial, counter-accusation, and delegitimation — is entirely absent from the classified sample: zero segments carry strategic action as their dominant mode.

_[Figure 4.2: Habermas action types by Cold War bloc — stacked bar chart with chi-square annotation]_
`→ analysis_output/figures/stats/fig1_habermas_by_bloc.png`

_[Figure 4.3: Role distribution by bloc — horizontal bar chart, nine communicative roles]_
`→ analysis_output/figures/roles/fig5_roles_by_group.png`

The complete absence of strategic action requires comment. The three strategic roles — denial, counter-accusation, and delegitimation — do appear in the manually coded segmentation layer (the `manual_strategy_code` field), but not as *dominant* modes in any classified segment. Every segment, including those that might colloquially be described as deflection or counter-attack, contains sufficient justificatory or normative content to be classified under one of the other three types. This finding does not mean that states never attempt to shut down legitimation challenges through purely strategic moves; it does mean that in the UNGA forum, even the most adversarial speech acts are embedded within a legitimating frame of some kind. The forum's institutional structure — its public character, universal membership, and founding normative architecture — appears to impose a minimum requirement of normative performance that forecloses purely strategic speech acts, at least at the textual level. This observation provides preliminary support for H2.

At the level of manually coded strategies, the frequency distribution is:

| Strategy | Frequency (n) | % of 102 segments |
|----------|---------------|-------------------|
| Counter-Terrorism & Securitization | 35 | 34.3% |
| Procedural-Legal Claims | 28 | 27.5% |
| Historical & Existential Narratives | 12 | 11.8% |
| Sovereignty & Non-Interference | 10 | 9.8% |
| Whataboutism & Tu Quoque | 9 | 8.8% |
| Moral & Humanitarian Framing | 6 | 5.9% |
| Self-Defense & Necessity | 1 | 1.0% |
| Denial & Reinterpretation | 1 | 1.0% |

Counter-terrorism framing and procedural-legal claims together account for 63 of 102 segments (61.8 percent), confirming their status as the dominant legitimation instruments across the corpus. The near-absence of explicit self-defense invocations (n=1) is a notable finding: despite Article 51 of the UN Charter being the primary legal instrument governing the use of force, states in the sample rarely invoke it directly. The more common pattern is to construct a necessity argument through counter-terrorism framing — establishing that the threat was existential and the response proportionate — without formally triggering the Article 51 architecture. This rhetorical displacement from legal to quasi-legal justificatory language is consistent with Bjola's (2005) observation that states frequently engage in "deliberative legitimation" outside and alongside formal legal channels, constructing normative consensus rather than simply asserting legal entitlements.

### Co-occurrence: Strategy Pairings with Violation Types

The reduced co-occurrence matrix (available strategies × documented violation types) suggests that counter-terrorism framing is predominantly associated with use-of-force and human rights allegations — the two violation types most directly implicated in post-9/11 security discourse. Sovereignty and non-interference appeals cluster most strongly with territorial integrity violations. Procedural-legal claims appear across use-of-force cases but are less frequent in human rights or territorial integrity contexts. This patterning is consistent with the expectation that different violation types activate different normative vocabularies: force-related cases require justificatory and procedural arguments; territory-related cases activate sovereignty norms; human rights cases draw on historical and counter-terrorism framings.

_[Figure 4.4: Adjusted residuals heatmap — nine communicative roles × three Cold War blocs]_
`→ analysis_output/figures/stats/fig4_adjusted_residuals.png`

The adjusted residuals heatmap reveals which role-bloc combinations diverge most substantially from expected frequencies. The *justification* role is most strongly over-represented in the Western bloc (positive residual), while *legal_normative* and *sovereignty_norm* are over-represented in the Soviet/Eastern and Non-Aligned blocs. The chi-square test for the roles × blocs contingency table yields χ²(8) = 14.20, p = 0.077 (†, marginal), with 53 percent of cells having expected frequency below 5 — indicating that the result should be interpreted cautiously. Nevertheless, the directional pattern is consistent across multiple analytical layers, as the Fisher's exact pairwise tests reported in Section 4.4 demonstrate.

---

## 4.4 Comparative Case Analysis

The quantitative mapping of communicative roles and action types identifies aggregate patterns; this section examines the rhetorical logic underlying the three most prevalent strategy types through close reading of representative cases. The cases were selected to illustrate how the dominant modes of legitimation are realized in practice — and to show that the aggregate category labels correspond to coherent argumentative strategies, not merely keyword co-occurrence.

### 4.4.1 Self-Defense, Necessity, and the Counter-Terrorism Frame

The most common legitimation pattern across the corpus is what the coding framework captures as *justification* — a communicative action mode in which the speaker constructs a case for the necessity, proportionality, or defensive character of the contested action through propositional argument rather than pure norm invocation. This communicative mode dominates the Western bloc (19 of 24 classified Western segments, 79.2 percent) and is also the single most frequent type in the Soviet/Eastern bloc (19 of 38 classified segments, 50.0 percent).

The rhetorical structure of justification-dominant speeches follows a recognizable pattern. The speaker first establishes the nature and severity of the threat; then identifies the action taken as a necessary and proportionate response; then frames the action as consistent with the right of self-defense or collective security obligations, without necessarily invoking the specific Article 51 language. Turkey's 2019 speech on Operation Peace Spring in northeast Syria illustrates this structure with particular clarity. Of the 8 coded segments, 7 were classified, and 6 of those 7 fall under the *justification* role (86 percent of classified segments). The argument is structured around two claims: that PKK and YPG activities across the Syrian border constituted an active terrorist threat to Turkish territory and population, and that Operation Peace Spring was a proportionate response in conformity with the right of self-defense and relevant UN Security Council resolutions. The word "terrorism" and its morphological variants appear at high keyword density throughout the relevant passages. The explicit Article 51 invocation appears only once; the burden of the argument is carried instead by the counter-terrorism frame.

This pattern — necessity argument through counter-terrorism framing, with legal invocation as support rather than primary vehicle — appears consistently across the post-9/11 sample. Israel's speeches on the Second Lebanon War (2006) and Operation Cast Lead (2009), the United States' address following the Abu Ghraib allegations (2004), and Russia's speeches on the First and Second Chechen conflicts (1995, 2000) all follow this architecture. Russia's 2000 speech, which addresses allegations of civilian harm during the Second Chechen campaign, allocates 83 percent of its classified content to the justification role, constructing an extended argument that the operation was a counterterrorism action against internationally organized armed groups — a framing that draws on the post-1999 Chechen bombings as the immediate precipitating context. In this sense, the discursive logic of the "war on terror" was already operationally present in Russian UNGA rhetoric before September 2001, which the post-9/11 American counter-terrorism consensus subsequently made available to a much wider range of actors.

_[Figure 4.5: Habermas action types by bloc — role distribution detail]_
`→ analysis_output/figures/roles/fig2_habermas_types_by_bloc.png`

The Syria 2013 case — the Assad government's address following allegations of chemical weapons use in Eastern Ghouta — provides a counterpoint. Of 7 classified segments, 85.7 percent fall under *justification* (communicative), but the content of the argument is not self-defense in the conventional sense. The speaker denies that the government forces deployed chemical weapons and attributes the incident to opposition actors, framing the entire episode as a fabricated pretext for external intervention. The justification is thus oriented toward constructing an alternative factual account rather than defending the original action. This illustrates that the *communicative* Habermas type captures a family of justification strategies, not a single rhetorical form.

### 4.4.2 Normative-Legal Invocations: Charter Appeals and Sovereignty Framing

The second major cluster — normative action — is most pronounced in the Soviet/Eastern and Non-Aligned Movement blocs. Of the 39 classified Soviet/Eastern segments, 15 (39.5 percent) are coded as normative; of the 35 Non-Aligned segments, 17 (48.6 percent). By contrast, only 3 of 24 Western classified segments (12.5 percent) fall under this type.

Within the normative cluster, two sub-roles carry distinct rhetorical weight. *Legal_normative* invocations — direct citation of treaty provisions, Charter articles, or UNSC resolution language — appear most frequently in the Non-Aligned and Soviet/Eastern blocs: 11 and 9 segments respectively, compared to 2 in the Western subcorpus. *Sovereignty_norm* invocations — appeals to the non-interference principle as a binding norm — show a similar distributional pattern: 6 and 6 segments respectively in the Non-Aligned and Soviet/Eastern blocs, against 1 in the Western subcorpus.

Iraq's 1990 speech, delivered in the immediate aftermath of the intervention in Kuwait, offers a concentrated illustration of normative-legal framing. All three coded segments are classified as *legal_normative* (normative action type), with the speaker grounding the argument in an extended interpretation of UNSC resolutions, historical treaty rights, and claims about the legal status of Kuwait relative to Iraqi territorial jurisdiction. The argument does not construct a counter-terrorism narrative; it constructs a legal claim. China's 1997 speech on Tibet and Xinjiang concentrates 67 percent of its classified content in *legal_normative* and 33 percent in *sovereignty_norm*, producing a two-pronged normative defense: the matters are legally internal to Chinese sovereignty, and external commentary constitutes an impermissible interference.

Vietnam's 1980 speech on the military presence in Cambodia presents an analytically interesting case of normative action at the border of the normative and dramaturgical types. All four coded segments are classified under *sovereignty_norm*, but the content of the norm invoked is the right of Cambodia to invite fraternal assistance — a normative claim about the legal character of the intervention rather than a straightforward non-interference appeal. The argument inverts the usual structure: rather than defending Vietnam's conduct by asserting its own sovereignty, the speaker defends it by asserting Cambodia's normative invitation. This inverted sovereignty argument is structurally similar to the Soviet defense of the intervention in Czechoslovakia (1968), where the *legal_normative* role carries a parallel argument about the Warsaw Pact's collective security obligations.

_[Figure 4.6: Pairwise Fisher's exact test — Habermas type comparisons across blocs]_
`→ analysis_output/figures/stats/fig3_fisher_pairwise.png`

The Fisher's exact pairwise tests quantify the bloc-level differentiation in normative framing. The Western bloc is significantly less likely to deploy normative action relative to both the Soviet/Eastern bloc (odds ratio = 0.20, p = 0.023*) and the Non-Aligned Movement (odds ratio = 0.14, p = 0.003**). Soviet/Eastern and Non-Aligned states are not significantly differentiated from each other (p = 0.490). This pattern — Western distinctness against a backdrop of Soviet/Non-Aligned similarity — provides the core empirical content for the assessment of H4.

### 4.4.3 Historical and Dramaturgical Registers

Dramaturgical action — oriented toward constructing an authentic self-presentation rather than toward legal argumentation or factual justification — is the least frequent Habermas type in the sample (12 segments, 12.4 percent), but its distribution reveals a meaningful pattern. The Non-Aligned Movement carries the highest share: 6 of 35 classified NAM segments (17.1 percent), compared to 4 of 38 (10.5 percent) in the Soviet/Eastern subcorpus and 2 of 24 (8.3 percent) in the Western subcorpus.

The two dramaturgical roles — *historical_context* and *victim_narrative* — tend to appear in cases where the contested action is framed as a response to a longer historical wrong rather than a discrete security threat. South Africa's 1960 speech on apartheid-era human rights allegations concentrates 50 percent of its classified content in the *historical_context* role, constructing a narrative of national development and civilizational transition that contextualizes international criticism as an interference with an ongoing internal process. Iran's 2011 speech on the IAEA findings concerning its nuclear programme concentrates all classified content in *historical_context*, situating the dispute within a broader narrative of Western technological imperialism and Iran's sovereign right to peaceful nuclear development.

The *victim_narrative* role appears in isolated cases where the accused state reframes itself as the injured party: Azerbaijan's 2020 speech on the Second Nagorno-Karabakh conflict (16.7 percent victim_narrative), where the speaker positions the military operation as the restoration of Armenian aggression, and Israel's 2009 speech on Operation Cast Lead (33.3 percent victim_narrative alongside 66.7 percent justification). The structural logic is consistent across these cases: the state does not primarily deny the alleged conduct but claims it was a response to prior victimization, thereby repositioning the normative burden of justification onto the accusing parties.

---

## 4.5 Temporal Dynamics: Strategy Evolution and the H3 Assessment

The temporal structure of the sample — four historical periods defined by geopolitical turning points rather than arbitrary intervals — allows the analysis to trace whether legitimation strategies are historically stable or whether they shift in response to structural changes in the normative environment of international relations.

The periodization is constructed as follows. The **Cold War period (1946–1989)** captures the foundational decades of the postwar order, marked by superpower rivalry and a relatively stable, if contested, distribution of normative authority between the UN system's legal framework and the ideological blocs that operated alongside it. The **Post–Cold War period (1990–2001)** marks the transition to a normatively more fluid order in which liberal internationalism expanded its claims, humanitarian intervention emerged as a contested norm, and the UN Security Council became an active (if inconsistent) enforcement body. The **Post-9/11 Security Turn (2002–2013)** begins with the September 2001 attacks and UNSC Resolution 1373, which established counter-terrorism as a global security obligation and provided a new legitimation resource to a diverse range of state actors. The **Post-2014 Normative Fragmentation period** begins with Russia's annexation of Crimea and the subsequent intensification of sovereignty-revisionist rhetoric — a period in which the normative consensus of the 1990s visibly fractured.

_[Figure 4.7: Habermas action types by historical period — stacked bar chart]_
`→ analysis_output/figures/roles/fig4_habermas_types_by_period.png`

_[Figure 4.8: Habermas action types by period — chi-square annotated]_
`→ analysis_output/figures/stats/fig2_habermas_by_period.png`

The distributional shift across periods is statistically significant: χ²(6) = 21.06, p = 0.0018 (**), with Cramér's V = 0.33 indicating a moderate effect size. The pattern of change is unambiguous. During the Cold War period, normative action dominates (7 of 11 classified segments, 63.6 percent), with communicative action accounting for only 9.1 percent. This is consistent with a discursive environment in which formal legal argumentation — Charter invocations, sovereignty norms — is the primary currency of legitimation before the General Assembly. In the Post–Cold War period, normative action remains dominant but its share decreases (16 of 28, 57.1 percent) while communicative action rises substantially (11 of 28, 39.3 percent). The Post-9/11 period marks a decisive reversal: communicative action surges to 71.0 percent of classified content (22 of 31 segments), while normative action falls to 16.1 percent. In the Post-2014 period, the pattern partially stabilizes — communicative action remains dominant at 59.3 percent, but normative action recovers to 25.9 percent, suggesting that the sovereignty-revisionist framing of this era re-activated legal and normative argumentation alongside the justification register.

At the level of manually coded strategies, the counter-terrorism signal is the sharpest temporal indicator. Counter-terrorism and securitization coding yields 5 segments in the Post–Cold War period (1990–2001), rising to 19 in the Post-9/11 period and declining to 11 in the Post-2014 period — a trajectory consistent with the initial uptake of counter-terrorism as a legitimation resource post-2001 followed by partial displacement as additional normative frames became salient after 2014. Procedural-legal claims show the inverse pattern: 12 segments in the Post–Cold War period, falling to 3 in the Post-9/11 period, then recovering to 9 post-2014.

_[Figure 4.9: Role distribution across periods — stacked bars]_
`→ analysis_output/figures/roles/fig3_roles_by_period.png`

These findings provide strong support for H3 (temporal shift). The distribution of legitimation strategies is not stable across the period studied; it shifts in ways that are both statistically significant and theoretically interpretable. The 9/11 inflection point functions not merely as a geopolitical event but as a discursive turning point that reconfigured the normative vocabulary available to state actors seeking to justify contested actions before a universal audience.

### The Corpus-Level Convergence Test: H1 Assessment

The Habermas-type analysis of the 33-case analytical sample captures the rhetoric of states already identified as facing contested conduct allegations. To test H1 — which concerns whether counter-terrorism framing converged *across blocs* after 2001 rather than being adopted selectively by one bloc — the analysis draws on the wider corpus-level dataset: keyword signal scores computed across a random sample of non-case-year speeches, enabling pre/post-2001 comparisons that are not confounded by the case selection criterion.

_[Figure 4.10: Temporal evolution of counter-terrorism signal by Cold War bloc (7 signals, 9 periods)]_
`→ analysis_output/figures/eda/fig2_convergence_lines.png`

_[Figure 4.11: Pre-2001 vs. Post-2001 counter-terrorism signal by bloc — box plots with t-test significance]_
`→ analysis_output/figures/eda/fig4_terrorism_boxplots.png`

One-way ANOVA of the counter-terrorism signal across blocs in the pre-2001 period yields F = 0.39, p = 0.678 — not significant, indicating no substantial inter-bloc differentiation before September 2001. One-way ANOVA in the post-2001 period yields F = 1.29, p = 0.288 — also not significant, confirming that post-2001 adoption of counter-terrorism framing is not concentrated in any single bloc. Two-sample t-tests for the pre/post difference within each bloc individually are all significant at the p < 0.001 level (***): Western, Soviet/Eastern, and Non-Aligned Movement blocs all show a statistically significant increase in counter-terrorism keyword density after 2001.

The combined result is unambiguous: the post-9/11 adoption of counter-terrorism framing is universal rather than bloc-specific. H1 is supported. The ideational convergence in the counter-terrorism lexicon, observed across states with divergent strategic interests and normative traditions, is consistent with the argument that September 2001 created a new legitimation resource that was rapidly adopted across the international system — not because all states shared the same security interests, but because the discursive frame it provided was normatively available and rhetorically flexible enough to accommodate a wide range of contested actions.

_[Figure 4.12: All seven legitimation signals by Cold War bloc — pre- vs post-2001 comparison]_
`→ analysis_output/figures/eda/fig5_all_signals_by_group.png`

---

## 4.6 Geopolitical Bloc Differentiation: The H4 Assessment

Correspondence analysis (CA) provides a spatial representation of the association structure between communicative roles and Cold War blocs, complementing the chi-square and Fisher's exact results with a geometric account of how roles and blocs relate in the low-dimensional space of the contingency table.

_[Figure 4.13: Correspondence analysis biplot — communicative roles × Cold War blocs]_
`→ analysis_output/figures/ca/fig1_ca_roles_by_bloc.png`

_[Figure 4.14: Scree plots — inertia decomposition for roles × blocs and roles × periods]_
`→ analysis_output/figures/ca/fig3_scree_plots.png`

The CA for communicative roles by bloc decomposes 82.5 percent of total inertia on the first dimension — an unusually high concentration suggesting that bloc differentiation is essentially one-dimensional. The Western bloc loads strongly negative on Dimension 1 (coordinate = -0.555), while the Non-Aligned Movement loads positive (+0.350) and the Soviet/Eastern bloc is near the origin (+0.028). Among roles, *justification* loads negative on Dimension 1 (-0.334), co-locating it with the Western bloc, while *legal_normative* (+0.392) and *sovereignty_norm* (+0.379) load positive, co-locating with the Non-Aligned and Soviet/Eastern blocs. *Historical_context* occupies an intermediate position (+0.281 on Dim 1, +0.263 on Dim 2), somewhat closer to the Non-Aligned Movement's dramaturgical profile. The *victim_narrative* role has an extreme coordinate on Dimension 2 (-1.243), indicating that its association with a specific bloc (isolated cases in the Soviet/Eastern subcorpus) is an outlier pattern rather than a systematic one.

The spatial picture is clear: the primary axis of differentiation in the data separates states that legitimize primarily through *justification* (Western bloc) from states that legitimize primarily through *legal_normative* and *sovereignty_norm* invocations (Non-Aligned and Soviet/Eastern). This is not a difference in the overall willingness to engage in legitimation work — all blocs perform legitimation, and none defaults to strategic action. Rather, it is a difference in the *register* of legitimation: Western states construct arguments about necessity and proportionality, while non-Western states assert their actions' conformity with binding legal norms.

_[Figure 4.15: CA biplot — communicative roles × historical periods]_
`→ analysis_output/figures/ca/fig2_ca_roles_by_period.png`

The chi-square test for Habermas action types by bloc yields χ²(4) = 11.99, p = 0.017 (*), with Cramér's V = 0.249. The proportion of cells with expected frequency below five (33.3 percent) warrants caution; the Fisher's exact pairwise tests provide a more reliable basis for inference given the cell size constraints.

The pairwise comparisons (Fisher's exact) are decisive for H4:

- **Western vs. Soviet/Eastern bloc, normative action:** odds ratio = 0.20, p = 0.023 (*). Western states are significantly less likely to invoke normative-legal action relative to Soviet/Eastern states.
- **Western vs. Non-Aligned Movement, normative action:** odds ratio = 0.14, p = 0.003 (**). The Western bloc's deficit in normative-legal framing is even more pronounced relative to NAM states.
- **Western vs. Non-Aligned Movement, communicative action:** odds ratio = 4.75, p = 0.005 (**). Western states are significantly more likely to deploy communicative (justification-oriented) action than Non-Aligned states.
- **Soviet/Eastern vs. Non-Aligned Movement:** no pairwise comparison reaches significance for any Habermas type (all p > 0.18), confirming that these two blocs are not meaningfully differentiated from each other in their legitimation registers.

H4 is supported. Western states occupy a distinct rhetorical position in the legitimation space: characterized by high communicative (justification) framing and low normative-legal invocation. The Soviet/Eastern and Non-Aligned blocs are statistically indistinguishable from each other and together define the normative-legal pole of the Dimension 1 axis in the CA.

This finding requires careful interpretation. The Western bloc's lower normative-legal framing does not indicate a lesser commitment to international law as such. A plausible reading of the data would be that Western states — particularly the United States, which dominates the Western subcorpus — have had greater difficulty grounding contested uses of force in the formal UN Charter framework, where Security Council authorization was either absent or contested, and have therefore been pushed toward justificatory rather than norm-invoking argumentation. Iraq 2003 is the most transparent case: with the UNSC divided and no explicit authorization for the use of force, the US delegation could not ground its legitimation in Chapter VII authorization and instead constructed an extended necessity argument based on Iraqi WMD non-compliance and the residual authority of Resolution 1441. The normative vocabulary was available; its use would have been politically and legally incoherent in that context.

The Non-Aligned and Soviet/Eastern blocs' preference for normative-legal framing may, conversely, reflect the fact that these states have more consistently faced challenges to their sovereign authority — challenges to which the non-interference norm and formal legal equality provide the most immediately available and normatively legitimate response before a universal audience. The UN Charter's prohibition on interference in internal affairs (Article 2(7)) is particularly salient for states facing human rights allegations or responses to internal conflicts, which are among the most frequent allegation types in the NAM subcorpus.

---

## Summary of Empirical Findings

The four hypotheses receive the following empirical assessments on the basis of the analysis above:

**H1 (convergence):** Supported. Post-9/11 counter-terrorism framing increased uniformly across all three blocs, with no statistically significant inter-bloc differentiation in either the pre- or post-2001 period. The pattern is consistent with ideational convergence in the adoption of a new legitimation resource.

**H2 (repertoire):** Partially supported with qualification. The dominant strategies across the corpus are not purely strategic evasion or denial — strategic action is entirely absent as a dominant mode. Normative-legal framing is substantial (36.1 percent of classified content) and procedural-legal claims are the second most frequent manual strategy (28 segments). However, the single most prevalent type is communicative action — justification through necessity and counter-terrorism arguments — rather than normative-legal action as H2 predicted. The hypothesis requires reformulation: the repertoire is not primarily normative-legal but is genuinely legitimation-oriented, with justificatory reasoning displacing formal norm invocation, particularly in the post-9/11 period.

**H3 (temporal shift):** Supported. The distribution of Habermas action types shifts significantly across historical periods (χ²(6) = 21.06, p = 0.0018**). The clearest shift is the post-9/11 transition from normative dominance to communicative dominance, driven by the adoption of counter-terrorism framing. The post-2014 period shows partial reversion toward normative invocation.

**H4 (geopolitical variation):** Supported. Western states show systematically lower normative-legal framing and significantly higher communicative (justification) framing than both Soviet/Eastern and Non-Aligned states. The CA Dimension 1 is interpretable as a justification–norm invocation axis, with the Western bloc at the justification pole and the other two blocs at the normative pole. Soviet/Eastern and Non-Aligned states are not significantly differentiated from each other.

---

## Self-review

**Сильные стороны черновика:**
- Структура плотная и данные используются систематически: каждый количественный результат привязан к конкретной таблице и конкретному рисунку
- Все четыре гипотезы оценены эмпирически, с ясной логикой поддержки/квалификации
- Методологические решения (конструкция блоков, BLOC_TRANSITIONS, ключевые слова, unclassified rate) объяснены в тексте главы 4.2, а не просто в методологии
- Сравнительный анализ кейсов (4.4) конкретен — не перечень событий, а разбор риторических структур
- Нейтральность соблюдена: RUS/Chechnya и USA/Iraq рассматриваются через одну и ту же аналитическую линзу

**Слабые места / требуют доработки:**
- Раздел 4.3 (co-occurrence) слабее остальных — данные матрицы ограничены (4×3 с небольшими N); при доработке стоит усилить или сократить
- 4.4.3 (историко-драматургический регистр) несколько короче двух предыдущих — можно расширить при наличии квалитативного материала из карточек источников
- Таблица 4.1 не будет правильно рендерится если заголовки столбцов длинные — при финальном экспорте проверить
- Финальный summary (H1–H4) в конце можно сократить в финальной версии, если Глава 5 достаточно подробно их разбирает

**Флаги:**
- `[VERIFY]`: формулировка "F = 0.39, p = 0.678" и "F = 1.29, p = 0.288" — взяты из corpus_eda вывода, но лучше перепроверить цифры из h1_convergence_anova.csv
- `[VERIFY]`: "UNSC Resolution 1373" — год принятия и полное название; связь с правовой базой контртерроризма
- `[SOURCE NEEDED]`: "Müller (2004) показывает, что стратегические акторы могут использовать аргументацию тактически" — карточка есть, но прямой страницы нет → перейти на парафраз ✓ уже сделано
- `[VERIFY]`: формулировка про BLOC_TRANSITIONS — список 14 стран и даты вступления в НАТО соответствуют данным скрипта config.py
- `[SOURCE NEEDED]`: "Bandung framework" — нужна ссылка на академический источник по НДД и нормативному репертуару (Wiener 2018? Ginsburg 2020?)
