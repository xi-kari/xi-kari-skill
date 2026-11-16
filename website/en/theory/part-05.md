---
title: "Part 5 Cross-Scale and Cross-Circle Transformations"
---

<div v-pre class="theory-source">

<a id="part_5"></a>

# Part 5 Cross-Scale and Cross-Circle Transformations {#part-title-5}

When an object, observation, or action moves from SP0 to SP1, this Part asks what expands, what contracts, which positions are incomparable, what justifies a conversion bridge, and what information the conversion loses. The general process is called scale transformation. The nine axes are compared using a product partial order. The term scale elevation applies only when the relation in that order is strict.

</div>

<SectionLesson section="intro-05-part" />

<div v-pre class="theory-source">


## 5.1 Contract[^tn-contract-06] Roles and Unambiguous References {#section-5-1}

A scale axis is one of nine definitions of kind D with the role `scale_axis_definition`. The nine conversion operators are procedures of kind O with the role `scale_transformation_operator`. U01–U11 are definitions of kind D for universal primitives and have the role `universal_primitive_definition`. Definitions and procedures make no claim to empirical truth. Specific claims of cross-layer causation must link to a pre-registered `root-instance`. The same requirement applies to object conversion. A null conclusion must also link to such an instance.

Always use qualified IDs for scale entities, from `scale_axis:A` to `scale_axis:J`, from `scale_operator:M01` to `scale_operator:M09`, and from `universal_primitive:U01` to `universal_primitive:U11`. The identifier `scale_axis:O` denotes organizational level. The expression `claim_type=O` denotes an operational procedure. The only dependencies are `inferential_requires`, `protocol_requires`, `specializes`, and `applies_to`. Protocols[^tn-protocol-06] use formal IDs such as `CAUSAL`, `EVIDENCE`, `ANALOGY`, and `SOURCE`. They must not use Chinese abbreviations or bare axis names.

</div>

<SectionLesson section="5.1" />

<div v-pre class="theory-source">


## 5.2 Nine-Axis States and Axis-by-Axis Comparison {#section-5-2}

Each object and transformation is bound to the following:

SP=&lt;A,X,T,O,C,R,I,N,J&gt;

| Axis | Core State Fields | Computational Witness for `expands` | Limits on Substitution |
| --- | --- | --- | --- |
| A Aggregation Level | Units, membership set, partition, aggregation rule, weights, and exclusions | The target population covers the source population, and the target partition is a registered coarsening of the source partition | O, X, I, and J must not substitute for A |
| X Spatial Extent | Coordinate system, spatial set, boundary channels, and external connections | Once the coordinates are aligned, the source space is a proper subset of the target space | A, O, I, and J must not substitute for X |
| T Time Span | Time reference, window role, start and end points, and time-lag model | With the same reference and role, the target interval properly contains the source interval | A current cross-section and a long-term path cannot substitute for each other |
| O Organizational Level | Organizational graph, version, nodes, containment edges, interfaces, and overlaps | In the same version of the organizational DAG, the target node covers the ancestor closure of the source node | A higher position in the organization does not amount to an expansion of J |
| C Causal Level | Causal model, variables, edges, intervention semantics, and abstraction mapping | The target model covers the source model through a semantics-preserving mapping and adds distinguishable levels | Level labels, temporal order, and correlation cannot substitute for a causal bridge |
| R Observation Resolution | Measurement protocol, distinguishable classes, parameters, error, and protective omission | The target protocol preserves every distinction in the source protocol and subdivides at least one class | High resolution does not imply completeness or authority to act |
| I Scope of Influence | Outcome, threshold, window, affected positions, and effect order | After alignment, the target set of affected positions properly contains the source set | Neither influence nor observation amounts to authorization |
| N Network Topology Scope | Graph and version, nodes, edges, semantics, and sampling boundary | A semantics-preserving graph embedding exists, and the target graph covers the source graph | Network centrality alone does not identify a center of responsibility |
| J Scope of Jurisdiction and Authorization | Set of atomic authorization tuples, each specifying its source, subject, single object, single action, geographic area, validity period, withdrawal, validity, and evidence | The normalized set of valid target tuples properly contains the source set, and each added tuple has an independent witness to its validity | No other axis can substitute for J. Taking a Cartesian product of the object and action sets is prohibited |

An axis can have only five relations: `equal`, `expands`, `contracts`, `incomparable`, and `unknown`. A comparison must preserve the source and target states, the rule and version used, the actual mappings or set differences, information loss, and uncertainty. It must allow others to review the comparison. Expansion or contraction must not be registered between identical states. On the same axis, `contracts` is the inverse of `expands`. A witness for a nontrivial relation must come from a comparison in the relevant domain. The record cannot supply such a witness by declaring itself “valid.” Without a basis that can be reviewed, the relation remains `unknown`.

All nine axes must be registered. Whether an axis applies depends on the object. If an entire axis genuinely does not apply, use a `not_applicable` object with a reason for the axis state and keep the axis in the record. A typical example is a natural process with neither an acting subject nor a concept of authorization. J does not apply to that process, which differs from having an empty set of authorizations. If the axis is inapplicable on both the source and target sides under the same applicability criterion, the witness may mark it `equal`. If it is inapplicable on one side and applicable on the other, the semantic domain has changed and the relation should be marked `incomparable`. If the material is insufficient, it remains `unknown`. This keeps the nine-axis interface stable and avoids imposing the semantics of human institutions on the world broadly conceived.

