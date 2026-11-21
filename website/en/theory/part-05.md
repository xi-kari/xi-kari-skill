---
title: "Part 5 Cross-Scale and Cross-Circle Transformations"
---

<div v-pre class="theory-source">

<a id="part_5"></a>

# Part 5 Cross-Scale and Cross-Circle Transformations {#part-title-5}

This Part asks a set of questions. When an object, observation, or action moves from the source scale (whose scale profile is written SP0) to the target scale (written SP1), what expands, what narrows, which positions cannot be compared, what justifies building a conversion bridge between the two ends, and what information does the conversion lose? The general process is called scale transformation. The nine scale axes define a product partial order (§5.3). The term scale elevation applies only when the relation in that order is strict.

</div>

<SectionLesson section="intro-05-part" />

<div v-pre class="theory-source">


## 5.1 Roles of Axes, Transformations, and Basic Concepts, and Unambiguous Reference {#section-5-1}

By proposition role (§2.2), the nine scale axes are definitions, the nine scale transformations are operational procedures, and the eleven basic structural concepts (§3.5) are also definitions. Neither definitions nor procedures pass themselves off as empirical facts. Specific claims of cross-layer causation, tested object conversion, or a null conclusion (that is, a determination that the null model holds) must all rest on a pre-registered formal test (§4.1). Pre-registration means setting down the target, criteria, and rules before seeing the results.

Dependencies between propositions are of only four kinds: inferential premises, method requirements, domain restrictions, and objects of application (§2.3). A reference to a method requirement needs to name which of the conditions it means, such as the conditions for causal claims, the conditions for evidence, the conditions for analogy, or the conditions for sources (§2.4–§2.7), rather than use a vague abbreviation. The nine axes, the nine transformations, and the eleven basic structural concepts are each referred to by their own names and are not confused with one another. For example, the axis written O in the scale profile denotes organizational level (§5.2), which is a different thing from an operational procedure.

</div>

<SectionLesson section="5.1" />

<div v-pre class="theory-source">


## 5.2 Nine-Axis States and Axis-by-Axis Comparison {#section-5-2}

Each object and each transformation carries a scale profile, written as follows:

SP=&lt;A,X,T,O,C,R,I,N,J&gt;

The nine letters stand, in order, for the nine scale axes. The table below sets out three things for each axis: what the state of the axis mainly sets out; what justifies determining that the target end “expands” relative to the source end on that axis; and what cannot substitute for that axis.

| Scale Axis | What the State Mainly Sets Out | Basis for Determining “Expands” | Limits on Substitution |
| --- | --- | --- | --- |
| Aggregation Level (A) | Units, membership set, partition, aggregation rule, weights, and exclusions | The target population covers the source population, and the target partition is a coarsening of the source partition, a coarsening that has been stated | Organizational level, spatial extent, scope of influence, or scope of authorization must not substitute for it |
| Spatial Extent (X) | Coordinate system, spatial set, boundary channels, and external connections | Once the coordinates are aligned, the source space is a proper subset of the target space | Aggregation level, organizational level, scope of influence, or scope of authorization must not substitute for it |
| Time Span (T) | Time reference, window role, start and end points, and time-lag model | With the same time reference and the same window role, the target interval properly contains the source interval | A current cross-section and a long-term path cannot substitute for each other |
| Organizational Level (O) | Organizational graph and its version, nodes, containment edges, interfaces, and overlaps | In the same version of the organizational graph (a directed acyclic graph), the target node covers the ancestor closure of the source node | A higher position in the organization does not amount to an expansion of the scope of authorization |
| Causal Level (C) | Causal model, variables, edges, intervention semantics, and abstraction mapping | The target model covers the source model through a semantics-preserving mapping and adds distinguishable levels | Level labels, temporal order, and correlation cannot substitute for a causal bridge |
| Observation Resolution (R) | Measurement protocol, distinguishable classes, parameters, error, and protective omission | The target protocol preserves every distinction in the source protocol and subdivides at least one class | High resolution does not imply completeness or authority to act |
| Scope of Influence (I) | Outcome, threshold, window, affected positions, and effect order | After alignment, the set of affected positions at the target end properly contains the set at the source end | Neither influence nor observation amounts to authorization |
| Network Topology Scope (N) | Graph and its version, nodes, edges, semantics, and sampling boundary | A semantics-preserving graph embedding exists, and the target graph covers the source graph | Network centrality alone does not identify a center of responsibility |
| Scope of Jurisdiction and Authorization (J) | A set of itemized authorizations, each setting down its source, subject, single object, single action, geographic area, validity period, withdrawal conditions, whether it is valid, and evidence | Once authorizations written differently but identical in content are merged, the valid itemized authorizations at the target end properly contain those at the source end, and each added authorization has an independent basis for its validity | No other axis can substitute for it. Pairing every object in a batch with every action in a batch (taking a Cartesian product) and treating the result as authorization is prohibited |

On each axis, the relation between source and target can take only five values: equal, expands, narrows, incomparable, and unknown. Every comparison must keep the states at the source end and the target end, the rule used and its version, the actual mappings or set differences, information loss, and uncertainty, so that others can review it. When the two states are identical, the relation must not be recorded as “expands” or “narrows.” On the same axis, “narrows” is the inverse of “expands.” The basis for a nontrivial relation must come from an actual comparison in the relevant domain. The record cannot acquire it by claiming itself “valid.” Without a basis that can be reviewed, the relation on that axis remains “unknown.”

All nine axes need to be accounted for, but this does not mean that all nine apply to every object. If an entire axis genuinely does not apply, mark it “not applicable” and state the reason, rather than deleting the axis. A typical example is a natural process with neither an acting subject nor anything that could count as authorization. The axis of jurisdiction and authorization does not apply to that process, which differs from “having an empty set of authorizations.” If the axis is inapplicable at both the source and target ends under the same applicability criterion, it may be marked “equal,” with an explanation in the basis. If it is inapplicable at one end and applicable at the other, the range of meaning of the axis has changed, and the relation should be marked “incomparable.” If the material is insufficient, it remains “unknown.” This keeps the framework of the nine axes stable and avoids forcing the meanings of human institutions onto the world broadly conceived.

