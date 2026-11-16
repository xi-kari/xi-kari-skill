---
title: "Part 11 Event-Driven Dynamic Projection"
---

<div v-pre class="theory-source">

<a id="part_11"></a>

# Part 11 Event-Driven Dynamic Projection {#part-title-11}

Dynamic projection starts from a joint state with evidential statuses recorded. It analyzes state differences, transmission, feedback, and branching after observed, reported, planned, hypothetical, or simulated events. Actions that actually occur can change reality with or without authorization. They must all be recorded according to the evidence. Whether an action occurred, how it is evaluated normatively, any legal or institutional authority, and permission to carry it out on this occasion must each be judged separately. Projection must specify which changes can be established directly, which are only conditional consequences, and which signals would support or weaken the corresponding paths.

</div>

<SectionLesson section="intro-11-part" />

<div v-pre class="theory-source">


## 11.1 The Difference Between Projection and Narrative Continuation {#section-11-1}

Narrative continuation can choose what comes next by coherence alone. Structural projection must preserve conditions, channels, competing paths, and the meaning of failure. If key variables are missing, the projection should stop at an unknown or generate variable candidates. It must not fill the gaps with the smoothest story. If several continuations are consistent with existing evidence, keep them as separate branches. If paths are incomparable, do not force an ordering.

The minimum inputs to projection are a frozen snapshot, event records, mechanism hypotheses, parameter ranges, a clock policy, a propagation policy, unknowns, and stopping conditions. The minimum outputs are a path graph, state differences at each step, support status, early signals, contrary signals, residuals, variable candidates, and write-back requirements.

| Input | What Must Be Frozen | Consequence If Left Unfrozen |
| --- | --- | --- |
| Joint snapshot | Actors, circles[^tn-circle-12], relations, M/Ψ, clocks, and evidence cutoff | The starting point is rewritten after the results |
| Event | Type, time, source, objects reached, and channels | Rumors, plans, and facts are conflated |
| Mechanism | Direction, carrier, delay, threshold, and failure conditions | Each outcome can be explained arbitrarily |
| Parameter | Value, interval, level, or explicit unknown | False precision masks uncertainty |
| Stopping | Conditions involving information, risk, exceeding bounds, and resources | The story continues indefinitely |

</div>

<SectionLesson section="11.1" />

<div v-pre class="theory-source">


## 11.2 The Event Contract[^tn-contract-12] {#section-11-2}

There are five kinds of event: observed, reported, planned, hypothetical, and simulated. The type must be included in the record. A reported event can affect people who believe it but must not automatically be treated as having occurred. A plan may change expectations without amounting to execution. A hypothetical event serves conditional analysis. A simulated event belongs only to a model run and must not be written back as a fact about reality.

An event record must include at least the event ID, time or window of occurrence, time of observation, source, affected actors, affected circles, channels, direct changes, evidential status, disputes, competing explanations, reversibility, duration, and subsequent observations.

| Event Type | Permitted Uses in Projection | Factual Status | Required Limits |
| --- | --- | --- | --- |
| Observed | Explanation, replay, and forward projection | Holds within the observation contract | Sources, omissions, and measurement error |
| Reported | Propagation of belief and conditional projection | That a report was made does not establish that its contents are true | The reporting party’s position, verification, and disputes |
| Planned | Expectations, preparations, and strategic interaction | Existence of the plan does not establish execution | Authorization, resources, and conditions for cancellation |
| Hypothetical | Counterfactuals and scenario comparison | No factual status in reality | Conditions, purpose, and feasibility |
| Simulated | Unfolding paths within the model | Model state only | Model version, parameters, and prohibition on extrapolation |

</div>

<SectionLesson section="11.2" />

<div v-pre class="theory-source">


## 11.3 The Joint State Update Formula {#section-11-3}

The joint state can be written as follows.

`Ω(t) = <A(t), C(t), R(t), M(t), Ψ(t), Q(t), E≤t, SP(t), W(t), K(t)>`.