Comparison on each axis must satisfy reflexivity, antisymmetry, and transitivity. To keep “almost equal” from breaking transitivity, first use `equality_rule` to normalize axis states into equivalence classes, then define the partial order on the quotient set of those classes. A tolerance may be used only when a pre-registered shared normalizer or fixed binning places both states in the same equivalence class. A rule that directly declares two arbitrary points equal when their “distance is below the threshold” must not be used. Reflexivity requires a normalized state to be `equal` to itself. Antisymmetry requires that if each of two states is less than or equal to the other, both belong to the same equivalence class. Transitivity holds only when the intermediate state, versions, and witnesses can be composed. Any break in the mappings, coordinates, graph versions, variables, or authorization chain returns the relation to `unknown`.

The primary quantity compared on an axis does not suffice by itself. If the axis record includes auxiliary states such as boundary channels, time-lag models, interfaces, error models, intervention semantics, or protective omissions, `expands` also requires composable, semantics-preserving mappings for these fields. If the primary extent increases and the auxiliary semantics conflict with no mapping between them, the relation may only be recorded as `incomparable` or `unknown`. This prevents a “wider extent” from passing as a “higher state on the entire axis.”

</div>

<SectionLesson section="5.2" />

<div v-pre class="theory-source">


## 5.3 Product Partial Order and Transformation Classification {#section-5-3}

SP0≼SP1 if and only if all nine axes are `equal` or `expands`. The strict relation SP0≺SP1 additionally requires at least one axis to be `expands`. The machine applies the classification rules in this order:

If any axis is `incomparable`, classify as `horizontal_or_incomparable`. An `unknown` relation on another axis does not override known incomparability.

Otherwise, if there is both expansion and contraction, classify as `mixed`. Two known relations in opposite directions rule out ordering under the product partial order, even if some axes remain `unknown`.

Otherwise, if any axis is `unknown`, classify as `unresolved`.

If all nine axes are `equal`, classify as `all_equal`.

If all axes are `equal` or `expands`, with at least one expansion, classify as `elevation`.

If all axes are `equal` or `contracts`, with at least one contraction, classify as `reduction`.

Thus, macro-level aggregation that also compresses resolution is typically `mixed` and should not be called elevation across the board. Analogies between domains are often `horizontal_or_incomparable`. With insufficient material, the classification is `unresolved`. Only instances classified as `elevation` may be called “scale elevation.” An increase in the scope of observation, space, organization, influence, or network leaves J unchanged. An expansion of J can be witnessed only by new, valid authorization tuples.

If a J state stored “one source + a set of subjects + a set of objects + a set of actions” as independent fields, it would generate object–action combinations that had never been authorized. The `authorization_tuple_contract` requires each atomic tuple to bind exactly one source, one decision-making subject, one object, and one action and to preserve the geographic area, validity period, withdrawal conditions, evidence, and independent review. Multiple objects or actions must be split into multiple tuples. Only normalized atomic tuples with a valid status enter the set comparison. The witness for J-axis expansion must list, in `comparison_payload`, the complete tuples added on the target side and absent from the source side, along with independent evidence of their validity. It must align with `j_authorization` in the record. Arbitrary strings, tuple IDs, self-assertions, actual control, observation coverage, increased influence, a higher position in the organization, and expansions on other axes cannot make J `expands`.

</div>

<SectionLesson section="5.3" />

<div v-pre class="theory-source">


## 5.4 Operator Outcome Statuses and the Null-Conclusion Check {#section-5-4}

The `operator_ids` of each atomic record must contain exactly one operator. Then `selected_operator_branch` selects exactly one internal branch from that operator’s branch registry. Finally, `claim_mode` declares the mode of this evaluation as `descriptive_mapping` (descriptive mapping), `root_hypothesis` (an instance of a family of empirical questions), `causal` (causal bridge), `object_conversion` (object conversion), or `intervention_conversion` (intervention conversion). The branch registry specifies which modes each branch allows. The three fields must be compatible and must be frozen before the results are read. Failure at the positive-support check must not lead to a switch of branch or a fallback to a looser descriptive mode. Material from one mode must not be used to rescue another. If an actual process contains multiple operators, it must be broken into an ordered chain of atomic records. The target object and SP1 at each step must align with the source object and SP0 at the next step. Each step must register its own outcome status, evidence, loss, and error. A single overall result cannot close the individual steps.

All operator procedures use the same four outcome statuses:

`supported` means the bridge, decision rule, and positive threshold for the selected branch all underwent pre-registration and have all been satisfied. A `root-instance`, a preselected subtype, and a single success criterion are mandatory only for G, causal, object-conversion, and intervention-conversion branches. A purely descriptive branch may mark those G-specific fields `not_applicable`.

`unsupported_or_undecided` means bridging is insufficient, or the positive-support check and the null-conclusion check have both failed to pass.

`null_supported` supports a limited null conclusion only when the pre-registered `null_decision_rule` and the equivalence or sufficiency test both pass. The rule may require statistical power. It may instead require sensitivity. The applicable requirement and the tolerance must also pass.

`not_evaluated` means the operator or the relevant branch has yet to run. A branch that has run and established its descriptive bridge can be `supported`. It must not be downgraded to “not evaluated” merely because it requires no G-instance.

