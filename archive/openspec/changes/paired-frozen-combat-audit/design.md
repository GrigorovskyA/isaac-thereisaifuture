## Approach

The diagnostic reads only the existing encoded policy vector and an integer
MultiDiscrete action. The first present enemy slot is nearest by encoder contract.
The shooting unit vector uses left/right/up/down screen coordinates. Cosine
alignment is geometric,not a hit or line-of-sight test. Coarse alignment means
within45degrees;no shooting is false. Missing targets,zero distance or clipped
relative coordinates yield unavailable geometry,excluded from alignment denominators.
HP features do not affect the proxy. No value is fed back to the policy or reward.

The experimental runner calls all three frozen policies on identical observations,
keeps their own recurrent states over the same history and resets all at window/
episode boundaries. Equal maximum128-decision windows (episode boundaries may end them early) use1536,6912,random,random,6912,1536.
Only the declared controller's action reaches the existing gated environment.
Unexecuted shadow actions have no attributed hits,damage,deaths or clears.
All outcomes reflect mixed sequential control and are descriptive,not a causal
policy comparison. Individual frozen policies are deterministic;random seed fixed.

Keep raw oracle snapshots/phase labels separate from policy-only decision records.
Bound all captures and replay only policy vectors for identical-input diagnostics.
No game-state restoration is available under current scope;do not manufacture
matched gameplay claims. Use native phase evidence to investigate visibility,
HP increases and withheld reward rather than changing combat strategy.

## Acceptance

Behavioral tests cover direction/sign,missing/clipped/zero targets,HP invariance,
and invalid inputs. Full Windows gate and actual checkpoint loading must pass.
One native finite audit records identity,executed/shadow separation,policy hashes,
all outcomes,deadline/censoring,cleanup and restored default-off deployment.
Actual revival coverage remains pending if not encountered. No archive is required.