An update can be written as follows.

`Ω(t+Δ) = F[Ω(t), e(t), u(t), ξ(t) | θ, h]`.

Here `e(t)` is the event, `u(t)` is an externally authorized action that actually occurred, `ξ(t)` is an exogenous disturbance or unmodeled residual, `θ` denotes the frozen hypotheses about mechanisms and parameters, and `h` is the historical term. The formula specifies only what must be recorded. It does not assert that there is a unique true F, and the function symbol must not be used in place of specific mechanisms.

Observed violations, actions beyond authorization, refusals to carry out orders, and unauthorized acts in another’s stead are recorded as `observed/reported` events under `e(t)` with their evidence. The actor, consequences, and status of their authority must be recorded separately. The lack of authority must not be grounds for deleting an event from the factual record. Violations that have not occurred enter only `hypothetical/simulated` branches. The definition of `u(t)` still requires authorization and actual occurrence. Feasibility in a scenario does not amount to permission in reality. 〔Studies 15.08, 21.03, 21.08, 28.06, 32.08〕

Each update must distinguish directly observed state differences, inferences supported by the mechanism contract, scenario values set to explore a path, and residuals still unexplained. All four retain their provenance in subsequent paths. Appearing together in a snapshot does not give them the same evidential status.

</div>

<SectionLesson section="11.3" />

<div v-pre class="theory-source">


### 11.3.1 States, Observations, and Identified Sets {#section-11-3-1}

A joint snapshot is a structured representation of the material currently available. It does not directly read every state of the world. Let `z(t)` denote the actual state yet to be inferred for the current task, and `o(t)` the record produced by observation rule H, sampling positions, and conditions of data collection. It can be written as `o(t)=H[z(t),m(t),ε(t)]`. `m(t)` includes who can enter the record, when they are measured, and which fields are withheld from disclosure for protection. `ε(t)` is used only when there is a corresponding error model. Unknowns must not all be called random noise. When conditions allow, numerical measurements can use additive error. Text and categorical records use their corresponding generation rules. Ω should preserve the distinction between the records and the judgments, so a change in observation rule is not mistaken for a change in the object.

The same set of records can correspond to several states or mechanisms. Let `Z(o)` denote the set of states still compatible with the record under the stated model and error bounds. If the answer to question q is the same in every state in `Z(o)`, the current material is sufficient for the question. A limited answer can be given without recovering every latent variable. If the values differ, the output should retain their range, any direction that can be identified, or the parts that genuinely remain unknown. Failure to detect a difference in a finite sample does not automatically establish that only one answer remains over the entire set.

The set also helps plan the next observation. First identify state distinctions that would change the current answer or the comparison of actions. Then check which feasible observations could distinguish them. More precision that leaves the answer unchanged need not help. A low-cost observation that narrows an important branch may be more valuable than expanding the whole variable table. Data collection remains subject to purpose, necessity, and protection. A need for identification does not confer permission to collect data.

</div>

<SectionLesson section="11.3.1" />

<div v-pre class="theory-source">


### 11.3.2 Event Processing and State Continuation {#section-11-3-2}

Each input retains the time of the event, the time the record was obtained, and the time it entered the model. Material that arrives late can change what is now known about the past, but it cannot rewrite the information set available at the time. When correcting a source, append the link to the correction and recompute the states and paths that depend on that source. Retain local results that do not depend on it. When multiple sources recount one event, retain those sources and a single candidate identity for the event to avoid applying the same shock more than once. Events with similar descriptions must not be merged without verification.

State updating consists of two operations. An evidence update revises the judgment about `z(t)`. Advancing the mechanism estimates the change from `z(t)` to a subsequent state. A credible record that “work stopped yesterday” is an evidence update today. The stoppage itself belongs to yesterday’s real events. Rerunning a model and obtaining another response that work “may have stopped” adds only simulated material. Both kinds of update can change Ω, but their reasons and evidential statuses must be kept separate.