Comparison between states on each axis must satisfy reflexivity, antisymmetry, and transitivity. The difficulty lies in cases that are “almost equal.” Suppose two states count as equal whenever they differ by less than some threshold. A first state may then count as equal to a second, and the second to a third, while the first and the third already differ by more than the threshold, and transitivity breaks (§4.19 makes the same point about error tolerance). To avoid this, first use the stated rule for deciding equality to sort axis states into equivalence classes. The partial order is then defined on the quotient set formed by those classes, not directly on the raw states. A tolerance can work in only one way: a pre-registered classification rule shared by both ends, or fixed binning, places the states at both ends in the same equivalence class. A rule that directly declares two arbitrary points equal when their “distance is below the threshold” must not be used. On this basis, reflexivity means that a classified state is equal to itself. Antisymmetry means that when each end is no greater than the other, both can only fall in the same equivalence class. Transitivity holds only when the intermediate state, the versions used, and the basis for each segment can be joined up. Any break in the mappings, coordinates, graph versions, variables, or authorization chain returns the relation to “unknown.”

The primary quantity compared on an axis does not suffice by itself. If the state of the axis also includes auxiliary content such as boundary channels, time-lag models, interfaces, error models, intervention semantics, or protective omissions, then determining “expands” also requires semantics-preserving mappings between these auxiliary contents that can be joined up. If the primary extent increases but the meanings of the auxiliary content conflict and no mapping can be found, the relation can only be recorded as “incomparable” or “unknown.” This keeps a “wider extent” from quietly passing as a “higher state on the entire axis.”

</div>

<SectionLesson section="5.2" />

<div v-pre class="theory-source">


## 5.3 Product Partial Order and Transformation Classification {#section-5-3}

Combining the relations on the nine axes gives the product partial order between two scale profiles: SP0≼SP1 if and only if the relations on all nine axes are “equal” or “expands.” The strict relation SP0≺SP1 additionally requires at least one axis to be “expands.” The class of a transformation is decided in the following order, and the transformation falls into the class of the first rule it meets:

If any axis is “incomparable,” classify the transformation as “horizontal or incomparable.” A known “incomparable” is not overridden by an “unknown” on another axis.

Otherwise, if both “expands” and “narrows” occur, classify it as “mixed.” Two known relations in opposite directions already rule out ordering under the product partial order, even if some axes remain “unknown.”

Otherwise, if any axis is “unknown,” classify it as “unresolved.”

If all nine axes are “equal,” classify it as “identical.”

If all axes are “equal” or “expands,” with at least one “expands,” classify it as “scale elevation.”

If all axes are “equal” or “narrows,” with at least one “narrows,” classify it as “scale reduction.”

Thus, macro-level aggregation that also lowers observation resolution is typically “mixed” and should not be called elevation across the board. Analogies between domains are often “horizontal or incomparable.” With insufficient material, the classification is “unresolved.” Only a transformation classified as “scale elevation” may be called by that name. An increase in the scope of observation, space, organization, influence, or network leaves the scope of authorization unchanged. The relation for the scope of authorization can be determined as “expands” only when new, valid itemized authorizations appear.

The state of the scope of authorization does not list “one source, a set of subjects, a set of objects, and a set of actions” separately and then put them together, because that would generate object–action combinations that had never been authorized. Authorization needs to be stated item by item. Each itemized authorization corresponds to exactly one source, one decision-making subject, one object, and one action, and also states the geographic area, validity period, withdrawal conditions, evidence, and independent review. Where several objects or several actions are involved, they must be split into several items. Only currently valid itemized authorizations enter the comparison, and items written differently but identical in content count as one. To determine that the scope of authorization expands, every authorization added at the target end and absent from the source end needs to be listed in full, together with its own independent evidence of validity, and the list needs to agree with what this transformation states about authorization. Arbitrary strings of text, the number of an authorization, a claim to hold authorization, actual control over the object, observation coverage, increased influence, a higher position in the organization, and expansions on other axes cannot change the relation for the scope of authorization to “expands.”

</div>

<SectionLesson section="5.3" />

<div v-pre class="theory-source">


## 5.4 Outcome Statuses of Transformations and the Null-Conclusion Criterion {#section-5-4}

An evaluation assesses one transformation, one branch of that transformation, and one mode of claim. Specifically, it first names which of the nine transformations is being evaluated; there must be one, and only one. It then selects one of the branches within that transformation (for examples of branches, see §5.5.2, §5.5.5, and §5.5.7). Finally, it states which mode of claim this evaluation takes: descriptive mapping, empirical test (that is, a formal test of one of the four empirical questions), causal bridge, object conversion, or intervention conversion. Which modes of claim each branch allows is laid down in advance. The transformation, the branch, and the mode of claim must be compatible with one another and must be fixed before the results are seen. If the positive criterion is not met, the branch must not be switched, and the evaluation must not fall back to descriptive mapping, whose requirements are looser. Material under one mode of claim must not be used to rescue another mode either.

If an actual process involves several transformations, it must be broken into a chain of steps, each containing only one transformation. The target object and target scale of each step need to align with the source object and source scale of the next step. Each step gives its own outcome status, evidence, loss, and error. A single overall result cannot close the individual steps.

All nine transformations use the same four outcome statuses:

Supported: the bridge, decision rule, and positive threshold of the branch selected this time have all been pre-registered and have all been met. Only a branch that belongs to an empirical test, a causal bridge, object conversion, or intervention conversion must have a formal test, a preselected subtype, and a single success criterion. A purely descriptive branch may mark these items, which belong only to empirical tests, “not applicable.”

Not supported or unresolved: bridging is insufficient, or the positive criterion has not been met and the null-conclusion criterion has not been met either.

Null conclusion supported: a null conclusion of limited scope is supported only when the pre-registered null-conclusion rule, the equivalence or sufficiency test, statistical power or sensitivity, and the tolerance all pass.

