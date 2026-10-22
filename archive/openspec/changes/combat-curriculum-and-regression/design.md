## Context

Item 07 provides scenarios, baselines and equal-budget evaluation with Wilson intervals.
Item 09 adds the decision rules around them.

## Decisions

- **Stages** reference scenario difficulties; train/validation scenarios come from `scenarios_for`.
  Stages never expose the test split. Curriculum and tolerance are frozen dataclasses with a SHA-256 hash.
- **Advancement** is a pure function: valid episodes >= minimum and clear-rate CI lower bound >= threshold.
- **Regression gate** compares new metrics on the old task set with the pre-extension snapshot:
  fails when the clear-rate CI upper bound or point estimate is below snapshot minus tolerance, or mean
  damage rises beyond tolerance. The tolerance hash is recorded in the result.
- **Baselines**: "beats" means the CI lower bound exceeds the baseline CI upper bound; scripted is reported either way.
- **ResultsLog**: JSONL hash chain with no delete API; reading verifies the chain.
- **Leakage**: a wrapper asserts every policy input is float32 of exactly `OBSERVATION_SIZE`.

## Risks / Trade-offs

- A size check cannot prove content is non-oracle; it complements the separate oracle log.
- A hash chain detects but does not prevent filesystem tampering.
