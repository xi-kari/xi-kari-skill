# CM identity bundle

This bundle is a co-reading boundary over source identities. It is not a new source definition.

## Identities

- `V90-CANON-CM-FEEDBACK` (CM-FEEDBACK): `V90-P00870`, `V90-P00871`, `V90-P00872`, `V90-P00873`, `V90-P00874`
- `V90-CANON-CM-LEARNING` (CM-LEARNING): `V90-P00875`, `V90-P00876`, `V90-P00877`, `V90-P00878`, `V90-P00879`, `V90-P00880`, `V90-P00881`
- `V90-CANON-CM-MAINTENANCE` (CM-MAINTENANCE): `V90-P00889`, `V90-P00890`, `V90-P00891`, `V90-P00892`, `V90-P00893`, `V90-P00894`, `V90-P00895`, `V90-P00896`
- `V90-CANON-CM-LOAD` (CM-LOAD): `V90-P00897`, `V90-P00898`, `V90-P00899`, `V90-P00900`, `V90-P00901`, `V90-P00902`, `V90-P00903`, `V90-P00904`
- `V90-CANON-CM-PHASE` (CM-PHASE): `V90-P00905`, `V90-P00906`, `V90-P00907`, `V90-P00908`, `V90-P00909`, `V90-P00910`, `V90-P00911`
- `V90-CANON-CM-SELECTION` (CM-SELECTION): `V90-P00912`, `V90-P00913`, `V90-P00914`, `V90-P00915`, `V90-P00916`, `V90-P00917`, `V90-P00918`

## Typed dependencies

- `V90-CANON-CM-FEEDBACK` --`inferential_requires`--> `V90-CANON-D2` (base)
- `V90-CANON-CM-FEEDBACK` --`inferential_requires`--> `V90-CANON-G2` (base)
- `V90-CANON-CM-FEEDBACK` --`protocol_requires`--> `V90-CANON-E4` (base)
- `V90-CANON-CM-FEEDBACK` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL` (base)
- `V90-CANON-CM-FEEDBACK` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL-DE06B986` (base)
- `V90-CANON-CM-FEEDBACK` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE` (base)
- `V90-CANON-CM-FEEDBACK` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` (base)
- `V90-CANON-CM-LEARNING` --`inferential_requires`--> `V90-CANON-CM-FEEDBACK` (base)
- `V90-CANON-CM-LEARNING` --`inferential_requires`--> `V90-CANON-G3` (base)
- `V90-CANON-CM-LEARNING` --`protocol_requires`--> `V90-CANON-E4` (base)
- `V90-CANON-CM-LEARNING` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL` (base)
- `V90-CANON-CM-LEARNING` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL-DE06B986` (base)
- `V90-CANON-CM-LEARNING` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE` (base)
- `V90-CANON-CM-LEARNING` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` (base)
- `V90-CANON-CM-LOAD` --`inferential_requires`--> `V90-CANON-D0` (base)
- `V90-CANON-CM-LOAD` --`inferential_requires`--> `V90-CANON-G2` (base)
- `V90-CANON-CM-LOAD` --`inferential_requires`--> `V90-CANON-G3` (cumulative)
- `V90-CANON-CM-LOAD` --`protocol_requires`--> `V90-CANON-E4` (base)
- `V90-CANON-CM-LOAD` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL` (base)
- `V90-CANON-CM-LOAD` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL-DE06B986` (base)
- `V90-CANON-CM-LOAD` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE` (base)
- `V90-CANON-CM-LOAD` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` (base)
- `V90-CANON-CM-MAINTENANCE` --`inferential_requires`--> `V90-CANON-D0` (base)
- `V90-CANON-CM-MAINTENANCE` --`inferential_requires`--> `V90-CANON-G2` (base)
- `V90-CANON-CM-MAINTENANCE` --`inferential_requires`--> `V90-CANON-G3` (cumulative)
- `V90-CANON-CM-MAINTENANCE` --`protocol_requires`--> `V90-CANON-E4` (base)
- `V90-CANON-CM-MAINTENANCE` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL` (base)
- `V90-CANON-CM-MAINTENANCE` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL-DE06B986` (base)
- `V90-CANON-CM-MAINTENANCE` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE` (base)
- `V90-CANON-CM-MAINTENANCE` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` (base)
- `V90-CANON-CM-MAINTENANCE` --`specializes`--> `V90-CANON-D1` (state_vocabulary)
- `V90-CANON-CM-PHASE` --`inferential_requires`--> `V90-CANON-D0` (base)
- `V90-CANON-CM-PHASE` --`inferential_requires`--> `V90-CANON-D1` (base)
- `V90-CANON-CM-PHASE` --`inferential_requires`--> `V90-CANON-G2` (causal-trigger)
- `V90-CANON-CM-PHASE` --`inferential_requires`--> `V90-CANON-G3` (hysteretic)
- `V90-CANON-CM-PHASE` --`protocol_requires`--> `V90-CANON-E4` (base)
- `V90-CANON-CM-PHASE` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL` (causal-trigger_or_hysteretic_only)
- `V90-CANON-CM-PHASE` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL-DE06B986` (causal-trigger_or_hysteretic_only)
- `V90-CANON-CM-PHASE` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE` (base)
- `V90-CANON-CM-PHASE` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` (base)
- `V90-CANON-CM-SELECTION` --`inferential_requires`--> `V90-CANON-D1` (base)
- `V90-CANON-CM-SELECTION` --`inferential_requires`--> `V90-CANON-G2` (carrier)
- `V90-CANON-CM-SELECTION` --`inferential_requires`--> `V90-CANON-G3` (history)
- `V90-CANON-CM-SELECTION` --`protocol_requires`--> `V90-CANON-E4` (base)
- `V90-CANON-CM-SELECTION` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL` (base)
- `V90-CANON-CM-SELECTION` --`protocol_requires`--> `V90-EXTERNAL-GATE-CAUSAL-DE06B986` (base)
- `V90-CANON-CM-SELECTION` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE` (base)
- `V90-CANON-CM-SELECTION` --`protocol_requires`--> `V90-EXTERNAL-GATE-EVIDENCE-C0F115F0` (base)
