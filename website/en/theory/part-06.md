---
title: "Part 6 Operation and Evolution"
---

<div v-pre class="theory-source">

<a id="part_6"></a>

# Part 6 Operation and Evolution {#part-title-6}

This Part develops explanations of processes from object contracts[^tn-contract-07]. Operation, feedback, learning, maintenance, load, phase, and systemic selection cannot be used interchangeably in an account. They are treated through conditional mechanisms with distinct inferential premises and enabling conditions. The mechanisms also differ in their counterfactuals and stopping points. Naming a mechanism does not supply sufficient conditions. Only when the checks on dependencies, conditions, minimum evidence, and competing explanations all pass may a mechanism instance be registered within the specified SP/T/K.

## 6.1 Operation Registration {#section-6-1}

An operation record must include at least inputs, a specified carrier or channel, state transitions, outputs, environmental conditions, a time window, and possible traces. If the output returns, also register the return channel, the receiving position, and the fields that change. For a claim about intertemporal effects, first distinguish historical formation, transmission by current carriers, and additional historical increments under §4.5. Check the materials on timing and mechanism for each. Only a claim about an additional historical increment requires a comparison between a history-aware model and a model in which the current state is sufficient. If the operation crosses scales, also complete the D3/E5 mapping. This registration makes it possible to test each delay, loss, alternative channel, and gap in evidence, as well as the limits of extrapolation, without forcing a complex process into a linear chain.

## 6.2 CM-FEEDBACK Effective Feedback {#section-6-2}

Inferential dependencies: D2 and G2. E4, CAUSAL, and EVIDENCE are method checks and add no empirical causes. Effective feedback does not require G3.

The enabling conditions are as follows. A prior state or output enters a later process through a specified return channel that a G2-instance has identified. Compared with a condition with no return or with the channel blocked, at least one subsequent state, transition probability, or constraint differs by more than the threshold. The temporal order and the changed fields have been registered before the results are known. The mechanism chain is:

Prior state or output → return signal → transmission through the specified channel → signal uptake at the receiving position → change in a subsequent state, probability, or constraint → review against a blocking counterfactual

Minimum evidence includes a G2-instance that passed its pre-registration check, the return channel and receiving position, temporal order, the changed fields, the subsequent difference, and a comparison with no return or a blocked channel. Do not register effective feedback if the signal arrives but the subsequent transition is unchanged, if an independent common input explains the change, or if the difference is unchanged after the return channel is cut. Effective feedback establishes only that the return caused a subsequent change on that occasion. It does not amount to learning, repair, or a positive outcome. It requires no durable historical trace.

### 6.2.1 Feedback Delay and the Stability Interval {#section-6-2-1}

A local model that can be analyzed on its own is x\_&#123;t+1&#125;=x\_t−k x\_&#123;t−d&#125;. Here x\_t is the signed, dimensionless deviation from the target, k is a fixed real-valued gain, and d is a fixed nonnegative integer delay. The sampling interval is fixed. The model excludes external shocks, measurement noise, saturation in execution, and state bounds. For every finite initial history, the zero solution is asymptotically stable if and only if 0&lt;k&lt;2sin[π/(4d+2)]. Equality at the bounds is outside the stability interval. The proof is in Appendix C.10.

For example, let k=0.8 and set every entry in the initial history to 1. The model is asymptotically stable at delays of 0 or 1 step and unstable at delays of 2 or 3 steps. In all four cases the first step takes the value from 1 to 0.2. With the channel blocked at k=0, the value stays at 1. The model thus exhibits both effective feedback and failure of stability. Crossing the stability boundary means that a nondecaying or growing mode exists. It does not imply that every trajectory, including the one with zero initial history, grows.

Stability does not guarantee that the deviation shrinks at every step, that transient peaks are acceptable, or that execution costs are affordable. A negative x\_t indicates only that the target has been overshot. It does not represent a negative number of tasks. The equation does not model nonnegativity, demand, heterogeneous service, strategic responses, or permissions in real queues. Independent measurement and model validation are needed before applying this criterion to a real process. The criterion must not be used to set a real-world corrective gain that has not been identified.

</div>

<SectionLesson section="6.2.1" />

<div v-pre class="theory-source">