Concurrent events may be combined in any order only if the operations commute, shared resources are not in conflict, and neither changes the other’s conditions. If two actions compete for a resource, overwrite the same record, or change each other’s available action set, retain branches for the possible orders or specify an explicit rule for concurrency. Similar timestamps do not establish simultaneity. The order in which execution calls return does not by itself reveal the causal order of real events.

</div>

<SectionLesson section="11.3.2" />

<div v-pre class="theory-source">


## 11.4 The Nine-Step Projection Loop {#section-11-4}

</div>

<SectionLesson section="11.4" />

<div v-pre class="theory-source">


### 11.4.1 Step One. Freeze the Current State {#section-11-4-1}

Record the evidence cutoff, objects, variables, unknowns, disputes, and model version. Information obtained after the cutoff must not be fed back into the starting point. If it needs to be used, create a new version of the run.

</div>

<SectionLesson section="11.4.1" />

<div v-pre class="theory-source">


### 11.4.2 Step Two. Identify Actors and Circles {#section-11-4-2}

Use Parts 9 and 10. If a circle has no grounds for object facts and the grouping gain claimed for it is not supported, retain it as a candidate grouping. If there is insufficient support for a personality hypothesis, retain it as a variable candidate. Do not turn candidates into entities merely to complete the graph.

</div>

<SectionLesson section="11.4.2" />

<div v-pre class="theory-source">


### 11.4.3 Step Three. Separate Conditions in the Two Channels {#section-11-4-3}

List the relevant material conditions separately for the task. Also list the relevant experience–meaning conditions and declare the bridges needed between channels. If missing information from the other channel affects the current judgment, retain the unknown. Do not fill the gap by assuming symmetry. A channel genuinely irrelevant to the current task may be marked not applicable with a reason. Do not collect experiential material for the sake of completing the form. Suspend only propagation that depends on the missing channel. Independently established states and paths can still be carried forward.

</div>

<SectionLesson section="11.4.3" />

<div v-pre class="theory-source">


### 11.4.4 Step Four. Declare Clocks, Thresholds, Capacity, and Delay {#section-11-4-4}

Identify each variable’s update clock. If a channel has capacity limits, delay, loss, saturation, reversal, or a recovery window, register them before propagation.

</div>

<SectionLesson section="11.4.4" />

<div v-pre class="theory-source">


### 11.4.5 Step Five. Inject an Event or Action {#section-11-4-5}

A run may include multiple events and actions ordered by time, with their independent sources retained. First determine whether an action occurred, then record the actor, object, consequences, and authorization status separately. Lack of authorization cannot justify deleting a fact about what actually occurred. Plans, proposals, and simulated actions that have yet to occur retain their conditional status and must not be recorded as executed. If a model initiates or carries out a real-world action, valid authorization must be obtained separately. A recommendation for deliberation requires only that its evidence, normative premises, costs, gaps in authority, and conditions for revising the judgment be stated clearly.

</div>

<SectionLesson section="11.4.5" />

<div v-pre class="theory-source">


### 11.4.6 Step Six. Propagate Along Declared Channels {#section-11-4-6}

First record directly confirmable state differences, then analyze return signals, indirect effects, and cross-circle cascades. An identified total effect of an intervention may enter a bounded judgment about the outcome. Unidentified parts of the internal mechanism remain unknown. The total effect must not be used to fill in missing edges of propagation. Explaining specific propagation requires corresponding material about channels and temporal order. Where there is only co-occurrence or correlation, retain common background, selection effects, and other competing explanations. Store state differences derived conditionally from the model separately from those observed in reality.

</div>

<SectionLesson section="11.4.6" />

<div v-pre class="theory-source">


### 11.4.7 Step Seven. Generate Paths at Branch Points {#section-11-4-7}

Conditions, thresholds, actor choices, external disturbances, or uncertainty about mechanisms can all produce branching. Keep mutually exclusive paths separate. Retain parallel paths if they can occur at the same time. Create a merge node only when the conditions for merging are clear.

