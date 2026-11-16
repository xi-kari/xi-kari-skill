---
title: "Part 16 Governance"
---

<div v-pre class="theory-source">

<a id="part_16"></a>

# Part 16 Governance {#part-title-16}

Using the framework to explain other objects does not exempt the framework itself from structural problems. Documentation can grow unwieldy, concepts can harden, tools can be captured by power, and users can come to depend for their identity on language they have invested in. The governance layer supplies practical interfaces for downgrading concepts, suspending assertions, blocking publication, rolling back versions, and replacing the framework. Decorative principles cannot do that work.

This Part governs four distinct objects: the current text and templates, the relations among concepts, the actual practices of users, and the community of maintainers, critics, people who provide counterexamples, and people affected. They must not be collapsed into a single “framework.” A consistent document does not establish that there is no misuse in practice. An active community does not establish that the empirical question families have been validated.

The framework cannot use its own language to establish that it is safe. Internal consistency, passing stress tests, passing validation, and complete reports establish only that certain outputs of a process are complete. They do not establish real-world safety, effective repair, or consent from affected people, and do not confer authorization to act in reality.

Tool implementations should turn these boundaries into verifiable governance constraints. Internal statuses cannot establish what holds in reality by their own declaration. Governance records do not confer real-world authorization. Terminal records do not erase history. Formal adoption requires grounds in external review or approval suited to the intended use. Substituting aliases, self-reporting independence, or citing records circularly cannot satisfy these requirements. Whether the requirements have been implemented in a particular program and actually used must be verified separately. The requirements in the text do not constitute evidence of implementation.

This Part’s status and permission rules apply to the framework’s own text, modules, formal assertions, governance changes, and related high-impact uses. The rules do not claim to replace legal procedures in different jurisdictions or treat an external institution as nonexistent or invalid merely because it has not adopted these record formats. The legal validity, normative justification, and actual protection of an external institution, and whether the framework endorses its use, must still be judged separately.

## 16.1 GOV-01 Framework Self-Diagnosis[^tn-diagnosis-17] and Separation of Objects {#section-16-1}

Self-diagnosis begins by specifying what is being examined. A blanket judgment that the whole framework is “healthy” cannot serve as the starting point.

For the document, check whether the text, table of contents, definitions, templates, and rules contradict one another.

For the concepts, check whether the empirical question families, universal variables, human adapter, normative choice, or procedures for action exceed their scope.

For practice, check how users actually diagnose, manage, teach, make public statements, and use AI.

For the community, check who controls naming, merging, interpretation, and publication, and who bears the consequences of misuse.

Each self-diagnosis must record at least the object type, version, rights holders, route for submitting counterexamples, harm observed, falsification conditions, and judgment ceiling. If dependence on jargon, cognitive lock-in, an expert monopoly, accommodation of commercial interests, or a veneer of AI compliance has already caused harm, the affected module may be restricted, suspended, or assessed for replacement.

## 16.2 GOV-02 Consensus Procedure and Authority Over Versions {#section-16-2}

“Everyone agreed in the end” does not establish effective consensus. For consensus to be effective, differing views must be able to enter safely, be recorded and answered, and materially change the text and practice. The procedure has at least seven steps.

Register the issue. Introducing a concept, substantially rewriting the text, changing empirical question families, and reporting misuse or counterexamples must first become traceable issues.

Disclose the material. List cases, counterexamples, user feedback, external research, failures in practice, and ethical risks.

Identify what is affected. Specify the users, people being diagnosed, low-power subjects, and settings that the change would affect.

Provide access for dissent. Users with little power, people being diagnosed, nonspecialist readers, and external critics must all be able to submit objections.

Distinguish decision levels. Minor revisions, changes to core concepts, and changes to empirical question families require distinct authority.

Preserve minority views. Objections that are not accepted must not be deleted. They enter the record of retained counterexamples and unresolved questions.

Write back to the version record. State what was introduced, removed, or downgraded, the reasons, and what evidence would lead to withdrawal of the change.

If the institutional arrangements rule out the possibility that dissent could trigger a necessary correction, the procedure may be recorded only as `nominal_only`. It cannot be used to restore a suspended module. Selection of participants, terms of office, time limits, and statutory powers must be pre-registered separately for the particular organization, jurisdiction, or community. Uniform numbers must not be copied without regard to the organization, jurisdiction, risk, and resources.

Each objection must have a `disposition`, grounds for how it was handled, evidence used, and its effects on the text, procedure, or action ceiling. An accepted objection’s effect must link to the actual `change_id`. Objections that are declined for stated reasons must remain on record. `applied` does not require token acceptance of at least one objection. It requires that reasons capable of changing a key judgment, protection, or permission all be addressed in a way suited to them. Suspend the affected adoption if any such objection remains unresolved, required independent review is missing, or any requirement of the rights floor or any nonwaivable requirement of applicable law is unmet. Whether an objection is decisive is determined under criteria published in advance, open to appeal, and independently reviewable. The proposer or a majority cannot establish that on its own.

`applied` indicates only that the governance change meets the framework’s conditions for internal adoption. It does not establish that the change works in reality or confer permission for external action. Upholding a correct decision for stated reasons can constitute an adequate review. If correction is needed and does not occur, a record of responding cannot count as completion. The value of participation, causal feedback, actual change to the text, eligibility for internal adoption, and real-world protection are judged separately. Emergency duties still operate under their independent authority, scope, validity period, and review conditions.