Not yet evaluated: the transformation or the relevant branch has not yet been carried out. A branch that has been carried out and has established its descriptive bridge can be “supported.” It must not be downgraded to “not yet evaluated” merely because it requires no formal test.

“The result was not statistically significant,” “the outcome appeared unchanged after cutting the link,” “the effect disappeared,” “the simple model performed comparably,” and “the evidence at the target end was insufficient” do not by themselves warrant “null conclusion supported.” This discipline applies to all nine scale transformations, not only to cross-layer causation.

</div>

<SectionLesson section="5.4" />

<div v-pre class="theory-source">


## 5.5 The Nine Scale Transformations {#section-5-5}

The nine transformations differ in meaning, and each one below is first summed up in a sentence that gives its distinct meaning. The sentence for aggregation must not be copied and passed off as the meaning of another transformation.

</div>

<SectionLesson section="5.5" />

<div v-pre class="theory-source">


### 5.5.1 Aggregation (M01) {#section-5-5-1}

Aggregation is summed up as “unit-to-population partition aggregation.” Its bridge needs to cover at least five items: a mapping for each unit, membership and exclusions, the handling of weights and missingness, alternative aggregation rules, and heterogeneity. The information lost in aggregation includes distribution tails, order, covariances, local temporal sequences, and the visibility of minority positions. The aggregation fails if any of the following occurs: the aggregate cannot be recomputed under the stated rules; a reasonable alternative rule reverses the direction; or an aggregate association is imputed back to individuals as an attribute. Even when aggregation is supported, the aggregate result must not be used to take direct action concerning members.

An aggregation comparison first fixes the estimand. Average improvement among a region’s current residents and improvement in a fixed cohort of pre-disaster residents are two different questions. People who moved away, died, could not attend, or did not apply must not be silently assigned “zero need.” Where needed, show the fixed cohort, the current cross-section, entrants, and those who exit side by side. A crude rate and a standardized rate can both be correct. Only if the two are claimed to answer the same question but disagree should one examine further whether the measurement definitions, selection, or inference went wrong. 〔Studies 03.04–03.05, 22.07, 24.01, 29.04, 31.04〕

</div>

<SectionLesson section="5.5.1" />

<div v-pre class="theory-source">


### 5.5.2 Nesting (M02) {#section-5-5-2}

Nesting is summed up as “boundary–membership embedding.” It must be treated along two separate routes.

Descriptive nesting tests only the mappings of boundaries, membership, overlap, exit, and interfaces. It can hold without any cross-layer causation.

Cross-layer causation must have a specified channel, a comparison suited to the claim, and temporal order. Evidence of empirical effects is obtained through a channel-effect test (§4.4) and under the conditions for causal claims (§2.4). The cross-scale mapping is checked separately against the definition of scale transformation (§3.4) and the epistemic constraint “Testing Cross-Scale Transfer” (§4.8.5). A corresponding scale-closure test (§4.6) is needed only for a further claim of scale closure failure, object conversion, or intervention conversion. A positive result from a scale-closure test is not a necessary condition for every case of cross-layer causation.

The absence of a conditional increment after controlling for the current state and the common environment does not by itself establish “no cross-layer effect.” A null conclusion of limited scope may be determined only if the three criteria of equivalence or sufficiency, statistical power or sensitivity, and tolerance all pass. Descriptive nesting creates no higher-level priority or lower-level obligation, and it does not expand the scope of authorization.

An account of a nesting must select one of four branches: descriptive nesting, cross-layer causation, object conversion, or intervention conversion. The four branches correspond respectively to four modes of claim: descriptive mapping, causal bridge, object conversion, and intervention conversion. Boundary material used for descriptive nesting must not be used to support the other three branches.

</div>

<SectionLesson section="5.5.2" />

<div v-pre class="theory-source">


### 5.5.3 Network Propagation (M03) {#section-5-5-3}

Network propagation is summed up as “transmission along paths with timing.” The nodes, edges, directions, weights, capacity, sampling boundary, candidate and alternative paths, delay, and loss must be stated. Connection or synchronization only proposes candidates. If the outcome is unchanged after the path is cut and the null-conclusion criterion has not been met, the status remains “not supported or unresolved.” Network sampling can miss weak edges, positions outside the network, and bridges that connect different networks. Retaining only the impacts at endpoints cannot recover the order of propagation either. Centrality does not amount to intent, responsibility, or authority to act.

Observe tie strength, bridge position, centrality, and mobilizable resources separately. Four contacts can come from four institutions yet share the same information source. An acquaintance can also offer an actual referral that others are unwilling to make. Network position helps locate channels. Their capacity, cost, substitutability, and arrival time determine whether they are actually usable for the specified task. Testing for multiple sources of social support differs from testing for independence among sources of factual information. 〔Studies 26.01–26.02〕

</div>

<SectionLesson section="5.5.3" />

<div v-pre class="theory-source">


### 5.5.4 Accumulation Over Time (M04) {#section-5-5-4}

Accumulation over time is summed up as “longitudinal composition within a window.” The time reference, baseline, window, time lag, threshold for durability, and the rules for accumulation, decay, and recovery must all be fixed in advance. Comparisons also need to be made with common trends, seasonality, cohorts, and alternative windows. An effect that disappears after controls are applied or changes with the window indicates only insufficient positive support. A finding of “no accumulation” must not be declared unless the null-conclusion criterion is met. Basic temporal composition does not establish a historical increment (§4.5) in advance. It is linked to a historical-increment test only if history still provides a conditional increment after controlling for the current state.

</div>

<SectionLesson section="5.5.4" />

<div v-pre class="theory-source">


### 5.5.5 Institutionalization (M05) {#section-5-5-5}