## 6.3 CM-LEARNING Feedback-Mediated Learning {#section-6-3}

Basic inferential dependencies: CM-FEEDBACK. E4, CAUSAL, and EVIDENCE are method checks. Feedback-mediated learning requires a return to cause an update that can be retained and is actually used in a subsequent task. Transmission by a current carrier and historical increments beyond the current representation are two branches, each requiring its own evidence.

`CM-LEARNING-carried` is the carrier branch. Its enabling conditions begin with effective feedback changing an internal state, parameter, rule, memory, or structure that can be located. A specified carrier retains the update or sustains continued updating, and the update is actually used in repeated rounds. The prespecified later task shows a reviewable difference relative to a predeclared baseline or an alternative process. A causal claim requires interruption, replacement, recovery, or a comparison that meets the conditions for identification. It must address common inputs, continued training, selection, attrition, and changes in measurement. A claim about transfer or predictive gain also requires evaluation suited to that claim, using an independent task or out-of-sample data. The mechanism chain is:

Effective feedback → locatable internal update → retention or continued updating through the update carrier → actual use in later rounds → change in the outcome of the prespecified task

A single parameter change, a single success, a single write-back, or the archiving of materials is insufficient to establish this learning mechanism. The corresponding mechanism claim is not supported if the update is not retained or used later, if a common input alone explains the task outcome, or if only a proxy measure changes while the prespecified task is unaffected. Effective feedback, learning in general, transfer across contexts, and net benefit are judged separately. Established learning does not imply improvement, a unified goal, or authorization to act.

When the goal itself changes, the reasons for forming the new goal and the decision procedure should be stated. The results, failures, and costs under the old goal should be preserved before a comparison is established for the new task. A goal reconstructed later must not be used to rewrite failure on the old task as success (see §2.14).

Learning in general can be supported by evidence from the relevant domain, such as new tasks that can be completed repeatedly, skills that are retained and used, or traceable teaching or organizational processes. It need not first qualify as a formal mechanism instance under this framework. A report may state together that “the practice has changed,” “the subsequent net effect remains undetermined,” and “the feedback-mediated mechanism has yet to be identified,” without collapsing these judgments into a single pass or fail. 〔Studies 16.02, 25.01–25.08, 31.08〕

Learning evaluation should also distinguish task completion with support, independent transfer after support is withdrawn, and subsequent outcomes in everyday life. Necessary support can form part of an expressive or collaborative task. In that case, failure without support does not negate an earlier success. If independent transfer was the original goal, testing it requires a comparison suited to that goal with support withdrawn. Responsibilities for choosing the goal, confirming retention of the update, measuring task performance, and judging net benefit are separate. Continuing support must not be used to deny a functional gain, and performance with assistance must not stand in for independent skill.

`CM-LEARNING-history` is the historical-increment branch. In addition to carrier updates, repeated use, and a task comparison, it requires a G3-instance that supports an additional historical conditional increment relative to an explicitly stated current representation. When the current carrier sufficiently retains what has been learned, this increment can disappear while learning through the carrier still holds. Known current carriers must not be omitted to manufacture an increment. Branches must not be switched after results are known to rescue the original test. The two routes specify their comparisons, counterexamples, and failure conditions separately.

</div>

<SectionLesson section="6.3" />

<div v-pre class="theory-source">


## 6.4 A Hypothetical Appeal Illustrating Feedback, Institutional Write-Back, and Learning {#section-6-4}

Suppose a hypothetical institution receives an appeal. This example illustrates the method of classification only. It draws on no real-world material and provides no external empirical proof.

The appeal is received and a receipt is generated. Records, rules, resources, roles, responsibilities, memory, and stopping conditions all remain unchanged. This is signal arrival alone, with neither effective feedback nor institutional write-back.

The appeal changes a case status field through a specified channel, but the change is not put into effect. This can be effective feedback in the sense of D2 while still falling short of complete institutional write-back in the sense of H3.

The field change is put into effect, and intake, field changes, actual execution, and duration are recorded. This is an instance of institutional write-back. It does not establish that the institution is normatively justified, nor does it amount to long-term repair.

