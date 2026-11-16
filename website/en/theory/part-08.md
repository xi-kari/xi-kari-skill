---
title: "Part 8 Human State Prototypes"
---

<div v-pre class="theory-source">

<a id="part_8"></a>

# Part 8 Human State Prototypes {#part-title-8}

## 8.1 What This Part Explains {#section-8-1}

S0–S6 apply only to human intentional collectives. These are teams, organizations, institutions, movements, communities, or governance arrangements that people form around a shared problem, commitment, goal, or arrangement of meaning that they can articulate. They continue to operate through roles, resources, rules, relations, and feedback. The prototypes do not express universal laws and cannot be applied directly to individual personality, a purely physical system, the evolution of a species, or the universe as a whole. Even within their domain of application, S0–S6 do not form a ladder of maturity, a required historical sequence, or a ranking of value.

The numbers serve only to distinguish prototypes and make them easy to find. They let us ask, “What structural configuration predominates now in this object, in this subsystem, and within this time window?” They do not warrant saying, “The number is higher, so the people are better, the institutional arrangements more justified, or the civilization more advanced.” A large collective can have S5 at its center, S3 at its periphery, S6 in a technical unit, and still have S1 in its intergenerational uptake. The same function can also show two prototypes at once. Such cases should be registered as `parallel` or `mixed` without collapsing the complexity into a single “overall stage.”

A state prototype yields only a descriptive classification that can be withdrawn. It confers no authorization to act. Any real-world intervention must separately state its normative premises and pass C12. It must compare options including taking no action, obtain atomic J authorization covering the specific subject, object, action, geographic area, and validity period, and be subject to O procedures and to appeal and rollback. A state label cannot serve as evidence for these checks.

## 8.2 Minimum Contract[^tn-contract-09] for State Judgments {#section-8-2}

For each judgment, first freeze the object’s `object_id`, the identity criterion K, the nine-axis scale profile SP=&lt;A,X,T,O,C,R,I,N,J&gt;, the time window, and the scope of the subsystem. Then record entry conditions, exit conditions, observables, counterexamples, falsification results, and missing data separately. There are only four classification modes: `single_dominant`, `mixed`, `parallel`, and `unknown`. The freeze applies to the criterion for tracking the object in this analysis. It does not require observed membership, actual boundaries, roles, commitments, or self-identification to have stabilized. If the definition of K needs to change, a new versioned record should be created that preserves the original criterion, materials, and judgment. Object identity should then be checked again. Until that check is complete, records under different K must not be joined directly as a path of the same object across windows.

| Field | Required Question | Stopping Point |
| --- | --- | --- |
| Object and K | Are we tracking the same human collective, or has the object changed while keeping the same name? | If K is not frozen, cannot be used to track the object, or leaves object identity unresolved, assess the object and its identity first and assign no prototype. Changes in membership or actual boundaries do not automatically amount to a change in K |
| Scale and time | Which units, spaces, windows, levels, affected positions, and networks are visible? | Wider observation does not expand J authorization |
| Entry and exit | What materials make a prototype a candidate, and what materials show that it no longer predominates? | Resemblance to a prototype does not establish that the object has entered it or must exit it |
| Observables | Which behaviors, records, channels, costs, recovery, and write-back can be reviewed? | A slogan, aggregate total, or official self-report alone is insufficient |
| Counterexamples and falsification | What else could produce the same appearance? What result would lead to withdrawal of the judgment? | A label assigned without actively seeking counterevidence counts only as an impression |
| Evidence coverage | What external materials support the judgments about entry, observations, and counterevidence? Can the evidence be resolved, and does it cover the current object? | Internal definitions, IDs, and accounts provided by the framework cannot substitute for evidence about the object |
| Missing data | Was it not collected, is it unobservable or inapplicable, are the sources in conflict, or is it unknown? | Missing data must not be filled in as “normal,” “absent,” or zero |
| Norms and action | Does the classification confer value, an obligation, or authority to act? | All states are `descriptive_only` and `action_authorization=none` |

The five missing-data statuses must be kept separate. `not_collected` means that the data can be obtained but have not been collected. `not_observable` means that they are unobservable under the current permissions, safety conditions, or measurement conditions. Subjects in vulnerable positions must not be required to expose themselves to complete a form. `not_applicable` requires an applicability check. `conflicted` means that qualifying sources conflict with one another. `unknown` means that attempts have been made and the distinction still cannot be made. A missing key entry, counterevidence, or scale field by itself supports only `unknown` or suspension of the relevant classification. `mixed` and `parallel` each require positive evidence of multiple prototypes and their corresponding positions. Lack of knowledge must not be renamed as a mixture. Local materials already established are retained within their original scope.

### 8.2.1 Runtime Classification Record {#section-8-2-1}

A prototype card yields a reviewable classification only when entered in a closed runtime record. The record must freeze all of the following together: `record_id`, the object and its identity criterion, the nine-axis scale, time window, subsystem scope, classification mode, candidate states, candidate paths, results for the five kinds of conditions, missing data, evidence about the object, uncertainty, independent review, appeal, rollback, and the boundary of non-authorization. Each entry, exit, observation, counterexample, and falsification result uses the same structure, `item_id + state_id + status + evidence_refs + reason`. The results must cover each candidate prototype item by item. A single overall assessment cannot substitute for them.