</div>

<SectionLesson section="11.4.7" />

<div v-pre class="theory-source">


### 11.4.8 Step Eight. Register Signals, Residuals, and Variable Candidates {#section-11-4-8}

List early and contrary signals for each path. State differences that the current variables cannot explain enter the residuals. A residual can prompt an entry in the ledger of variable candidates, but cannot automatically supply a value in reality.

</div>

<SectionLesson section="11.4.8" />

<div v-pre class="theory-source">


### 11.4.9 Step Nine. Write Back the Results {#section-11-4-9}

When actual results arrive, append which paths are supported, when results diverged from the projection, whether a simple baseline performed better, how well the projection was calibrated, and which mechanisms or variables should be downgraded, split, given revised boundaries, or retired. Write-back does not overwrite the original run.

</div>

<SectionLesson section="11.4.9" />

<div v-pre class="theory-source">


## 11.5 Propagation, Delay, and Thresholds {#section-11-5}

An account of propagation must at least distinguish the arrival of a signal from an effective change of state. If information is seen but does not change a subsequent transition, record only arrival. If it changes beliefs without prompting action, record the change in experience–meaning state. Register a corresponding structural change only if the signal changes resources, behavior, rules, or relationships.

| Propagation Factor | Question for the Record | Possible Nonlinearity |
| --- | --- | --- |
| Channel | What carrier conveys the impact from the source to the target? | Channel closure, filtering, or substitution |
| Capacity | How much can be carried per unit of time? | Saturation, congestion, and queues |
| Delay | When does it arrive, and when does it take effect? | Delayed feedback or a mistaken finding of no effect |
| Threshold | What conditions must be reached before the state changes? | Abrupt changes, hysteresis, and cascades |
| Loss | What is lost or changed in propagation? | Drift in meaning or dissipation of resources |
| Direction | Is the impact symmetric? | One-way dependence or offsetting effects in the opposite direction |
| Recovery | How does the object return to its previous state or move to a new one after a shock? | Resilience, cumulative damage, and lock-in |

When the same event reaches different circles through different channels, the effects can be opposite. Additional resources may reduce load in one circle but intensify competition in another. A public statement may repair external legitimacy but activate shame or distrust within the circle. A projection should record each channel separately. Net effects must not hide differences in distribution.

</div>

<SectionLesson section="11.5" />

<div v-pre class="theory-source">


## 11.6 Feedback and Cross-Circle Cascades {#section-11-6}

Feedback requires a prior state or output to change a subsequent state, transition probability, or constraint through a return channel. A cascade requires a local change to trigger changes in other circles through membership overlap, bridging, shared resources, top-down institutional transmission, or network propagation. Both require evidence of temporal order and channels.

| Kind of Cascade | Typical Chain | What to Observe | Stopping Condition |
| --- | --- | --- | --- |
| Membership | Overlapping members carry behavior, emotions, or information into another circle | Actual transmission as distinct from shared background | Members stop participating or information is not received |
| Resources | One circle takes up, releases, or reallocates resources | Accounting boundaries, conversion, and loss | Resources are isolated or an alternative source is available |
| Meaning | An interpretation of the event changes identity, legitimacy, or trust | Differences in interpretation across positions | The interpretation does not reach other circles or does not change their experience–meaning states. Effects on action or rules are checked separately |
| Institutions | An appeal, audit, or event changes rules that are then implemented at lower levels | Decisions, execution, and actual write-back | The rule is not implemented or is offset locally |
| Platforms | Recommendations, metrics, or public evaluations amplify propagation | Algorithms, selective visibility, and reflexivity | Exposure stops increasing or the audience does not respond |

The importance of a cascade does not automatically increase with scale. A small circle can have a large impact through a crucial bridge, while a large circle may have no effective propagation because its channels are blocked. A projection should focus on positions, channels, and thresholds. Membership counts alone are insufficient.

