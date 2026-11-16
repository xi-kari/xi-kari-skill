---
title: "Appendix C Common Method Kernel and Cross-Disciplinary Bridging"
---

<div v-pre class="theory-source">

<a id="part_19"></a>

# Appendix C Common Method Kernel and Cross-Disciplinary Bridging {#part-title-19}

This appendix lists methodological responsibilities that can be shared when texts interoperate. Each text retains its own authoritative definitions and way of operating. The common kernel requires no shared chapter structure, artifact count, or numbering. It does not make one text independent empirical evidence for another.

## C.1 Method Kernel and Stable References {#section-c-1}

| Chinese Reference | Content | Where to Find It |
| --- | --- | --- |
| Definition layer | Objects, states, feedback, scales, circles, information status, and recasting | Framework definitions and authoritative definitions in *World Model* |
| Method constraints CMC1–CMC3 | Task and representation, evidential status of materials, and facts and eligibility to act | §4.17 |
| Conditional formal propositions F | Task recovery, closure, common feasible actions, composition of conversions, error, and dynamic refinement | §4.18–4.19 and this appendix |
| Empirical question families G1–G4 | Grouping, channels, historical increments, and representational closure | Instance contracts in Part 4 |
| Outcome and mechanism contracts C1–C12 | Outcome registration, mechanism composition, and bridging to normative procedures | The individual contracts in Part 4 |
| Governance invariants | Freezing, evidence, baselines, authorization, protection, and the life cycle | Existing governance clauses in both texts |

## C.2 Common Method Constraints {#section-c-2}

CMC1 requires the task, representation, horizon, environment, operations, and error to be declared together. Test static recovery, dynamic closure, and intervention sufficiency separately. CMC2 requires preserving the evidential status of materials, source lineage, inferential premises, and scope of support. Reprocessing material does not count as independent empirical evidence. CMC3 requires facts, value judgments, and eligibility to act to be established separately. See §4.17 for the full formulation.

The three constraints specify responsibilities for using models. They do not constitute three empirical laws of the world. Whether they reduce errors or impose unnecessary burdens in real tasks requires separate evaluation. Compliance with the procedures does not establish the framework’s effectiveness.

## C.3 Shared Governance Invariants {#section-c-3}

Invariant one. Freeze the record before results and only append afterward.

Invariant two. Lack of support for a positive claim does not amount to support for the null model.

Invariant three. Definitions, contracts, internal teaching examples, and internal simulations cannot supply external empirical support on their own.

Invariant four. The evidential status of materials, proposition role, artifact status, and whether fields are missing are orthogonal dimensions. Keep them separate.

Invariant five. A single artifact cannot automatically satisfy responsibilities for source tracing, modeling, foresight, evaluation, authorization, and execution.

Invariant six. Model complexity must be subject to simplification, removal of unnecessary elements, and review of necessity suited to the task. Claims of predictive or empirical capability require comparison with a simple baseline and independent evaluation material. Formal proofs, interpretation of texts, and normative arguments are checked according to their own tasks. Inapplicable out-of-sample metrics must not be imposed on them.

Invariant seven. Residuals generate only competing candidates. They do not automatically generate variables in reality.

Invariant eight. Capabilities have domains of applicability and validity periods, and are subject to drift, suspension, rollback, and retirement.

Invariant nine. Aggregate results must not erase low-power positions, privacy, non-disclosure for protection, appeal, or exit.

## C.4 Preserving Differences Across Texts {#section-c-4}

Interoperability should separately check proposition layers, empirical question-family contracts, null conclusions, scale closure, noncommutation tests, and inferential dependencies, as well as information status, artifact systems, typed unknowns, experimental evaluation, evidence of capability, and model life cycles. A complete contract in one text cannot be replaced by a similar name or case in the other. When the correspondence has yet to be established, keep the differences explicit.

The framework’s nine scale operators need not be aligned with the standard operator steps in *World Model*. The framework’s 14-section scale transformation record is also kept separate from the closed artifact system of *World Model*. The two share only the minimum meanings of what is preserved, changed, collapsed, or omitted, new unknowns, source lineage, domain of applicability, residuals, and stopping.

## C.5 A Mathematical Example of Bridging Scales {#section-c-5}

Consider a microstate x, a coarse-graining map M, microscopic evolution F, and macroscopic evolution F̄. If the difference between M(F\_t(x)) and F̄\_t(M(x)) remains within tolerance ε over the specified initial conditions, parameter domain, error norm, and time interval, one can discuss approximate commutation for that task. If this holds for only one statistic, it cannot be extended to equivalence of the entire state. A proof must also state the order of limits, how the error is controlled, and the interval of validity. A short-time approximation alone cannot establish a long-term conclusion. This is a general formal example and does not claim to give such a theorem for social objects.