## 16.3 GOV-03 Correcting Empirical Assertions and Choosing Which Question Families to Keep {#section-16-3}

Correction starts by distinguishing three objects. A proposition about a specific instance can be overturned by counterevidence suited to it. A generalization across instances or a claim about coverage can be limited by counterexamples within its scope. G1–G4 as a classification of questions have no independent empirical truth value. Whether to keep, restrict, or retire them depends on whether they omit important questions, reduce confusion, what they cost to use, and their net benefit relative to a domain method or a simpler baseline. Positive results in several instances do not establish that a question family exhausts reality or that the classification is optimal.

Question families and their application modules can use the following five management statuses. These statuses govern use and maintenance and do not replace the evidential status of any specific proposition.

`normal_use`. Continue use for stated purposes. Each instance claim is still judged on its own evidence. Frequent use does not establish that the classification adds value.

`boundary_restricted`. Restrict use where the classification misses important distinctions or adds burdens for particular objects, tasks, scales, or institutional settings.

`suspended`. Suspend affected uses and retain existing independent facts when the classification or module continues to produce identifiable misjudgments or high-risk misuse.

`replacement_competition`. Compare domain methods, simpler methods, and alternative question classifications on the same tasks and materials with resources suited to the comparison. Assess judgment quality, omissions, unwarranted abstention, and total burden separately.

`retired_from_core`. The question classification no longer constrains the shared core. Material that remains useful can be retained as a domain tool or a historical record. Preserve known results from its specific instances separately according to their evidence.

Public assertions have the progression `internal_draft → open_assertion → publishable`. At any stage they may move to `downgraded`, `suspended`, `publication_blocked`, `withdrawn`, or `replaced`. The framework as a whole can operate only among `active`, `boundary_restricted`, `suspended`, `replacement_competition`, `replaced`, and `retired`.

`retired_from_core`, `withdrawn`, `replaced`, and `retired` are terminal states. They have no outgoing transition to `active` or another in-service state. Rollback cannot restore old authorization. A return to service under a successor method requires a new identifiable identity, fresh external authorization, and preservation of the history of the old terminal state.

Repeated counterexamples, consistent misjudgment of a kind of subject, ever-expanding scope of explanation, and evasion of refutation by saying only “the other party is not a system,” “there has not been enough time,” or “the evidence is not deep enough” all trigger suspension and review. Counterexamples must be handled in a way suited to what they bear on in the argument. A valid local counterexample changes the corresponding boundary. Repeated systemic failure triggers comparison with alternatives. Misuse causing serious harm suspends the affected use. If review finds that a counterexample does not refute the original claim, preserve the reasons and the conditions under which they would cease to hold. A correct claim must not be changed just to show responsiveness. Counterexamples must not all be set outside the theory.

The consequences of a counterexample should match the claim it actually bears on. First check the object, measurement, auxiliary conditions, mechanism, and scope of extrapolation. Then decide whether to make a local correction or replace the core. Do not attribute every anomaly to the core or reclassify every anomaly as falling outside it. A local revision requires independent grounds and new testable consequences. Conditions must not be added after the fact merely to explain a known failure.

## 16.4 GOV-04 Tracking Cases, Counterexamples, Assertions, and Forecasts {#section-16-4}

The five kinds of authoritative record are linked. Each serves its own purpose and cannot substitute for another.

`COUNTEREXAMPLE-REGISTRY`. Record the object of the counterexample, scale and window, observable facts, reasons it is not noise, original and alternative explanations, requirements for handling it, and subsequent signals.

`CASE-REGISTRY`. Preserve successes, failures, early dispersals, unfinished processes, counterexamples, indeterminate cases, and excluded cases. For excluded cases, record “whether the insufficiency of material is itself a blind spot of the framework.”

When using a set of cases to compare mechanisms of formation, failure, or dispersal, or to estimate the proportion of a result, state the object, outcome, spatial and temporal window, and entry rule. Preserve actions and processes that had a relevant opportunity to occur but did not. Do not put all unrelated nonoccurrences into the same denominator. Assess the possibility of occurrence and the conditions for detecting it in the material separately. Lack of a record that can be checked cannot be entered directly as zero. A theoretical expectation cannot be the sole reason to exclude a real counterexample. If a boundary is disputed, preserve the judgments under different reasonable scopes and how they change. Interpreting a single case does not require defining a population for frequency estimates. A professional case-selection record that meets the same requirements can be cited directly (Mahoney and Goertz, 2004, authors’ manuscript).

`CLAIM-REGISTRY`. Record the assertion’s text, type, object, scale, affected positions, evidence, counterevidence, alternative explanations, withdrawal conditions, action ceiling, and publication status.

`FORECAST-REGISTRY`. Record the prediction, time window, triggers, early signals, contrary signals, competing predictions, and outcome at expiry. This is conditional foresight. It does not determine anyone’s fate.

`VERSION-LOG`. Enter counterexamples, narrowed boundaries, downgrades, suspensions, blocks on publication, withdrawals, replacements, retirements, rollbacks, and remedies in a public ledger.

A formal judgment made in the framework’s name must have a corresponding `CLAIM-REGISTRY` record to qualify for publication or high-impact use under the framework. Ordinary discussion, independent domain research, and well-grounded local opinions remain responsible for sources, correction, and use according to their own tasks. They do not lose their standing as knowledge for lack of a framework ID. More cases on record do not establish broader applicability. Internally selected cases do not amount to external validation. Strong-judgment and authorization requirements still apply when the output enters organizational action or automated decisions.