Two local effects can form a transmission chain only with shared conditions for response. Consider two subgroups of equal weight. In the first, the event changes the mediator, but the mediator does not affect the outcome. In the second, the mediator can affect the outcome, but the event cannot change the mediator. The mean effect on each edge is one-half, yet the effect of the event on the outcome across the entire chain can still be zero. This finite construction shows that the mean edge effects cannot be multiplied unconditionally even if the two studies use the same population. It is also necessary to know whether the successive effects occur in objects, states, and times that allow them to connect.

A cascade record should therefore check how the output of the preceding segment enters the next one, the scope of support for joint response, capacity and delay, and offsetting and parallel paths. A limited total effect already identified through an eligible comparison can be retained directly. What is added here is the responsibility to explain the specific propagation. It does not require explaining all micromechanisms before acknowledging any effect. When an edge has yet to be identified, retain the independently established upstream changes and terminal effects according to their own evidence.

</div>

<SectionLesson section="11.6" />

<div v-pre class="theory-source">


## 11.7 A Graph of Branching Paths {#section-11-7}

A path node must include at least the parent node, condition set, triggering event or action, state differences, affected clocks, support status, a probability or ordering expression, early signals, contrary signals, the next node, and the reason for termination. The path graph should be a directed acyclic graph. If there is a feedback loop in reality, represent it with new nodes unfolded over time. A node must not be its own cause and effect within the same run.

Four kinds of uncertainty can produce branches: uncertainty about facts, uncertainty about mechanisms, actor choices, and exogenous disturbances. Different kinds should not be merged into a single vague probability. Give priority to verifying uncertain facts. Address mechanism uncertainty through observations that distinguish the alternatives. For uncertainty about choices, retain strategies and authorization. For exogenous disturbances, use scenario ranges and resilience checks.

| Source of Branching | Example | Appropriate Output | Inappropriate Output |
| --- | --- | --- | --- |
| Facts | Did the event actually occur? | Conditional paths before verification | Choosing one version as fact |
| Mechanisms | Does silence come from fear or strategy? | Signals that distinguish the alternatives and parallel paths | Shutting down inquiry with a personality label |
| Choice | An actor cooperates, resists, or exits | Conditions and consequences of each choice | Claiming that free choices can be predicted precisely |
| Disturbance | Change in policy, prices, disasters, or technology | Stress scenarios and conditions for recovery | Attributing unmodeled residuals to fate |

</div>

<SectionLesson section="11.7" />

<div v-pre class="theory-source">


## 11.8 The Ledger of Variable Candidates {#section-11-8}

Residuals that the model cannot explain must neither be deleted nor immediately named as real variables. The candidate ledger turns “what might we have missed?” into a testable task. Each candidate record must include at least the source residual, name, possible type, possible channel, observable implications, competing candidates, minimal test, privacy and risk, current status, evidence, and conditions for upgrading or rejecting it.

Candidate statuses include proposed, under test, supported candidate, rejected, and retired. Even with support, a candidate still has to enter the relevant object or variable contract. It must not directly become a stable personality, a supported circle, or a causal mechanism. Candidates proposed after results can improve the next model but cannot retroactively support the original prediction.

| Candidate Source | Permitted Action | What Must Be Avoided |
| --- | --- | --- |
| Residuals in the system | Propose several competing candidates and observations that distinguish them | Absorbing all errors into one mysterious variable |
| Account by a person concerned | Preserve the person’s position, the meaning of their account, and its verifiable parts | Automatically downgrading it to subjective noise or elevating it to a complete account of the facts |
| Recurrence across cases | Establish candidate mechanisms and limits of extrapolation | Treating similar narratives as universal laws |
| Model search | Pre-register the next round of testing | Selecting the best results for reporting after seeing them |
| AI suggestions | Generate and compare candidates. Form judgments and analytical recommendations when the evidence, permitted uses, and explicit normative premises allow | Letting AI output verify facts about reality or authorize action |