Mathematical bridging requires carrying the source object, target object, mapping, scaling law or limit, initial values, retained historical information, error, and failure boundary together. It does not require all models to use the same representation, imply that every transfer across scales causes task-relevant loss, or identify losses from social recasting with physical entropy. Establishing a mathematical proof, showing that a real object meets its premises, and deciding which option to adopt in practice are three separate responsibilities.

Related studies are 05.05 “Gödel, Incompleteness, and Computability,” 05.06 “Effective Theories, Scale Closure, and Coarse-Graining,” and 05.08 “Model Selection, Parsimony, and Expressive Power.” These numbers help locate material. To check a particular mathematical conclusion, return to the assumptions, proofs, and domains of validity in the original works. A bibliography entry cannot substitute for verification.

See Appendix D for the framework’s map of applications by domain. Each domain retains its terminology, measurements, arguments, and professional boundaries. Teaching examples in the map illustrate conditions and the structure of counterexamples. They do not stand in for experiments that have been carried out or actual cases. Topic numbers connect existing research materials and do not rank theoretical importance.

## C.6 F1 Task Recovery and Worst-Case Error {#section-c-6}

Let X be a nonempty set of source states, π:X→Y a deterministic representation with Y=π(X), and q:X→V the target. For each y∈Y, the preimage X\_y=&#123;x:π(x)=y&#125; is called a representation fiber. The decoder may use only y. It must not read the source state, identity labels, or undeclared history behind the scenes.

**Task recovery proposition.** There exists g:Y→V such that q=g∘π if and only if q is constant on each fiber. If it exists, g is unique on the actual image Y.

Proof. If q=g∘π, the same representation is passed to the same function, so it gives the same target value. Conversely, on each nonempty fiber define its common target value to be g(y). This definition is unambiguous and gives g(π(x))=q(x) for every x. Each y has a source state, so any g satisfying the condition must take that common value. This proposition establishes only the existence of a function between sets. Whether it can be computed on an infinite domain by an algorithm that always halts, and whether a finite budget suffices, are separate questions.

**Finite scalar recovery proposition.** Further suppose X is finite, q is real-valued, the decoder can output any real number, and loss is the worst-case absolute error over the entire domain. Let a\_y=min\_&#123;x∈X\_y&#125;q(x) and b\_y=max\_&#123;x∈X\_y&#125;q(x). Then

inf\_g max\_&#123;x∈X&#125;|q(x)−g(π(x))| = (1/2)max\_&#123;y∈Y&#125;(b\_y−a\_y).

Proof. For any output c, the sum of its distances to the two endpoints is at least b\_y−a\_y. At least one distance is therefore at least half the range. With c=(a\_y+b\_y)/2, all target values in the fiber lie between the endpoints, and the maximum distance is exactly half the range. Taking the midpoint in each fiber and then the maximum over all fibers attains the lower bound.

For a nonnegative tolerance ε, a decoder with error at most ε over the entire domain exists if and only if the range of every fiber is at most 2ε. With an infinite state domain, use suprema and check boundedness. Vector values, restricted outputs, average loss, and probability weighting each give a different optimization problem. Half the range cannot serve as a universal score of information loss across domains.

Suppose the target is binary, the loss is zero-one loss, and the finite set of source states is uniformly distributed. Let n\_y0 and n\_y1 be the counts for the two labels in each fiber. The minimum error rate is |X|⁻¹∑\_y min(n\_y0,n\_y1). Only one label can be chosen for each fiber. Choosing the more frequent label attains the smaller of the two error counts. The error under randomized labeling is a convex combination of these two counts and cannot be lower. This expression describes the given distribution. It does not estimate error frequencies in a real population.

## C.7 F4 Composition of Conversions and Actual Execution {#section-c-7}

Let f:X→Z and h:Z→W, with the final query q already satisfying q=g∘f. The composition h∘f can still recover q if and only if g is constant on every fiber of h restricted to f(X). If q=k∘h∘f, intermediate values corresponding to the same final representation must have the same g value. Conversely, define k by the common g value on each final fiber. The condition concerns only the reachable image f(X). It imposes no constraint on intermediate values without a corresponding source state.

For example, let X=&#123;0,1&#125;². The first stage retains both positions, and the second stores only their sum, while the final query still asks for the first position. The stages individually complete the tasks of storing and counting. Their composition merges (0,1) and (1,0), so it cannot answer the final query. Retaining the Boolean value at the first position repairs this problem without recovering all source details. Changing the final query to counting is simply a different task that can succeed.