Governance changes have seven additional runtime registries: canonical actor, evidence, relationships of interest, authorization, external review, objections, and the structured `VERSION-LOG`. Every `evidence_ref` must resolve to an evidence record with integrity status `verified`. Reviewers, members who make the decision, and subjects of authorization must use a `canonical actor ID`. Check each one’s relationship to the proposer for funding, evaluation, identity, promotion, control, and commercial interests. Aliases can be used only for retrieval and cannot substitute for identity. The issuer of authorization must not also be its holder or the proposer.

## 16.5 GOV-05 The Pre-Concept Gate and Ceiling on Conceptual Validity {#section-16-5}

The framework must not force something into the category of “structural domain” and then use its own concept to prove that classification. Before formal mapping, answer in plain language. Can the parts be observed together? Is there a minimum boundary? Do actions within it repeatedly affect one another? Is there a shared problem, direction, risk, or constraint? Who bears the costs of maintaining it? Can results or bad news change subsequent practice?

If the pre-concept gate fails, the output is limited to describing phenomena, registering risks, or analyzing narratives. Even after it passes, the concept may be used at only one of five levels of strength.

Expressive level. Helps only to state feelings or similarities clearly.

Exploratory level. Can generate only questions and signals to observe.

Diagnostic level. External observable material permits judgments with low to moderate confidence.

Strong-judgment level. The object, evidence, scale, responsibility, and observation checks have all passed.

Action level. Requires external review, appeal, anti-retaliation, compensation, and withdrawal in addition to normative choice under Part 14, J authorization, and O procedures.

## 16.6 GOV-06 Absence Signals, Protective Opacity, and Suppressive Opacity {#section-16-6}

What is not visible can still carry information. Absence of an anchor may mean no shared orientation ever formed. Absence of feedback may mean there is no channel or people are afraid to speak. Absence of conflict may come from fear, dependence, or punishment. Absence of repair may mean there is no interface for it. Absence of exit may mean the cost of leaving is unbearable. Absence of language may mean people lack the means to express themselves.

Opacity has three kinds.

`protected`. Protects vulnerable subjects, privacy, witness safety, experience that is still taking shape, and feedback from people with little power.

`functional`. Reduces information overload and preserves room for necessary professional judgment, ritual, buffering, or undisturbed decision-making. It requires subsequent review and tracing of responsibility.

`suppressive`. Obscures responsibility, blocks feedback, evades review, produces fear, preserves a monopoly on power, or prevents people who were harmed from proving the harm.

Classification must answer four questions. Who is protected? Who benefits? Who can review independently? When is the opacity lifted? Opacity must not be recorded as a healthy boundary if the four answers, independent review, time limits, or conditions for lifting it are incomplete. Suppressive opacity directly triggers measures against capture, external review, and a block on public release.

The time limits and conditions for lifting opacity govern continued review of the grounds for confidentiality. They do not require sensitive material to be disclosed automatically on a particular date. Review may continue protection or disclose only what is sufficient for a limited judgment. Inability to confirm that opacity is justified does not establish suppression. A confidentiality label also cannot conceal falsified records, evasion of responsibility, or obstruction of credible verification.

## 16.7 GOV-07 Operating Limits of Stage 6 and Stopping Observational Recursion {#section-16-7}

The qualified reference for this module is `governance.module.GOV-07 → hsp.domain.human_intentional_collective → hsp.state.S6`. It applies only to objects that independent runtime records confirm are human intentional collectives and whose status includes `hsp.state.S6`. It does not apply to individual humans, nonhuman systems, or human collectives that have yet to meet S6. Stage 6 here is no universal level of the world broadly conceived.

Stage 6 does not transcend entropy increase or describe a perfect system. For a specified function, object, and limited window, it requires evidence of problem detection, correction of errors, restoration of function, and continuity when others take over. It must also meet the conditions of applicability in Part 8. Record detection lag, repair lag, recurrence rates, resource margins, and load distribution separately. Processes measured in different units must not be combined into a single speed. Current operation that is going well can support a judgment about the corresponding function. It cannot by itself certify Stage 6. Genuine recovery under continuing support does not automatically cease to count because support has yet to be removed.

Observational recursion may expand only when a new response changes boundaries, identity, resources, channels for action, uptake relationships, feedback write-back, risk, or public memory, or supplies a new signal that is costly to produce. Recursion must end when two consecutive rounds yield only the same kind of response, the object begins manipulating diagnostic rules, continued tracking would increase exposure, the informational gain is less than the disruption to the structure, or the diagnostician can no longer distinguish the object’s state from the products of observation.

After stopping, do not keep asking “what the object really is.” State only that a particular response pattern can be confirmed under current observation conditions. Further judgment requires external review or new external evidence that distinguishes the alternatives.

## 16.8 GOV-08 Malicious Compliance and Auditing Selective Evidence {#section-16-8}

Malicious compliance occurs when forms, evidence chains, reviews, and appeals are completed selectively while sources are still manipulated, weak signals filtered, inaction dressed up, or responsibility obscured. It differs from open violation. Check each of ten signals. There is only one source. Counterexamples are dismissed as noise or emotion. Open assertions become labels. Appeals never change outcomes. Supposedly independent parties are controlled by the same chain of power. AI reports lack original materials and external verification. Diagnostic language is used to justify inaction or avoid accountability. Potential fields, entropy increase, and stages are used to dress up inaction. Love, mission, the larger interest, or professional expertise are invoked to continue extracting from people with little power. People who appeal are subsequently described as irrational because they appealed.

