---
title: "An accurate average can miss local overload"
description: "Sufficiency belongs to a particular question, not to a representation in the abstract."
---

# An accurate average can miss local overload

Two queues contain (0,20) tasks or (10,10) tasks. Both have mean 10. If local overload means a queue exceeds 15, the first state is overloaded and the second is not. **The mean is accurate, but cannot answer this particular question.**

## What was lost, and what can be retained

Once the two states have become the same recorded mean, no decoder using only that mean can distinguish them. This is the task-recovery condition (F1): all source states sharing a representation must require the same answer to the specified query.

The mean still answers mean and total-load questions correctly. Adding the maximum queue length is enough to answer local overload and maximum length. It does not reveal which position has the larger queue. If different positions have different service capacities, that missing location can matter to the next state.

The aim is to retain distinctions needed by the task. Restoring every microscopic detail is not a universal success criterion. Conversely, a successful static answer does not establish dynamic closure or sufficiency after a new intervention. The book’s two-queue result also cannot be transferred unchanged to three queues.

## Different questions in real cases

The [2022 Hurricane Ian forecast cone](../cases/representation-hurricane-cone) describes uncertainty about the cyclone center’s track. Storm-surge heights are a different target, addressed by separate NHC products. The case clarifies intended uses; it does not supply a formal state-space test of the task-recovery condition or evidence about how every resident interpreted the graphic.

The [Mars Climate Orbiter unit mismatch](../cases/mars-climate-orbiter) is different again. Distinct impulses remained distinct numerical values; knowing the actual units permitted conversion. The site reads this as an execution/specification issue, rather than the irreversible collapse illustrated by the two queues. NASA’s own causal findings remain the evidence for the accident.

## Try changing the target

If the target is total tasks, the mean and the known number of queues suffice. If it is whether any queue exceeds 15, the maximum suffices. If it is which queue needs help, position matters. Changing the question can produce a valid new task; it does not retroactively make an inadequate answer to the old question correct.

Read [C.6](/en/theory/appendix-c#section-c-6), [C.7](/en/theory/appendix-c#section-c-7), [C.9](/en/theory/appendix-c#section-c-9), and [prediction under intervention](./prediction).