`single_dominant` has exactly one candidate. `mixed` and `parallel` each require at least two candidates and an explicit record of the corresponding paths. `unknown` assigns no supported prototype and must explain which key materials are still insufficient to distinguish the prototypes. Local facts and observations of components already established remain in the evidence about the object. They must not be deleted because the overall prototype is unknown. If the runtime record does not allow supporting items in the candidate conditions field for `unknown`, keep the materials in the evidence about the object and the rationale. Do not fabricate a complete prototype. At a minimum, each candidate requires evidence about the object for entry and observation items. Once any falsification item is `supported`, the candidate is blocked. Weaker wording cannot keep it in the record as a candidate. Each validation must also be supplied with an external `evidence_ids` registry. At every level of the record, `evidence_refs` must resolve to evidence about the object in the record and recursively to that external registry. A missing registry, a top-level self-report, or a reference that resolves to nothing cannot pass. Internal IDs, definitions, and self-reported judgments cannot substitute for evidence about the object.

The reviewer record has the structure `reviewer_id + independent + reviewed_at + material_version + outcome`. Appeal and rollback each link to a structured procedure ID and status. After NFKC normalization, removal of leading and trailing whitespace, and case normalization, `reviewer_id` must differ from the object ID and must not be an alias derived from it. A different string cannot turn the object itself into an independent reviewer. Review, appeal, and rollback must not be represented by self-reported strings such as “reviewed” or “appeal available.” Regardless of the outcome of review, the record always has `normative_status=descriptive_only` and `action_authorization=none`. When a state label is withdrawn or rewritten, the original evidence, objections, and chain of versions should be preserved.

The U, H, G, and C IDs serve four distinct purposes in this Part. U provides interfaces for objects, states, channels, load, and phases. H supplies adaptations for meaning, uptake, institutional write-back, power, and historical carriers in the human world. G specifies when upgrading a pattern to an empirical mechanism requires a qualified independent instance. C specifies where inference must stop. These contract links supply no evidence about the object at hand.

Descriptions of S0–S6 configurations do not require the multiple-interval pattern of CM-PHASE. An object that meets the necessary conditions of one prototype throughout the observed window may still receive a corresponding limited classification. That classification does not establish that a phase transition has occurred. A further claim about multiple intervals, a threshold, or a mechanism of phase transition is checked under CM-PHASE and the relevant G instance. Conversely, establishing a formal pattern with two intervals does not by itself show that an object fits a particular human collective prototype.

## 8.3 S0–S6 State Prototypes {#section-8-3}

### 8.3.1 S0 Prototype of Coalescence Around an Anchor {#section-8-3-1}

S0 describes a “candidate collective taking shape.” It confers no designation of “lower-level organization.” A shared problem, candidate goal, or expression of meaning begins to draw together attention, relationships, time, and small amounts of resources. Membership, actual boundaries, roles, ways of making commitments, and expressions of shared identity are still forming or changing. The analysis must still use a K frozen for this analysis and capable of tracking the object. Changes in a state that is taking shape cannot substitute for a judgment about identity. At least one candidate generative actor repeatedly translates, convenes, tries things out, or bears actual costs. An independent uptake layer has yet to form. A candidate collective may disperse, go dormant, be incorporated into another arrangement, or turn to a new goal at this point. Estimating how often each path occurs requires the relevant population of opportunities and observational material. The rates cannot be inferred from the prototype definition. The process ending does not by itself constitute a finding of failure.

| Aspect | S0 Diagnostic Card[^tn-diagnosis-09] |
| --- | --- |
| Entry | `S0-E1` Under a K frozen for this analysis and capable of tracking the object, a shared problem or arrangement of meaning produces visible local clustering, but membership, actual boundaries, or ways of making commitments have yet to stabilize. `S0-E2` Candidate generative action recurs and uptake remains limited. |
| Exit | `S0-X1` While the same K remains applicable and object identity is traceable within the windows, the anchor, actual boundaries, and generative roles stabilize across windows, and traceable commitments and early uptake appear. S1 may be tested. `S0-X2` The collective disperses, splits, is absorbed, or goes dormant and need not pass through S1. If the original K no longer applies, assess object conversion or termination separately. |
| Observables | `S0-O1` Competing formulations are still under negotiation. `S0-O2` Resources cluster amid high rates of entry and exit. `S0-O3` Generative actors take on translation, convening, or trial and error. `S0-O4` Failed attempts and the history of alternatives are still retained. |
| Counterexamples | A trending topic or platform recommendation can create short-lived synchronization. Administrative naming can create a formal team. Observe whether commitments and object boundaries persist after rewards, exposure, or orders are removed. |
| Falsification | Withdraw S0 if shared direction, the clustering of action, and generative roles all fail to differ from those in a matched temporary gathering. S0 also does not predominate if stable roles, uptake, and repeated operation have long been in place. |
| Scale | Distinguish generative actors, early participants, potential leavers, and outside parties who assign the name. Individual personalities must not be aggregated into a collective state. |
| Evidence for stronger claims | A difference in resources, action, or coordination caused by an arrangement of meaning requires an H1-instance. Formation caused by a specified channel requires a G2-instance. Check historical traces under H5 and obtain evidence for future effects of current carriers under §4.5. Add G3 only for a historical increment beyond the current representation. |
| Contract links | U01/U02/U03/U08/U09/U11, H1/H2/H5, G1/G2/G3, C1/C2/C4/C5/C10/C12. |