Institutionalization is summed up as “durable institutional write-back.” Write-back means that feedback changes rules, records, resources, or roles, and the change is actually carried out. Institutionalization involves five judgments that need to be kept apart. The first is whether the institution exists in fact. The others are whether it is legally valid, whether it is normatively justified, whether protection is in place, and whether it should continue. Durable changes in records, roles, resources, decision rules, or subsequent transitions can support the fact of institutionalization. Invalid authorization, inadequate participation, failed protection mechanisms, or a lack of arrangements for appeal, anti-retaliation, and restoration are governance failures, normative disputes, and grounds for downgrading action. They cannot erase the fact that the institution already exists. Conversely, its existence does not establish its legal validity, normative justification, adequacy of protection, or warrant for continuation.

An account of an institutionalization can only choose among four branches: institutional fact, causal effect of the institution, institutional object conversion, and institutional intervention conversion. None of these five items, namely a review of legal validity, governance quality, normative justification, adequacy of protection, and whether to continue, can pass itself off as a positive or null conclusion of the “institutional fact” branch.

</div>

<SectionLesson section="5.5.5" />

<div v-pre class="theory-source">


### 5.5.6 Emergence (M06) {#section-5-5-6}

Emergence is summed up as “interaction generates a pattern at the target scale.” The source units, interaction rules, target object, and target pattern must be compared with a pre-registered simple additive model using the same metric. Comparable performance by the simple additive model supports “additivity is sufficient” only if the three criteria of sufficiency or equivalence, statistical power or sensitivity, and tolerance all pass. Otherwise, the result remains unresolved. A unique micro-level cause cannot be inferred from the macro-level pattern, which does not by itself establish downward causation. A claim of downward constraint must have a specified channel, causal evidence suited to the claim, and a mapping that meets the definition of scale transformation (§3.4) and the epistemic constraint “Testing Cross-Scale Transfer” (§4.8.5). Additional claims about scale closure, or about object conversion or intervention conversion, require separate evidence from a scale-closure test (§4.6).

</div>

<SectionLesson section="5.5.6" />

<div v-pre class="theory-source">


### 5.5.7 Delegation or Representation (M07) {#section-5-5-7}

Delegation or representation is summed up as “classification of facts about representation and optional transfer of authorization.” Five things must be recorded separately: the claim to represent; the fact of acts actually carried out on another’s behalf; contested or self-appointed representation; valid delegation; and the transfer of authority within the scope of authorization. Even without authorization, the acts actually carried out, their impacts, and the associated responsibility may still be recorded, but an expansion of the scope of authorization must not be determined. Invalid authorization triggers a stop or a downgrade. It cannot erase the acts already performed or their consequences. Being in the majority, high visibility, influence, a self-proclaimed claim to represent, or actual control does not amount to valid delegation.

An account of a delegation or representation must select one of four branches: claim to represent, acts actually carried out on another’s behalf, validity of the delegation, or transfer of authority. Even if one of the first three branches is supported, it does not change the scope of authorization. The scope of authorization may be determined to expand only if the transfer-of-authority branch, the itemized authorizations, the independent evidence of validity, and what this transformation states about authorization all pass.

</div>

<SectionLesson section="5.5.7" />

<div v-pre class="theory-source">


### 5.5.8 Compression or Abstraction (M08) {#section-5-5-8}

Compression or abstraction is summed up as “many-to-one representational compression.” The source material, algorithm, threshold, version used, error, irrecoverable information, and invariants required for the task must all be traceable. The four statuses “unknown,” “not applicable,” “unobservable,” and “withheld for protection” must be kept distinct, and none of them can be compressed into “absent.” A representation with material task-relevant losses for a proposed high-impact action must not be used to support that action.

Compression can be illustrated by a precise condition for task sufficiency. Let x be the source state, z=f(x) its representation, and q(x) the answer currently required. There exists a function g such that q=g∘f if and only if f(x₁)=f(x₂) always implies q(x₁)=q(x₂). The condition shows that the original state may be irrecoverable even when the current question can still be answered exactly. It gives no guarantee that g is easy to compute or that the representation remains sufficient for a different question, environment, or intervention. 〔Studies 05.01–05.02, 05.05–05.06, formal illustration here〕

Consider a finite, nonempty state domain and a real-valued target q. If the decoder can output any real number and loss is measured by the worst-case absolute error over the whole domain, the minimum recovery error from the representation is exactly half the largest oscillation of the target within a preimage. A preimage here means all the source states mapped to the same representation. Let `a_z` and `b_z` denote the minimum and maximum target values in each nonempty preimage. The optimal error is (1/2)max&#95;z(b&#95;z−a&#95;z), attained by outputting the midpoint for each preimage. Given a tolerance ε, there exists a decoder with error at most ε if and only if the oscillation within each preimage is at most 2ε. The formula cannot be applied directly to vector or integer outputs, average loss, or an unknown distribution.

Successive conversions must preserve the same final question. Let f:X→Z and h:Z→W, and let the first stage be sufficient for the final target q, that is, q=g∘f. The final representation h∘f remains sufficient if and only if g is constant on every preimage under h restricted to the actual image f(X). Unreachable intermediate values need not be constrained. Nor can the completion of a different local task at the second stage close the original final question. See Appendix C.6–C.7 for the condition and its proof.

</div>

<SectionLesson section="5.5.8" />

<div v-pre class="theory-source">


### 5.5.9 Horizontal Transfer (M09) {#section-5-5-9}

Horizontal transfer is summed up as “analogical transfer across domains.” The mappings, differences, discontinuities, prohibited mappings, the chain of responsibility at the target end, and differences in the scope of authorization must be stated. Material from the source domain only proposes candidates at the target end. Both “supported” and “null conclusion supported” must come from independent tests at the target end. If the evidence at the target end is insufficient, the status is “not yet evaluated” or “not supported or unresolved.” This insufficiency does not establish the absence of the target mechanism. An analogy creates no authorization to act in the target domain.

</div>

<SectionLesson section="5.5.9" />

<div v-pre class="theory-source">


## 5.6 Limits of Basic Structural Concepts Across Scales {#section-5-6}

The eleven basic structural concepts are definitions. They carry no empirical null models or falsification templates of their own. Four limits in particular must be held.