The framework can only identify residuals the current set of variables cannot explain, propose several distinguishable variable candidates, and design a minimal test with acceptable risk for each. It cannot decide on its own that a candidate is true in reality.

</div>

<SectionLesson section="11.8" />

<div v-pre class="theory-source">


## 11.9 Scenarios, Counterfactuals, and Simulation {#section-11-9}

Scenario projection asks, “If these conditions hold, what paths emerge?” A counterfactual asks, “If an event or mechanism had been different, how might the outcome that actually occurred have changed?” Simulation unfolds specified rules and parameters. All three must be kept separate from descriptions of fact.

Counterfactuals especially require comparable conditions. When removing an event, also state which subsequent states, actors’ information, and circle relations change as a result. Do not remove an unwelcome cause while retaining all its consequences. The precision of a simulation cannot exceed what its inputs and evidence of mechanisms support. When parameters are unknown, use ranges, levels, or sensitivity analysis. Do not generate unsupported decimal places.

Counterfactuals must preserve the information boundaries at the time. Replacing an event or choice means reassessing the beliefs, resources, orders, and downstream behavior it affects. Do not remove an announcement while holding fixed the attendance and subsequent execution it brought about. Evidence for a short-range branch does not mean an alternative history decades later is already knowable. The actions of ordinary people, the discretion of frontline personnel, and organizational constraints can all enter the explanation. There is no need to assign causal percentages without a basis for identifying them. 〔Studies 03.03, 32.04, 32.08〕

The strength of a counterfactual conclusion depends on whether mechanisms still compatible with the evidence give the same answer under the altered operation. Two mechanisms can both produce observations of `X=M=Y`. In one, X changes Y through M. In the other, X changes M and Y separately. This co-movement alone cannot establish whether setting M directly would change Y. More observations of the same kind can improve the precision of the record but need not resolve this equivalence between mechanisms. A design that distinguishes the two mechanisms or independently grounded assumptions are needed. If independent materials already identify the total effect of a specified treatment within stated limits, retain that effect even if a particular mediator has yet to be identified.

Counterfactual analysis can therefore produce one answer, a set of feasible answers, or conditional bounds. Treat a direction as robust only when all compatible mechanisms support the same conclusion. If the conclusion reverses across plausible mechanisms, report the conditions under which it reverses and list the evidence needed to distinguish the mechanisms as the next observation. Historically, “removing a person from the post they came to occupy” and “that person having never been there” have different starting points and processes of adaptation. They cannot share the same counterfactual answer.

</div>

<SectionLesson section="11.9" />

<div v-pre class="theory-source">


## 11.9.1 Multi-Order Recursive Projection of the Future {#section-11-9-1}

Advancing time over multiple steps, re-entry from a simulated state, and anticipatory reflexivity are three orthogonal dimensions. Advancing time over multiple steps carries a state forward in time within a single run. Simulation re-entry uses a simulated future generated in the first round as the starting point for a child run. Anticipatory reflexivity occurs when actors in the simulation form expectations about the more distant future or other people’s responses and change their current strategies. These three operations must not be conflated under the single term “recursion.”

Three orders are one default way to organize exploratory projection. The first unfolds direct consequences and competing paths. The second checks how those changes alter the available actions, resources, relationships, and adaptation. The third checks institutionalization, lock-in, reversal, and changes in conditions for generation. The orders mark responsibilities in projection. They do not amount to three points in time, natural stages, or levels of capability. Do not force recursion for static questions or tasks without a distinct question at the next order. Stop when conditions are insufficient.

The layer that generates possibilities may be bold. The state layer must be strict, the evidence layer must not raise its own status, and the action layer still needs separate authorization. Boldness can expand the space of plausible mechanisms, competing paths, and branches with low probability and severe consequences. It also helps produce clear judgments within the limits of the evidence. The strength of a judgment is supported only by evidence, conditions of applicability, and permitted uses. Tone or the number of generated possibilities cannot make it stronger.

