---
title: "Mars Climate Orbiter: a unit mismatch at an interface"
description: "Distinguish sufficient information, the specified units, actual execution, and the reported causes."
kind: "Documented case"
source_type: "Official accident investigation"
---

# Mars Climate Orbiter: a unit mismatch at an interface

Mars Climate Orbiter was lost on arrival at Mars in September 1999. NASA’s mission record identifies a navigation error involving a unit conversion. The investigation gives a more specific account of what failed and which organizational checks did not catch it.

## What the investigation records

The ground software SM_FORCES produced thruster-impulse data in pound-force seconds, although the interface specification required newton seconds. Navigation processing interpreted the values using the specified units, underestimating the relevant force effect by a factor of about 4.45. The report also lists verification, communication, staffing, and training issues as contributing factors. See the [Phase I report](https://llis.nasa.gov/llis_lib/pdf/1009464main1_0641-mr.pdf), printed pages 6–7 and 16–17.

The specification already contained the unit requirement. A correct document therefore coexisted with nonconforming output. Data anomalies were noticed in April; the unit mismatch was identified on September 29, six days after the loss. Navigation estimates were then recomputed using corrected values (pages 13–14, 16, and 18).

The report’s wording on verification is qualified. End-to-end testing of the small-forces ground software “did not appear to be accomplished”; whether independent verification and validation had been completed “was not clear.” These statements should not be strengthened into a definite claim that no such testing ever occurred (pages 7, 15, and 25).

## Read the interface without merging the questions

[C.7](/en/theory/appendix-c#section-c-7) separates representational sufficiency from correct actual execution. In the book’s finite example, a representation can merge states requiring different answers; no new decoder can recover a distinction already lost. The Orbiter mismatch differs: distinct impulses remained distinct numbers, and knowing the actual units permitted conversion.

Reading the accident as a failure to implement or use the intended unit mapping is this site’s interpretation. NASA’s report supplies the accident findings; it does not use the framework’s classification. The theory also does not require every real failure to have a uniquely identifiable category when inputs or rules are unknown.

Receiving a file establishes transmission, not correct interpretation. Likewise, identifying a faulty interface does not settle all responsibility. Production, use, validation, supervision, and authority each require their own evidence. The person most visible at the last step is not automatically responsible for every contributing condition.

## What this case does not establish

It is not an empirical version of [§2.4.2’s two-type causal counterexample](/en/theory/part-02#section-2-4-2): the report does not estimate two average causal effects and multiply them. [C.12](/en/theory/appendix-c#section-c-12) distinguishes representation composition from causal-chain composition and joint feasibility.

Nor does explaining a known accident establish that this framework would have predicted it beforehand. The case supports a narrower reading question: what information crossed the interface, with which units and rules, and what was actually checked?

## Sources and further reading

- NASA, [Mars Climate Orbiter Mishap Investigation Board, Phase I Report](https://llis.nasa.gov/llis_lib/pdf/1009464main1_0641-mr.pdf), November 10, 1999; page locators above.
- NASA, [Mars Climate Orbiter mission record](https://science.nasa.gov/mission/mars-climate-orbiter/).
- [Representation](../concepts/representation), [causal chains](../concepts/chain), and [responsibility](../concepts/responsibility).

This English account follows the sources and factual scope of the existing Chinese case page; it adds no new investigation findings.