“Feedback and State Updating” (§3.5.7). Basic feedback requires only a return channel and a subsequent state update. It does not require a historical-increment test. A claim that feedback has mediated learning must also have corresponding evidence of an update carrier, retention across rounds, actual use, and task outcomes. A historical-increment test is added only when the claim is a historical conditional increment beyond the current representation (see §4.5 and §6.3).

“Load, Capacity, and Recovery Margin” (§3.5.9). An instantaneous demand–capacity gap does not require a historical-increment test. Cumulative damage or delayed recovery must be checked separately against the current carrier of damage or capacity, how that carrier formed, and subsequent recovery. A historical-increment test applies only when a further claim is made about a historical increment beyond the current representation.

“Trace, Memory, and Paths” (§3.5.10). This concept only records candidate traces, their carriers, and their retention windows. It does not establish path dependence in advance. That history still provides a conditional increment after controlling for the current state must still be shown by a historical-increment test.

“Phase, Transition, and Dissolution” (§3.5.11). The basic phase pattern requires neither a historical-increment test nor a scale-closure test. Causal triggering takes a separate channel-effect test. Continuation or delayed recovery sustained by the current carrier takes evidence under §4.5. Historical-increment hysteresis beyond the current representation takes a separate historical-increment test. A claim of tested object conversion takes a separate scale-closure test.

Likewise, the concept “Candidate Object” (§3.5.1) only records candidate objects and does not guarantee grouping gain in advance. The definition of “Relations and Constraints” (§3.5.5) does not establish causation. The descriptions of channels within “Flow, Channels, and Transmission” (§3.5.6) do not establish a channel effect.

</div>

<SectionLesson section="5.6" />

<div v-pre class="theory-source">


## 5.7 Unified Scale Transformation Record {#section-5-7}

A scale transformation record is a complete account of one scale transformation. It covers fourteen aspects. Every aspect and every item within it must appear and must not be omitted.

Identity and purpose: which transformation the record concerns, which concept it addresses, which propositions it involves, and what it is for; and which version of the record this is.

Scale: the scale profiles of the source scale and the target scale; the differences on each of the nine axes; which axes are unchanged; the class into which this transformation falls (§5.3); and the state of the scope of authorization, stated as itemized authorizations.

Objects: the effective objects at the source end and the target end; the identity criterion at each end; the identity mapping between the objects at the two ends; and units, population, boundaries, members, and exclusions.

Semantics: the core content that stays the same; the content allowed to change; the content lost; and prohibited mappings.

Transformation: which transformation is evaluated (only one), the selected branch, and the mode of claim (§5.4); the conversion rule; the causal bridge; the time lag; the mapping error; the validity period; the formal test relied on, together with the preselected subtype and success criterion; the positive decision rule and the null-conclusion rule; the positive threshold; the equivalence or sufficiency test; statistical power or sensitivity; the tolerance; and the outcome status.

Variables: inputs, states, outputs, and dependencies between variables.

Evidence: the evidence at the source end and the target end; coverage; heterogeneity; counterexamples; absence signals; alternative explanations; residual tests; and replication or external validation.

Loss: compressed details; irrecoverable information; positions with low visibility; and local exclusion zones.

Responsibility: actors, decision makers, authorizing parties, uptake carriers, responsible parties, beneficiaries, and cost bearers.

Norms: value premises; the type of choice (§14.2); the normative choice record; the normative premises actually adopted this time; the source of authorization; the check under the conclusion rule “Normative Bridging” (§4.14.1); and the four-step operational procedure (§14.6).

Protection: whether protection applies; low-power positions; safe channels for submission; and anti-retaliation.

Action: the judgment ceiling; the action ceiling; prohibited actions; stopping conditions; the responsible person; and the selected action, stated specifically enough to be matched item by item against the approved option.

Correction: appeal, review, restoration, repair, and write-back.

Duration and exit: validity period, review points, suspension, and exit.

Whether the object is preserved, converted, or incomparable across the transformation is determined jointly by three things: the identity criterion at the source end, the identity criterion at the target end, and the identity mapping between the objects at the two ends. A shared name supplies no evidence of identity. An account of the identity mapping must keep all of the following: the main points of each of the two identity criteria; the results of the four checks, that is, whether the source object passes under the source criterion, the source object under the target criterion, the target object under the source criterion, and the target object under the target criterion; the forward and reverse mappings; which criteria were preserved and which were violated; the basis showing that these criteria were pre-registered and finalized before the results were seen; and validation materials that can be reviewed. Each check has only three possible results: passed, failed, and undetermined. A blanket “yes” or “no” must not cover up which check did not pass.

| Identity Classification | Minimum Conditions | Ceiling on Conclusions |
| --- | --- | --- |
| Same object | The mappings are valid in both directions. All four checks pass. Some criteria are preserved, and none is violated | The object’s identity may be retained within the current definition. This does not imply that its semantic, causal, or normative properties are also preserved |
| Object converted | The source object passes under the source criterion, the target object passes under the target criterion, and the target object fails under the source criterion. Which items are violated, and what was pre-registered before the results were seen, are both stated specifically. In addition, the mode of claim is object conversion, and there is a supported scale-closure test of the subtype for object or intervention conversion (§4.6) | Only an object conversion under the pre-registered identity criteria can be determined. The identity criteria must not be rewritten after the results are seen to manufacture a conversion |
| Incomparable | Each object passes under the criterion of its own end, and at least one cross check (the object at one end under the criterion of the other end) fails. The forward and reverse mappings both keep a complete record of attempts, at least one of which has been shown invalid, with evidence that corresponds to real material | Records that the two ends are known to be incomparable. The outcome status can only be “not supported or unresolved,” not “not yet evaluated” |
| Undetermined | The necessary mappings, criteria, or evidence are still insufficient to complete the classification. Each of the four checks keeps its known “passed” or “failed” result or its still uncertain “undetermined” result, and the check that blocks the overall judgment is identified | The outcome status can only be “not supported or unresolved” or “not yet evaluated.” The known parts are not cleared, and an overall “undetermined” is not taken to imply “incomparable” or “object converted” |