Three or more signals block strong judgments. At five or more signals, record a high risk of malicious compliance. Only risk registration, a request for external review, and exploratory steps for protection may then be output. The party audited cannot certify the reviewer’s independence.

Three and five are procedural thresholds for starting protection and review. They are neither constants read from nature nor calibrated probabilities of malice. A trigger means a strong judgment should not proceed under present conditions. It does not establish that anyone deliberately deceived others. Review must state dependencies among the signals, costs of false alarms and misses, and the particular circumstances. Any change to the thresholds should disclose its grounds through the version procedure. Thresholds must not be changed on the spot after a case outcome is known.

## 16.9 GOV-09 AI Boundaries and What Process Outputs Can Establish {#section-16-9}

AI can organize materials and verify their identity, propose and compare mechanisms, form grounded judgments and critiques that can be refuted, recommend options under disclosed objectives, normative premises, and constraints, and draft institutional arrangements, plans, and commentary for deliberation. Outputs should state the current choice, key grounds, costs, strongest opposing case, and conditions that would change it. They should also present in full the substantive analysis already conducted. AI must not invent sources or protection conditions. Fluent text, internal scores, and completion of a procedure cannot establish the commissioning party’s good faith, effective anti-retaliation, or actual repair. AI cannot substitute for independent review or bearing responsibility. It cannot independently make a high-risk real-world decision or substitute a claim that the procedure passed for a decision by a subject with authority. An analytical recommendation does not amount to actual adoption. High-risk decisions and real-world execution still require the applicable procedures for strong judgments, protection, normative choice, and authorization.

AI outputs should check original facts, testimony from affected positions, counterexamples, feedback from people with little power, external review, records of appeals changing outcomes, who controls the evidence, and AI’s selection and rewriting of material, according to the task and proposed conclusion. For each, state how it relates to the conclusion, whether it is available, and what limits follow from its absence. The count of missing items alone does not determine the ceiling for the whole output. Do not make a factual finding without decisive evidence for it. Retain competing explanations when causal identification lacks discriminating evidence. Without adequate protection and review, do not certify actual safety, consent, fairness, repair, or eligibility for high-impact adoption. Evaluations of arguments in texts, local factual judgments, and conditional recommendations under explicit premises that are unaffected by the gaps can stand separately. Give reasons for any finding of inapplicability. It must not substitute for an unknown or bypass a real risk. Outputs still governed by strong-judgment and real-world action provisions remain subject to their requirements.

Process outputs do not establish what holds in reality. Fluent prose, automatic scoring, internal stress tests, consistency matrices, validation passes, report counts, and complete forms cannot establish repair, consent, safety, or effectiveness.

## 16.10 GOV-10 Six Components of Weak-Signal Protection {#section-16-10}

Weak signals cannot depend only on a diagnostician being “willing to listen.” `WEAK-SIGNAL-PROTECTION` must register each of the following items.

WS1 Anonymous or low-exposure submission. People can submit facts without first disclosing their identity.

WS2 Independent parties to receive and take up the material. It must not go only to the chain of power being questioned.

WS3 Anti-retaliation records. Record loss of power, isolation, stigma, punishment, and changes in resources after feedback.

WS4 Calibration by group. Overall satisfaction or average performance must not hide deterioration among groups at the margins.

WS5 Delayed disclosure. When safety is at risk, protect those providing signals before discussing disclosure.

WS6 Evidence of write-back. After a signal is taken up, actual changes to rules, resources, responsibilities, or authoritative records must be visible.

If any component is missing, the output may say only that “the risk to weak signals has been recognized.” It must not claim that “weak signals have been protected.” One weak signal does not directly establish a conclusion. It also does not automatically disappear because it is infrequent, anonymous, emotional, or incomplete in form.

## 16.11 GOV-11 An Intermediate Path Without Institutional Infrastructure {#section-16-11}

Families, intimate relationships, friendships, small teams, and temporary communities often lack independent reviewers, stable appeal procedures, and complete evidence chains. They can still involve ongoing harm, control of information, relational dependence, and risks to reputation or safety. `NO-INFRASTRUCTURE-PATH` does not simulate institutions that are absent, require people affected to take risks gathering evidence, or equate “cannot be reviewed” with “no facts can be recorded.”

It can output only a protective open assertion. State the current material, the continuing pattern that most warrants concern, prohibited uses, escalation signals, withdrawal signals, and a low-risk next step. The objective moves from “proving who is wrong” to reducing exposure, preserving records, restoring support, seeking an outside perspective, and observing subsequent signals. It must not be used for punishment, dossiers, eligibility decisions, public classification, or deprivation of resources.

## 16.12 GOV-12 Protection of Subjects Unable to Exit {#section-16-12}

Children, people with severe dependencies, people whose income sources are controlled, incarcerated people, people bound to care arrangements, or people with extremely limited resources may be unable to exit. Remaining does not amount to consent. `INABILITY-TO-EXIT-PROTECTION` requires six safeguards: prioritize safety, provide trusted representatives, restore minimal choices, information, records, and connections to support, keep records with low exposure, provide local buffers and alternative ways out, and prohibit romanticizing inability to exit as love, loyalty, maturity, sacrifice, or service to the larger interest.