S0 permits only a finding of compatibility with the prototype of coalescence around an anchor for the specified object, scale, and window. It cannot establish that participants lack capability, value, or willingness. It cannot authorize support, dissolution, screening, or exclusion.

### 8.3.2 S1 Prototype of a Generative Core Taking Shape {#section-8-3-2}

Under S1, a candidate anchor, object boundaries, and at least one generative role can already be identified repeatedly across decisions. Basic rules, language, resource channels, and the first carriers of memory are taking shape. The main work of translation, decision-making, resource mobilization, conflict handling, or repair of relationships remains concentrated in one or a few generative roles. Independent parties able to take up the work are scarce. Centrality describes structural dependence and does not establish the legitimacy of leadership.

| Aspect | S1 Diagnostic Card |
| --- | --- |
| Entry | `S1-E1` K, the anchor, and the generative roles can be identified repeatedly. `S1-E2` Key functions depend on the generative core on an ongoing basis beyond a single emergency concentration. |
| Exit | `S1-X1` New entrants form sustained arrangements for uptake, responsibility, and boundary interfaces. S2 may be tested. `S1-X2` The generative core splits, exits, is taken over, or goes dormant, or the object disperses. Follow the corresponding path. |
| Observables | `S1-O1` The anchor and boundaries show initial stability. `S1-O2` Key decisions depend on the generative core. `S1-O3` Rules and carriers of memory begin to recur. `S1-O4` Entry from outside is limited and targeted. |
| Counterexamples | A founder may still announce decisions publicly in a mature organization even though the actual uptake layer is already extensive. A newly created administrative unit may be only a role unit of a higher-level object. Trace actual execution, rights to stop, feedback, and operation when the core is temporarily absent. |
| Falsification | Dependence on the core is refuted if uptake across multiple centers remains stable with little involvement from the generative core. If the anchor is unstable but the same K still applies and the object can be tracked, retest S0. If the original K no longer applies or object identity is unclear, first check for object conversion or termination or retain `unknown`, then classify objects that can be identified. |
| Scale | Freeze the record of generative roles, early parties taking up the work, higher-level parties who assign the name, and external supporters. Record `conflicted` when the organizational chart conflicts with actual channels. |
| Evidence for stronger claims | Effects of the anchor and of the generative core on outcomes require H1 and G2, respectively. Obtain evidence under §4.5 for carrier effects of early institutions or trauma, test traces under H5, and test historical conditional residuals separately under G3. |
| Contract links | U01/U02/U03/U04/U06/U07/U09/U11, H1/H2/H3/H4, G1/G2/G3, C1/C2/C3/C5/C9/C10/C11/C12. |

S1 must not be read as “immature,” “backward,” or “should be integrated.” It cannot confer permanent leadership, greater power, or standing to impose institutional arrangements or replace others on generative actors.

### 8.3.3 S2 Prototype of Initial Expansion and Differentiated Uptake {#section-8-3-3}

S2 describes continued expansion of boundaries, membership, the population served, geographic reach, platform interfaces, or networks of collaboration. New entrants bring different understandings, skills, resources, and risks. Positions outside the generative core begin to emerge for taking up work, exiting, maintaining dissent, and participation that remains unresolved. Expansion can improve the capability to coordinate and also adds problems involving translation, feedback, recovery, and power. Disagreement by itself does not amount to destabilization. There are grounds to describe a structural problem only if an observable mechanism persistently blocks uptake, feedback, or recovery.

| Aspect | S2 Diagnostic Card |
| --- | --- |
| Entry | `S2-E1` At least one kind of boundary continues to expand and changes relations. `S2-E2` Distinguishable positions of uptake, cost, exit, and unresolved participation emerge outside the generative core. |
| Exit | `S2-X1` Repeated loads and pressures produce interconnected constraints that persistently divide channels. S3 may be tested. `S2-X2` Expansion stops or recedes, or the object jumps, splits, merges, is taken over, goes dormant, or collapses. |
| Observables | `S2-O1` The pattern of entries and exits and the composition of interfaces change. `S2-O2` Roles and responsibilities differentiate. `S2-O3` Feedback volume, translation costs, time lags, and recovery needs change. `S2-O4` Identification with the group, dissent, exit, and safety are recorded separately. |
| Counterexamples | Growth in membership or user counts need not change the structure. Conflict becoming public may also reflect improved safety of expression that finally makes old problems visible. |
| Falsification | With the statistical definitions frozen, withdraw S2 if growth is not sustained and changes none of the boundaries, roles, responsibilities, interfaces, or loads. The classification should also be withdrawn if the supposed differentiation comes solely from labels assigned by the center. |
| Scale | The whole, the center, new parties taking up the work, leavers, and externalized costs must all be included. Wider observation does not increase J authority over new members. |
| Evidence for stronger claims | Differences in outcomes caused by expansion or by a channel require G2/CAUSAL. Cross-scale claims separately go through D3/E5, and claims of closure or conversion are tested separately under G4. Coordination by an anchor requires H1. Observational effects of expression, disclosure, and power require H4. Historical traces require H5, carrier transmission is checked under §4.5, and historical conditional residuals are tested separately under G3. |
| Contract links | U01/U02/U03/U04/U06/U07/U08/U09/U11, H1/H2/H3/H4/H5, G1/G2/G3/G4, C1/C2/C3/C4/C5/C6/C7/C9/C10/C11/C12. |