A determination of object identity must be open to independent recomputation or review by others. The same object under the same criteria can be checked directly. Any other preservation or conversion must retain the objects at both ends, both identity criteria, the direction of the mapping, the results of the four checks, and the supporting materials. A name, a number, a claim of being “valid,” or a mark that identifies material without touching its meaning cannot substitute for this check of meaning.

When the mode of claim is object conversion, the identity classification must agree with the four outcome statuses. Only “supported” corresponds to “object converted.” “Null conclusion supported” corresponds to “same object” when the three null-conclusion criteria (equivalence or sufficiency, statistical power or sensitivity, and tolerance) are all met. “Not supported or unresolved” permits only preservation of the object, a known “incomparable,” or “undetermined.” When the object conversion test has not yet been carried out, the overall classification remains “undetermined,” and any results already checked independently are retained. Neither the absence of a test nor a failed test can therefore justify recording the target in advance as “already converted.” Other modes of claim must not also report “object converted” in the same step. Object conversion must be split off and tested on its own as a separate step.

When the mode of claim is empirical test, causal bridge, object conversion, or intervention conversion, the formal test relied on must be named. The last three must also give a causal bridge, which must not be left empty. Only descriptive mapping may mark the formal test, subtype, and success criterion “not applicable.” For a mode of claim other than descriptive mapping to determine “supported” or “null conclusion supported,” the formal test relied on must also correspond to a real record, and the following must be checked item by item: which test it is, which of the four empirical questions it belongs to, which version of the pre-registration applies, what the preselected subtype and single success criterion are, and what status the test itself is in. A name or number that merely looks correctly formatted cannot stand in for a test. A descriptive bridge may be recorded as “supported” if it meets the positive criterion. Record “not yet evaluated” only when the selected mode of claim has not yet been carried out.

The fourteen aspects form a stable framework; they do not project the meanings of human governance onto every object. Whether protection applies must be stated explicitly, with the object type, downstream use, rationale, and evidence. It must not be inferred from the fact that a list such as the list of actors is empty. An object may be nonhuman, with its use limited to two kinds: description only, or a nonhuman intervention shown by evidence to have no effect on humans or sentient beings. In that case, the two items of safe submission and anti-retaliation may be marked “not applicable,” with reasons stated. Real-world experimental or engineering interventions, however, still have an acting subject and an object. The specific authorization, the person responsible for the action, and the arrangements for stopping, review, and restoration must be stated. Only purely descriptive use allows the axis of jurisdiction and authorization to be inapplicable. Energy, matter, or computational resources in a natural system do not by themselves trigger these requirements for protecting people. When the object is human, sentient nonhuman, mixed, or unknown, or the use concerns the evaluation of people, the allocation of their scarce resources, their rights, their exposure to risk, or real-world action involving them, the items of protection immediately become content that must be accounted for. An earlier “not applicable” must not carry over. Where the object is a sentient nonhuman, see §14.8 for how each item is put into effect. The inapplicability of protection never implies that action is justified. Normative choice still requires a separate judgment.

The person responsible for the action specifies only who is responsible for carrying out or stopping it. Having such a person provides no basis for inferring that the mode of claim is intervention conversion, nor does it establish that the action is effective or justified. Every external action must correspond to a normative choice record (see Part 14) and disclose its value premises and the normative premises actually adopted this time. The normative premise “Explanation Does Not Confer Authority to Act” (§14.3) can by itself only block actions that exceed authorization. It cannot generate an affirmative option. The feasible options in the choice record are not a list of names but options whose content is set down. For each option, its kind, action type, target object, geographic area, validity period, reversibility, expected impacts, and distributional impacts are fixed in advance, and the options explicitly include one no-action option. The selected action must correspond to one of the external-action options and must match it item by item on action, object, geographic area, and validity period. All three of the following must be rejected: pointing in fact to the no-action option while using it as the basis for an external action; matching only the name in words while the content does not match item by item; and rewriting both the action and the authorization while the approved option remains unchanged. There must also be at least one currently valid, independently reviewed itemized authorization that covers this subject, object, action, geographic area, and period together and agrees with the stated source of authorization. An authorization unrelated to this action cannot back the proposed action, even if it is formally valid. The record must also have the following: the ten components that “Normative Bridging” requires, all of them passed; the records of each step of the four-step operational procedure; the person responsible for the action; prohibited actions; and the arrangements for stopping, protection, appeal, review, and restoration. If any item is missing, the action ceiling can only be taking no action or continuing deliberation. Whether an intervention conversion has occurred empirically is judged separately by the relevant formal test.

Joining several transformation steps one after another only sets the order of composition. Support gained at one step does not automatically carry to the next. Checking such a chain must ensure that each step has its own separate record, not confused with other steps; that each step contains only one transformation; that the objects and identity criteria referred to by adjacent steps are compatible; and that the target scale of each step matches the source scale of the next. If any step is unresolved, becomes invalid, or exceeds its loss limit, this must be retained in the conclusion for the whole chain. Success at the final step cannot override it.

Evaluation of the whole chain must also state whether the final task is consistent with the tasks at the individual steps and whether shared resources have been committed more than once. Two tasks can each be feasible with one unit of capacity and yet be impossible to complete together if they share that unit in the same period. If time limits, resources, or permitted strategies are legitimately changed, the new joint option should be evaluated. Representational sufficiency, joint causal response, and joint resource feasibility each have their own criteria. Passing one cannot substitute for passing the other two.

</div>

<SectionLesson section="5.7" />

<div v-pre class="theory-source">


## 5.8 Consistency Checks and the Protection Floor {#section-5-8}

A consistency check deals only with formal matters: whether the items, references, versions, and outcome statuses are consistent with one another, and whether the recorded axis relations have been combined correctly. It cannot replace the judgments that substantive comparisons in each domain make about geometry, organizational graphs, causal abstraction, network embedding, object identity, or authorization validity. Without substantive comparisons and independent materials about the objects, a complete record or algorithmic output cannot justify determining scale elevation. A record may take any form, but it must meet the same requirements for traceability and review.