People should not have to remain exposed to prove their circumstances. Allow submission through a representative, delayed expression, phased disclosure, outside arrangements to take over, preservation of evidence, and refusal of direct dialogue. The objective of protection under conditions that prevent exit is to reduce harm, preserve subjecthood, and expand future choices. An ideal exit must not be forced.

The tasks taken on by a trusted representative must be specified. Record the grounds and scope separately for assisting understanding and expression, submitting materials for someone, handling a matter delegated by the person, and making a decision on the person’s behalf. A representative’s statement cannot automatically be recorded as the person’s own expression or consent. Preserve means of communication the person can use, conflicts of interest, conditions for refusing or changing support, review of objections, and continuity of necessary support. If the person’s wishes remain unclear, state the support efforts made, grounds for interpretation, and uncertainty. Substitute decisions and emergency measures in records or institutions also require separate checks on their institutional basis and normative disputes. Kinship, professional qualifications, or convenience of representation do not establish full standing to represent. Recording requirements must not be used to interrupt necessary support or force disclosure. See the Committee on the Rights of Persons with Disabilities, General Comment No. 1 (2014) and its 2018 corrigendum. For representation and authorization, see M07 and D.21.

## 16.13 GOV-13 Complex Trauma and the Absence of a Healthy Baseline {#section-16-13}

Some structures have never had a healthy state. First distinguish structures that departed from a healthier state, structures with a nominal anchor that has hollowed out in practice, newly formed structures that never developed a healthy anchor, and structures whose rules, identities, boundaries, and relations were formed through trauma.

For the latter two, `TRAUMA-NO-HEALTHY-BASELINE` asks what minimum safety means now, whether the subject is receiving predictable support for the first time, whether they can express themselves without punishment, whether small instances of trust can be repeated, which survival strategies previously protected them but are becoming constraints, and whether a new anchor can be found or must be built together. It does not ask “how to get back to the original state.”

Treatment, clinical care, caregiving, child protection, or legal tasks requiring particular qualifications should be handled under the corresponding professional procedures. Expertise and credentials do not confer authority over the whole of someone’s life. Goals the person values, communication they can understand, objections, and refusal must still be addressed in the relevant procedure. Emergency duties and authority over particular matters require independent grounds that apply to the case. The framework cannot infer them into existence. State scope, validity period, review, and continuity of support separately. The framework cannot use its theory to invent a healthy past. See §1.3, §2.8, and §14.2 for limits on authority, and §15.3.8 for emergency tasks.

“Trauma-built” is a candidate description of the formation history of some structures. It does not designate complex post-traumatic stress disorder or another clinical diagnosis. Harm that calls for protection now can be recorded first. The formation history, particular psychological mechanisms, and professional classification each need evidence. Present harm cannot be used to infer that every relationship was formed by trauma. People do not have to establish that an ideal past once existed to receive support.

## 16.14 GOV-14 Keeping Open-Ended Undertaking, Normative Premises, and Metaphorical Drift Separate {#section-16-14}

Love must not be treated as “the remainder that structure cannot explain” or as a favored label for a motive. A description of bounded voluntary undertaking uses `HV11-R1-voluntary-limited-action`. First check the action, identifiable costs, direction, voluntariness, and genuine conditions for refusal, exit, or negotiation. Also check competing explanations such as interests, fear, benefits of identity, inertia, dependence, and coercion. The result can be achieved, unrealized, harmful, or unknown. Successful structural consequences are not an entry requirement for R1. Failed attempts must not disappear by definition.

A causal judgment about structural consequences uses `HV11-R2-structural-consequence`. Whether the action changes safety, the ability to refuse, appeal, resources, or later possibilities for affected positions must be judged separately under the relevant G2/causal contract. A beneficial result cannot establish voluntariness retroactively. Sincerity and high costs cannot substitute for evidence of effects. Normative approval of the action also requires disclosure of the N premises adopted, the protection floor, and costs to others affected. Whether the description holds, whether the effect holds, and whether the action deserves approval are questions that can each be answered affirmatively or negatively. Risks identified by R0 can generate requirements for protection directly without waiting for R1 or R2 to receive support.

These routes constrain the framework’s judgments about particular undertakings and their consequences. They do not exhaust the meaning of love, care, or goodwill in general. Kindness at low cost, private companionship, creative attempts that did not succeed, and the value of ordinary relationships can matter in the appropriate context. Failure to meet a route’s conditions does not negate the actor’s inner life or personality. Voluntarily bearing a limited cost does not create an unlimited duty to continue. Necessary arrangements for others to take over and release from responsibility must be justified separately for the matter at hand.

A broad utility representation can incorporate concern for others, identity, or commitments. Representing a choice as optimal does not by itself identify the reasons for acting or replace a judgment about its normative standing (see Sen, 1977). Filling in benefits after seeing choices so that any outcome becomes optimal cannot distinguish competing explanations. Exploratory extensions can be retained. A claim of new explanatory capability must state which outcomes the new model can distinguish relative to the old one, on what grounds, and what materials would make the explanation fail. See §2.4 and D.15.

Normative premises must be disclosed and referred to Part 14. The framework openly commits to protecting subjects with little power and rejecting uses of structural language that erase responsibility. It favors access to appeal and withdrawal and the continued development of successors able to take up the work. They do not follow automatically from facts as neutral conclusions.