S2 does not permit labeling people who do not identify with the collective, who leave, or whose participation is unclear as “negative subjects” on that basis alone. A “need for dimensional expansion” cannot authorize enforcing uniform beliefs, restricting exit, or excluding dissenters.

### 8.3.4 S3 Prototype of Development Under Interconnected Constraints {#section-8-3-4}

Under S3 the collective still operates or develops, but several recurring constraints have become connected. Approvals, resources, trust, responsibility, information, platforms, or external dependencies form mutually reinforcing bottlenecks that persistently fragment feedback, uptake, recovery, or the return flow of costs. The question is whether the problems form a connected structure that can be reviewed. The number of problems or the naming of a person as a barrier does not answer that question.

| Aspect | S3 Diagnostic Card |
| --- | --- |
| Entry | `S3-E1` At least two kinds of constraint reinforce one another and affect channels across windows. `S3-E2` Operation continues, but uptake at the downstream end, feedback, resources, or recovery bear a sustained extra load. |
| Exit | `S3-X1` Key relations, permissions, resources, or interfaces begin to be reconfigured in practice. S4 may be tested. `S3-X2` The object enters regression, a pseudo-steady state, dormancy, takeover, forced rewrite, migration, or collapse. |
| Observables | `S3-O1` A network of constraints and bottlenecks. `S3-O2` Output persists while losses, rework, and hidden labor increase. `S3-O3` Repair is repeatedly started but does not write back. `S3-O4` The center and periphery, metrics and uptake, and nominal and actual arrangements remain divided. |
| Counterexamples | Protective layering and redundancy can improve reliability in a high-risk environment. Deliberate load reduction for reconfiguration can also slow output temporarily. Check whether the restrictions block necessary feedback or provide error isolation and alternative paths. |
| Falsification | After excluding common inputs, measurement bias, and short-term peaks, S3 does not predominate if the constraints are not connected or if alternative channels, write-back, and recovery at the downstream end of uptake remain effective. |
| Scale | Separate the center, periphery, functional units, downstream uptake positions, and affected positions outside the object. Allow `parallel`. Disappearance of weak signals cannot be treated as disappearance of the problems. |
| Evidence for stronger claims | Masking by power or mediation requires H4. Specified channels and mutual reinforcement require G2. Examine current constraints formed through history under §4.5 and test additional historical residuals under G3. Failure of cross-scale closure requires G4. |
| Contract links | U02/U03/U05/U06/U07/U08/U09/U10/U11, H1/H2/H3/H4/H5, G2/G3/G4, C2/C3/C4/C5/C6/C7/C9/C10/C11/C12. |

An S3 classification cannot authorize “breaking barriers,” purges, takeover, forced reform, or shifting transition costs to vulnerable positions. It indicates only that the constraint network and competing explanations should be distinguished further.

### 8.3.5 S4 Prototype of a Window for Structural Reconfiguration {#section-8-3-5}

S4 describes a genuine window for reconfiguring key structures. It gives no assurance that a reform is already right. Old relations, permissions, resource channels, feedback write-back, or boundary interfaces are being dismantled, replaced, or bypassed. Old and new arrangements coexist. There are conversion costs, duplicated work, knowledge transfer, short-term declines in output, and growing recovery needs. The outcome remains open. It can be improvement, stagnation, alienation, forced rewriting, or collapse.