</div>

<SectionLesson section="11.9.1" />

<div v-pre class="theory-source">


### 11.9.2 Recursive Interfaces and Lineage {#section-11-9-2}

Before each re-entry, conduct a recasting audit. Record the current order, parent run, parent path, parent node, simulated time, the current order’s time window and the cumulative window, model version, inherited assumptions, new conditions, what is preserved, changed, collapsed, or omitted, new unknowns, effective variables for the target, residuals, identity across re-entry, the return path, and the reason for stopping. The simulated starting point must not be rewritten as present reality.

A child run must inherit the unresolved unknowns, losses, and residuals of its parent run. Selecting a hypothetical branch only narrows the conditions. It does not mean material from reality has eliminated the uncertainty. Increasing the number of draws may reduce computational error. It does not increase empirical support about outcomes in reality.

</div>

<SectionLesson section="11.9.2" />

<div v-pre class="theory-source">


### 11.9.3 Branching, Merging, and Pruning {#section-11-9-3}

At each order, check whether there are substantive grounds for the main path, its strongest competitor, a path with low probability and severe consequences, and a route for residuals. Retain all conditions for paths that have grounds. If a category is inapplicable or a path of that kind cannot be constructed, explain why. Do not invent an event to fill a category. Branches must correspond to explainable differences in mechanisms, choices by actors, external disturbances, or unknowns of a specified kind. Retaining a path with severe consequences means only that it calls for investigation or preparation. It does not establish that its real-world probability is known.

Branches may be merged only when object identity is preserved, key states are equivalent within a predetermined tolerance, differences in history do not change subsequent transitions, and the available actions and constraints agree going forward. Pruning rules must be declared in advance. Preserve pruned branches, reasons for pruning, any possible probability mass, and the level of harm. Low probability alone cannot justify removing a path with severe consequences.

</div>

<SectionLesson section="11.9.3" />

<div v-pre class="theory-source">


### 11.9.4 Early Stopping {#section-11-9-4}

Stop or downgrade if object identity or scale identity fails, key assumptions cannot be inherited, the transition mechanism falls outside its domain, the recursive interface lacks closure, or branches proliferate without signals to distinguish them. Also stop or downgrade if the results reverse across the board under small changes, residuals exceed the threshold for the intended use, a deeper order adds nothing relative to a shallower one and a simple baseline, the calibrated time window is exceeded, a boundary of rights or authorization is reached, or the third-order limit is reached. The stopping record must state what can still be said and what cannot.

</div>

<SectionLesson section="11.9.4" />

<div v-pre class="theory-source">


## 11.10 Stopping Conditions for a Projection Run {#section-11-10}

Affected propositions and the paths that depend on them should be suspended or downgraded if a key object lacks grounds for object facts or a grouping-gain claim on which a path depends is not supported, the event’s factual status is unclear, a propagation channel is missing, a cross-scale mapping fails, or the number of paths grows without signals to distinguish them. The same rule applies if the model is extremely sensitive to small changes in parameters, privacy or safety risks exceed the value of the information, the projection is asked to generate a diagnosis, punishment, or authorization directly, or a simple baseline already performs as well or better. If a shared premise or the overall conditions for use fail, all related runs stop.

Stopping is part of the output. It must not be used to conceal failure. The stopping record should state where the projection stopped, what has been obtained, which unknowns prevent continuation, which next observation would be most informative, and what risk further projection would add.

</div>

<SectionLesson section="11.10" />

<div v-pre class="theory-source">


## 11.11 An Example of a Cross-Circle Cascade {#section-11-11}

Continue with the public departure from a job in Part 10. The starting snapshot shows that the employee faces long working hours and the pressure of care work, team trust is declining, company management is concerned with reputation, the professional community provides outside opportunities, and public opinion on the platform has yet to form. The event is the employee publishing an account of their departure. Part of its content can be verified, and part is personal narrative.