When the write-back produces an update to a rule or state that can be retained, the update enters several later rounds of similar cases, and a corresponding task comparison and causal basis are available, a candidate for feedback-mediated learning through a carrier may be proposed. If a historical conditional increment beyond the current state is additionally claimed, a G3-instance tests it independently.

Thus, neither feedback nor write-back amounts to learning. The evidence requirements increase from one of the three to the next. Having an appeal entry point or making a public response cannot satisfy them all at once.

## 6.5 CM-MAINTENANCE Maintenance and Preservation–Dissipation {#section-6-5}

Basic inferential dependencies: D0 and G2. E4, CAUSAL, and EVIDENCE are method checks. D1 specifies the state terms used here. Maintenance requires advance declaration of the current K or a functional criterion F, together with a maintenance window. A G2-instance must identify replenishment, replacement, correction, or removal as the specified channel that changes how K/F continues to hold. The comparison must also cover maintenance, reduced maintenance, mismatched maintenance, and cessation of maintenance.

The mechanism chain is:

Wear, drift, loss, or component exit → specified maintenance channel → replenishment/replacement/correction/removal → change in how long K/F holds or in the probability of failure

`CM-MAINTENANCE-current` checks the effect of maintenance inputs on maintaining the current K/F. `CM-MAINTENANCE-carried-cumulative` uses §4.5 to check the current carrier of wear or capability, how previous inputs formed the carrier, and how the carrier is retained or replenished across windows. It also checks longitudinal and causal evidence that maintenance changes how K/F holds later. `CM-MAINTENANCE-cumulative` is the historical-increment branch. Add G3 only when a historical conditional increment beyond the current representation is claimed. The maintenance claim should be narrowed or withdrawn if the object continues to satisfy K/F in the target window without ongoing maintenance, if a change in maintenance input makes no difference to the relevant outcome, or if an independent shock explains the supposed wear. The contract also fails if the old maintenance criteria are still used after the original K has changed.

A need for maintenance does not imply that an object should persist indefinitely. The existence of a maintenance channel cannot directly designate a named party to take up the work, assign responsibility, or impose a duty to make sacrifices. Mismatched maintenance can prolong the period during which the old K holds while undermining the target F. An orderly stop, object conversion, or dissolution may also be outcomes permitted by the contract.

Maintenance analysis must also distinguish tasks during normal operation, migration, failure, and recovery. Interface standards specify conditions under which interoperability is possible. Actual compatibility still depends on implementation versions, business semantics, environment and load, testing, and on-site adaptation. The existence of parts does not imply that their specifications fit, their quality can be verified, personnel can reach the site, or personnel are authorized to shut the system down. Additional maintenance work can take place outside the original object and be supplied by users, households, contractors, or other institutions. Central work orders and operational outputs alone cannot account for the total amount of maintenance.

Test redundancy against failure conditions. A count of backups alone is insufficient. Two paths may share a power source, software state, transport channel, supplier, operator, or approval node. They can substitute for each other in normal operation and still fail together during a fault. Spare capacity, exposure to common causes, the time needed to switch, on-site skills, and the actual authority to switch should be verified separately. The communications, roads, fuel, spare parts, and personnel on which recovery depends should be included in the same window. Adding backups, reducing coupling, and retaining independent local operation are only candidates. Their net effects depend on the specific failure and the cost of maintenance.

## 6.6 CM-LOAD Load, Capacity, and Recovery {#section-6-6}

Basic inferential dependencies: D0 and G2. E4, CAUSAL, and EVIDENCE are method checks. Demand and capacity must be quantities of the same type or have explicit units and a conversion mapping. Demand, available capacity, replenishment, and spillover must be measured in the same window and at the same position. A G2-instance supports only the measured channel and its relevant dimensions.

The mechanism chain is:

Demand of a matching type enters the specified channel → occupies available capacity → produces an immediate gap or cross-boundary spillover → load reduction/replenishment/capacity expansion changes the gap. To explain subsequent accumulation or delayed recovery, separately check carriers of damage, capacity, or recovery and their effects across windows.