“The result was not statistically significant,” “the outcome appeared unchanged after cutting the link,” “the effect disappeared,” “the simple model performed comparably,” and “the evidence for the target was insufficient” do not by themselves warrant `null_supported`. This rule applies to every operator from M01 to M09, including the ones concerned with cross-layer causation.

</div>

<SectionLesson section="5.4" />

<div v-pre class="theory-source">


## 5.5 The Nine Scale Transformation Operators {#section-5-5}

Each operator has a distinct `semantic_signature`. The aggregation statement for M01 must not be copied and passed off as that of another operator.

</div>

<SectionLesson section="5.5" />

<div v-pre class="theory-source">


### 5.5.1 M01 Aggregation {#section-5-5-1}

The signature is “unit-to-population partition aggregation.” At minimum, the bridge must cover a mapping for each unit, membership and exclusions, weights and missingness, alternative aggregation rules, and heterogeneity. Information loss includes distribution tails, order, covariances, local temporal sequences, and the visibility of minority positions. The procedure fails if the aggregate cannot be reproduced under the registered rules, if a reasonable alternative rule reverses the direction, or if an aggregate association is imputed to individuals as an attribute. Even when aggregation is supported, the aggregate result must not be used to take direct action concerning members.

An aggregation comparison first fixes the estimand. Average improvement among a region’s current residents and improvement in a fixed cohort of pre-disaster residents are two different questions. People who moved away, died, could not attend, or did not apply must not be silently assigned zero need. Where needed, show the fixed cohort, the current cross-section, entrants, and those who exit side by side. A crude rate and a standardized rate can both be correct. Only if the rates are claimed to answer the same question but disagree should the measurement definitions, selection, or errors of inference be examined further. 〔Studies 03.04–03.05, 22.07, 24.01, 29.04, 31.04〕

</div>

<SectionLesson section="5.5.1" />

<div v-pre class="theory-source">


### 5.5.2 M02 Nesting {#section-5-5-2}

The signature is “boundary–membership embedding.” It must be divided into two branches:

Descriptive nesting tests only boundaries, membership, overlap, exit, and interface mappings. It can hold without any cross-layer causation.

Cross-layer causation requires a specified channel, a comparison suited to the claim, and temporal order. Evidence of empirical effects must be obtained under G2 and `CAUSAL`. The cross-scale mapping must separately go through D3/E5. A corresponding G4 instance is required only for a further claim of scale closure failure or of object or intervention conversion. Cross-layer causation can be established without a positive G4 result.

The absence of a conditional increment after controlling for the current state and the common environment does not by itself establish “no cross-layer effect.” A limited null conclusion may be registered only if the equivalence or sufficiency, statistical power or sensitivity, and tolerance checks all pass. Descriptive nesting creates no higher-level priority, lower-level obligation, or expansion of J.

A record must select one branch from `descriptive_nesting`, `cross_layer_causal`, `object_conversion`, and `intervention_conversion` and bind it to the corresponding descriptive, causal, object conversion, or intervention conversion mode. Boundary material from descriptive nesting must not be used to support the other three branches.

</div>

<SectionLesson section="5.5.2" />

<div v-pre class="theory-source">


### 5.5.3 M03 Network Propagation {#section-5-5-3}

The signature is “transmission along paths with timing.” The nodes, edges, directions, weights, capacity, and sampling boundary must be registered. The record must also include candidate and alternative paths, delay, and loss. Connection or synchronization yields only candidates. If the outcome is unchanged after the path is cut and the null-conclusion check has not passed, the status remains `unsupported_or_undecided`. Network sampling can miss weak edges, off-network positions, and bridges between networks. Retaining only endpoint impacts cannot recover the order of propagation. Centrality does not amount to intent, responsibility, or authority to act.

Observe tie strength, bridge position, centrality, and mobilizable resources separately. Four contacts can come from four institutions yet share the same information source. An acquaintance can also offer an actual referral that others are unwilling to make. Network position helps locate channels. Their capacity, cost, substitutability, and arrival time determine whether they are actually usable for the specified task. Testing for multiple sources of social support differs from testing for independence among sources of factual information. 〔Studies 26.01–26.02〕

</div>

<SectionLesson section="5.5.3" />

<div v-pre class="theory-source">


### 5.5.4 M04 Accumulation Over Time {#section-5-5-4}

The signature is “longitudinal composition within a window.” The time reference, baseline, window, time lag, durability threshold, and accumulation, decay, and recovery rules must be frozen. The comparisons must address common trends, seasonality, cohorts, and alternative windows. An effect that disappears after controls are applied or changes with the window indicates only insufficient positive support. A finding of “no accumulation” must not be published unless the null-conclusion check passes. Basic temporal composition does not establish G3 in advance. A `G3-instance` is linked only if historical terms still provide a conditional increment after controlling for the current state.

</div>

<SectionLesson section="5.5.4" />

<div v-pre class="theory-source">


### 5.5.5 M05 Institutionalization {#section-5-5-5}

