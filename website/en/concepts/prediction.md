---
title: "Predicting ordinary behavior is not enough for intervention"
description: "A representation can preserve one prediction while hiding different responses to action."
---

# Predicting ordinary behavior is not enough for intervention

The book constructs two micro-level states, A₁ and A₂. Under ordinary dynamics, each moves to B with probability 0.2. For that prediction, merging them into A can be sufficient. Under a specified intervention, the probabilities become 0.8 and 0.1. The same recorded A now hides a task-relevant difference.

## Recover only what this task needs

If A₁ occupies share p within A, the intervention probability is 0.8p + 0.1(1 − p) = 0.1 + 0.7p. Adding p can resolve this particular mixture question without reconstructing every micro-level detail.

That repair has a boundary. Knowing the current share does not establish a rule for how the share itself will evolve. It also does not prove that the representation remains sufficient under a different action, a longer horizon, or a different outcome target. Static task recovery, dynamic closure, and intervention sufficiency require separate checks.

All probabilities here are stipulated teaching values. The calculation is not evidence about a real intervention and supplies no authorization to conduct one.

## Forecast evaluation is another distinct task

A real forecast needs a target, input cutoff, horizon, baseline, evaluation rule, and an outcome record. If a warning is followed by protective action and no observed event, three questions remain distinct: how the forecast scores against its registered target, whether the response prevented harm, and whether adopting that response was justified.

With a complete binary outcome label of zero and a registered probability of 0.8, the Brier score is 0.64. That score does not establish the response’s causal effect. If observation failed and the outcome is unknown, entering zero would be an error.

The [Hurricane Ian case](../cases/representation-hurricane-cone) helps distinguish track, surge, and action questions in a documented forecasting context. It does not transfer the constructed A₁/A₂ probabilities to a real storm.

Read [§4.6](/en/theory/part-04#section-4-6), [§12.6](/en/theory/part-12#section-12-6), and [representational sufficiency](./representation).

## Explore the teaching model

<PredictionExplorer />