Direct effects include the team receiving the information, the platform obtaining a text that can be circulated, and management facing pressure to respond. On the first path, the company makes only a public denial. In the short term, external public opinion may branch toward either fading or amplification. If members inside the company interpret the denial as suppression, team trust declines and further departures occur through bridges in the professional community. On the second path, the company acknowledges the problem and starts verifiable adjustments to resources and appeals. If these are carried out, working hours and processes change on the organizational clock. Trust may recover more slowly on the experience–meaning clock. On the third path, changes in family care conditions ease the employee’s pressure after leaving. This does not directly change the team’s state unless the employee continues to bridge information or resources.

Early signals can include the number of internal appeals, records of hours actually worked, members’ public statements, and changes in hiring and departures. Contrary signals can include no actual change in resources after a policy is announced, increasing internal silence despite declining external exposure, or the professional community failing to form a bridge. Residuals may come from the states of key managers, the platform’s recommendation mechanism, or unobserved legal constraints. These enter only the ledger of variable candidates.

The projection still cannot say which path the company “should” take. It provides conditional consequences and signals that distinguish the paths. Forecast registration, comparison of options, normative premises, and authorization are addressed in the next Part.

</div>

<SectionLesson section="11.11" />

<div v-pre class="theory-source">


## 11.12 Outputs of This Part {#section-11-12}

A qualifying projection output should include a frozen joint snapshot, event type and evidence, mechanism and parameter assumptions, update steps, and a path graph. For every path, it should record conditions, clocks, support status, and early and contrary signals. It should also include residuals and variable candidates, stopping conditions, a plan for writing back results, and an explicit statement separating prediction and action.

Projection can improve structured preparation for what follows, but it remains conditional. Without registration before results, a simple baseline, calibration, and continuing write-back, it cannot support a claim that foresight capability has improved. Without normative grounds and authorization, it cannot support a claim that an action should be carried out. An analysis based on explicit normative premises can recommend an option, reject it, or recommend deferral. None of these judgments establishes that the option has been authorized for execution. For each such judgment, its grounds, costs, opposing case, and conditions for revision must be stated in full.

</div>

<SectionLesson section="11.12" />

<div v-pre class="theory-source">


## 11.13 Action Choice and Updating Conditions {#section-11-13}

For dynamic questions involving actors, having a model evaluate a set of static options is insufficient. At each step, first use the current state to identify actions actually available, actions ruled out, and the source of the restrictions. Then analyze how an actor might choose given their information, resources, relationships, habits, and goals. Capability, belief, willingness, and actual action must be kept separate. Being able to act does not mean the actor will act. Stating an intention does not mean it has been carried out. An analyst’s recommendation does not amount to adoption by the actor.

For each choice with a basis in the material, specify which mechanism it triggers, which states change first, who is affected through which interfaces, and how these changes alter the set of actions available at the next step. State differences must be expressed in concrete terms such as resources, rules, relationships, beliefs, or feasible actions. Feeding the same materials to another model and generating another narrative cannot substitute for updating a state. If the material does not determine the choice, retain several conditional paths. Do not decide for the actor just to continue the projection.

Later projection starts from explicitly stated conditional state differences and inherits unresolved unknowns and restrictions. When real feedback arrives, first verify its source and event status. Then compare the original path, competing paths, and the simple baseline. Distinguish factual errors, mechanism errors, different choices of action, deviations in execution, and external changes. The corrected result should change the states, parameters, scope of mechanisms, or paths used in the next round. Keeping only the text of the feedback while retaining the same choice rule does not warrant claiming that the model has learned.

[^tn-circle-12]: Translator's note: Circles may be parallel, nested, overlapping, or bridged.

[^tn-contract-12]: Translator's note: A contract here is an analytical agreement registered and frozen before results, akin to pre-registration.

</div>

<SectionLesson section="11.13" />

<div v-pre class="theory-source">

</div>
