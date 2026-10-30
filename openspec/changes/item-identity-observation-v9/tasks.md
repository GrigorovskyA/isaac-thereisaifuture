## 1. Implementation

- [x] 1.1 Wire frame schema 7: pedestal item facts on `Entity`, `active_quality` and
  `active_tags` on `Inventory`, `tag_counts` on `EntityFrame`; validation tests.
- [x] 1.2 Encoder (observation schema 9): `item_bucket`, pedestal item block, active item block,
  held tag counts, new offsets and `OBSERVATION_SIZE` 11691; layout and encoding tests.
- [x] 1.3 Lua observer: `item_facts` (quality, type, charges, tags, every call wrapped), tag flags
  read by name, active item facts, tag counts with the held list cache, blind pedestal rule, frame
  schema 7; Lua tests with a stubbed ItemConfig and a test that the Lua and Python tag lists match;
  worst-case byte tests with item facts.
- [x] 1.4 Contract: `training-pure-v4.yaml` schema 9 and a new hash; schema 8 refused; synthetic
  frames and `sim.py`; docs (RL_DESIGN, ENTITY_OBSERVATION_PROTOCOL, OBSERVATION_PROTOCOL, README).

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [ ] 2.2 Windows `scripts/Check.ps1`; redeploy the observer mod (`main.lua` and `metadata.xml`);
  native passive audit: a pedestal collectible shows a non-zero quality and bucket, tag bits match
  the item (for example a Guppy item reads the GUPPY bit), the active item facts are filled, the
  held tag counts change after taking a tagged item, the maximum snapshot bytes stay below 131072,
  and a blind pedestal under the curse of the blind does not show its item. Every Isaac API name
  listed as unverified in the proposal reads real values, not fallbacks.
- [ ] 2.3 Start the reward v11 lineage with `--initialize` (new contract hash); no acceptance
  claim before a native run.
