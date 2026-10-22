# Design

SessionPlan explicitly records time_budget_only. That mode requires <=14400s,
steps=1e9,max_restarts=5000,time-dominant navigation. CLI derives these counts and
rejects conflicting explicit count flags; diagnostics still require both flags.
Preflight refuses smaller config total steps or wall cap before approval/game.
No automatic budget migration or policy initialization. Existing CPU/native rates
and four-second restart pacing bound possible decisions/restarts below sentinels.
The mode records nonbinding_schema_sentinels in plan.json; it is not an unbounded
approval. Keep fixed deadline and all current fault/disk/input/cleanup guards.
Do not automatically retry the completed pilot or grant a further New Run.