The status of a concept used across domains must be marked as metaphor, analogy, candidate mechanism, corroborating empirical evidence, formal model, or verified rule. “Resembles” must not be rewritten as “follows.” Cases from physics, biology, or animal behavior do not directly establish conclusions about human organizations or institutions. Each metaphor must specify similarities, differences, risks of misuse, and evidence that would lead to stopping its use.

## 16.15 GOV-15 Knowledge Lineage and Source Transparency {#section-16-15}

For each concept that can be traced, record its intellectual affinities, specific source, version, what was retained, adapted, or abandoned, cross-cultural and cross-domain risks, and what the source can and cannot support. Acknowledging intellectual affinities does not weaken the framework. It reduces mystification and dogmatism.

Theoretical material cannot substitute for case evidence, a single case for a universal rule, an internal summary for original records, or an AI summary for a traceable source. The framework establishes interfaces for interoperability with other theories. It does not present itself as an overarching framework that absorbs them all.

Connections among bodies of knowledge should preserve where disagreements arise. Some theories estimate different outcomes. Some propose competing mechanisms for the same outcome. Some adopt different value premises. Common naming must not erase these differences. When retaining a method, state what it adds to the current task that can be distinguished. If a domain method already suffices, it should be possible to use only that method.

## 16.16 GOV-16 Usage-Threshold Debt and Accessibility Audits {#section-16-16}

Greater complexity can help prevent crude application and can also create six kinds of usage-threshold debt. Learning requires time and cognitive resources. Translation between plain language and terminology loses information. Evidence can be difficult to collect safely. External review may be unavailable. The more people invest, the harder it can be to exit. The identity of someone who “knows the framework” can bring interpretive authority and social capital.

Accessibility requires more than adding a shorter version to the complete text. Provide plain language, ceilings for different levels of use, expression through a representative or with assistance, ways to submit nontextual material, equal weight for appeals, and a way for people to protect themselves before learning the whole framework. State explicitly when appropriate that people can first protect themselves, record facts, and seek support without learning the framework.

Without equivalent routes for appeal, protection, and withdrawal, the framework must not be used for substantively high-impact purposes or embedded in automated decisions. Public dissemination requires closer scrutiny in light of the object, factual allegations, identifiability, and consequences. Ordinary analysis still requires accessible means of correction and withdrawal. Mastery of terminology, complete reading, internal certification, or paid training does not constitute external eligibility.

Usage-threshold debt also includes the labor of maintainers and collaborators. More fields, charts, or complete reading do not automatically produce understanding and fairness. Their value must show up in clearer questions, counterexamples that are addressed, better limits on transfer, and the actual ability of people affected to correct results. People who need assistance expressing themselves should not first have to demonstrate independently the full ability to express themselves before receiving support that makes expression possible.

## 16.17 GOV-17 Tool Use, Commercialization, Weaponization, and Risks of Forking {#section-16-17}

Courses, consulting, AI tools, organizational software, scorecards, review forms, and public standards that use the framework must retain evidence tracing, downgrading of judgments, protection for low-power positions, access to appeal, anti-retaliation, human review, stopping, and withdrawal. They must not present a lightweight template as a complete diagnosis, internal certification as external review, or AI output as an independent investigation. Customer satisfaction must not stand in for evidence of effectiveness. Do not force a strong diagnosis to make a delivery, let the paying party alone control evidence, feedback, and public framing, or let “framework certification” create a new monopoly on eligibility.

Users with sustained disagreements over core commitments may create a fork. A fork does not amount to betrayal. Running different frameworks under the same name without acknowledging a fork creates a greater risk. Each fork must state which empirical question families it retains, which boundaries it abandons, which concepts it changes, and what new risks of misuse arise.

## 16.18 GOV-18 Retiring Open Assertions Captured by Power {#section-16-18}

An open assertion is only a target for correction under uncertainty. It must be retired if it is repeatedly cited as a conclusion, enters performance evaluation, records, discipline, eligibility, resource allocation, or public memory, or is used to suppress appeal. Retirement is also required if media, organizations, or AI reduce it to a label, if it becomes a basis for prolonged exclusion or deprivation of resources under the name of “observe first,” or if the judgment is retained while its withdrawal conditions are lost.

After retirement, state explicitly that action on its basis must cease. Restate the evidence limits, alternative explanations, and withdrawal conditions. Delete or flag records that have already been misused. If harm has occurred, proceed to repair, compensation, and examination of the chain of responsibility. If misuse cannot be stopped, the framework must decline to endorse the use.

## 16.19 GOV-19 Version Write-Back and the Feedback Loop {#section-16-19}

The version log is the authoritative record for writing back counterexamples and governance decisions. It is not an appendix to release notes. For every counterexample, narrowed boundary, downgraded judgment, suspension, block, withdrawal, replacement, retirement, rollback, or remedy, record the event, time, responsible party, affected IDs, previous and new statuses, evidence, counterexamples, consequences for the text, consequences for the procedure, consequences for the action ceiling, and downstream write-back.

Archiving counterexamples without effective review does not complete a correction loop. A valid counterexample should change the affected text, procedure, or action ceiling. A counterexample that does not hold can be declined for reasons, but those grounds and a way to review them must be preserved. A prolonged absence of actual handling of feedback may trigger a review of whether the channel has failed. Absence of changes in the log establishes neither perfection nor, by itself, failure. Correct the log with new entries and retain the old entries and traces of failure.