| Aspect | S4 Diagnostic Card |
| --- | --- |
| Entry | `S4-E1` At least one key field actually changes beyond renaming or publicity. `S4-E2` Old and new arrangements coexist, transition costs can be traced, and K continues to be checked. |
| Exit | `S4-X1` Channels, feedback, uptake, and recovery improve across windows without concealed outsourcing. S5 may be tested. `S4-X2` The new structure is unusable, and the object enters dormancy, regression, takeover, forced rewriting, a pseudo-steady state, or collapse. |
| Observables | `S4-O1` Changes in permissions, resources, roles, responsibilities, or stopping conditions are actually written back. `S4-O2` Dual systems and conversion costs. `S4-O3` Buffers, redundancy, cooldown, stopping, and rollback. `S4-O4` Outcomes from multiple positions enter actual feedback. |
| Counterexamples | Large-scale renaming, replacing people, or redrawing flowcharts may be symbolic reform. Dismantling old arrangements, overload, and declining output may also reflect a destructive purge or withdrawal of resources. |
| Falsification | Withdraw S4 if actual relations, permissions, resources, and execution do not change. If no usable new structure exists and functions remain disrupted, the process must not be presented as reconfiguration that brings improvement. |
| Scale | Cover the windows for the pre-change baseline, transition, cooldown, rollback, and recovery. Distinguish those who initiate reform, those who execute it, those who take up the work, and those who bear the costs. |
| Evidence for stronger claims | A claim that reconfiguration causes improvement or harm requires G2/CAUSAL. Object or intervention conversion requires G4. Whether failed attempts affect the future through a current carrier is assessed under §4.5, and additional historical residuals are tested separately under G3. A “tunneling” analogy cannot substitute for that evidence. |
| Contract links | U03/U05/U06/U07/U09/U10/U11, H1/H2/H3/H4/H5, G2/G3/G4, C2/C3/C4/C5/C6/C7/C9/C10/C11/C12. |

A “transition valley” is at most a description to be tested. It cannot justify unlimited costs, irreversible harm, the removal of appeal, or sacrifices imposed on those in low-power positions. S4 confers no authorization for dismantling, purges, or forced transfer.

### 8.3.6 S5 Prototype of Efficient Coordination and Flexible Expansion {#section-8-3-6}

S5 describes coordination with relatively low losses among channels for resources, information, feedback, responsibility, uptake, and recovery in the current environment and time window. Local disturbances usually fail to produce lasting interconnected barriers. Boundaries can expand and contract with some flexibility. Resource advantages, costs shifted through outsourcing, silence, whitewashed metrics, or institutional loopholes can still make these conditions appear to hold when they do not. High output is therefore insufficient evidence, and long-term persistence does not prove legitimacy.

| Aspect | S5 Diagnostic Card |
| --- | --- |
| Entry | `S5-E1` Key channels operate with low losses across windows, can be substituted, and permit write-back. `S5-E2` Expansion, preservation, and dissipation work together without relying on closing off feedback or suppressing dissent. |
| Exit | `S5-X1` Distributed uptake, self-renewal, recovery, and new generation hold across disturbances. S6 may be tested. `S5-X2` Loopholes, alienation, a pseudo-steady state, regression, functional transfer, X0, takeover, or collapse cause the prototype to stop predominating. |
| Observables | `S5-O1` Alternative uptake arrangements and channels are actually usable. `S5-O2` Output, feedback, recovery, and maintenance all continue. `S5-O3` Boundaries are open, protection and exit can be implemented, and costs flow back. `S5-O4` Audits of loopholes can produce write-back. |
| Counterexamples | Resource abundance, selective metrics, failed complaint channels, compliance out of fear, or shifting maintenance debt into the future can all create the appearance of “success.” |
| Falsification | Withdraw S5 if the efficiency advantage disappears after maintenance, recovery, exit, and external costs are included, or if local failures cascade rapidly when the center is minimally involved. |
| Scale | Management totals must be broken down to the positions of maintainers, people taking up the work with little power, leavers, and external positions affected. Cover high and low loads and the windows for disturbance, recovery, and maintenance. |
| Evidence for stronger claims | Causes of efficient coordination and effects of loopholes require G2/H4. Historical traces, sustained carrier effects, and additional residuals are assessed under H5, §4.5, and G3, respectively. Replication across scales requires D3/E5 mapping and independent evidence at the target. Claims of closure or conversion are tested separately under G4. |
| Contract links | U01–U11, H1/H2/H3/H4/H5, G1/G2/G3/G4, C1–C12. |

S5 does not label an object as “good,” “mature,” or “ready to export its model.” Persistence, growth, and selection do not establish legitimacy. They cannot authorize expansion, replication, takeover, or demands that members take on more.

### 8.3.7 S6 Prototype of Adaptive Dynamic Balance {#section-8-3-7}

S6 describes a collective with distributed uptake, effective feedback, and the capability to recover, update, and generate anew. Ordinary fluctuations do not lock in its direction for long. Autonomous units can stabilize locally, coordinate laterally, and receive backing from a higher level. A pool of potential successors, memory attached to positions, authorization, and handovers allow newcomers actually to enter and modify existing arrangements. The collective maintains function through continual calibration, with fluctuations still present.