The four missingness statuses form a closed set, to which nothing else is added. “Unknown” means that it is not yet known. “Not applicable” means that it genuinely does not apply under the definition. “Unobservable” means that materials cannot be obtained under current conditions (§2.9). “Withheld for protection” means that it is not disclosed in order to protect. None of the four means “absent,” and deleting the item cannot substitute for marking its status.

Uptake carriers and responsible parties must be written down separately. Taking something up, being visible, being affected, or having greater capability does not by itself create responsibility. Whenever there is an effect on the rights of humans or sentient subjects, on the allocation of their scarce resources, on their exposure to risk, or on how they are treated in practice, the protection floor (§14.8) must identify low-power positions and local exclusion zones. It must provide arrangements for safe submission, anti-retaliation, stopping, appeal, review, and restoration. In these cases, it must not be marked “not applicable.” Insufficient protection lowers both the judgment ceiling and the action ceiling. A purely descriptive record may, under certain conditions, mark protection “not applicable,” but downstream actions cannot carry over that inapplicability. Once the use changes, the protection review must be reopened.

</div>

<SectionLesson section="5.8" />

<div v-pre class="theory-source">


## 5.9 Evidence Boundaries and Independent Support {#section-5-9}

The names, numbers, summaries of meaning, and classifications of the nine scale transformations specify only how a transformation should be described and tested. They provide no empirical support that the transformation occurred, the mapping is valid, or the target property holds. Concept labels internal to the framework, examples, how completely the items are filled in, and results reported by the algorithm itself must not serve as evidence at the source end or the target end in place of materials about the objects.

Every actual transformation must obtain independent, verifiable materials separately for the source object and the target object. It must state the mapping, what is preserved, changed, or lost, the error, and the competing explanations, and it is judged in the same way by the four outcome statuses, the positive criterion, and the null-conclusion criterion. Source-domain materials can only propose candidates for the target end. Without independent support at the target end, the conclusion remains “a mapping awaiting testing” or “unknown.”

</div>

<SectionLesson section="5.9" />

<div v-pre class="theory-source">


## 5.10 Cross-Circle Relation Transformation {#section-5-10}

Scale transformation and cross-circle relation transformation must be kept separate. Scale transformation asks which variables are preserved, changed, or lost for the same question between the source scale and the target scale. Cross-circle relation transformation asks how two or more candidate circles[^tn-circle-06] stand in parallel, contain one another, overlap, bridge, compete, or form temporarily at the same or different scales. A change in relations may accompany a change in scale. Neither term can stand in for the account of the other.

An account of a cross-circle relation needs to set out, at minimum, the source of the relation, its target, the type of static relation, whether membership or interfaces serve as the basis, direction, channel, delay, threshold, time window, evidence, and counterexamples. It also sets out before-and-after snapshots. “Transformed” is used only for the outcome of a relation update. A formerly parallel relation may become bridged when a bridging party appears. An overlapping relation may become nested through institutional integration, and a temporary circle may become institutionalized or undergo dissolution. Each such transformation needs a check of whether the identity criterion is preserved. If the identity criterion no longer holds, record an object conversion or a dissolution (§6.10). A new name must not be used to carry the old object forward.

| Question to Answer | What to Use | Distinctions to Preserve |
| --- | --- | --- |
| Can an individual’s state represent a team? | Aggregation (§5.5.1), the account of the scale transformation, and distributional loss | Team membership alone does not make a member’s state representative of the team |
| Is a team contained within an organization? | Nesting (§5.5.2) and a specific basis for containment | Having a superior in common does not imply membership containment |
| Are two circles associated because they share members? | The overlap relation, membership mappings, and the common environment | Overlap does not by itself produce effective feedback |
| Does a bridging party change another circle? | Network propagation (§5.5.3), a channel, and a counterfactual | Contact does not amount to transmission. Transmission does not amount to representation |
| Does a temporary group form a durable object? | The identity criterion, longitudinal material about the object, and institutionalization (§5.5.5). A claim of grouping gain takes a separate grouping-gain test, and a claim of a historical conditional increment takes a separate historical-increment test | Traces do not amount to institutionalization. The fact of durability need not depend on an additional historical residual |

When the same actor belongs to several circles, the actor’s distinct roles, visible information, responsibilities, risks, and ability to exit in each circle need to be retained. An actor must not first be merged into a single state that is then copied to every circle. Cross-circle projection should start from local states, propagate through stated membership or interface channels, and record the loss caused by aggregation at each step.

Translation involves both tasks and permissions. Accurately relaying what someone said, helping both sides understand each other, having permission to publish that person’s exact words, and signing an agreement on their behalf are four distinct capabilities or qualifications. The same translation can suffice to book an appointment and may still be insufficient to preserve poetic rhythm or distinctions in legal status. Insufficiency for the latter task does not justify saying retroactively that the former was never completed. The limited translation that succeeds should be retained, and the meanings and rights that did not transfer with it should be stated. 〔Studies 12.10, 26.08–26.09〕

</div>

<SectionLesson section="5.10" />

<div v-pre class="theory-source">


### 5.10.1 Three Kinds of Transformation Must Be Kept Separate {#section-5-10-1}

Scale transformation asks which variables are preserved, changed, or lost for the same question between one scale profile and another. Cross-circle relation transformation asks how parallelism, containment, overlap, bridging, competition, or temporary relations among candidate circles are updated. Representational or discursive recasting (§3.4.1) asks how content with an identified source enters the vocabulary, variables, or expressions of the target task. All three can occur together, but they must be split apart and accounted for separately, in order.

Recasting needs its own account of what it preserves, changes, and loses. It can use the scale transformations “Network Propagation,” “Compression or Abstraction,” and “Horizontal Transfer,” or others (§5.5). Each of these operations has its own account, and they are linked according to their respective inputs, outputs, criteria, and failure conditions. A further transformation must not be counted merely because a name differs, and failures of different operations must not be merged into a single overall status.