The signature is “durable institutional write-back.” It separates five judgments about an institution. The first is whether it exists in fact. The other judgments are whether it is legally valid, whether it is normatively justified, whether protection is in place, and whether it should continue. Durable changes in records, roles, resources, decision rules, or subsequent transitions can support the fact of institutionalization. Invalid authorization, inadequate participation, failed protection mechanisms, and a lack of appeal, anti-retaliation, or rollback mechanisms constitute governance failures, normative disputes, and grounds for downgrading action. These shortcomings cannot erase the fact that the institution already exists. Conversely, its existence does not establish its legal validity, normative justification, adequacy of protection, or warrant for continuation.

`selected_operator_branch` allows only `institutional_fact`, `institutional_causal_effect`, `institutional_object_conversion`, and `institutional_intervention_conversion`. A legal validity review, governance quality, normative justification, adequacy of protection, or a judgment about whether to continue cannot serve as a positive or null conclusion for `institutional_fact`.

</div>

<SectionLesson section="5.5.5" />

<div v-pre class="theory-source">


### 5.5.6 M06 Emergence {#section-5-5-6}

The signature is “interaction generates a pattern at the target scale.” The source units, interaction rules, target object, and target pattern must be compared with a pre-registered simple additive model using the same metric. Comparable performance by the simple additive model supports “additivity is sufficient” only if the sufficiency or equivalence, statistical power or sensitivity, and tolerance checks pass. Otherwise, the result remains unresolved. A unique micro-level cause cannot be inferred from the macro-level pattern, which does not by itself establish downward causation. A downward constraint requires a specified channel, causal evidence suited to the claim, and a D3/E5 mapping. Additional claims about scale closure or the conversion of an object or intervention require separate evidence under G4.

</div>

<SectionLesson section="5.5.6" />

<div v-pre class="theory-source">


### 5.5.7 M07 Delegation/Representation {#section-5-5-7}

The signature is “classification of facts about representation and optional transfer of authorization.” The claim to represent, actual acts in another’s stead, contested or self-appointed representation, valid delegation, and transfer of J-axis authority must be recorded separately. Even without authorization, the acts performed, their impacts, and the associated responsibility may still be recorded. Expansion of J must not be registered in that case. Invalid authorization triggers a stop or a downgrade. It cannot erase the acts already performed or their consequences. A majority, visibility, influence, self-assertion, or actual control does not amount to valid delegation.

The record must select one branch from `representation_claim`, `actual_acts`, `delegation_validity`, and `J_transfer`. Even if one of the first three branches is supported, it cannot change J. J may expand only if `J_transfer`, structured authorization tuples, independent evidence of validity, and `j_authorization` all pass.

</div>

<SectionLesson section="5.5.7" />

<div v-pre class="theory-source">


### 5.5.8 M08 Compression/Abstraction {#section-5-5-8}

The signature is “many-to-one representational compression.” The source material, algorithm, threshold, version, error, irrecoverable information, and invariants required for the task must be traceable. Keep `unknown`, `not_applicable`, `not_observable`, and `withheld_for_protection` distinct. None may be compressed into “absent.” A representation with material task-relevant losses for a proposed high-impact action must not be used to support that action.

A precise condition for task sufficiency illustrates compression. Let x be the source state, z=f(x) its representation, and q(x) the answer currently required. If and only if f(x₁)=f(x₂) always implies q(x₁)=q(x₂), there exists a function g such that q=g∘f. The original state may be irrecoverable even when the current question can still be answered exactly. This condition gives no guarantee that g is easy to compute or that the representation remains sufficient for a different question, environment, or intervention. 〔Studies 05.01–05.02, 05.05–05.06, formal illustration here〕

Consider a finite, nonempty state domain and a real-valued target q. If the decoder can output any real number and loss is measured by the worst-case absolute error over the whole domain, the minimum recovery error from the representation is exactly half the largest oscillation of the target within a preimage. Let `a_z` and `b_z` denote the minimum and maximum target values in each nonempty preimage. The optimal error is (1/2)max&#95;z(b&#95;z−a&#95;z), attained by outputting the midpoint for each preimage. Given a tolerance ε, there exists a decoder with error at most ε if and only if the oscillation within each preimage is at most 2ε. The formula cannot be applied directly to vector or integer outputs, average loss, or an unknown distribution.

Successive conversions must preserve the same final query. Let f:X→Z and h:Z→W. The first stage is sufficient for the final target q, with q=g∘f. The final representation h∘f remains sufficient if and only if g is constant on every preimage under h restricted to the actual image f(X). Unreachable intermediate values need not be constrained. Completing a different local task at the second stage cannot resolve the original final query. See Appendix C.6–C.7 for the condition and its proof.

</div>

<SectionLesson section="5.5.8" />

<div v-pre class="theory-source">


### 5.5.9 M09 Horizontal Transfer {#section-5-5-9}

The signature is “analogical transfer across domains.” The mappings, differences, discontinuities, prohibited mappings, chain of responsibility in the target domain, and differences on the J axis must be registered. Material from the source domain only generates target candidates. Both `supported` and `null_supported` must come from independent target instances. If target evidence is insufficient, the status is `not_evaluated` or `unsupported_or_undecided`. This insufficiency does not establish the absence of the target mechanism. An analogy creates no authorization to act in the target domain.

</div>

<SectionLesson section="5.5.9" />

<div v-pre class="theory-source">


## 5.6 Limits of Universal Primitives Across Scales {#section-5-6}

Universal primitives are interfaces of kind D. They no longer carry empirical null models or falsification templates. Four limits in particular must be fixed:

Basic feedback under U07 requires only a return channel and an update to a subsequent state. It does not require G3. Feedback-mediated learning also requires corresponding evidence of an update carrier, retention across rounds, actual use, and task outcomes. G3 is added only when the claim is a historical conditional increment beyond the currently registered state (see §4.5 and §6.3).

An instantaneous demand–capacity gap under U09 does not require G3. Cumulative damage or delayed recovery requires separate verification of the current carrier of damage or capacity, how that carrier formed, and subsequent recovery. G3 applies only when a claim about a historical increment beyond the current representation is added.

U10 registers only candidate traces, their carriers, and their retention windows. It does not establish path dependence in advance. G3 must still demonstrate a conditional increment from historical terms after controlling for the current state.

The basic phase pattern under U11 requires neither G3 nor G4. Test causal triggering separately under G2. For continuation or delayed recovery sustained by the current carrier, obtain evidence under §4.5. Test hysteresis of the kind that adds a historical increment beyond the current representation separately under G3. Test object conversion separately under G4.

Likewise, U01 only registers candidate objects and does not guarantee G1 in advance. The definition of a relation under U05 does not establish causation. The channel fields under U06 do not establish a channel effect.

</div>

<SectionLesson section="5.6" />

<div v-pre class="theory-source">


## 5.7 Unified Scale Transformation Record {#section-5-7}

Every instance must include all 14 sections and all fields.

| Section | Required Fields |
| --- | --- |
| `identity` | `contract_id`, `concept_id`, `version`, `proposition_ids`, and `purpose` |
| `scale` | SP0, SP1, nine `axis_differences`, `unchanged_axes`, `transformation_class`, and `j_authorization` |
| `objects` | Valid source and target objects, `source_K`, `target_K`, `identity_mapping`, units, population, boundaries, members, and exclusions |
| `semantics` | `preserved_core`, `allowed_changes`, `lost_elements`, and `prohibited_mappings` |
| `transformation` | One operator, `selected_operator_branch`, `claim_mode`, rule, causal bridge, time lag, mapping error, validity period, `root-instance`, subtype, success criterion, positive and null decision rules, positive threshold, equivalence or sufficiency test, statistical power or sensitivity, tolerance, and outcome status |
| `variables` | Inputs, states, outputs, and dependencies between variables |
| `evidence` | Source and target evidence, coverage, heterogeneity, counterexamples, absence signals, alternative explanations, residual tests, and replication or external validation |
| `loss` | Compressed details, irrecoverable information, positions with low visibility, and local exclusion zones |
| `responsibility` | Actors, decision makers, authorizing parties, uptake carriers, responsible parties, beneficiaries, and cost bearers |
| `normative` | Value premises, choice type, normative choice record, runtime N principles, source of authorization, the C12 check, and O1–O4 procedures |
| `protection` | Protection applicability, low-power positions, safe submission, and anti-retaliation |
| `action` | Judgment ceiling, action ceiling, prohibited actions, stopping conditions, responsible person, and a machine-resolvable `selected_action` |
| `correction` | Appeal, review, rollback, repair, and write-back |
| `lifecycle` | Validity period, review points, suspension, and exit |

Together, `source_K`, `target_K`, and `identity_mapping` determine whether the object is preserved, converted, or incomparable. A shared name supplies no evidence of identity. The mapping record must preserve the summaries of the source and target K, the results of the four checks on the source and target objects under both sets of K, the forward and reverse mappings, the preserved and violated criteria, the pre-registration reference frozen before the results were read, and reviewable validation artifacts and hashes. Criterion results may only be `passed`, `failed`, or `undetermined`. A single Boolean value must not obscure which check did not pass.

| K Mapping Classification | Minimum Conditions | Outcome Ceiling |
| --- | --- | --- |
| `same_object` | The mappings are valid in both directions. All four checks on the source and target objects under `source_K` and `target_K` pass. The set of preserved criteria is nonempty, and the set of violated criteria is empty | The object identity may be retained under the current contract. This does not imply that its semantic, causal, or normative properties are also preserved |
| `converted_object` | `source_under_source_K` and `target_under_target_K` pass, and `target_under_source_K` fails. The violations and the reference to pre-registration before the results are read are specific. The record also uses `object_conversion` mode and has a supported G4b instance | Register only the object conversion under the pre-registered K. K must not be rewritten after the results to manufacture a conversion |
| `incomparable` | Both objects pass under their own K, and at least one cross-K check fails. The forward and reverse mappings preserve a complete record of attempts, with at least one validation showing invalidity and with evidence that can be resolved | Records known incomparability. The only permitted status is `unsupported_or_undecided`, distinct from “not evaluated” |
| `undetermined` | The necessary mappings, criteria, or evidence are still insufficient to complete the classification. Preserve the known `passed` and `failed` results and the `undetermined` results separately for the four checks, and identify which one blocks the overall judgment | Only `unsupported_or_undecided` or `not_evaluated` is permitted. Preserve the partial findings, and do not infer incomparability or object conversion from an unresolved overall judgment |

Object identity must be open to independent recomputation or review. The same object under the same criteria can be checked directly. Nontrivial preservation or conversion requires retaining both objects, both sets of K, mapping direction, the four criterion results, and the supporting materials. A name, ID, self-reported validity status, or hash cannot substitute for this semantic verification.