`CM-LOAD-instant` registers only demand and capacity of the same type and their immediate gap within the same window. `CM-LOAD-carried-cumulative` checks under §4.5 how historical exposure formed the current damage or capacity state, whether that state is retained or recovers across windows, and the subsequent outcomes and comparison conditions. Causal claims require grounds for identification appropriate to the claim. `CM-LOAD-cumulative` is the historical-increment branch. G3 separately tests the conditional increment beyond the current representation. Capacity that expands at the same time can absorb demand. An instantaneous gap may leave no lasting difference once it closes. Load therefore need not accumulate monotonically, and an instantaneous overload need not cause damage or collapse.

Load must be registered by position and distribution. A mean alone is insufficient. For capacity, distinguish peak and sustained levels, alternative channels, and replenishment. For recovery, distinguish recovery of visible output, of K/F, and of the internal margin. Quantities of different types cannot be directly subtracted. A need for recovery does not by itself impose a duty to make sacrifices on any subject or grant any subject authorization.

A recovery judgment should specify what recovered, for whom, under what support conditions, and through what point in time. Gather evidence separately for the quantity, quality, continuity, and accessibility of actual output. Obtain separate evidence for staff recuperation, spare parts, maintenance backlogs, and continuity of funding. Separately document the added burdens outside the boundary from care, commuting, borrowing money, or substitute services. Subsequent disruptions and near misses also require separate evidence. The pre-disaster population, current population, eligible people, and actual users must not be silently substituted for one another when calculating recovery rates. Confirming a particular limited function does not require all other outcomes to recover at the same time.

Temporary facilities, continuing outside support, or assistive equipment can provide real functional repair. Dependence on support does not by itself indicate failed recovery. The sustainability and expiration of support should be verified, along with whether alternative arrangements for providing that support are already in operation. Any demand peaks, maintenance cycles, or seasonal exposures that have yet to be experienced should also be specified. The term “false recovery” should be reserved for a claim that extends beyond what the evidence supports about the object, population, function, or conditions for continuation. That alone provides no basis for inferring deception. If destabilization recurs after recovery, compare the persistence of earlier damage, unreplenished reserves, interruption of support, new shocks, and changes in measurement definitions separately. A new failure must not erase an earlier result stated within its proper limits. Necessary support must not be withdrawn to validate recovery.

</div>

<SectionLesson section="6.6" />

<div v-pre class="theory-source">


## 6.7 CM-PHASE Phase and Threshold Transition {#section-6-7}

Basic inferential dependencies: D0 and D1. E4 and EVIDENCE are the shared method checks for the phase pattern branch. Add CAUSAL when making a causal claim about a trigger, persistence through a carrier, or historical-increment hysteresis. It is not a prerequisite for basic pattern classification. A purely predictive historical increment does not thereby become causal. Basic phase identification does not require G3. Under the same candidate object contract and K, testing for at least two reproducibly distinguishable ranges of operation is possible once the state variables, candidate parameters or trigger conditions, threshold, and robustness checks for noise and binning are registered in advance.

The mechanism judgments have the following branches.

`CM-PHASE-pattern` is the phase pattern. It requires “the same K, two reviewable intervals, and a prespecified threshold pattern.” It registers only the relation between the intervals and the threshold and makes no causal claim about the trigger.

`CM-PHASE-causal-trigger` is causal triggering. It requires “a specified trigger channel and either an intervention on the channel or natural variation suitable for identification.” A G2-instance is also required to locate the effect of the trigger.

`CM-PHASE-carried-persistence` checks how, under the same K, the current carrier maintains a phase, sustains it across windows, or gives rise to delayed recovery. Use §4.5 to document the carrier and temporal order, make longitudinal comparisons, and obtain causal evidence appropriate to the claim. `CM-PHASE-hysteretic` is limited to the historical-increment branch of hysteresis. A G3-instance separately tests the conditional increment beyond the current representation. An identical curve shape cannot stand in for evidence under either route.

The phase conclusion should be withdrawn if a continuous trend fully explains the change within the same state distribution, if the threshold shifts arbitrarily with the binning, or if K had already ceased to hold before the transition. Record the result as continuous change, an effect of how the measurements were partitioned, or object conversion/dissolution, respectively. A reversible phase need not have a historical path. Only the historical-increment hysteresis branch adds G3. Phases do not form a mandatory S0–S6 sequence of maturation. A new phase does not thereby rank higher, become better, or carry greater authorization.

## 6.8 CM-SELECTION Variation–Differential Retention–Reproduction {#section-6-8}