</div>

<SectionLesson section="5.10.1" />

<div v-pre class="theory-source">


### 5.10.2 Reviewing Recasting Loss {#section-5-10-2}

If two source states that can be distinguished in the source task cannot be distinguished in the target representation, record a task-relevant loss for that distinction. An identity mapping, reversible encoding, or mapping sufficient for the target task may yield no detected relevant loss. The rule is therefore “do not assume losslessness in advance.” It does not say that a mapping is “necessarily lossy.”

| Review Item | Minimum Question | Distinctions to Preserve |
| --- | --- | --- |
| Preservation | Which facts, relations, modalities, rights, or uncertainties must stay the same? | Preserving a title does not amount to preserving its semantics |
| Change | Which formats, units, levels of granularity, or expressions may change? | Permitting change does not permit arbitrary changes in meaning |
| Collapse | Which differences at the source end are merged at the target end? | Collapsing a difference does not imply that it is absent at the source end |
| Omission | What was left out of the target representation, and why? | Withholding for protection does not amount to absence |
| Addition | Which explanations, inferences, or target variables does the conversion produce? | Adding a variable does not amount to discovering a real-world entity |
| Return | When an anomaly occurs, which parent record (the record one level up from which it directly comes) or which arrangement is revisited? | Returning only reopens review. It does not patch what has already been done |

Round-trip reconstruction, from the target representation back to the source representation, can serve as a test but is insufficient by itself. A conversion may appear to round-trip by using hidden source records while failing to preserve the semantics of the target task. A one-way summary, by contrast, may be sufficient for the specified task. Review must return to the items to preserve that were stated in advance, the tolerances for loss, and the results at the target end.

Whether the target representation retains a needed distinction and whether the actual rule uses it correctly are two separate judgments. An error in acting on the representation does not by itself establish a recasting loss. If the distinction is still discernible but used incorrectly, record the gap in the rule or its execution. Representational loss and execution errors can also coexist. Their grounds should then be stated separately, and other local results that have already been established should be retained.

When both kinds of failure occur, the same unavoidable error should not be counted again as an additional failure of the rule. If the target answer is nonunique within a preimage (the source states mapped to the same target representation), no deterministic rule using only the current representation can answer correctly for all of its source states. This by itself establishes that the representation is insufficient. If the target answer is unique in another nonempty preimage but the actual rule gives the wrong answer, that case alone suffices to show, independently, that the rule is in error. When it is unclear what representation is actually used internally, the original material’s continued public availability does not establish that those implementing the rule had grasped the distinction at the time. The existence of material, timely access to it, and actual use must be checked separately.

</div>

<SectionLesson section="5.10.2" />

<div v-pre class="theory-source">


### 5.10.3 Effective Variables, Closure, and Returning in Response to Residuals {#section-5-10-3}

An effective variable is a candidate variable proposed for a target scale or task in order to compress the state and improve an explanation, foresight[^tn-foresight-06], or comparison of options fixed in advance. Proposing an effective variable must at the same time state the object, scale, time window, and task it addresses, how it is measured, the simple baseline it is compared with, how large its error is, when it fails, and when it is retired. “Effective” does not mean that the variable is a real entity, a root cause, a universally applicable variable, or a basis for authorization.

The target representation carries no presumption of dynamic closure. For static descriptions or questions at the same scale, first check sources, conversion rules, and answers to the task, using the conditional formal propositions “Task Recovery” (§4.18.1) and “Task Preservation through Successive Conversions” (§4.18.4) when necessary. Check formal dynamical models for closure under the conditional formal proposition “Closure under Dynamics and Admissible Interventions” (§4.18.2), and obtain separate evidence for their correspondence to reality. For a descriptive mapping, the items that belong only to empirical tests do not apply and may be marked “not applicable” with reasons. A corresponding scale-closure test, with its positive criterion and null-conclusion criterion, is needed only when seeking formal empirical support under §4.6 for scale closure, object conversion, or intervention conversion. A scale change must not be fabricated to fill in every item. Failure to find a significant increment does not by itself establish closure. When an increment occurs, record the corresponding impact as a candidate for memory, noise, hysteresis, an unresolved term, or a residual. The shape alone must not be used to name a new entity.

The scale transformation record (§5.7) must state the target task under the two aspects “Identity and purpose” and “Semantics.” Under the three aspects “Transformation,” “Evidence,” and “Loss,” it must state which parent representation (the representation one level up from which the new representation directly comes) is used, which differences were collapsed, where to return when an anomaly occurs, the result of the reconstruction test, and the candidate effective variables at the target end. If the relevant information is missing, retain an explicit missingness status. A completely filled-in table must not be taken to establish that all of the source semantics have been preserved.

</div>

<SectionLesson section="5.10.3" />

<div v-pre class="theory-source">


## 5.11 Representing Parallelism and Nesting Together {#section-5-11}

Real-world structures cannot be reduced to a single hierarchical tree. Local containment relations can coexist with lateral networks, membership overlap, competition for resources, and bridging through platforms. They are represented by a directed multigraph of relations. Each node keeps the definition of its own object, and each edge keeps the definition of its own relation. “Higher layer” denotes only a particular relation of containment, jurisdiction, or aggregation. It carries no implication of greater reality, correctness, or authority.

When several circles share an environment but have no direct channel, the model retains a node for the common conditions and must not invent a direct edge between the circles. When a channel is open only within the time window of an event, its edge has a start time and an end time. When different relations run in opposite directions, draw separate edges. This makes it possible to determine after an event which relation actually changed, without redrawing the whole structure as a story told after the fact.

[^tn-circle-06]: Translator's note: Circles may be parallel, nested, overlapping, or bridged.

[^tn-foresight-06]: Translator's note: Foresight in this book requires a registered target, horizon, and baseline, along with calibration.

</div>

<SectionLesson section="5.11" />

<div v-pre class="theory-source">

</div>