The runtime `VERSION-LOG` must do more than contain free-text references. Every entry must resolve as structured data and precisely bind the governance `record_id`, `subject`, source/target version, `transition`, previous status, new status, and event type. Only standardized numeric versions are accepted. `source_version` must equal the `schema_version` of the framework currently being validated. `target_version` must strictly increase. Material in the same package cannot establish its own validity through cross-references among `none`, aliases, or fabricated versions. `applied` must also include at least one actual change to the text, procedure, or action ceiling and use different `before_hash` and `after_hash` values to show actual write-back. Review, the effects of objections, and downstream repair must all point to the same log entry.

Register text identity, theory version, structured contract version, software version, and the version actually consumed at runtime separately, with links that resolve between them. Renaming the theory or moving to a new major version does not reset the software version automatically or establish that installed content has been migrated. Writing back the text, building the software, using the recorded version at runtime, producing answers that meet requirements, and benefiting a real task have distinct points of verification.

The endpoint of governance feedback should match the problem. A typo correction concerns the authoritative text and its propagation. Correcting a numerical value in the source also requires checking the calculations that depend on it. Use beyond authority must be traced to actual execution and remedy. Upholding a correct decision for stated reasons can constitute adequate review. If an erroneous decision is overturned but the change has yet to take effect, only the changed decision is confirmed. The version log and hashes locate changes. They cannot substitute for the meaning or real effects of those changes.

## 16.20 GOV-20 External Review Packages and Gates for Public Release {#section-16-20}

Internal stress testing is an internal wind tunnel for finding misuse of terms, misjudgment of paths, and inconsistencies. It must not be used to establish that the framework is reliable in reality or better than alternatives, or for marketing or certification.

An external review package includes the assertions to review, a traceability matrix, publication status, known defects, review questions and criteria, reviewer identities and conflicts of interest, feedback write-back, and protection for reviewers. Review types include source tracing, review by people in affected positions, review by domain experts, red-team review for misuse, review of public language, and review of publication gates. If a kind of review remains absent for a long time, especially review by people in affected positions, the gap itself blocks publication.

Reviewers cannot establish external status by declaring it themselves. Reviewers, decision members, decision-making bodies, authorization issuers, scope of authorization, subjects, target versions, validity periods, and relationships of interest must all resolve in the runtime registries. The external approval record must also bind precisely to the current governance record, `subject`, target version, `transition`, and list of objections. `applied` may use only an external review with an `approved` decision. An alias for the same person, an internal stamp, or self-issued authorization cannot substitute for it.

Every strong judgment for public release must pass nine checks individually: complete traceability, source quality, handling of counterexamples, affected positions, shifts in burden, adversarial testing for misuse, public language, external review, and the strong-judgment kit. If any item fails, the judgment must not be published as a strong judgment. Passing all of them yields only `publishable`. It still confers no authorization to act.

### 16.20.1 Organizing Methods and Reviewing a Sample {#section-16-20-1}

Instructions for use and reference entries organized from the original text may be reviewed by sampling within a stated scope. Before sampling, state the population, categories, selection basis, and question to be judged. Cover different mechanisms, objects, and output types. Include entries concerning high-impact use, conversion across scales, or theoretical boundaries. A small convenience sample cannot represent categories it does not cover.

If review finds omitted concepts, widened scope of application, or confusion between the original and derived material, expand review of the relevant categories and trace the methods and conclusions that depend on the entry. Sampling results must distinguish entries actually reviewed from those not reviewed individually. Give the grounds and scope of a decision to adopt the entire batch separately. Permission to sample, passing procedural checks, or finding no errors so far in the sample does not amount to item-by-item confirmation by the author. These cannot substitute for substantive review of real-world high-impact judgments.

An empirical judgment offered by the author that serves as a theoretical method should be entered in the relevant part of the original text with its applicable objects, grounds, counterexamples, and stopping conditions. Editorial suggestions that have not entered the original text remain candidates. Supplementary method entries must not create a separate theory attributed to the author. Entry into the original text changes its textual status and does not automatically turn personal experience into a universal empirical proposition or proof of effectiveness.

## 16.21 GOV-21 Benign Demise of the Framework and Interfaces for Replacement {#section-16-21}

Maturity for a framework includes knowing when to exit. Explaining everything is no criterion of maturity. Benign demise need not mean that the entire text disappears. A concept, module, or empirical question family can leave the core. Five conditions can trigger this. A module is persistently superseded by a simpler, more falsifiable method with less unintended harm. A concept increases the cost of understanding without improving diagnosis. An empirical question family continually relies on exceptions in a key domain. Users suppress outside theories or real counterexamples to preserve the framework. Gains from the framework’s identity, commercial value, or power exceed gains in judgment quality.

Replacement must state how far this framework can judge, where it starts to fail, what the successor method takes over, how the two cross-check each other, what records and unresolved harms must be handed off, who is responsible for the handoff, and when it takes effect. The decision may be `restrict`, `suspend`, `compete`, `replace`, `retire`, or `handoff`. The framework’s creator, maintainers, or commercial beneficiaries must not veto replacement unilaterally or preserve it indefinitely by adding concepts without limit.

The stronger the framework’s explanatory power, the more important it is to preserve withdrawal. Greater publication capability requires greater protection for counterexamples from people with little power. Greater automation requires treating AI output as auxiliary material. No structural diagnosis can erase a person’s particular circumstances or dissolve responsibility into complexity, stages, potential fields, entropy increase, or love.