Basic inferential dependencies: D1. E4, CAUSAL, and EVIDENCE are method checks. This mechanism has its own operationalization. It does not follow automatically from the definition of “evolution has occurred,” and a conceptual explanation or the framework’s account cannot establish it directly.

The three outputs must be kept separate.

`CM-SELECTION-pattern` is the selection pattern. It requires “V, D, R, entry into the next round, repeated rounds, and random drift as a competing explanation.” Before results, define distinguishable variations V and their sources. In comparable environments, observe differential outcomes D that exceed the threshold. The differences must carry forward into the next round through retention R and be reviewable across repeated rounds. Test random drift, common external causes, and sampling bias at the same time. The sole basic dependency is D1.

`CM-SELECTION-carrier` is the specific mechanism. It requires “a specified channel of retention or reproduction and either a perturbation of the channel or natural variation suitable for identification.” Beyond an established pattern, a G2-instance is required to locate the carrying mechanism.

`CM-SELECTION-history` is the path across rounds. It requires “a conditional increment from historical terms across rounds and control for the current state.” Beyond an established pattern, a G3-instance is also required.

Change without D amounts to change alone. A one-off difference with no R, no entry into the next round, and no repeated rounds is a one-off outcome. Do not register a selection pattern if the random-drift model is already sufficient. If retention remains unchanged after the candidate reproduction channel is perturbed, do not register that specific mechanism. One instance of persistence does not amount to differential retention. What is retained does not thereby become better, more advanced, or more justified. Systemic selection is distinct from choice by an acting subject and from collective governance choice. A choice by an acting subject requires a subject, options, and evidence of a decision. Collective governance choice requires normative premises, J-axis authorization, and O procedures.

## 6.9 Conditions for Coevolution {#section-6-9}

A candidate for coevolution may be proposed when two candidate objects change each other’s environments, feasible paths, specified channels, or retention conditions and the effects in both directions are traceable within their respective time windows. The record must separately include the two objects’ D0 contracts and K, their respective SP/T, the G2 channels in both directions, temporal order, differences in speed, and the shared environment outside the two objects. Obtain separate evidence under §4.5 for carrier effects across rounds. Add the corresponding G3-instance separately only for claims of historical conditional increments beyond the current representation.

Joint change, synchronized fluctuations, and long-term correlation cannot substitute for bidirectional mechanisms. One-way dependence, common shocks, and synchronization of measurement protocols are competing explanations that must be considered. Coevolution does not imply symmetry, mutual benefit, shared values, or a duty to maintain the relationship.

A shared final state does not establish a shared mechanism. Two processes can converge on the same fixed point while having different update rules, speeds of return, transients, and responses to intervention. A simpler representation may suffice if the only question concerns the long-run terminal value. The original conclusion does not automatically extend to questions about whether the target can be reached by a deadline or about targeted operations. Analyses of recovery, coevolution, and cross-circle continuation must retain these differences as required by the question. Convergence of the curves cannot substitute for identifying the mechanism.

## 6.10 Dissolution, Object Conversion, and the Limits of Repair {#section-6-10}

The criterion for dissolution is that the original K no longer holds. If the original K fails but another object contract can hold, object conversion should be distinguished from termination. A phase change is distinguished from dissolution only if the original K continues to hold. Dissolution does not automatically count as failure, and persistence does not automatically count as success.

Repair uses the target K* or F* made public before results as its criterion. It can make use of old traces, and it can change components, boundaries, relations, interfaces, carriers, and scale positions. It does not turn back time to an earlier state. A claim about a repair window requires K*/F* and a comparison of how intervening at different times affects the attainability of the target and cost. Use the carrier route to obtain evidence about current constraints formed through history. G3 is additionally required only for a claim of a historical conditional residual beyond the current representation. Even if these empirical conditions hold, whether the goal is normatively justified, who chooses it, who is responsible, and who may implement it are still subject to review under the N layer, the J axis, and O1–O4.

### 6.10.1 Formation, Maintenance, Recovery, and Replication {#section-6-10-1}