Representational sufficiency and correct execution must also be tested separately. Suppose the representations of three source states are f=(0,0,1), the required answers are q=(0,1,1), and the actual rule is g\_actual=(0,0). The first two states require different answers for representation 0, establishing that the representation is insufficient. The third state clearly requires 1 for representation 1, but the actual output is 0. This separately witnesses an independent error in the rule. Changing the rule to (0,1) repairs that error without removing the conflict in representation between the first two states. States for which the output is correct do not lose that correctness because of failures elsewhere.

This counterexample does not require every real-world fault to be uniquely classified. If the internal representation, input at the time, or actual rule is unknown, retain the gap. The continued existence of an original document cannot substitute for evidence that the reviewer obtained it in time. Being able to consult it after an error differs from having it available as input before the action.

</div>

<SectionLesson section="C.7" />

<div v-pre class="theory-source">


## C.8 F2 Closure and F5 Error Propagation {#section-c-8}

Let F:X→X be deterministic one-step dynamics. There exists F̄:Y→Y satisfying π∘F=F̄∘π if and only if π(x)=π(x′) implies π(F(x))=π(F(x′)). The proof follows by replacing the target q in C.6 with π∘F. If the condition holds on the whole domain, then π∘F^t=F̄^t∘π for each nonnegative integer t. The zero-step case is immediate. To go from step t to step t+1, apply the commutation relation once.

If U is the set of permitted actions and each action has a specified F\_u, verify the condition for each permitted action before composing the updates step by step for any action sequence fixed in advance. If action feasibility depends on states that were collapsed, also ensure that a macroscopic action can be executed in all relevant source states in the same fiber, or explicitly limit its availability. If different microscopic implementations are grouped under one macroscopic action, check separately whether they give the same macroscopic result.

In a finite stochastic system, let P(x,x′) be the transition kernel. If the probability sum ∑\_&#123;x′∈B&#125;P(x,x′) for reaching each target block B is the same for every source state in a given block, define the macroscopic transition kernel using that common value. Whatever the conditional distribution of source states within the block given the current macroscopic block and past records, averaging that common value leaves it unchanged. The projected process therefore updates under this macroscopic kernel. If the same macroscopic one-step law is required for all initial distributions, the blockwise equality condition is also necessary. Check it by starting with all mass at each source state in the same block in turn. Retaining only the next-step mean, or obtaining equality by chance for one initial mixture, does not meet this distributional requirement for all initial states.

Approximate closure also needs a horizon. Let d be a metric on Y. Suppose each reachable x satisfies d(π(F(x)),F̄(π(x)))≤ε, and F̄ satisfies d(F̄(y),F̄(y′))≤L d(y,y′) in the region reached. Starting from y\_0=π(x\_0), let e\_t=d(π(x\_t),y\_t). The triangle inequality gives e\_&#123;t+1&#125;≤ε+Le\_t, and the recurrence yields e\_t≤ε∑\_&#123;j=0&#125;^&#123;t−1&#125;L^j. If the per-step error or L changes over time, adapt the recurrence. The fixed-parameter formula must not still be applied.

These propositions state exact closure and error propagation under the conditions for approximate closure, respectively. They cannot determine whether an empirical model meets the statewise bound, whether it leaves the working region, or whether an intervention belongs to the original operation set. Closure under the usual distribution, closure under intervention, and normative usability still have to be established separately.

## C.9 Different Tasks for Two Queues {#section-c-9}

Consider two ordered queues (q₁,q₂)∈&#123;0,…,30&#125;², giving 961 states in total. The local overload target is max(q₁,q₂)&gt;15. For the sole purpose of computing expected error, make the 961 source states equiprobable. This differs from making the means equiprobable and does not imply that real queues follow a uniform distribution.

If only the mean m=(q₁+q₂)/2 is retained, (0,20) and (10,10) both give m=10, but the overload answers differ. For a sum s from 16 to 30, the same fiber has 2(s−15) overloaded states and 31−s non-overloaded states. The labels of the other fibers are unambiguous. The minimum number of classification errors is therefore ∑\_&#123;s=16&#125;^&#123;20&#125;2(s−15)+∑\_&#123;s=21&#125;^&#123;30&#125;(31−s)=85, and the error rate is 85/961≈8.844953%. This is the exact count on the complete artificial state domain.