In object conversion mode, the classification must agree with the four outcome statuses. Only `supported` corresponds to `converted_object`. `null_supported` corresponds to `same_object` when all three null-conclusion checks pass. `unsupported_or_undecided` permits only preservation, known incomparability, or an unresolved classification. When the object conversion test has yet to run, the overall classification remains `undetermined`, and any local criterion results already verified independently are retained. An unrun or failed test therefore cannot justify preemptively recording the target as “already converted.” Other `claim_mode` values must not also report `converted_object` in the same atomic record. Object conversion must have its own atomic test.

When `claim_mode` is `root_hypothesis`, `causal`, `object_conversion`, or `intervention_conversion`, `root_instance_ids` must be filled in. The last three modes also require a nonempty causal bridge. Only `descriptive_mapping` may mark `root-instance`, subtype, and success criterion `not_applicable`. To record `supported` or `null_supported` in a non-descriptive mode, submit a resolvable `root-instance` registry to the validator and check the instance ID, root family, contract version, preselected subtype, single success criterion, and instance status. An apparently correct string prefix cannot stand in for an instance. A descriptive bridge may be recorded as `supported` if it passes the positive-support check. Record `not_evaluated` only when the selected mode has yet to run.

The 14 sections provide a stable interface without projecting human governance semantics onto all objects. `protection.applicability` must explicitly record the object type, downstream use, rationale, and evidence references. It must not be inferred from empty lists such as `actors`. If the object type is `nonhuman` and the uses are limited to `description_only` or to `nonhuman_intervention_without_human_or_sentient_effect` with evidence of no effect on humans or sentient subjects, `safe_submission` and `anti_retaliation` may be marked `not_applicable` with reasons. Real-world experimental or engineering interventions still have an acting subject and an object. Specific J, a person responsible for the action, stopping provisions, review, and rollback must be entered. Only purely descriptive use may mark J as inapplicable. Energy, matter, or computational resources in a natural system do not by themselves trigger this human protection contract. When the object is human, sentient nonhuman, mixed, or unknown, or the use concerns the evaluation of people, the allocation of their scarce resources, their rights, their exposure to risk, or real-world action involving them, the protection fields immediately become mandatory. An earlier inapplicability status must not carry over. The inapplicability of protection never implies that action is normatively justified. Normative choice still requires a separate judgment.

`action_owner` specifies only who is responsible for carrying out or stopping an action. It provides no basis for inferring `claim_mode=intervention_conversion` or establishing that the action is effective or justified. Every external action must link to a selection record through `selection_record_id` and disclose `value_premises` and the runtime `normative_principle_ids`. N1 alone can only block actions that exceed authorization. It cannot generate an affirmative proposal for action. The `feasible_alternatives` in the selection record must be structured options with stable `option_id` values. For each option, freeze `option_kind`, action type, target object, geographic area, validity period, reversibility, expected impacts, and distributional impacts. There must be exactly one option with `option_kind=no_action`, uniquely referenced by `no_action_option_id`. `selected_action.selected_option_id` must resolve to an `external_action` option. The selected action must match that option field by field on action, object, geographic area, and validity period. Selection of a no-action ID, matching only a natural-language label, and rewriting both the action and J without changing the approved option must all be rejected. At least one currently valid, independently reviewed atomic J authorization tuple must cover that subject, object, action, geographic area, and validity period together, and it must agree with the source of authorization. An unrelated authorization cannot back the proposed action even if it is formally valid. The record must also include a passed 10-component `c12_gate`, O1–O4 `procedure_ids`, a person responsible for the action, prohibited actions, stopping provisions, protection, appeal, review, and rollback. If any item is missing, the action ceiling is limited to taking no action or continuing deliberation. Empirical intervention conversion is judged separately by the relevant `root-instance`.

The record chain supplies only the order of composition. Support does not automatically carry from one step to the next. Chain validation must ensure that each step has a unique `contract_id` and exactly one operator, that adjacent object references and identity criteria are compatible, and that each SP1 matches the next SP0. If any step is unresolved, becomes invalid, or exceeds its loss limit, this must be retained in the output for the chain. Success at the final step cannot override it.

Evaluation of the chain must also specify whether the final task is consistent with the tasks at the individual steps and whether shared resources have been committed more than once. Two tasks can each be feasible with one unit of capacity and yet be infeasible together if they share that unit in the same period. If time limits, resources, or permitted strategies are legitimately changed, the new joint option should be evaluated. Representational sufficiency, joint causal response, and joint resource feasibility each have their own criteria. Passing one cannot substitute for passing the other two.

</div>

<SectionLesson section="5.7" />

<div v-pre class="theory-source">


## 5.8 Machine Validation and the Protection Floor {#section-5-8}

Machine validation checks the consistency of fields, references, versions, and outcome statuses and verifies that the recorded axis relations have been combined correctly. It cannot replace domain comparators in judgments about geometry, organizational graphs, causal abstraction, network embedding, object identity, or authorization validity. Without substantive comparisons and independent materials about the objects, a complete record or algorithmic output cannot justify registering scale elevation. Whatever schema or registry the implementation uses, it must meet the same requirements for traceability and review.

The four missingness statuses form a closed vocabulary. `unknown` means currently unknown. `not_applicable` means genuinely not applicable under the contract. `not_observable` means unobservable through the current channel and within the current window. `withheld_for_protection` means withheld for protection. None means “absent,” and deleting a field cannot substitute for a status.