That an arrangement forms, that it can then be maintained, that it can recover after a disturbance, and that it can be replicated elsewhere are four outcomes, each with its own conditions and evidence. Formation usually requires start-up conditions and a path of transition from the original state. Whether maintenance depends on continuing replenishment, replacement, and correction is tested under §6.5. Recovery depends on the carriers and margins still available after the disturbance, the external replenishment that can be reached, and the time remaining; whether what recovers is output, K/F, or internal margins is specified separately under §6.6. Aiming at a K*/F* made public in advance rather than seeking a return to the original state is called repair and is judged under §6.10. When the arrangement is replicated in a new location, the results in the original location provide only a candidate; the new location must itself have the corresponding personnel, equipment, time, and conditions for error correction, and must have its own materials.

The four are judged separately, and none can vouch for another. All four are also descriptive judgments and do not mean that the arrangement should be maintained, recovered, or replicated. Operating well in the current period can coexist with no one taking it up in the next round; that longer-term or wider-scope results have not yet been demonstrated also does not cancel local results already achieved under prespecified criteria. When replication or scaling up fails, distinguish at least four situations: the scheme itself fails, including cases where the results in the original location were not caused by the scheme; the scheme was not implemented as written in advance; the new location lacks enabling conditions the mechanism requires; or scaling up itself changed the treatment or the object (§2.4.1). Both what was implemented and the enabling conditions must be written down before results and be verifiable independently of results. An implementation deviation or a missing condition raised only after failure is registered only as a candidate to be tested in the next round and does not change the present record.

</div>

<SectionLesson section="6.10.1" />

<div v-pre class="theory-source">


## 6.11 Final Gate for Mechanism Outputs {#section-6-11}

For each of the six conditional mechanisms, complete the object and scale declaration, inferential dependencies, enabling conditions, mechanism chain, minimum evidence, competing explanations, counterexamples, and failure boundary in that order. If any item is missing, retain only a candidate mechanism or a question to check. Feedback alone does not establish learning. Instantaneous load does not establish accumulation, and a basic phase does not establish hysteresis. A selection pattern neither establishes a mechanism nor warrants a value judgment. Maintenance and repair do not establish a duty to persist. Conceptual explanations and teaching examples only illustrate how to use the contracts. They supply no external empirical support.

## 6.12 Operation with Multiple Asynchronous Clocks {#section-6-12}

A multi-circle joint state includes at least immediate, interactive, organizational, institutional, and long-term clocks. An event can first change fast variables, then change expectations about relationships through repeated interaction, then change resources through organizational decisions, and only then potentially lead to institutional write-back. If these changes are compressed into one moment, a delay can be misread as a lack of effect, or a short-term fluctuation as long-term evolution.

Changes in fast variables do not automatically indicate long-term institutional outcomes or outcomes in everyday life. Industrial expansion, a signed agreement, the end of overt violence, the completion of facilities, or public cooperation still calls for checking execution, distribution, rights, relations, and continuity. If the material is insufficient, retain the local results that are known and stop extrapolating over longer ranges.

Each mechanism should declare its update clock and its bridges across clocks. The arrival of a feedback signal does not establish that organizational rules have changed. An organizational decision does not amount to institutional execution. A change in institutional text does not imply actual write-back at every local position. A bridge across clocks must specify the carrier, execution, confirmation, and failure conditions.

| Clock Transition | Minimum Evidence for the Bridge | Common Failures |
| --- | --- | --- |
| Immediate→Interaction | A difference in state persists over multiple rounds and changes the other party’s response | A one-off emotional reaction fades |
| Interaction→Organization | Changes in relations or strategies are incorporated into roles, processes, resources, or records | Verbal consensus is not put into practice |
| Organization→Institution | Verifiable changes in rules or procedures, arrangements for responsibility, and actual execution. Authorization, legal validity, and normative justification are registered separately | A document is issued without implementation, or an institutional change that actually occurred is omitted because it lacked legal validity |
| Institution→Long Term | Continued execution, maintenance, learning, and alternative paths | Rebound after short-term compliance |

The table records how changes actually carry forward. Legal validity, normative justification, and authorization do not serve as criteria for establishing that an event occurred. Rule changes and their execution must enter the process record if there is corresponding factual evidence, even when they violate rules, exceed authorization, or are contested. Record their authorization and legal status separately. Explaining how they formed and what consequences they had does not amount to permitting their implementation. Conversely, authorization, issuance of a rule, or an institution’s announcement of completion cannot substitute for evidence of actual execution.