| Aspect | S6 Diagnostic Card |
| --- | --- |
| Entry | `S6-E1` With little involvement from the center, multiple positions can still sense changes, correct errors, recover, and write back. `S6-E2` People taking up the work, rules, and boundaries can be renewed continually without dependence on the same irreplaceable individuals. |
| Exit | `S6-X1` Slower recovery, larger fluctuations, failed write-back, dependence on the center, or interruption of uptake leads to regression or another path. `S6-X2` The end of the mission, functional transfer, a split, a merger, paradigm replacement, or X0 changes the object contract. |
| Observables | `S6-O1` Recovery and renewed destabilization after a disturbance. `S6-O2` Coordination among multiple centers and backup arrangements. `S6-O3` New people taking up the work go from training to taking charge of it in practice. `S6-O4` Feedback, audits, appeals, and rule revisions maintain a closed loop. |
| Counterexamples | Strong control, disappearance of weak signals, protection of resources, or concealed firefighting by the center can all create low fluctuation. Frequent personnel changes and reorganizations may simply treat staff as expendable. |
| Falsification | Under comparable disturbances, withdraw S6 if recovery keeps slowing, local failures cascade, correction depends on a single point, or successors cannot obtain knowledge, permissions, and protection. |
| Scale | Cover windows for disturbances, recovery, and succession, and long windows for slow variables. Overall averages cannot hide harm at the periphery. Freeze the record of autonomy, lateral coordination, backing from higher levels, and actual authorization. |
| Evidence for stronger claims | Effects of regulation, feedback, and arrangements with multiple centers require G2/CAUSAL. For learning, institutional memory, and intergenerational uptake, first check carrier retention and actual continuity. Test traces under H5 and additional historical increments under G3. Cross-scale extrapolation requires D3/E5 and independent target evidence. Claims of closure or conversion are tested separately under G4. |
| Contract links | U01–U11, H1/H2/H3/H4/H5, G1/G2/G3/G4, C1–C12. |

S6 does not mark an absolute final state, a society without conflict, or the end of history. A collective can regress, split, be taken over, transfer functions, enter X0, or collapse. The classification cannot confer decision-making authority over others on any object.

## 8.4 Library of Nonlinear Paths {#section-8-4}

State prototypes must be used together with the path library to avoid reverting to a stage theory. A path describes “how a state configuration or object contract changes.” It does not describe “how better people advance to a higher level.” Several paths can be candidates within the same window. When evidence is insufficient, retain `unknown`.

| Path ID | Meaning | Key Distinction |
| --- | --- | --- |
| `mixed` | Necessary features of two or more prototypes occur together for the same object, scale, and window | If the differences can be mapped consistently to separate subsystems, the record should use `parallel` |
| `parallel` | Different regions, levels, functions, or positions at the center or periphery are in different states at the same time | The states must not be collapsed into an “overall stage.” Preserve K, evidence, and exit conditions for each subsystem separately |
| `jump` | Adjacent observation windows show a shift from one configuration to a nonadjacent one, with no discernible window of persistence in an intermediate prototype | First rule out overly sparse sampling and missing material. Record skipped functions, costs, and unknowns |
| `regression` | One or more functions deteriorate relative to the baseline of the same object | Distinguish abrupt and gradual decline, jumps at thresholds, and cascades. Deliberate load reduction, X0, and functional transfer do not count as regression |
| `split` | The original object divides into two or more candidate objects with different K | Temporary project groupings and modularization need not change the object. Register each new object separately |
| `merge` | Multiple objects form a new object or are absorbed by one of them | An alliance need not constitute a merger. Record the boundary, memory, exit, and outstanding responsibilities of the weaker party separately |
| `dormancy` | Visible activity decreases while memory, relationships, symbols, capabilities, or conditions for reactivation remain | Distinguish protective withdrawal, stagnation from exhaustion, disappearance of material, and actual collapse |
| `takeover` | An external subject gains control of key resources, permissions, or interfaces | External support or oversight need not constitute a takeover if genuine autonomy and the right to stop are preserved |
| `functional_transfer` | A core function moves to another object. The function can continue while the original identity, relationships, or memory disappear | Outsourcing one task does not amount to a transfer. Functional continuity does not establish continuity of responsibility or memory |
| `paradigm_replacement` | A new object with a different K, interfaces, or rules bypasses the old object without repairing it | An upgrade within the same object or a change of brand name need not constitute paradigm replacement. Outstanding obligations remain |
| `trauma_built_development` | Boundaries, identity, rules, or ways of taking up work form under harm, deprivation, failure, or threat | A narrative of trauma does not automatically establish future effects. Assess separately whether the arrangement provides protection and whether it reproduces the original harm |
| `pseudo_steady` | Surface indicators are stable while actual uptake is being exhausted, weak signals disappear, feedback fails to write back, or debts increase | Keep two ledgers, one for appearances and one for actual conditions. Revisit costs, recovery, the right to stop, and feedback from the downstream end |
| `forced_rewrite` | A subject with greater power rewrites the object when consent that can be reviewed and corrected, exit, and protection of memory are lacking | Distinguish this from authorized, negotiated revision that can be withdrawn and appealed. Check for irreversible erasure of identity |
| `external_carrier_migration` | When repair is closed off, personnel, capabilities, resources, relationships, evidence, or memory move to a safer system for taking them up | A move with no capability to take up what is transferred is not safe migration. Romanticizing departure or privatizing harm does not establish safety either |
| `collapse` | The original K ceases to hold, and functions, uptake, relationships, or boundaries break down without a plan | Distinguish collapse from X0, functional transfer, protective dormancy, and object reorganization. Releasing resources does not justify harm |