The rule “report local overload only if the mean exceeds 15” misclassifies 240 states. The 155 errors above the optimal risk for the representation are due to the choice of rule. Those excess errors cannot all be attributed to information loss inherent in aggregation. If the task changes to recovering the maximum queue length, (0,30) and (15,15), both with mean 15, require answers of 30 and 15 respectively. The optimal real-valued output of 22.5 gives a worst-case error of 7.5. If the output must be an integer, the optimal radius for this fiber becomes 8. Output constraints themselves can therefore change the answer.

Adding the maximum M makes it possible to answer local overload and maximum length exactly, but still does not preserve which position is larger. With exactly two queues, the smaller value is 2m−M. If each position serves at most c tasks per round and no new tasks arrive, then

M′=(M−c)\_+，m′=[(M−c)\_++(2m−M−c)\_+]/2,

where a\_+=max(a,0). Thus (m,M) has dynamic closure under this symmetric model. When capacity is tied to position as (15,10), the states (0,20) and (20,0) with the same representation become (0,10) and (5,0) respectively. The next representations differ, so closure fails. With three queues, (20,20,5) and (20,15,10) both have mean 15 and maximum 20, but their totals after serving up to 15 queued tasks at each position are 10 and 5 respectively. The two-queue result cannot be extrapolated directly.

This example retains both positive and negative results. A total can answer a query about the total exactly, and adding a task-relevant variable can repair some shortcomings. The same addition need not work for interventions tied to position, heterogeneous dynamics, or more dimensions. Recovery of all microscopic information need not be a success condition for every task.

</div>

<SectionLesson section="C.9" />

<div v-pre class="theory-source">


## C.10 The Strict Stability Condition for Feedback With Fixed Delay {#section-c-10}

Consider x\_&#123;t+1&#125;=x\_t−k x\_&#123;t−d&#125;, where d is a fixed nonnegative integer, k is a fixed real number, and the initial history x\_&#123;−d&#125;,…,x\_0 has finite values. The variable x is a signed deviation. The equation has no noise, external input, saturation, or state constraints. The zero solution is asymptotically stable for all initial histories if and only if

0&lt;k&lt;k\_c(d)=2sin[π/(4d+2)].

