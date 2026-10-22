## Context

The last check had a transient empty exit during the operator-observed revival
loop. Current oracle/visible capture filters on active/nondead entities,not on
vulnerability. API references are primary IsaacDocs Entity and EntityNPC pages;
they do not establish installed-build behavior.

## Goals / Non-Goals

Observe NPC and potentially vulnerable/effect phase candidates locally. Do not
change filters,gate behavior,reward,wire fields,model or implement target selection.

## Decisions

- Literal Config.target_phase_diagnostics=false by default. Call an isolated
  pcall observer after final policy/oracle lists are built. No additional room scan.
- Read ToNPC,IsEnemy,IsVulnerableEnemy,IsActiveEnemy(false/true),IsDead,Exists,
  Visible,Type/Variant/SubType,HP/maxHP,NPC State and current position. NPCs and
  vulnerable/enemy entities are always candidates,including any such effect.
  Passive effects require literal target_phase_passive_effects=true,default false.
  Native audit exhausted128 labels with122 passive effect lifetimes and six NPCs;
  this diagnostic-only selection preserves scarce history for target phases.
- Record GetChampionColorIdx when available as local-only raw NPC evidence.
  User clarified the observed mob was a red champion;do not infer Globin from
  revival behavior or a modifier from HP/color alone. Missing optional method
  leaves the field unavailable without stopping other diagnostic facts.
- A private pointer+seed lookup assigns <=128 local labels; raw keys never log.
  Correlate existing bridge IDs where available and membership after policy caps.
  Semantic changes trigger records; position is payload only. Gone means absence.
- At most64 room entities/sample,10Hz,120s,512 lines and800 chars/line. Stop rather
  than partially imply complete coverage. All diagnostic errors are contained.
  The window does not reset on handshake,room change or software episode reset.
- Primary stages a verified source copy with only the literal diagnostic flag
  enabled while Isaac is closed. Back up exact old deployment; restore default
  source after the worker closes. Worker never deploys. Record hashes/configuration.

## Risks / Trade-offs

Opt-in passive effects may consume the finite label budget; record a stop and
report incomplete coverage. Default mode does not establish coverage of passive
non-NPC/non-enemy/non-vulnerable effects. IsVulnerableEnemy is engine evidence,not
proof of a successful hit. Raw
NPC state is diagnostic oracle data,not a new policy feature. Sampling may miss
short phases. An absent candidate does not establish a death or a missed phase.

## Migration Plan

No schema/checkpoint migration. Disable the flag for ordinary deployment. Native
audit needs a newly recorded finite budget and remains pending until sampled
facts correlate the reported revival behavior. No archive without that evidence.