Path names likewise generate no value or responsibility. For example, `regression` does not amount to moral decline, `split` need not be failure, `merge` need not be progress, `takeover` is not automatically unlawful, and `external_carrier_migration` does not require individuals to flee on their own. Paths only allow competing explanations into the record. Mechanisms, justification, and action still require their own contracts.

## 8.5 X0 Orderly Exit and Benign Demise {#section-8-5}

X0 does not designate an eighth state or S7, and it is not counted as an eighth stage. It is an independent life-cycle path for human collectives. Maintaining the original object must no longer serve the registered anchor, and its core functions must be able to be completed, terminated, or taken up more safely. Personnel, relationships, resources, memory, debts, and appeals must also be able to be dealt with explicitly. When these conditions hold, record how the object closes out its mission, transfers functions, releases resources, preserves memory, settles outstanding responsibilities, and retains limited weak ties.

X0 requires neither S5 nor S6. A temporary initiative in S0 can close in an orderly way when it finds that the problem is already being taken up elsewhere. An expansion project in S2 can wind down if continuing to expand would only create harm. An institution stuck in S3 may also enter orderly exit if repair is infeasible and external uptake is adequate. Conversely, S6 cannot claim eligibility to disband on the strength of a “higher-stage” label. Capabilities at a stage, normative justification, and operational conditions are three distinct matters. No state ID can become a prerequisite for eligibility for self-initiated exit.

The machine contract encodes this boundary with `origin_policy` set to `any_registered_origin`. There is no minimum state requirement. `required_state_ids` is empty, and `s5_or_s6_prerequisite` is always `false`. The entry and completion conditions for X0 must not refer to S0–S6 as eligibility requirements. The IDs may only describe the starting position and must not become a threshold for exit.

### 8.5.1 Candidate Entry for X0 {#section-8-5-1}

First, the anchor has been fulfilled, ceased to apply, or been taken up by a safer object, or continuing to maintain the object chiefly serves the organization’s own persistence. This judgment must be independently reviewable. The center must not certify completion for itself after rewriting the goal. Second, personnel, functions, resources, relationships, records, debts, and irreplaceable values have been inventoried, and there are verifiable receiving parties or protective arrangements. Short-term setbacks, tight funding, leadership fatigue, or evasion of responsibility can create similar appearances. A narrative alone cannot justify a finding of “benign completion.”

### 8.5.2 Completion Conditions for X0 {#section-8-5-2}

| Aspect of Completion | What Must Be Preserved | Signs of Failure |
| --- | --- | --- |
| Anchor and object | Independent verification of completion, termination, or invalidity. The time when K ends and matters still open | Redefining the goal, deleting failures, or the center unilaterally declaring completion |
| Core functions | Mark each as completed, terminated, transferred, or unresolved. Record the receiving party’s capability, permissions, resources, and rollback provisions | A declaration alone, with no continuity for maintainers or users |
| Personnel and relationships | Safety, basic rights and interests, the right to stop, protection against retaliation, and arrangements for continuing care and relationships of dependence | Privatizing organizational obligations by leaving members to bear them on their own |
| Resources | Traceable objects, boundaries, sequence, timing, and destinations to prevent capture by those with greater power | Dividing resources internally first, then leaving the losses to low-power positions |
| Memory and evidence | Preserve successes, failures, repairs, and memory attached to positions. Specify access, privacy, correction, and protection against retaliation | Keeping only a record of victories while deleting or exposing materials from vulnerable positions |
| Debts and responsibility | Continuing responsible parties for contracts, labor, data, maintenance, environmental matters, appeals, and future risks | Responsibility, review, and maintenance all disappear when the object is deregistered |
| Weak ties | Limited to advice, shared experience, and buffering, with clear boundaries and duration | Reviving the original power structure without new authorization |

X0 outcomes should at least distinguish “candidate,” “in progress,” “partially complete,” “complete,” and `unknown`. If there are unknowns about the affected groups, outstanding obligations, the receiving party's capability, appeals, or the safety of memory, the result must not be recorded as “benign completion.” A transfer of functions without continuity of memory and responsibility may be only `functional_transfer`. Unilateral closure and rewriting of identity by an external power may be `takeover` or `forced_rewrite`. A breakdown with no uptake is `collapse` and must not be dressed up as “orderly exit.”

An X0 classification grants no authority to dissolve the object, abolish posts or units, transfer assets, publish archives, waive debts, or consent on members’ behalf. It identifies only the objects, obligations, evidence, protections, and unknowns that must be entered in the same ledger to judge whether an exit is orderly.

</div>

<SectionLesson section="8.5.2" />

<div v-pre class="theory-source">


## 8.6 How Regulation, Early Warning, and Uptake Enter State Judgments {#section-8-6}

A static snapshot alone cannot establish a state classification. The regulation layer requires observing the target, sensing, comparison, execution, feedback, and time lag. The early-warning layer requires checking whether slower recovery, larger fluctuations, more severe consequences of similar disturbances, and local flickering form a cluster. The repayment layer requires tracing who makes commitments, who bears the costs, to whom returns flow, and whose costs or claims are deferred to the future. If the apparent stability of S5 or S6 depends on off-ledger labor, silence, and future debt, the case should be treated as a candidate for `pseudo_steady`.