## 6.13 Cross-Circle Cascades and Coevolution {#section-6-13}

A cascade occurs when a local change in one circle[^tn-circle-07] triggers changes in other circles through overlapping membership, bridging interfaces, shared resources, network propagation, or top-down institutional transmission. The object, channel, scale, and evidence must be checked again at each step. The first step holding does not warrant assuming that all later steps hold. Capacity limits, filtering, delays, offsetting effects, and local exclusion zones can cut a cascade short.

For cross-circle propagation, first identify what propagates and what conditions the target needs in order to change. A message can arrive through a single bridge. An action that requires actual cooperation from several people, confirmation from different sources, or adequate support for acting safely can stall in that same network. A count of relays from one source cannot stand in for a count of independent confirmers, and a count of confirmers cannot stand in for actual collaboration. A bridge’s effect depends on how the sources are related, where the transmission arrives, the order of arrival, the duration of action, and the conditions of feasibility. It cannot be determined directly from the shortest path, the number of connections, or any one model threshold.

Also distinguish one failure triggering the next, multiple failures jointly obstructing recovery, and a common external cause damaging multiple locations at the same time. The first requires evidence of transmission at each hop. The other two require checks on recovery dependencies and exposure to common causes, respectively. Mechanisms of human adoption based on multiple sources can coexist with supply dependencies among facilities, but their state variables and thresholds cannot be interchanged. Complex contagion does not guarantee that higher clustering is more beneficial. Gains from reinforcement can be offset by reduced reach across groups.

Coevolution requires at least two objects to change one another’s selection environments, transition probabilities, or constraints over a period of time while retaining their independent K. If one object is simply absorbed by another, record it as nesting or object conversion. Synchronized changes due solely to a common external environment do not qualify as coevolution. If a return signal changes no subsequent state, classify the observed relationship only as coupling or shared exposure.

Multi-circle cascades and coevolution carry no inherent direction of value. Tighter coupling can improve coordination or increase vulnerability and diffuse responsibility. Decoupling can reduce efficiency or protect local autonomy and the ability to limit losses. Evaluation and action still belong to the normative layer.

## 6.14 The Search Order for Mechanisms and Paths {#section-6-14}

For a specific question, first screen for potentially applicable mechanisms according to the object, scale, window, and requested output. Then look for paths based on observed differences in state. The state prototypes for human collectives apply only to objects that meet the corresponding conditions. Actors, technical systems, and natural processes must not be assigned the same set of states merely because their names are similar.

Start the search with four kinds of material. These are the object’s current state that can be confirmed, direct changes that can be confirmed after the event, channels, capacities, and clocks that can carry later changes, and mechanisms and external disturbances not yet distinguished. Use a state’s exit conditions to propose candidate paths and observed changes to propose candidate mechanisms. Then check the enabling conditions, stages of propagation, and minimum evidence item by item. The order serves only to locate candidates. Finding one earlier does not make it more likely to be true.

When using a candidate, retain competing candidates and simple baselines that can explain the same phenomenon. Return signals should be distinguished from learning. Local overload should be distinguished from temporary rises in demand, declining capacity, and common external causes. Cross-circle cascades should be distinguished from synchronized exposure. Counterexamples and exclusions specified in the relevant full contract must not be omitted merely because the search found a match.

For each candidate path, state separately the conditions under which it continues to hold, the observable changes the mechanism should produce first, signals to the contrary, and the stopping point. Without evidence of enabling conditions, a candidate can still guide observations designed to distinguish the alternatives. It cannot be promoted to an identified mechanism. An early signal must not be just a scaled-down restatement of the outcome. When paths share evidence, citing it again does not add independent support.

The search order may be adjusted in light of missed cases, misclassifications, and the cost of use. Adjustments must preserve the original limits of applicability for the mechanisms and be compared with simpler search methods. Ease of search, a complete set of cards, or the use of the same order by several analysts does not establish that a real-world mechanism holds.

[^tn-contract-07]: Translator's note: A contract here is an analytical agreement registered and frozen before results, akin to pre-registration.

[^tn-circle-07]: Translator's note: Circles may be parallel, nested, overlapping, or bridged.

</div>
