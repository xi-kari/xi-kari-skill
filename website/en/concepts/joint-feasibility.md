---
title: "Each task is feasible; the combined plan may not be"
description: "Resources must be available together at the required place and time."
---

# Each task is feasible; the combined plan may not be

The book gives two tasks, each requiring one full unit of capacity in a time slot. Both must finish by the end of period one. Period-one capacity is one. Either task is feasible alone; **the pair has no schedule satisfying the original deadlines**.

## Capacity and timing are both conditions

Increasing period-one capacity to two makes the pair feasible in the model. Validly moving one deadline to period two also works if that period has one unit of capacity. Adding capacity only in period two while retaining both original deadlines does not repair the missed deadline.

These alternatives change different conditions. A later deadline cannot be silently inserted after failure and counted as success against the original plan. In a real project, capacity, demand, permission to reschedule, and consequences for affected people require evidence of their own.

## A second problem: one action under incomplete information

F3 concerns a related but distinct issue. Suppose the observation leaves two possible states. The acceptable action set is {left} in one and {right} in the other. Each state has an acceptable action, but their intersection is empty: no single action selected from this observation is acceptable in both.

If both states allow a validly authorized preservation action, the intersection can become nonempty without fully identifying the state. An additional observation may also help, but its cost, timeliness, risk, and availability must be assessed. Investigation is not automatically free or useful.

| Claim | Required check |
| --- | --- |
| Every task can be done separately | Each task’s own constraints. |
| All tasks can be done together | Their combined resource and deadline constraints. |
| One action works despite uncertainty | A common acceptable action across the listed compatible states. |

The formal statements establish consequences of supplied constraints. They do not certify that real resources exist or that a named actor has permission to use them. Acceptable-action sets must already incorporate the task’s required protection and valid authority.

Read [C.12](/en/theory/appendix-c#section-c-12), [causal chains](./chain), and [responsibility](./responsibility).

## Explore the teaching model

<JointExplorer />