Clues generated by the same sequence or shared channel of change do not become independent pieces of evidence merely because they cluster. Dependent clues can still be used jointly. Their value for early warning must be evaluated under compatible dynamics, noise, sampling, and observation windows, against fixed targets, horizons, real-time baselines, and signals in the opposite direction (Scheffer et al., 2009). See D.31 and §12.6.

Clustering is not a universal prerequisite for early warning. A single domain-specific signal can be sufficient for a limited judgment. The absence of critical slowing down or a second signal does not prove safety or invalidate an existing specialist forecast. A joint rule requires a joint distribution or corresponding validation. An increase in its positive predictive value does not guarantee a reduction in total loss given false alarms, missed detections, and action costs.

Uptake cannot be assessed merely by asking whether there is a successor. Check whether a pool of potential successors, shadow roles, memory attached to positions, authorization paths, handover windows, translation of legitimacy, and protective conditions are actually in place. A clean departure by generative actors leaves a vacuum of authority if those taking up the work cannot enter. Frequent changes in personnel do not amount to adaptive renewal if key knowledge and permissions remain locked in the original center. Use H2 to distinguish uptake carriers, cost bearers, beneficiaries, rights to stop, and responsible parties. Use H3 to determine whether feedback actually changes fields and whether those changes are executed. Use H4 to examine power and observation channels, H5 to verify traces, and §4.5 to test actual continuity through the carrier. If a historical increment beyond the current representation is also claimed, test it under G3. For the candidate mechanism by which this kind of dependence strengthens across rounds, see §7.6.1.

## 8.7 Limits and Exclusions of the Current Prototypes {#section-8-7}

S0–S6 are prototypes of human collective states. A proposed classification can be refuted, can lack necessary data, can apply in parallel, and can be withdrawn. Each candidate must be checked item by item for entry, exit, observations, counterexamples, falsification, scale, evidence, missing data, and the boundary of non-authorization. If these conditions are missing, retain only an impression or mark the classification unknown. The numbers do not represent a universal evolutionary path from 0 to 6. States allow regression, parallelism, mixing, jumps, dormancy, splits, mergers, takeover, functional transfer, and collapse.

X0 is an independent life-cycle path and does not depend on S5, S6, or any minimum state. Capabilities at a stage, normative justification, and the operating conditions for exit must be judged separately. A match to a prototype cannot itself authorize dissolution, advancement, elimination, or forced conversion.

A physical metaphor must supply a formal mapping, the dimensions of the quantities involved, falsifiable predictions, and conditions for ending the analogy to enter the formal mechanism library. For example, “quantum tunneling” cannot explain why a human collective jumps to another configuration. In this framework, recording failed attempts as a historical conditional increment beyond the currently registered state still requires support from the corresponding G3-instance (see §4.5). No necessary coordination is presumed between biological death and social renewal, or between love and intergenerational transmission. Intergenerational uptake is recorded only through roles, memory, authorization, and handover interfaces.

The seven prototypes make no claim to exhaust the states of human collectives. If cases consistently fall outside them, first preserve the unexplained residuals. Then use independent materials to test whether prototypes need to be added, merged, or split. Cases must not be forced into the numbered categories.

Prototype fit, interobserver agreement, stability across windows, and practical gains over using variables directly are distinct questions. Clear cards can make a classification easier to review but cannot establish that it is reliable or more effective than a specialist description. Without actual comparisons, do not report accuracy, predictive gains, or savings in reading time. If the task calls only for direct description of members, channels, and load, the prototypes may be skipped.

## 8.8 Boundary With Actor States and Multi-Circle Projection {#section-8-8}

S0–S6 describe candidate states of human intentional collectives under a specified object contract. They do not describe individual personality, psychological maturity, or moral rank. Part 9 covers actors’ slow, intermediate-timescale, and fast variables. Part 10 covers parallel, nested, overlapping, bridging, competitive, and temporary relations among multiple collectives. Classifying a circle[^tn-circle-09] to which a person belongs as S2 does not imply that the person’s personality is at S2. A person displaying stable capability likewise does not imply that their circle is in S5 or S6.

Multi-circle projection can represent different circles as fitting different prototypes at the same time. It can also represent the same circle as having a mixed state on different scale axes. State changes must be tied to events, channels, and time windows. An institutional change in an outer layer does not automatically update inner relations, and individual exit does not automatically cause the collective to dissolve. If prototype classification adds no value beyond using the variables directly, the prototypes should be skipped in favor of a simpler joint state.

[^tn-contract-09]: Translator's note: A contract here is an analytical agreement registered and frozen before results, akin to pre-registration.

[^tn-diagnosis-09]: Translator's note: Diagnosis here denotes a nonclinical assessment of a collective configuration against the stated criteria.

[^tn-circle-09]: Translator's note: Circles may be parallel, nested, overlapping, or bridged.

</div>