## 16.22 GOV-22 Multi-Circle Complexity and Governance of Foresight {#section-16-22}

Multi-circle capability creates five kinds of governance debt. Object debt arises when circles are treated as entities because they are named. Variable debt arises when candidates from residuals are automatically filled in as facts. Complexity debt arises when variables and paths grow without out-of-sample gains. Calibration debt arises when forecasts are published without registering results. Power debt arises when predictions are used for screening, monitoring, punishment, or manipulation. When any debt exceeds its threshold set in advance, the framework should reduce the model, downgrade the output, suspend high-impact use, or retire the relevant module.

The forecast registry must retain successes, failures, unresolved results, invalidated targets, and results that cannot be evaluated. Do not publish only hits. External reviewers can check model versions, input cutoffs, simple baselines, metrics, and outcome write-back. A claim of foresight capability is automatically downgraded if long-term calibration deteriorates, errors concentrate in particular groups, the complex model ceases to outperform the baseline, or results continue to depend on variables added after the fact.

## 16.23 GOV-23 Governing Personality, Privacy, and Overreach by Automation {#section-16-23}

Personality hypotheses carry a high risk of misuse. Governance must check collection purposes, authorization, privacy level, permitted uses, cross-circle propagation, appeals by people concerned, deletion or correction, model versions, and downstream impacts. Prohibited uses include clinical diagnosis, adjudicating the essence of a personality, discriminatory screening, unauthorized risk scoring, and using silence as evidence.

AI can propose and compare variable candidates and paths, verify the identity of materials, form judgments that can be refuted, and offer recommendations under publicly stated normative premises. It cannot certify reality through its own generated content, diagnose personality, decide values for others, or issue permissions. Block any automated system that promotes `candidate` to `observed`, promotes `simulated` to a real-world event, or promotes foresight results to authorization, and keep an audit record. Human review is effective only when reviewers can see evidence, counterexamples, and uncertainty, have the relevant capability, time available in advance, and a manageable workload, and can actually refuse, modify, or suspend an action. Those signals must reach the executor in time to change what it does. A click in an interface alone is insufficient.

Evaluate human oversight by whether correct recommendations can be adopted appropriately, incorrect ones intercepted, problems without prompts detected, and affected people able to correct results. More overrides are not necessarily better, and complete compliance does not establish reliability. For narrowly scoped actions that run faster than humans can judge them one at a time, machine-checkable constraints and minimum permissions can be studied. Responsibility for choosing goals, omissions in constraints, taking over in exceptional cases, and remedies must still be explicit. System-wide risks must not all be shifted to the person who clicks last.

</div>

<SectionLesson section="16.23" />

<div v-pre class="theory-source">


## 16.24 GOV-24 Model Degradation, Retirement, and Replacement {#section-16-24}

The framework must have mechanisms for retirement and replacement. If a simpler method consistently performs better in explanation, foresight, protection, and accessibility, use the replacement interface to hand off cases, contracts, records of failure, and appeals. Preserving the existing framework is no objective in itself. At retirement, retain necessary source chains, records of responsibility, and remedies for harm. Stop using the retired model for new decisions and disclose which conclusions remain valid, which are downgraded, and which cannot be transferred.

Replacement comparisons must assess at least judgment quality and total burden together. First fix the task, materials, input cutoff, resources, and method of evaluation. Retain a sufficiently strong domain method and accurate references back to sources for comparison. Then check misjudgments, omissions, unwarranted abstention, time, disclosure, and maintenance labor separately. Entry of a candidate into the text establishes only editorial adoption. If candidates from the same source share one change, the gains from adoption cannot be counted once per candidate. Line breaks, character counts, and file counts can be verified. Those counts cannot stand in for measures of reader costs or work outcomes.

Without an actual comparison, do not claim that the framework is better than alternatives, that they have been shown to be equivalent, or that the framework is useless. Preserve historical comparisons according to their actual versions, tasks, and denominators for failure. Local improvements can hold while regressions in other dimensions and delivery failures still have to be shown. When theory, software, and materials all change together, a comparison can evaluate the combination. Differences between combinations cannot all be attributed to one theoretical statement or one form of packaging.

</div>

<SectionLesson section="16.24" />

<div v-pre class="theory-source">


## 16.25 Context-Specific Parameters and Missing Information {#section-16-25}

External procedures in each setting must determine who participates in consensus and its time limits, the observation windows, samples, and decision makers for restoring empirical question families, and safe channels, custodians, and remedial institutions for weak signals. They must also determine risk weights for gaps in AI outputs and criteria for comparisons with alternatives across disciplines, cultures, and jurisdictions. Registration must state the applicable organization, jurisdiction, object, risk level, evidence base, validity period, and review conditions. Numbers from one setting must not be copied into universal thresholds. If these fields are missing, the conclusion remains downgraded, suspended, or subject to competition. The framework must not fill them in itself.

A missing parameter blocks only judgments and uses that depend on it. Other conclusions with independent grounds are retained within their own scope. Keep unknowns preserved for protection, lack of the ability to observe, genuine inapplicability, and outstanding evidence needs separate. In actual use, also assess proportionality by comparing whether extra recording can change the judgment and reduce harm with the delays, exposure, and maintenance costs it creates.

[^tn-diagnosis-17]: Translator's note: Diagnosis here is an assessment of a specified object against stated criteria within this framework.

</div>