`carrying_vehicles` and `responsible_subjects` must be recorded in separate fields. Uptake, visibility, being affected, and greater capability do not by themselves create responsibility. Whenever there is an effect on the rights of humans or sentient subjects, on the allocation of their scarce resources, on their exposure to risk, or on how they are treated in practice, the protection floor must identify low-power positions and local exclusion zones. It must provide safe submission, anti-retaliation, stopping provisions, appeal, review, and rollback. In these cases, it must not be marked not applicable. Insufficient protection lowers both the judgment ceiling and the action ceiling. Downstream actions cannot inherit conditional inapplicability from purely descriptive records. A change of use requires reopening the protection review.

</div>

<SectionLesson section="5.8" />

<div v-pre class="theory-source">


## 5.9 Evidence Boundaries and Independent Support {#section-5-9}

The names, IDs, semantic signatures, and classifications of M01–M09 specify only how a transformation should be described and tested. They provide no empirical support that the transformation occurred, the mapping is valid, or the target property holds. Internal concept labels, examples, field completeness, and results reported by the algorithm itself must not be entered into `source_evidence` or `target_evidence` in place of materials about the objects.

Every actual transformation must obtain independent, resolvable materials separately for the source and target objects. It must specify the mapping, what is preserved, changed, or lost, the error, and the competing explanations, and undergo the same outcome classification and the same positive-support and null-conclusion checks. Source-domain materials can only generate candidates for the target. Without independent support on the target side, the conclusion remains a mapping awaiting testing or unknown.

</div>

<SectionLesson section="5.9" />

<div v-pre class="theory-source">


## 5.10 Cross-Circle Relation Transformation {#section-5-10}

Scale transformation and cross-circle relation transformation must be kept separate. Scale transformation asks which variables are preserved, changed, or lost for the same question between SP0 and SP1. Cross-circle relation transformation asks how two or more candidate circles[^tn-circle-06] stand in parallel, contain one another, overlap, bridge, compete, or form temporarily at the same or different scales. A change in relations may accompany a change in scale. Neither term can substitute for the contract governing the other.

A cross-circle record includes, at minimum, the source of the relation, its target, the type of static relation, the basis for membership or interfaces, direction, channel, delay, threshold, time window, evidence, and counterexamples. It also includes before-and-after snapshots. `transformed` is used only as an outcome of a relation update. A formerly parallel relation may become bridged when a bridging party appears. An overlapping relation may become nested through institutional integration, and a temporary circle may become institutionalized or undergo dissolution. Each such relation change requires checking whether K is preserved. If K no longer holds, record an object conversion. A new name must not be used to carry the old object forward.

| Transformation Question | What to Use | Distinctions to Preserve |
| --- | --- | --- |
| Can an individual’s state represent a team? | M01 aggregation, a scale contract, and distributional loss | Team membership alone does not make a member’s state representative of the team |
| Is a team contained within an organization? | M02 nesting and a specific basis for containment | Having a superior in common does not imply membership containment |
| Are two circles associated because they share members? | The overlap relation, membership mappings, and the common environment | Overlap does not by itself produce effective feedback |
| Does a bridging party change another circle? | M03 propagation, a channel, and a counterfactual | Contact does not amount to transmission. Transmission does not amount to representation |
| Does a temporary group form a durable object? | K, longitudinal material about the object, and M05. Test a claim of grouping gain separately under G1 and a claim of a historical conditional residual separately under G3 | Traces do not amount to institutionalization. A durable fact need not depend on an additional historical residual |

Multiple memberships require retaining the same actor’s distinct roles, visible information, responsibilities, risks, and ability to exit across circles. An actor must not be aggregated into a single state that is then copied to every circle. Cross-circle projection should start from local states, propagate through declared membership or interface channels, and register aggregation loss at each step.

Translation involves both tasks and permissions. Accurately relaying what someone said, helping both sides understand each other, having permission to publish that person’s exact words, and signing an agreement on their behalf are four distinct capabilities or qualifications. The same translation can suffice to book an appointment and may still be insufficient to preserve poetic rhythm or distinctions in legal status. Insufficiency for the latter task does not justify retroactively recording the former as never completed. The limited translation that succeeds should be retained, and the meanings and rights that did not transfer should be made explicit. 〔Studies 12.10, 26.08–26.09〕

</div>

<SectionLesson section="5.10" />

<div v-pre class="theory-source">


### 5.10.1 Three Kinds of Transformation Must Be Kept Separate {#section-5-10-1}

Scale transformation asks which variables are preserved, changed, or lost for the same question between one scale profile and another. Cross-circle relation transformation asks how parallelism, containment, overlap, bridging, competition, or temporary relations among candidate circles are updated. Representational or discursive recasting asks how a payload with an identified source enters the vocabulary, variables, or expressions of the target task. All three can occur together, but they must be split into ordered records.

Recasting is a kind of operating contract that gives its own account of what is preserved, changed, and lost. It can use propagation, compression, horizontal transfer, or other operators. Contracts are linked according to their respective inputs, outputs, criteria, and failure conditions. Operators must not be added solely because names differ, and failures of different operations must not be merged into a single overall status.

</div>

<SectionLesson section="5.10.1" />

<div v-pre class="theory-source">


### 5.10.2 Recasting Loss Audit {#section-5-10-2}