Expanding the state to (x\_t,x\_&#123;t−1&#125;,…,x\_&#123;t−d&#125;) yields a finite-dimensional linear recurrence with characteristic polynomial p(λ,k)=λ^&#123;d+1&#125;−λ^d+k. All characteristic roots lie strictly inside the unit circle if and only if the solution tends to zero for every initial history. The modes associated with repeated roots decay despite their polynomial factors when the root modulus is strictly less than 1.

At k=0 there is a root at 1, so the system is not asymptotically stable. For k&lt;0, p(1,k)&lt;0, while p(λ,k) is positive for sufficiently large positive λ. There is therefore a real root greater than 1. For sufficiently small positive k, the root at 1 enters the unit circle as λ=1−k+O(k²). The remaining roots, originally at 0, stay inside the circle. Small positive gains are therefore stable. When d=0, the only root 1−k directly gives 0&lt;k&lt;2.

For positive k, write a boundary root as λ=e^&#123;iθ&#125;, with 0&lt;θ&lt;2π. From k=λ^d(1−λ) we obtain

k=2sin(θ/2)exp&#123;i[(d+1/2)θ−π/2]&#125;.

For k to be positive and real, θ=(π+4πm)/(2d+1) with m=0,…,d. The first boundary at positive gain comes from the smallest angle and its conjugate angle, giving k\_c(d). The roots vary continuously with the parameter and are bounded at finite parameter values. They must pass through the boundary before leaving the unit circle.

We must also rule out renewed stability at higher gains. On the unit circle, p\_λ=λ^&#123;d−1&#125;[(d+1)λ−d] is nonzero, so boundary roots are simple. Implicit differentiation gives

d log|λ|/dk = (2d+1)(1−cosθ)/&#123;k|(d+1)e^&#123;iθ&#125;−d|²&#125;&gt;0.

Thus all crossings at positive k go outward, with no re-entry. Together with stability at small gains, this gives the necessary and sufficient interval stated above. Equality at the boundary leaves a nondecaying mode. A root modulus slightly below 1 in floating-point arithmetic is no basis for including the boundary. Above the boundary a growing mode exists, while the special all-zero history still remains zero.

With k=0.8 fixed, the critical values for d=0 and 1 are 2 and 1, respectively, and the system is stable. The critical values for d=2 and 3 are approximately 0.618034 and 0.445042, respectively, and the system is unstable. For an all-ones initial history, the first step in all four cases gives 0.2. The feedback term already affects the state in the model, while convergence differs. Even when the system is stable, the result still places no bound on transient peaks or costs and does not establish acceptability to people or real-world repair. Time-varying delays, stochastic disturbances, nonlinearity, and constraints on execution require new analysis.

## C.11 Historical Increments and Omissions in the Current Representation {#section-c-11}

Use the same 961 equiprobable initial states, but let each queue serve at most 5 tasks per round with no new arrivals. Advance the full state by F(q₁,q₂)=((q₁−5)\_+,(q₂−5)\_+). The prediction target is the mean after the second round. Compare four inputs after the first round: the current mean, the current mean with the initial mean, the full current state, and the full current state with the initial mean. Under squared loss, outputting the conditional mean of the target for each input fiber attains the minimum expected loss.

| Prediction Input | Minimum Mean Squared Error Under the Given Distribution |
| --- | ---: |
| Current mean | 0.579016561 |
| Current mean and initial mean | 0.271143397 |
| Full current state of both queues | 0 |
| Full current state of both queues and initial mean | 0 |

The calculation advances each of the 961 initial states and retains its original weight. It does not make the states after the first round uniform again. In particular, (0,20) advances to (0,15) and has a next mean of 5. The state (10,15) advances to (5,10) and has a next mean of 2.5. Both current means are 7.5, while the initial means differ. The historical mean helps distinguish differences collapsed by the current projection. The full current state already suffices to determine the future.

This establishes that a historical predictive increment can arise from an omission in the current representation. It does not establish that real systems universally lack memory. Real data still require attention to measurement, confounding, temporal order, leakage, and model selection. If the full current carrier is unavailable, one cannot claim to have ruled out a historical increment. If earlier experience affects the outcome through a current skill and the residual disappears once that skill is represented sufficiently, the result limits only the additional prediction given the skill. It does not negate the total effect of earlier experience or rule out learning in general.

## C.12 Three Limits on Composing Local Successes {#section-c-12}

Whether conversions can compose to give the same final answer, whether causal effects can link into a chain, and whether actions can be jointly executed with available resources concern functions, joint responses, and sets of constraints, respectively. They can occur in the same workflow. A generic status of “connected” cannot make them interchangeable.

See §2.4.2 for the causal counterexample. The types s∈&#123;0,1&#125; have equal weight, with m(a)=a(1−s) and y(a,m)=sm. The average effect from treatment to mediator and the average effect from mediator to outcome are both 1/2, whereas the effect of the full chain is 0 because different types carry the two effects. This rules out multiplying edge means unconditionally. It does not withdraw an independently identified total effect.

The resource counterexample consists of two unit tasks, each taking a full period. Both must be completed before the end of the first period, which has capacity of only 1. Each task is feasible alone, but there is no feasible joint schedule. Joint execution becomes feasible if capacity in that period rises to 2, or if one deadline is legitimately moved to the second period and that period has capacity of 1. If both original deadlines remain, adding capacity in the second period cannot make up for the original deadline. The conclusion follows directly from the stated constraints. It does not certify real-world demand, capacity, or authorization.

**F3 Common feasible action proposition.** For a finite, single-round deterministic task, let X\_y be a nonempty observation class and A\_ok(x) the set of eligible actions for each state. There exists an action depending only on y that is eligible for every x∈X\_y if and only if ∩\_&#123;x∈X\_y&#125;A\_ok(x) is nonempty.

Proof. If such an action a exists, it belongs to the eligible set of every compatible state and therefore to the common intersection. Conversely, choose any a in the nonempty intersection. It is eligible in every compatible state, and choosing it does not require knowing which state actually holds. Nonemptiness of each state’s set separately is only a necessary condition. For example, if the eligible sets of two states are &#123;左&#125; and &#123;右&#125;, meaning left and right, respectively, each has an option but they share no action. If both allow an authorized preservation action, the intersection can be nonempty while the state remains incompletely identified.

The eligible sets in the proposition must already incorporate the resources, protections, and valid permissions required by the task. Writing an action in mathematical terms cannot substitute for these real-world conditions. The proposition concerns only the listed compatible states and cannot guarantee that unknown states will never occur. When undertaken lawfully, further observation, waiting, or preservation can change the information and policy sets. None of these occurs automatically. Probability-based choices that tolerate risk, randomization, and sequential policies are analyzed separately according to their own objectives. Representational sufficiency, computability, accessibility, implementability, resources, and authority to adopt must be justified separately for the specific use.

</div>

<SectionLesson section="C.12" />

<div v-pre class="theory-source">

</div>
