## Decisions
Reuse the already bounded room-entity scan during live capture. Diagnostics are off unless Config.tear_diagnostics is literal true and the approved live loop is active. No extra callback or collision return value is introduced.

A single nonrenewable 120-second window, 100ms sample interval, 64 lifetime labels, 64 scanned entities and 1024 lines bound work and storage. Lines are at most 900 bytes; errors terminate diagnostics only. Store scalar tear samples and opaque local labels, never entity references or raw pointer/seed identities. Context changes stop the audit rather than mix trajectories.

Record owned player tears after update: observed positions/velocity/height/falling fields/grid class/flags, displacement from first sampled pose and sampled cumulative path. Disappearance is sampled absence, never a reason for removal or a hit. First observation can follow spawning, so distances are lower bounds, not effective weapon range.

Record player TearRange as an API statistic, not a guaranteed physical endpoint. For nearest exported policy enemy, query Room:CheckLine mode3 with wall/crushable ignores false; log returned clearance/first hit separately from actual tear travel. Flags such as spectral/piercing and engine hitboxes can invalidate simplistic interpretations. Missing optional API fields are unavailable; failing access stops only diagnostics.

All records stay in the native local log. No fields enter bridge snapshots, model observations, recurrent state, normalizer, reward or action decisions. Frozen native run uses exact compatible extended t6912; no optimizer or model writes. Deploy and restore observer only while game closed.

## Sources
- https://wofsauge.github.io/IsaacDocs/rep/Room.html#checkline
- https://wofsauge.github.io/IsaacDocs/rep/EntityTear.html
- https://wofsauge.github.io/IsaacDocs/rep/EntityPlayer.html
Installed enums/source are checked; documentation alone is not native acceptance.

## Native compatibility amendment
The first native capture stopped its audit at the first tear while normal capture continued. TearFlags uses BitSet128 in the API; never coerce a userdata or an unsafe large bitset number into a diagnostic float. Record flags=na plus its Lua type, and query spectral/piercing through read-only HasTearFlags when available. Preserve bounded sanitized stop-error detail for other native differences.
Source: https://wofsauge.github.io/IsaacDocs/rep/enums/TearFlags.html
