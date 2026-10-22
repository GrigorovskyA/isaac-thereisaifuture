# Design

Keep continue/new-run defaults unchanged. Only mode=new-run plus literal boolean
replace_existing=True permits verified existing file2 Continue. Require fresh
selected-slot metadata and loaded game-state version, refuse absence/ambiguity,
record explicit intent and issue one Up before New Run and character confirmation.
Retain 60s global/menu/focus/release guards; at most10 keys for this mode versus
8 for defaults. Accept only native [New,2]; later structured snapshot must show
active Isaac before gameplay. This API is not authorization; caller must carry
fresh task-specific human approval. Production session runner remains Continue;
a finite local subclass may override menu entry for the one approved experiment.
No automatic replacement fallback, config/learning or deployment change.