If two source states that can be distinguished in the source task cannot be distinguished in the target representation, register a task-relevant loss for that distinction. An identity mapping, reversible encoding, or mapping sufficient for the target task may yield no detected relevant loss. The rule is “do not assume losslessness in advance.” It does not say that a mapping is “necessarily lossy.”

| Audit Item | Minimum Question | Distinctions to Preserve |
| --- | --- | --- |
| Preservation | Which facts, relations, modalities, rights, or uncertainties must stay the same? | Preserving a title does not amount to preserving its semantics |
| Change | Which formats, units, levels of granularity, or expressions may change? | Permitting change does not permit arbitrary changes in meaning |
| Collapse | Which source distinctions are merged on the target side? | Collapsing a distinction does not imply that it is absent from the source |
| Omission | What was left out of the target representation, and why? | Non-disclosure for protection does not amount to absence |
| Addition | Which explanations, inferences, or target variables does the conversion produce? | Adding a variable does not amount to discovering a real-world entity |
| Return | Which parent record or contract is revisited when an anomaly occurs? | Returning only reopens review. It does not patch the old run |

Round-trip reconstruction can serve as a test but is insufficient by itself. A conversion may appear to round-trip by using hidden source records while failing to preserve the semantics of the target task. A one-way summary may be sufficient for the specified task. Review must return to the predeclared items to preserve, the tolerances for loss, and the results on the target side.

Whether the target representation retains a needed distinction and whether the actual rule uses it correctly are two separate judgments. An error in acting on the representation does not by itself establish a recasting loss. If the distinction is still discernible but used incorrectly, record the gap in the rule or its execution. Representational loss and execution errors can also coexist. Their grounds should be stated separately, and other local results that have already been established should be retained.

When both kinds of failure occur, the same unavoidable error should not be counted again as an additional failure of the rule. If the target answer is nonunique within a preimage, no deterministic rule using only the current representation can answer correctly for all source states. This by itself establishes that the representation is insufficient. If the target answer is unique in another nonempty preimage but the actual rule gives the wrong answer, that provides a sufficient witness to an independent error in the rule. When the actual internal representation is unknown, the original material’s continued public availability does not establish that those implementing the rule had the distinction available to them at the time. The existence of material, timely access to it, and actual use must be checked separately.

</div>

<SectionLesson section="5.10.2" />

<div v-pre class="theory-source">


### 5.10.3 Effective Variables, Closure, and Returning in Response to Residuals {#section-5-10-3}

An effective variable is a candidate variable proposed for a target scale or task. The proposal is to compress the state and improve explanation for a prespecified task. The intended improvement may also concern foresight[^tn-foresight-06] or the comparison of options. It must be tied to an object, scale, time window, task, measurement, and simple baseline. Error, failure, and retirement must also be specified for the variable. Effectiveness does not establish that the variable is a real entity, a root cause, a universal variable, or a basis for authorization.

The target representation carries no presumption of dynamic closure. For static descriptions or same-scale queries, first check sources, conversion rules, and answers to the task, using F1 and F4 when necessary. Check formal dynamical models for closure under F2 and obtain separate evidence for their real-world mappings. G-specific fields that do not apply to a descriptive mapping may be marked `not_applicable` with reasons. Apply the positive-support and null-conclusion checks of the relevant G4 instance only when seeking formal empirical support under §4.6 for scale closure, object conversion, or intervention conversion. A scale change must not be fabricated to meet a format requirement. Failure to find a significant increment does not by itself establish closure. When an increment occurs, register the corresponding impact as a candidate for memory, noise, hysteresis, an unresolved term, or a residual. The shape alone must not be used to name a new entity.

The unified scale transformation record must specify the target task in its purpose and semantics fields. Its transformation, evidence, and loss fields must record the parent representation, collapsed differences, return point, reconstruction test, and candidate effective variables for the target. If the information is missing, retain an explicit missingness status. A complete table cannot establish that all of the source semantics have been preserved.

</div>

<SectionLesson section="5.10.3" />

<div v-pre class="theory-source">


## 5.11 Representing Parallelism and Nesting Together {#section-5-11}

Real-world structures cannot be reduced to a single hierarchical tree. Local containment relations can coexist with lateral networks, membership overlap, competition for resources, and bridging through platforms. The representation layer uses a directed multigraph of relations. Nodes retain their own object contracts, and edges retain their own relation contracts. “Higher layer” denotes only a particular relation of containment, jurisdiction, or aggregation. It carries no implication of greater reality, correctness, or authority.

When several circles share an environment but have no direct channel, the model retains a node for the common conditions and must not invent a direct edge between the circles. When a channel is open only within an event window, its edge has a start time and an end time. When different relations run in opposite directions, create separate edges. This makes it possible to determine after an event which relation actually changed, without redrawing the whole structure as a story told after the fact.

[^tn-contract-06]: Translator's note: A contract here is an analytical agreement registered and frozen before results, akin to pre-registration.

[^tn-protocol-06]: Translator's note: A protocol here is a methodological check that a judgment must pass.

[^tn-circle-06]: Translator's note: Circles may be parallel, nested, overlapping, or bridged.

[^tn-foresight-06]: Translator's note: Foresight in this book requires a registered target, horizon, and baseline, along with calibration.

</div>

<SectionLesson section="5.11" />

<div v-pre class="theory-source">

</div>
