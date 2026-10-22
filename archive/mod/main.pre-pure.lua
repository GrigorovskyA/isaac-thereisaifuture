-- Default read-only observer; opt-in lifecycle and explicitly authorized native actions.
local mod = RegisterMod("Isaac Future Observer", 1)
local Config = {
    host = "127.0.0.1", port = 9528, max_bytes = 16384, io_bytes = 4096,
    timeout_ms = 3000, retry_ms = 1000, sample_ms = 200,
    -- Operator-supplied metadata is optional; never pretend it is runtime detection.
    game_version = nil, steam_build = nil,
    -- Default disabled; optional private expiring approval is loaded once per mod load.
    action_authorization = nil,
    action_authorization_path = "mods/isaac_threrisaifuture_observer/action_authorization.json",
    -- Diagnostic only; just the literal true opts in. Never sent on the wire.
    callback_trace = false,
    -- Sparse firing samples; just the literal true opts in. Local log only.
    firing_diagnostics = false,
    -- Lifecycle diagnostics: rare callback/authority records; literal true opts in. Local log only.
    lifecycle_diagnostics = false,
    -- Local-only bounded target membership audit; literal true enables it.
    target_phase_diagnostics = false,
    -- Passive visual effects can exhaust audit labels; NPC/enemy/vulnerable forms always qualify.
    target_phase_passive_effects = false,
    -- Local-only sampled tear trajectories and projectile-line queries; literal true opts in.
    tear_diagnostics = false,
    -- Live loop (training approval only): faster samples, bounded approval and restart pacing.
    live_sample_ms = 50, training_max_seconds = 28800, live_restart_interval_ms = 4000,
    live_oracle_enemies = 64,
}
local state = {
    tcp = nil, phase = "closed", rx = "", tx = "", offset = 1,
    since = 0, next_retry = 0, last_sample = 0, session = nil,
    sequence = 0, epoch = 0, updates = 0, visit = 0, active = false,
}
local json, socket
local capabilities = { "snapshot_v1", "availability", "raw_health_v1", "death_restart_v1" }
local restart = {
    requested = false, armed = false, deadline = nil, attempts = 0,
    pending = nil, awaiting = nil, seen_epoch = -1, disabled = false,
}
local actions = {
    requested = false, armed = false, sequence = 0, heartbeat = 0, hold = nil,
    authority_deadline = nil, approval_loaded = false,
}
-- Live loop: entity observation, actions and death restart in one approved session.
local live = { on = false, navigation = false, navigation_grid = false, firing_geometry = false, policy_geometry = false }
local diagnostic = nil

-- Bounded opt-in callback trace: one nonrenewable window per mod load, fixed-size state.
-- It logs only; it never touches the wire, policy data, input returns or cleanup.
-- hold/rel are scalar step-evidence correlation state (accepted hold, one pending release).
local trace = { started = false, done = false, count = 0, deadline = nil, busy = false,
    hold = nil, rel = nil, input_frame = nil }
local TRACE_MAX_ATTEMPTS, TRACE_WINDOW_MS, TRACE_LINE_MAX = 512, 10000, 300

local function trace_live() return trace.started and not trace.done end
local function trace_firing_only()
    return Config.firing_diagnostics == true and Config.callback_trace ~= true
end
local function trace_forget() trace.hold, trace.rel, trace.input_frame = nil, nil, nil end
local function trace_fail() trace.done = true; trace_forget() end
local function trace_num(value)
    assert(type(value) == "number" and value % 1 == 0 and math.abs(value) <= 2^53-1,
        "Invalid trace scalar")
    return string.format("%.0f", value)
end
local function trace_read(read)
    if trace.done then return nil end
    if trace.busy then trace_fail(); return nil end
    trace.busy = true
    local ok, value = pcall(read)
    trace.busy = false
    if not ok then trace_fail() end
    if trace.done then return nil end
    return value
end

local function trace_start()
    if (Config.callback_trace ~= true and Config.firing_diagnostics ~= true)
        or trace.started or trace.done then return end
    local deadline = trace_read(function()
        local now = Isaac.GetTime()
        if trace.done then return nil end
        trace_num(now)
        return now + TRACE_WINDOW_MS
    end)
    if deadline and not trace.done then trace.deadline, trace.started = deadline, true end
end

local function trace_event(label, extra)
    if trace_firing_only() and (label == "render_enter" or label == "render_exit"
        or label == "update_enter" or label == "update_exit"
        or label == "hold_update" or label == "release_update") then return false end
    if trace.busy then trace_fail(); return false end
    if not trace_live() then return false end
    trace.busy = true
    local emitted = false
    local ok = pcall(function()
        local now = Isaac.GetTime()
        if trace.done then return end
        trace_num(now)
        local stop = now >= trace.deadline and "deadline"
            or trace.count >= TRACE_MAX_ATTEMPTS - 1 and "count" or nil
        if stop then label, extra = "stop", " reason=" .. stop end
        trace.count = trace.count + 1
        local frame = Game():GetFrameCount()
        if trace.done then return end
        local tail = " time_ms=" .. trace_num(now) .. " frame=" .. trace_num(frame)
            .. " update=" .. trace_num(state.updates) .. " session=" .. tostring(state.session)
            .. " epoch=" .. trace_num(state.epoch) .. " room=" .. trace_num(state.visit)
            .. (actions.sequence > 0 and " seq=" .. trace_num(actions.sequence) or "")
        local function build(name, more)
            return "[Isaac Future Trace] id=" .. trace.count .. " event=" .. name
                .. (more or "") .. tail
        end
        local line = build(label, extra)
        if #line > TRACE_LINE_MAX then
            stop, line = "line_limit", build("stop", " reason=line_limit")
        end
        assert(#line <= TRACE_LINE_MAX, "Trace identity exceeds line limit")
        if stop then trace.done = true; trace_forget() end
        if Isaac.DebugString then Isaac.DebugString(line) else print(line) end
        emitted = not stop and not trace.done
    end)
    if not ok then trace_fail() end
    trace.busy = false
    return emitted
end

-- Diagnostic reads only; missing/invalid properties never become policy features.
local function trace_cooldown(player)
    return trace_read(function()
        local function scalar(value)
            if type(value) ~= "number" or value ~= value or math.abs(value) > 1000000 then
                return "na"
            end
            return string.format("%.6g", value)
        end
        return " fire_delay=" .. scalar(player.FireDelay)
            .. " max_fire_delay=" .. scalar(player.MaxFireDelay)
    end)
end
local function trace_input(hook, button, value, entity)
    if not trace_live() then return end
    local ok = pcall(function()
        -- The firing-only mode samples the commanded direction at the value hook,
        -- at most once per game frame. Keep the older exhaustive callback trace
        -- unchanged when callback_trace is explicitly enabled.
        if trace_firing_only() then
            local h = actions.hold
            if hook ~= InputHook.GET_ACTION_VALUE or not h or h.shoot == "none" then return end
            local selected = h.shoot == "left" and ButtonAction.ACTION_SHOOTLEFT
                or h.shoot == "right" and ButtonAction.ACTION_SHOOTRIGHT
                or h.shoot == "up" and ButtonAction.ACTION_SHOOTUP
                or h.shoot == "down" and ButtonAction.ACTION_SHOOTDOWN
            if button ~= selected then return end
            local frame = Game():GetFrameCount()
            if trace.input_frame == frame then return end
            trace.input_frame = frame
        end
        local names = { [InputHook.IS_ACTION_PRESSED] = "IS_ACTION_PRESSED",
            [InputHook.IS_ACTION_TRIGGERED] = "IS_ACTION_TRIGGERED",
            [InputHook.GET_ACTION_VALUE] = "GET_ACTION_VALUE" }
        local A = ButtonAction
        local shooting = button == A.ACTION_SHOOTLEFT or button == A.ACTION_SHOOTRIGHT
            or button == A.ACTION_SHOOTUP or button == A.ACTION_SHOOTDOWN
        local extra = ""
        if shooting then
            extra = trace_cooldown(entity:ToPlayer())
            if not extra then return end
        end
        trace_event("input", " hook=" .. (names[hook] or tostring(hook)) .. " button="
            .. tostring(button) .. " returned=" .. tostring(value) .. extra)
    end)
    if not ok then trace_fail() end
end

-- Raw bridge facts only; no consumed-update or physical-neutrality claim.
local function rel_current()
    local r = trace.rel
    if r and (r.session ~= state.session or r.epoch ~= state.epoch or r.visit ~= state.visit) then
        trace.rel, r = nil, nil
    end
    return r
end
local function trace_update()
    if not trace_live() then return end
    if trace_firing_only() then return end
    local data = trace_read(function()
        local h, t, r = actions.hold, trace.hold, rel_current()
        local frame = Game():GetFrameCount()
        if trace.done then return nil end
        trace_num(frame)
        if h and t and t.seq == h.sequence and t.epoch == state.epoch
            and t.visit == state.visit and (not t.last or frame > t.last) then
            t.last = frame
            return { event="hold_update", extra=" hold_seq=" .. trace_num(h.sequence)
                .. " left=" .. trace_num(h.until_frame-frame)
                .. " upd_since=" .. trace_num(state.updates-t.upd) }
        elseif not h and r and not r.post and state.updates > r.upd then
            return { event="release_update", rel=r, extra=" hold_seq=" .. trace_num(r.seq)
                .. " hold=absent upd_since=" .. trace_num(state.updates-r.upd) }
        end
    end)
    if not data then return end
    if trace_event(data.event, data.extra) and data.rel and trace.rel == data.rel then
        data.rel.post = true
        if data.rel.input then trace.rel = nil end
    end
end
local function trace_release_input(entity, hook, button)
    if not trace_live() then return end
    if trace_firing_only() then return end
    local data = trace_read(function()
        local r = rel_current()
        if not r or r.input or actions.hold or not entity then return nil end
        trace_num(hook); trace_num(button)
        local H, A = InputHook, ButtonAction
        if hook ~= H.IS_ACTION_PRESSED and hook ~= H.IS_ACTION_TRIGGERED
            and hook ~= H.GET_ACTION_VALUE then return nil end
        local buttons = { [A.ACTION_LEFT]=true, [A.ACTION_RIGHT]=true, [A.ACTION_UP]=true,
            [A.ACTION_DOWN]=true, [A.ACTION_SHOOTLEFT]=true, [A.ACTION_SHOOTRIGHT]=true,
            [A.ACTION_SHOOTUP]=true, [A.ACTION_SHOOTDOWN]=true }
        if not buttons[button] then return nil end
        local player = entity:ToPlayer()
        if trace.done or not player then return nil end
        local key = GetPtrHash(player)
        if trace.done then return nil end
        local current = Isaac.GetPlayer(0)
        if trace.done or not current then return nil end
        local current_key = GetPtrHash(current)
        if trace.done or key ~= current_key then return nil end
        return { rel=r, extra=" hold_seq=" .. trace_num(r.seq) .. " hook=" .. trace_num(hook)
            .. " button=" .. trace_num(button) .. " override=nil" }
    end)
    if not data then return end
    if trace_event("release_input", data.extra) and trace.rel == data.rel then
        data.rel.input = true
        if data.rel.post then trace.rel = nil end
    end
end
local function trace_release(h, reason)
    if not trace_live() then return end
    local data = trace_read(function()
        if h.epoch ~= state.epoch or h.visit ~= state.visit then trace_fail(); return nil end
        local frame = Game():GetFrameCount()
        if trace.done then return nil end
        local now = Isaac.GetTime()
        if trace.done then return nil end
        trace_num(frame); trace_num(now)
        return { extra=" reason=" .. tostring(reason or "transition"):sub(1,40)
            .. " hold_seq=" .. trace_num(h.sequence)
            .. " frame_due=" .. (frame >= h.until_frame and 1 or 0)
            .. " wall_due=" .. (now >= h.deadline and 1 or 0)
            .. " left=" .. trace_num(h.until_frame-frame),
            rel={ seq=h.sequence, session=state.session, epoch=state.epoch,
                visit=state.visit, upd=state.updates, post=false, input=false } }
    end)
    if not data then return end
    if trace_event("release", data.extra) and reason ~= "replaced" then
        trace.rel = data.rel
    end
    trace.hold = nil
end
local function trace_accepted(c, h)
    trace_start()
    if not trace_live() then return end
    local data = trace_read(function()
        if not h or actions.hold ~= h or h.epoch ~= state.epoch or h.visit ~= state.visit then
            trace_fail(); return nil
        end
        return { extra=" move=" .. c.move .. " shoot=" .. c.shoot
            .. " frames=" .. trace_num(c.frames) .. " until=" .. trace_num(h.until_frame)
            .. " deadline_ms=" .. trace_num(h.deadline),
            hold={ seq=c.sequence, epoch=state.epoch, visit=state.visit,
                upd=state.updates, last=nil } }
    end)
    if not data then return end
    local r = trace.rel
    if r then
        local ok, extra = pcall(function()
            return " hold_seq=" .. trace_num(r.seq) .. " by_seq=" .. trace_num(c.sequence)
        end)
        if not ok then trace_fail(); return end
        if not trace_event("release_superseded", extra)
            then return end
    end
    trace.rel = nil
    if trace_event("action_accepted", data.extra) then trace.hold = data.hold end
end

-- Raw callback facts only. No OracleEvent, outcome, reward or input authority.
local probe = { requested=false, started=false, done=false, busy=false, count=0, labels=0,
    ids={}, pending={}, post={}, deadline=0, sample=0 }
local PROBE_LIMIT, PROBE_MS, PROBE_LABELS = 1024, 120000, 128
local function probe_clear()
    probe.done, probe.ids, probe.pending, probe.post = true, {}, {}, {}
end
local function probe_value(value)
    if value == nil then return "na" end
    assert(type(value) == "boolean" or (type(value) == "number" and value == value
        and math.abs(value) <= 2^53-1), "Invalid diagnostic scalar")
    local text = tostring(value)
    assert(#text <= 32, "Diagnostic scalar too long")
    return text
end
local function probe_event(label, facts, stop)
    if not probe.started or probe.done then return end
    if probe.busy then probe_clear(); return end
    probe.busy = true
    local ok, err = pcall(function()
        local now = Isaac.GetTime()
        local reason = now >= probe.deadline and "deadline"
            or probe.count >= PROBE_LIMIT-1 and "count" or stop
        local extra
        if reason then
            label, extra = "stop", " reason=" .. reason
            probe_clear()
        else
            extra = facts and facts()
            if probe.done then return end
            if facts and extra == nil then return end
            extra = extra or ""
            if label ~= "post_update" then probe.dirty = true end
        end
        probe.count = probe.count + 1
        local line = "[Isaac Future OracleProbe] id=" .. probe.count .. " event=" .. label
            .. " time_ms=" .. now .. " frame=" .. Game():GetFrameCount()
            .. " update=" .. state.updates .. " session=" .. tostring(state.session)
            .. " epoch=" .. state.epoch .. " room=" .. state.visit .. extra
        assert(#line <= 400, "Diagnostic line too long")
        if Isaac.DebugString then Isaac.DebugString(line) else print(line) end
    end)
    probe.busy = false
    if not ok then
        if tostring(err):find("Diagnostic label budget exhausted", 1, true) then
            probe_event("stop", nil, "labels")
        elseif tostring(err):find("Diagnostic pending target budget exhausted", 1, true) then
            probe_event("stop", nil, "pending")
        else probe_clear() end
    end
end
local function probe_queue_post(entity, key, id, attempt)
    for _, entry in ipairs(probe.post) do
        if entry.label == id then
            entry.attempts = entry.attempts + (attempt and 1 or 0)
            entry.init = entry.init or not attempt
            return
        end
    end
    if #probe.post >= 16 then error("Diagnostic pending target budget exhausted") end
    local frame = Game():GetFrameCount()
    if probe.done then error("Diagnostic reentry during staging") end
    probe.post[#probe.post+1] = { entity=entity, key=key, label=id,
        frame=frame, update=state.updates,
        attempts=attempt and 1 or 0, init=not attempt, age=0, samples=0 }
end
local function probe_entity(entity, fresh, pending, attempt)
    if not entity then return " label=na" end
    local key = tostring(GetPtrHash(entity)) -- Internal only; never exported or used as a reward ID.
    if probe.done then error("Diagnostic reentry during identity read") end
    local id = probe.ids[key]
    if not id or fresh then
        if probe.labels >= PROBE_LABELS then error("Diagnostic label budget exhausted") end
        probe.labels = probe.labels + 1
        id, probe.ids[key] = probe.labels, probe.labels
    end
    if pending then
        probe.pending[id] = true
        probe_queue_post(entity, key, id, attempt == true)
    end
    return " label=" .. id .. " entity_type=" .. probe_value(entity.Type)
        .. " variant=" .. probe_value(entity.Variant) .. " hp=" .. probe_value(entity.HitPoints)
end
local function probe_removed(entity)
    local key = tostring(GetPtrHash(entity))
    for _, entry in ipairs(probe.post) do
        if entry.key == key then
            entry.entity, entry.key, entry.removed = nil, nil, true
        end
    end
end
local function probe_context(entry)
    return " label=" .. entry.label .. " queued_frame=" .. entry.frame
        .. " queued_update=" .. entry.update .. " attempts=" .. entry.attempts
        .. " init=" .. tostring(entry.init)
end
-- Sets entry.sampled only when HP was actually read; any unavailable status leaves it false.
local function probe_read(entry, extra)
    if entry.removed then return extra .. " status=removed" end
    if probe.ids[entry.key] ~= entry.label then return extra .. " status=identity_changed" end
    local entity = entry.entity
    local exists = entity:Exists()
    if probe.done then return nil end
    assert(type(exists) == "boolean", "Invalid diagnostic Exists result")
    if not exists then return extra .. " status=missing" end
    if tostring(GetPtrHash(entity)) ~= entry.key then return extra .. " status=identity_changed" end
    if probe.done then return nil end
    local entity_type = entity.Type
    if probe.done then return nil end
    local variant = entity.Variant
    if probe.done then return nil end
    local hp = entity.HitPoints
    if probe.done then return nil end
    entry.sampled = true
    return extra .. " status=sampled entity_type=" .. probe_value(entity_type)
        .. " variant=" .. probe_value(variant) .. " hp=" .. probe_value(hp)
end
-- Raw timing facts only: up to 3 samples over at most 4 observer post-update callbacks.
local PROBE_SAMPLES, PROBE_CALLBACKS = 3, 4
local function probe_flush_post()
    local list = probe.post
    if #list == 0 then return end
    -- A frame getter may reenter a lifecycle hook before per-entry logging starts.
    -- Invalidate that window instead of emitting an old target in the new room.
    if probe.busy then probe_clear(); return end
    probe.busy = true
    local ok, frame = pcall(function() return Game():GetFrameCount() end)
    probe.busy = false
    if not ok then probe_clear(); return end
    if probe.done then return end
    for i=1,#list do
        local entry = list[i]
        entry.age = entry.age + 1
        local first = entry.samples == 0
        if first or entry.removed or frame > entry.last then
            local index = entry.samples + 1
            entry.sampled = false
            probe_event(first and "post_update_hp" or "post_update_hp_later", function()
                local extra = probe_context(entry)
                if not first then
                    extra = extra .. " sample=" .. index .. " prior_frame=" .. entry.last
                end
                return probe_read(entry, extra)
            end)
            if probe.done then return end
            entry.samples, entry.last = index, frame
            entry.finished = not entry.sampled or index >= PROBE_SAMPLES
        end
        if not entry.finished and entry.age >= PROBE_CALLBACKS then
            probe_event("post_update_hp_expired", function()
                return probe_context(entry) .. " samples=" .. entry.samples
                    .. " callbacks=" .. entry.age .. " status=expired"
            end)
            if probe.done then return end
            entry.finished = true
        end
        if entry.finished then entry.entity, entry.key = nil, nil end
    end
    local kept = {}
    for i=1,#list do
        if not list[i].finished then kept[#kept+1] = list[i] end
    end
    probe.post = kept
end
local probe_callbacks = { "MC_ENTITY_TAKE_DMG", "MC_POST_NPC_INIT", "MC_NPC_UPDATE",
    "MC_POST_NPC_DEATH", "MC_POST_ENTITY_KILL", "MC_POST_ENTITY_REMOVE",
    "MC_PRE_SPAWN_CLEAN_AWARD" }
local probe_available = type(GetPtrHash) == "function"
for _, name in ipairs(probe_callbacks) do
    if ModCallbacks[name] == nil then probe_available = false end
end
local function probe_start()
    if not probe.requested or not probe_available or probe.started or probe.done
        or actions.requested or restart.requested or state.phase ~= "streaming" then return end
    local ok = pcall(function()
        probe.deadline, probe.sample = Isaac.GetTime() + PROBE_MS, Isaac.GetTime()
        probe.started = true
        probe_event("attach")
    end)
    if not ok then probe_clear() end
end
local function probe_update()
    if not probe.started or probe.done then return end
    local ok = pcall(function()
        probe_flush_post()
        if probe.done then return end
        local now = Isaac.GetTime()
        if now < probe.sample and not probe.dirty then return end
        probe.sample, probe.dirty = now + 200, false
        probe_event("post_update", function()
            local game, player = Game(), Isaac.GetPlayer(0)
            local result = " paused=" .. probe_value(game:IsPaused())
                .. " clear=" .. probe_value(game:GetRoom():IsClear())
            if not player then return result .. " player=unavailable" end
            return result .. " dead=" .. probe_value(player:IsDead())
                .. " red=" .. probe_value(player:GetHearts())
                .. " max_red=" .. probe_value(player:GetMaxHearts())
                .. " soul=" .. probe_value(player:GetSoulHearts())
                .. " bone=" .. probe_value(player:GetBoneHearts())
        end)
    end)
    if not ok then probe_clear() end
end
local function probe_poll()
    if not probe.started or probe.done then return end
    local ok = pcall(function()
        if Isaac.GetTime() >= probe.deadline then probe_event("stop", nil, "deadline") end
    end)
    if not ok then probe_clear() end
end
if probe_available then
    local ok = pcall(function()
        mod:AddCallback(ModCallbacks.MC_ENTITY_TAKE_DMG, function(_, entity, amount, flags, source, countdown)
            probe_event("damage_attempt", function()
                probe.dirty = true
                return probe_entity(entity, false, true, true) .. " requested=" .. probe_value(amount)
                    .. " flags=" .. probe_value(flags) .. " countdown=" .. probe_value(countdown)
                    .. " source_type=" .. probe_value(source and source.Entity and source.Entity.Type)
            end)
            -- Always nil, including read/log failure. Never cancel damage or later callbacks.
        end)
        mod:AddCallback(ModCallbacks.MC_NPC_UPDATE, function(_, npc)
            if not probe.started or probe.done then return end
            local read_ok = pcall(function()
                local id = probe.ids[tostring(GetPtrHash(npc))]
                if id and probe.pending[id] then
                    probe_event("npc_update_hp", function() return probe_entity(npc) end)
                    probe.pending[id] = nil
                end
            end)
            if not read_ok then probe_clear() end
        end)
        for _, entry in ipairs({ {"MC_POST_NPC_INIT", "npc_init"},
            {"MC_POST_NPC_DEATH", "npc_death"}, {"MC_POST_ENTITY_KILL", "entity_kill"},
            {"MC_POST_ENTITY_REMOVE", "entity_remove"} }) do
            local callback, label = entry[1], entry[2]
            mod:AddCallback(ModCallbacks[callback], function(_, entity)
                if not probe.started or probe.done then return end
                probe_event(label, function()
                    if (label == "entity_kill" or label == "entity_remove")
                        and not entity:ToNPC() and not entity:ToPlayer() then return nil end
                    probe.dirty = true
                    if label == "entity_remove" then probe_removed(entity) end
                    return probe_entity(entity, label == "npc_init", label == "npc_init")
                end)
            end)
        end
        mod:AddCallback(ModCallbacks.MC_PRE_SPAWN_CLEAN_AWARD, function()
            probe_event("clean_award", function() probe.dirty = true; return "" end)
            -- Never return a value: rewards, completion marks and endings must proceed.
        end)
    end)
    if not ok then probe_clear() end
end

-- Opt-in read-only entity export; these tables never contain oracle/reward data.
local entities = { requested = false, ids = {}, next_id = 0 }
local entity_caps = { enemy=12, projectile=20, obstacle=12, pickup=4 }

local function entity_capable()
    return type(Isaac.GetRoomEntities) == "function" and type(GetPtrHash) == "function"
        and EntityType ~= nil and GridEntityType ~= nil
end

local action_note
local function release(reason)
    local h = actions.hold
    actions.hold = nil
    if h and action_note then action_note("release reason=" .. (reason or "transition"), h) end
    if h then trace_release(h, reason) end
end

local function training_mode()
    local a = Config.action_authorization
    return type(a) == "table" and a.profile_mode == "training"
end

local function action_authorized()
    local a = Config.action_authorization
    if type(a) ~= "table" or a.slot ~= 2
        or not state.active or type(a.expires_at) ~= "number"
        or a.expires_at % 1 ~= 0 or a.expires_at <= os.time()
        or (actions.authority_deadline and Isaac.GetTime() >= actions.authority_deadline)
        then return false end
    if a.profile_mode == "training" then
        -- Session-scoped training approval survives death restarts; never epoch-bound.
        if a.game_epoch ~= nil or a.expires_at > os.time() + Config.training_max_seconds
            or type(a.max_restarts) ~= "number" or a.max_restarts % 1 ~= 0
            or a.max_restarts < 1 or a.max_restarts > 5000 then return false end
    elseif (a.profile_mode ~= "isolated" and a.profile_mode ~= "ordinary_profile_exception")
        or a.game_epoch ~= state.epoch or a.max_restarts ~= nil
        or a.expires_at > os.time() + 1800 then return false end
    for _, key in ipairs({ "profile_id", "profile_evidence", "slot_evidence",
        "runtime_authorization" }) do
        if type(a[key]) ~= "string" or #a[key] < 1 or #a[key] > 128
            or not a[key]:match("%S") then return false end
    end
    return true
end

local close, restart_budget

-- Opt-in lifecycle diagnostics: one nonrenewable 20-minute, 256-record budget per mod load
-- (reconnects and epochs do not renew it). Fixed labels and bounded integers only; no
-- approval evidence, paths or error text. It reads state and logs; it never arms, reloads,
-- renews, issues commands or changes wire output, input results or cleanup.
local life = { started = false, done = false, count = 0, deadline = nil, busy = false,
    MAX = 256, WINDOW_MS = 1200000, LINE_MAX = 768,
    MODES = { training = true, isolated = true, ordinary_profile_exception = true },
    CLOSE = { ["Game exited; observer closed"] = "game_exit", ["Peer disconnected"] = "peer",
        ["Observer unloaded"] = "unload", ["Action authority or heartbeat expired"] = "authority" } }

-- Explicit unavailable marker: keeps field lists free of nil holes.
local function na(value) if value == nil then return "na" end return value end

local function life_value(value)
    if type(value) == "boolean" then return value and "1" or "0" end
    if type(value) == "number" then return trace_num(value) end
    assert(type(value) == "string" and #value <= 32 and value:match("^[%w_]+$"),
        "Invalid lifecycle label")
    return value
end

-- Explains the existing predicate's result; it never replaces action_authorized().
local function life_authority(now)
    local a = Config.action_authorization
    if type(a) ~= "table" then return "none", false end
    if action_authorized() then return "ok", true end
    if not state.active then return "inactive", false end
    if type(a.expires_at) ~= "number" or a.expires_at <= os.time() then return "expired", false end
    if actions.authority_deadline and now >= actions.authority_deadline then return "lease", false end
    return "other_validation", false
end

local function life_facts(now, out)
    local a = Config.action_authorization
    local auth, eligible = life_authority(now)
    local deadline, limit = restart_budget()
    local awaiting, pending = restart.awaiting, restart.pending
    local remaining = function(t) return t and t - now or "na" end
    local facts = {
        "frame", na(Game():GetFrameCount()), "session", state.session or "none",
        "epoch", state.epoch, "room", state.visit, "phase", state.phase,
        "active", state.active, "live", live.on, "approval", type(a) == "table",
        "loaded", actions.approval_loaded,
        "mode", type(a) ~= "table" and "none" or life.MODES[a.profile_mode] and a.profile_mode
            or "other",
        "auth", auth, "eligible", eligible, "lease_ms", remaining(actions.authority_deadline),
        "expires_s", type(a) == "table" and type(a.expires_at) == "number"
            and a.expires_at % 1 == 0 and a.expires_at - os.time() or "na",
        "act_armed", actions.armed, "rs_armed", restart.armed, "rs_disabled", restart.disabled,
        "attempts", restart.attempts, "limit", na(limit), "budget_ms", remaining(deadline),
        "awaiting", awaiting and awaiting.epoch or "na",
        "await_ms", awaiting and remaining(awaiting.deadline) or "na",
        "pending", pending and pending.epoch or "na",
    }
    for _, item in ipairs(facts) do out[#out + 1] = item end
end

local function life_event(label, extra)
    if Config.lifecycle_diagnostics ~= true or life.done then return end
    if life.busy then life.done = true; return end
    life.busy = true
    local ok = pcall(function()
        life.count = life.count + 1
        local now = Isaac.GetTime()
        trace_num(now)
        if not life.started then life.started, life.deadline = true, now + life.WINDOW_MS end
        local stop = now >= life.deadline and "deadline" or life.count >= life.MAX and "count"
            or nil
        local function build(fields)
            local parts = { "[Isaac Future Lifecycle]" }
            for i = 1, #fields, 2 do
                parts[#parts + 1] = fields[i] .. "=" .. life_value(fields[i + 1])
            end
            return table.concat(parts, " ")
        end
        local head = { "id", life.count, "event", stop and "stop" or label, "time_ms", now }
        local fields = { table.unpack(head) }
        if stop then
            fields[#fields + 1], fields[#fields + 2] = "reason", stop
        else
            for _, item in ipairs(type(extra) == "function" and extra() or extra or {}) do
                fields[#fields + 1] = item
            end
        end
        life_facts(now, fields)
        local line = build(fields)
        if #line > life.LINE_MAX then
            stop = "line_limit"
            head[4] = "stop"
            head[#head + 1], head[#head + 2] = "reason", stop
            line = build(head)
        end
        assert(#line <= life.LINE_MAX, "Lifecycle identity exceeds line limit")
        if stop then life.done = true end
        if Isaac.DebugString then Isaac.DebugString(line) else print(line) end
    end)
    if not ok then life.done = true end
    life.busy = false
end

local function action_guard(now)
    if not actions.armed then release(); return end
    if not action_authorized() or (now >= actions.heartbeat and not live.on) then
        close("Action authority or heartbeat expired")
        return
    end
    -- Live loop: a missed heartbeat releases input; disconnects still close and release.
    if now >= actions.heartbeat then release("heartbeat") end
    local game, player = Game(), Isaac.GetPlayer(0)
    if game:GetNumPlayers() ~= 1 or not player or player:IsDead() or game:IsPaused() then
        release()
        return
    end
    local h = actions.hold
    if h and (now >= h.deadline or game:GetFrameCount() >= h.until_frame
        or game:GetFrameCount() < h.frame or h.epoch ~= state.epoch
        or h.visit ~= state.visit) then release("expiry") end
end

local function note(message)
    if diagnostic ~= message then
        local text = "[Isaac Future Observer] " .. message:sub(1, 300)
        if Isaac.DebugString then Isaac.DebugString(text) else print(text) end
        diagnostic = message
    end
end

action_note = function(event, h)
    local ok, data = pcall(function()
        local player = Isaac.GetPlayer(0)
        return " frame=" .. Game():GetFrameCount() .. " x=" .. player.Position.X
            .. " y=" .. player.Position.Y
    end)
    note("Action " .. event .. " session=" .. tostring(state.session)
        .. " epoch=" .. state.epoch .. " sequence=" .. h.sequence
        .. " time_ms=" .. Isaac.GetTime() .. (ok and data or " state=unavailable"))
end

local function load_action_authorization()
    if Config.action_authorization ~= nil then return true end
    local file = io.open(Config.action_authorization_path, "rb")
    if not file then return false end
    local raw = file:read(2049)
    file:close()
    if not raw or #raw > 2048 then error("Local approval exceeds 2048 bytes") end
    local a, after = json.decode(raw)
    if type(a) ~= "table" or not after or not raw:sub(after):match("^%s*$") then
        error("Invalid local action approval")
    end
    local allowed = { profile_id=true, profile_mode=true, profile_evidence=true,
        slot_evidence=true, runtime_authorization=true, slot=true, game_epoch=true,
        expires_at=true, max_restarts=true }
    for key in pairs(a) do if not allowed[key] then error("Unknown local approval field") end end
    Config.action_authorization = a
    return true
end

close = function(reason)
    life_event("close", { "reason", reason == nil and "none" or life.CLOSE[reason] or "other" })
    probe_event("stop", nil, "disconnect")
    if probe.started then probe_clear() end
    probe.requested = false
    release(reason or "closed")
    if trace_firing_only() then
        trace_event("stop", " reason=close")
    else
        trace_event("close", " reason=" .. tostring(reason or "closed"):sub(1, 60))
    end
    trace.done = trace.done or trace.started
    trace_forget()
    actions.requested, actions.armed, actions.sequence = false, false, 0
    state.snapshot_frame, state.pending_frame = nil, nil
    restart.requested, restart.armed, restart.pending = false, false, nil
    if state.tcp then pcall(function() state.tcp:close() end) end
    state.tcp, state.session = nil, nil
    entities.requested, live.on = false, false
    state.phase, state.rx, state.tx, state.offset = "closed", "", "", 1
    state.next_retry = Isaac.GetTime() + Config.retry_ms
    if reason then note(reason) end
end

local function queue(message, now)
    local encoded = json.encode(message)
    if #encoded > Config.max_bytes or #state.tx > 0 then
        close("Output limit exceeded")
        return false
    end
    state.tx, state.offset, state.since = encoded .. "\n", 1, now
    return true
end

local function hello(raw, now)
    if raw:find("\r", 1, true) then error("CR delimiter is forbidden") end
    local request, after = json.decode(raw)
    if type(request) ~= "table" or not after or not raw:sub(after):match("^%s*$") then
        error("Malformed hello")
    end
    if request.type ~= "hello" or request.protocol_version ~= 1
        or request.schema_version ~= 1 or type(request.session_id) ~= "string"
        or #request.session_id ~= 32 or not request.session_id:match("^[0-9a-f]+$")
        or type(request.required_capabilities) ~= "table" then error("Unsupported hello") end
    if not actions.approval_loaded then
        actions.approval_loaded = load_action_authorization()
    end
    local names, seen = {}, {}
    local advertised = {}
    for _, name in ipairs(capabilities) do advertised[#advertised + 1] = name end
    if entity_capable() then advertised[#advertised + 1] = "entity_observation_v1" end
    if probe_available and not probe.started and not probe.done then
        advertised[#advertised + 1] = "oracle_probe_v1"
    end
    if action_authorized() then
        advertised[#advertised + 1] = "safe_actions_v1"
        if training_mode() and entity_capable() then
            advertised[#advertised + 1] = "live_loop_v1"
            advertised[#advertised + 1] = "combat_navigation_v1"
            advertised[#advertised + 1] = "combat_navigation_grid_v2"
            advertised[#advertised + 1] = "firing_geometry_v1"
            advertised[#advertised + 1] = "firing_boundary_support_v1"
            advertised[#advertised + 1] = "combat_geometry_v2"
        end
    end
    life_event("hello", function()
        local want, offer = false, false
        for _, name in ipairs(request.required_capabilities) do
            want = want or name == "live_loop_v1"
        end
        for _, name in ipairs(advertised) do offer = offer or name == "live_loop_v1" end
        return { "live_req", want, "live_adv", offer }
    end)
    local supported = {}
    for _, name in ipairs(advertised) do supported[name] = true end
    if #request.required_capabilities > #advertised then error("Too many capabilities") end
    for _, name in ipairs(request.required_capabilities) do
        if not supported[name] or seen[name] then error("Unsupported capability") end
        seen[name] = true
        names[#names + 1] = '"' .. name .. '"'
    end
    -- The shipped decoder accepts non-JSON extensions. Admit only canonical hello
    -- syntax (whitespace is allowed), rejecting duplicates, extensions and endpoints.
    local canonical = '{"type":"hello","protocol_version":1,"schema_version":1,'
        .. '"session_id":"' .. request.session_id .. '","required_capabilities":['
        .. table.concat(names, ",") .. ']}'
    if raw:gsub("%s+", "") ~= canonical then error("Noncanonical hello") end
    if seen.live_loop_v1 then
        if not (seen.entity_observation_v1 and seen.safe_actions_v1 and seen.death_restart_v1)
            or seen.oracle_probe_v1 or seen.entity_action_v1 then
            error("Live loop requires exactly entity, action and restart modes")
        end
    else
        if seen.safe_actions_v1 and training_mode() then
            error("Training approval requires the live loop")
        end
        if seen.safe_actions_v1 and seen.death_restart_v1 then error("Incompatible modes") end
        if seen.oracle_probe_v1 and (seen.safe_actions_v1 or seen.death_restart_v1
            or seen.entity_action_v1) then error("Oracle probe requires read-only mode") end
        if seen.entity_observation_v1 and (seen.safe_actions_v1 or seen.death_restart_v1) then
            error("Entity observations require read-only mode")
        end
    end
    if seen.combat_navigation_v1 and not seen.live_loop_v1 then
        error("Combat navigation requires the live loop")
    end
    if seen.combat_navigation_grid_v2 and not seen.combat_navigation_v1 then
        error("Navigation grid requires combat navigation")
    end
    if seen.firing_geometry_v1 and not seen.combat_navigation_grid_v2 then
        error("Firing geometry requires measured navigation")
    end
    live.on = seen.live_loop_v1 == true
    live.navigation = seen.combat_navigation_v1 == true
    live.navigation_grid = seen.combat_navigation_grid_v2 == true
    if seen.combat_geometry_v2 and not seen.live_loop_v1 then error("Policy geometry requires live loop") end
    live.policy_geometry = seen.combat_geometry_v2 == true
    live.firing_geometry = seen.firing_geometry_v1 == true
    if seen.firing_boundary_support_v1 and not seen.firing_geometry_v1 then
        error("Boundary support requires firing geometry")
    end
    live.boundary_support = seen.firing_boundary_support_v1 == true
    entities.requested = seen.entity_observation_v1 == true
    actions.requested = seen.safe_actions_v1 == true
    restart.requested = seen.death_restart_v1 == true
    probe.requested = seen.oracle_probe_v1 == true
    state.session, state.sequence = request.session_id, 0
    state.phase = "streaming"
    local metadata = Config.game_version ~= nil or Config.steam_build ~= nil
    queue({
        type = "hello_ack", protocol_version = 1, schema_version = 1,
        session_id = state.session, capabilities = advertised, mod_version = "0.5.0-dev",
        lua_version = _VERSION, extender_present = not not _G.REPENTOGON,
        game = {
            version = Config.game_version or json.null,
            steam_build = Config.steam_build or json.null,
            provenance = metadata and "operator_config" or "unavailable",
        },
    }, now)
    probe_start()
end

local function vector(value)
    if not value then return json.null end
    local function finite(v)
        assert(type(v) == "number" and v == v and math.abs(v) <= 100000,
            "Invalid entity coordinate")
        return math.floor(v * 1000 + 0.5) / 1000
    end
    return { x=finite(value.X), y=finite(value.Y) }
end

local function navigation_grid(room, grid_size)
    assert(grid_size > 0 and grid_size <= 1024, "Navigation grid exceeds 1024 cells")
    local width = room:GetGridWidth()
    assert(type(width) == "number" and width % 1 == 0 and width >= 3 and width <= 32
        and grid_size % width == 0, "Invalid navigation grid width")
    width = math.floor(width)
    local height = math.floor(grid_size / width)
    assert(height >= 3 and height <= 32, "Invalid navigation grid height")
    local origin, right, below = room:GetGridPosition(0), room:GetGridPosition(1),
        room:GetGridPosition(width)
    assert(right.X-origin.X == 40 and right.Y == origin.Y
        and below.Y-origin.Y == 40 and below.X == origin.X,
        "Unsupported navigation grid spacing")
    local mask = {}
    for index=0,grid_size-1 do
        local position = room:GetGridPosition(index)
        assert(position.X == origin.X + (index % width)*40
            and position.Y == origin.Y + math.floor(index/width)*40,
            "Navigation grid is not a regular lattice")
        local path = room:GetGridPath(index)
        assert(type(path) == "number" and path == path, "Navigation path value unavailable")
        local safe = room:IsPositionInRoom(position, 12) and path < 900
        if safe then
            for _, delta in ipairs({ {0,0}, {-12,-12}, {-12,12}, {12,-12}, {12,12} }) do
                if room:GetGridCollisionAtPos(Vector(position.X+delta[1],position.Y+delta[2])) ~= 0 then
                    safe = false; break
                end
            end
        end
        local grid = room:GetGridEntity(index)
        if grid then
            local kind = grid:GetType()
            if kind == GridEntityType.GRID_PIT or kind == GridEntityType.GRID_SPIKES
                or kind == GridEntityType.GRID_SPIKES_ONOFF or kind == GridEntityType.GRID_TNT then
                safe = false
            end
        end
        mask[#mask+1] = safe and "1" or "0"
    end
    return {origin=vector(origin),spacing=40,width=width,height=height,
        walkable=table.concat(mask)}
end

-- Diagnostic facts never alter membership, wire data, reward or input authority.
local target_phase = { started=false, done=false, count=0, labels={}, next_id=0,
    previous={}, last=-1000, deadline=0 }
local function phase_line(event, facts)
    if target_phase.done then return false end
    local stop = target_phase.count >= 511
    target_phase.count = target_phase.count + 1
    local text = "[Isaac Future TargetPhase] event=" .. (stop and "stop" or event)
        .. " session=" .. tostring(state.session) .. " epoch=" .. state.epoch
        .. " visit=" .. state.visit .. " frame=" .. Game():GetFrameCount()
        .. " time_ms=" .. Isaac.GetTime() .. " " .. (stop and "reason=lines" or facts)
    assert(#text <= 800, "Target phase line too long")
    if stop then target_phase.done = true end
    if Isaac.DebugString then Isaac.DebugString(text) else print(text) end
    return not stop
end
local function phase_stop(reason)
    phase_line("stop", "reason=" .. reason)
    target_phase.done = true
end
local function phase_sample(list, policy, oracle, policy_keys, oracle_keys)
    if Config.target_phase_diagnostics ~= true or not live.on or target_phase.done then return end
    local ok = pcall(function()
        local now = Isaac.GetTime()
        if not target_phase.started then
            target_phase.started, target_phase.deadline = true, now + 120000
        end
        if now >= target_phase.deadline then phase_stop("deadline"); return end
        if now - target_phase.last < 100 then return end
        target_phase.last = now
        if #list > 64 then phase_stop("scan"); return end
        local visible_ids, oracle_ids, present = {}, {}, {}
        for _, item in ipairs(policy) do visible_ids[item.entity_id] = true end
        for _, item in ipairs(oracle.enemies) do oracle_ids[item.entity_id] = true end
        for _, entity in ipairs(list) do
            local npc = entity:ToNPC()
            local vulnerable, enemy = entity:IsVulnerableEnemy(), entity:IsEnemy()
            if npc or vulnerable or enemy or (Config.target_phase_passive_effects == true
                and entity.Type == EntityType.ENTITY_EFFECT) then
                local key = "e:" .. tostring(GetPtrHash(entity)) .. ":" .. tostring(entity.InitSeed)
                local lifetime = state.epoch .. ":" .. key
                local label = target_phase.labels[lifetime]
                if not label then
                    if target_phase.next_id >= 128 then phase_stop("labels"); return end
                    target_phase.next_id = target_phase.next_id + 1
                    label = target_phase.next_id
                    target_phase.labels[lifetime] = label
                end
                local bridge_id = entities.ids[key]
                local policy_id, oracle_id = policy_keys[key], oracle_keys[key]
                local champion_color = npc and type(npc.GetChampionColorIdx) == "function"
                    and npc:GetChampionColorIdx() or nil
                local fields = { label=label, bridge_id=bridge_id, type=entity.Type,
                    policy_id=policy_id, oracle_id=oracle_id,
                    variant=entity.Variant, subtype=entity.SubType, npc_state=npc and npc.State,
                    champion_color=champion_color,
                    exists=entity:Exists(), dead=entity:IsDead(), visible=entity.Visible,
                    active=entity:IsActiveEnemy(false), active_dead=entity:IsActiveEnemy(true),
                    vulnerable=vulnerable, enemy=enemy, hp=entity.HitPoints, max_hp=entity.MaxHitPoints,
                    policy=policy_id ~= nil and visible_ids[policy_id] == true,
                    oracle=oracle_id ~= nil and oracle_ids[oracle_id] == true,
                    room_clear=oracle.room_clear }
                local parts = {}
                for _, name in ipairs({"label","bridge_id","policy_id","oracle_id","type","variant","subtype","npc_state","champion_color",
                    "exists","dead","visible","active","active_dead","vulnerable","enemy",
                    "hp","max_hp","policy","oracle","room_clear"}) do
                    parts[#parts+1] = name .. "=" .. probe_value(fields[name])
                end
                local signature = table.concat(parts, " ")
                present[label] = signature
                if target_phase.previous[label] ~= signature then
                    if not phase_line("state", signature .. " x=" .. probe_value(entity.Position.X)
                        .. " y=" .. probe_value(entity.Position.Y)) then return end
                end
            end
        end
        for label in pairs(target_phase.previous) do
            if not present[label] and not phase_line("gone", "label=" .. label) then return end
        end
        target_phase.previous = present
    end)
    if not ok then
        pcall(phase_stop, "error")
        target_phase.done = true
    end
end

-- Sampled facts only: absence is not a collision reason; range is an API statistic.
local tear_audit = { started=false, done=false, busy=false, count=0, next_id=0, labels={},
    previous={}, tracks={}, last=-1000, deadline=0, context=nil }
local function tear_line(event, facts)
    if tear_audit.done then return false end
    local stop = tear_audit.count >= 1023
    tear_audit.count = tear_audit.count + 1
    local text = "[Isaac Future TearAudit] event=" .. (stop and "stop" or event)
        .. " session=" .. tostring(state.session) .. " epoch=" .. state.epoch
        .. " visit=" .. state.visit .. " frame=" .. Game():GetFrameCount()
        .. " time_ms=" .. Isaac.GetTime() .. " " .. (stop and "reason=lines" or facts)
    assert(#text <= 900, "Tear audit line too long")
    if stop then tear_audit.done = true end
    if Isaac.DebugString then Isaac.DebugString(text) else print(text) end
    return not stop
end
local function tear_stop(reason, detail)
    tear_line("stop", "reason=" .. reason
        .. (detail and " detail=" .. tostring(detail):gsub("[^%w_]", "_"):sub(1,100) or ""))
    tear_audit.done, tear_audit.labels, tear_audit.previous, tear_audit.tracks = true, {}, {}, {}
end
local function tear_sample(list, room, player, policy)
    if Config.tear_diagnostics ~= true or not live.on or tear_audit.done then return end
    if tear_audit.busy then tear_audit.done = true; return end
    tear_audit.busy = true
    local ok, err = pcall(function()
        local now = Isaac.GetTime()
        local context = tostring(state.session) .. ":" .. state.epoch .. ":" .. state.visit
        if not tear_audit.started then
            tear_audit.started, tear_audit.deadline = true, now + 120000
            tear_audit.context = context
        end
        if context ~= tear_audit.context then tear_stop("context"); return end
        if now >= tear_audit.deadline then tear_stop("deadline"); return end
        if now - tear_audit.last < 100 then return end
        tear_audit.last = now
        if #list > 64 then tear_stop("scan"); return end
        local function fields(values, names)
            local parts = {}
            for _, name in ipairs(names) do parts[#parts+1] = name .. "=" .. probe_value(values[name]) end
            return table.concat(parts, " ")
        end
        local target
        for _, entity in ipairs(policy) do
            if entity.kind == "enemy" then target = entity; break end
        end
        local clear, hit
        if target and type(room.CheckLine) == "function" then
            clear, hit = room:CheckLine(player.Position,
                Vector(player.Position.X + target.position.x, player.Position.Y + target.position.y),
                3, 0, false, false)
            assert(type(clear) == "boolean", "Invalid CheckLine result")
        end
        local h = actions.hold
        if not tear_line("target", fields({ x=player.Position.X, y=player.Position.Y,
            range=player.TearRange, target_id=target and target.entity_id,
            dx=target and target.position.x, dy=target and target.position.y,
            clear3=clear, hit_x=hit and hit.X, hit_y=hit and hit.Y, seq=h and h.sequence },
            {"x","y","range","target_id","dx","dy","clear3","hit_x","hit_y","seq"})) then return end
        local present = {}
        for _, entity in ipairs(list) do
            if entity.Type == EntityType.ENTITY_TEAR then
                local tear = entity:ToTear()
                local owner = tear and tear.SpawnerEntity and tear.SpawnerEntity:ToPlayer()
                if owner and GetPtrHash(owner) == GetPtrHash(player) then
                    local key = tostring(GetPtrHash(entity)) .. ":" .. tostring(entity.InitSeed)
                    local label = tear_audit.labels[key]
                    if not label then
                        if tear_audit.next_id >= 64 then tear_stop("labels"); return end
                        tear_audit.next_id = tear_audit.next_id + 1
                        label = tear_audit.next_id
                        tear_audit.labels[key] = label
                    end
                    local x, y = tear.Position.X, tear.Position.Y
                    local prev, original = tear_audit.previous[label], tear_audit.tracks[label]
                    local flags = tear.TearFlags
                    -- Repentance flags may be BitSet128 userdata, never coerce them to a float.
                    local numeric_flags = type(flags) == "number" and flags == flags
                        and math.abs(flags) <= 2^53-1 and flags or nil
                    local spectral, piercing
                    if type(tear.HasTearFlags) == "function" and type(TearFlags) == "table" then
                        if TearFlags.TEAR_SPECTRAL ~= nil then
                            spectral = tear:HasTearFlags(TearFlags.TEAR_SPECTRAL)
                        end
                        if TearFlags.TEAR_PIERCING ~= nil then
                            piercing = tear:HasTearFlags(TearFlags.TEAR_PIERCING)
                        end
                    end
                    local item = { label=label, x=x, y=y, vx=tear.Velocity.X, vy=tear.Velocity.Y,
                        height=tear.Height, falling=tear.FallingSpeed, accel=tear.FallingAcceleration,
                        flags=numeric_flags, spectral=spectral, piercing=piercing,
                        grid=tear.GridCollisionClass,
                        origin_x=original and original.origin_x or x,
                        origin_y=original and original.origin_y or y }
                    item.path = (original and original.path or 0)
                        + (prev and math.sqrt((x-prev.x)^2 + (y-prev.y)^2) or 0)
                    item.distance = math.sqrt((x-item.origin_x)^2 + (y-item.origin_y)^2)
                    present[label] = item
                    tear_audit.tracks[label] = item
                    if not tear_line("sample", fields(item,
                        {"label","x","y","vx","vy","height","falling","accel","flags","grid",
                         "origin_x","origin_y","distance","path","spectral","piercing"})
                        .. " flags_type=" .. type(flags)) then return end
                end
            end
        end
        for label, prev in pairs(tear_audit.previous) do
            if not present[label] and not tear_line("absent", fields(prev,
                {"label","x","y","distance","path"})) then return end
        end
        tear_audit.previous = present
    end)
    tear_audit.busy = false
    if not ok then pcall(tear_stop, "error", err); tear_audit.done = true end
end

local function weapon_evidence(player)
    local data = {status="unavailable"}
    if type(player.HasWeaponType) ~= "function" then return data end
    local range = player.TearRange
    if type(range) ~= "number"
        or range ~= range or range <= 0 or range > 4000 then return data end
    data.tear_range = range -- native world units; never multiply TearRange by40 again
    if type(WeaponType) ~= "table" or type(WeaponType.WEAPON_TEARS) ~= "number"
        or type(WeaponType.NUM_WEAPON_TYPES) ~= "number"
        or WeaponType.NUM_WEAPON_TYPES < 2 or WeaponType.NUM_WEAPON_TYPES > 32 then return data end
    local ok, plain = pcall(function() return player:HasWeaponType(WeaponType.WEAPON_TEARS) end)
    if not ok or type(plain) ~= "boolean" then return data end
    if not plain
        or type(TearFlags) ~= "table" or TearFlags.TEAR_NORMAL == nil
        or player.TearFlags ~= TearFlags.TEAR_NORMAL then
        data.status = "unsupported"
        return data
    end
    for weapon=2,WeaponType.NUM_WEAPON_TYPES-1 do
        local known, present = pcall(function() return player:HasWeaponType(weapon) end)
        if not known or type(present) ~= "boolean" then return data end
        if present then data.status = "unsupported"; return data end
    end
    data.status = "plain_tears"
    return data
end

local function capture_boundary_support(room, player, grid)
    local px,py = player.Position.X,player.Position.Y
    local best,best_distance
    -- At most1024 cells; row-major ties match the Python validator.
    for y=0,grid.height-2 do
        for x=0,grid.width-2 do
            local index = y*grid.width+x
            local function walk(i) return grid.walkable:sub(i+1,i+1)=="1" end
            if walk(index) and walk(index+1) and walk(index+grid.width)
                and walk(index+grid.width+1) then
                local left,top = grid.origin.x+x*40,grid.origin.y+y*40
                local qx,qy = math.min(math.max(px,left),left+40),math.min(math.max(py,top),top+40)
                local d = (qx-px)^2+(qy-py)^2
                if d<=3200 and (not best_distance or d<best_distance) then
                    best_distance = d
                    -- Match the snapshot's raw player position, not rounded entity deltas.
                    best = {version=1,patch=index,source={x=px,y=py},
                        position={x=qx,y=qy},clear=json.null}
                end
            end
        end
    end
    if best then
        local ok,clear = pcall(function()
            return room:CheckLine(Vector(px,py),Vector(best.position.x,best.position.y),0,0,false,false)
        end)
        if ok and type(clear)=="boolean" then best.clear=clear end
    end
    return best or json.null
end

local function capture_firing_geometry(room, player, grid, policy, handles)
    local data = { version=1, status="unavailable", clear_cells=json.EMPTY_ARRAY,
        candidate_overflow=0 }
    if not grid or type(player.HasWeaponType) ~= "function"
        or type(room.CheckLine) ~= "function" then return data end
    local weapon = weapon_evidence(player)
    data.status, data.tear_range = weapon.status, weapon.tear_range
    if data.status ~= "plain_tears" then return data end
    if live.boundary_support then
        data.boundary_support = capture_boundary_support(room,player,grid)
    end
    local range = data.tear_range
    local target, target_id
    for _, item in ipairs(policy) do
        local entity = item.kind == "enemy" and handles[item.entity_id] or nil
        if entity and entity:IsVulnerableEnemy() then
            target, target_id = entity, item.entity_id
            break
        end
    end
    if not target then return data end
    data.target_id, data.target_position = target_id, vector(target.Position)
    data.target_vulnerable = true
    local cells, checked = {}, 0
    -- At most1024 lattice cells and32 native line queries per capture, no commands.
    for index=0,grid.width*grid.height-1 do
        if grid.walkable:sub(index+1,index+1) == "1" then
            local x = grid.origin.x + (index % grid.width) * grid.spacing
            local y = grid.origin.y + math.floor(index / grid.width) * grid.spacing
            local dx, dy = math.abs(x-target.Position.X), math.abs(y-target.Position.Y)
            local distance = math.sqrt(dx*dx+dy*dy)
            if math.min(dx,dy) <= 8 and distance >= 80 and distance <= range-20 then
                if checked >= 32 then
                    data.candidate_overflow = data.candidate_overflow + 1
                else
                    checked = checked + 1
                    local clear = room:CheckLine(Vector(x,y), target.Position, 3, 0, false, false)
                    assert(type(clear) == "boolean", "Invalid firing line result")
                    if clear then cells[#cells+1] = index end
                end
            end
        end
    end
    data.clear_cells = #cells > 0 and cells or json.EMPTY_ARRAY
    return data
end

local function capture_policy_geometry(room, player, policy, frame_id)
    local weapon = weapon_evidence(player)
    local data = {version=2,frame_id=frame_id,weapon=weapon.status,
        tear_range=weapon.status == "plain_tears" and weapon.tear_range or json.null,
        movement={},enemies={}}
    local function line(a,b,mode)
        if type(room.CheckLine) ~= "function" then return json.null end
        local ok,clear = pcall(function() return room:CheckLine(a,b,mode,0,false,false) end)
        if not ok or type(clear) ~= "boolean" then return json.null end
        return clear
    end
    for _,delta in ipairs({{-40,0},{40,0},{0,-40},{0,40}}) do
        local clear = json.null
        if player.CanFly == false then
            clear = line(player.Position,Vector(player.Position.X+delta[1],player.Position.Y+delta[2]),0)
        end
        data.movement[#data.movement+1] = clear
    end
    for _,item in ipairs(policy) do
        if item.kind == "enemy" then
            local clear = json.null
            if weapon.status == "plain_tears" then
                clear = line(player.Position,Vector(player.Position.X+item.position.x,
                    player.Position.Y+item.position.y),3)
            end
            data.enemies[#data.enemies+1] = {entity_id=item.entity_id,clear=clear}
        end
    end
    if #data.enemies == 0 then data.enemies=json.EMPTY_ARRAY end
    return data
end

local function capture_entities(room, player, data)
    local list = Isaac.GetRoomEntities()
    assert(type(list) == "table" and #list <= 1024, "Room entity scan exceeds 1024")
    local grid_size = room:GetGridSize()
    assert(type(grid_size) == "number" and grid_size % 1 == 0
        and grid_size >= 0 and grid_size <= 2048, "Room grid scan exceeds 2048")
    local groups = { enemy={}, projectile={}, obstacle={}, pickup={} }
    local retained = {}
    local phase_policy = Config.target_phase_diagnostics == true and {} or nil
    local phase_oracle = Config.target_phase_diagnostics == true and {} or nil
    local oracle_enemies, oracle_overflow = {}, 0
    local firing_handles = live.firing_geometry and {} or nil
    local function identity(key)
        local id = entities.ids[key]
        if not id then
            entities.next_id = entities.next_id + 1
            assert(entities.next_id <= 9007199254740991, "Entity identity exhausted")
            id = entities.next_id
        end
        retained[key] = id
        return id
    end
    local function add(kind, key, position, velocity)
        local relative = vector({ X=position.X-player.Position.X, Y=position.Y-player.Position.Y })
        local item = { kind=kind, entity_id=identity(key), spawn_generation=0,
            position=relative, velocity=vector(velocity), hp=json.null, max_hp=json.null }
        groups[kind][#groups[kind]+1] = item
        if phase_policy then phase_policy[key] = item.entity_id end
    end
    for _, entity in ipairs(list) do
        -- Seeds and pointers are internal lifetime keys, never policy features.
        local key = "e:" .. tostring(GetPtrHash(entity)) .. ":" .. tostring(entity.InitSeed)
        if entities.ids[key] then retained[key] = entities.ids[key] end
        if entity:Exists() and entity.Visible and not entity:IsDead() then
            local kind
            if entity:IsActiveEnemy(false) then kind = "enemy"
            elseif entity.Type == EntityType.ENTITY_PROJECTILE then kind = "projectile"
            elseif entity.Type == EntityType.ENTITY_PICKUP then kind = "pickup" end
            if kind then
                add(kind, key, entity.Position, entity.Velocity)
                if firing_handles and kind == "enemy" then
                    firing_handles[groups.enemy[#groups.enemy].entity_id] = entity
                end
            end
        end
        -- Live-loop reward labels only; leaves through the separate oracle block.
        -- Invisible (e.g. burrowed) enemies stay listed so hiding is not a kill.
        if live.on and entity:Exists() and not entity:IsDead()
            and entity:IsActiveEnemy(false) then
            local max_hp, hp = entity.MaxHitPoints, entity.HitPoints
            if type(max_hp) == "number" and type(hp) == "number" and max_hp > 0
                and max_hp <= 1000000 and hp == hp then
                if #oracle_enemies >= Config.live_oracle_enemies then
                    oracle_overflow = oracle_overflow + 1
                else
                    hp = math.max(0, math.min(hp, max_hp))
                    oracle_enemies[#oracle_enemies + 1] = { entity_id=identity(key),
                        hp=math.floor(hp * 1000 + 0.5) / 1000,
                        max_hp=math.max(0.001, math.floor(max_hp * 1000 + 0.5) / 1000) }
                    if phase_oracle then phase_oracle[key] = oracle_enemies[#oracle_enemies].entity_id end
                end
            end
        end
    end
    -- Only ordinary visible geometry; no doors, hidden rooms, rock subtype or contents.
    local allowed_grid = {}
    for _, name in ipairs({ "GRID_ROCK", "GRID_ROCKB", "GRID_ROCKT", "GRID_ROCK_BOMB",
        "GRID_ROCK_ALT", "GRID_ROCK_SS", "GRID_PIT", "GRID_SPIKES", "GRID_SPIKES_ONOFF",
        "GRID_POOP", "GRID_TNT", "GRID_WALL" }) do
        local kind = GridEntityType[name]
        if kind then allowed_grid[kind] = true end
    end
    for index=0,grid_size-1 do
        local grid = room:GetGridEntity(index)
        if grid and grid.CollisionClass ~= 0 and allowed_grid[grid:GetType()] then
            add("obstacle", "g:" .. index .. ":" .. grid:GetType(), grid.Position, nil)
        end
    end
    entities.ids = retained
    local result, overflow = {}, {}
    for _, kind in ipairs({ "enemy", "projectile", "obstacle", "pickup" }) do
        local group = groups[kind]
        table.sort(group, function(a,b)
            local ad = a.position.x*a.position.x + a.position.y*a.position.y
            local bd = b.position.x*b.position.x + b.position.y*b.position.y
            return ad == bd and a.entity_id < b.entity_id or ad < bd
        end)
        if #group > entity_caps[kind] then overflow[kind] = #group - entity_caps[kind] end
        for i=1,math.min(#group,entity_caps[kind]) do result[#result+1] = group[i] end
    end
    local oracle = nil
    if live.on then
        oracle = { room_clear = room:IsClear() == true, player_dead = player:IsDead() == true,
            enemies = #oracle_enemies > 0 and oracle_enemies or json.EMPTY_ARRAY,
            enemy_overflow = oracle_overflow }
        if live.navigation then
            local level, doors = Game():GetLevel(), {}
            for slot=0,7 do
                local door = room:GetDoor(slot)
                if door and door:IsOpen() and not door:IsLocked()
                    and door.TargetRoomType == RoomType.ROOM_DEFAULT then
                    doors[#doors+1] = { slot=slot, position=vector(room:GetDoorSlotPosition(slot)) }
                end
            end
            oracle.navigation = { version=1, room_index=level:GetCurrentRoomIndex(),
                stage=level:GetStage(), stage_type=level:GetStageType(),
                room_type=room:GetType(), shape=room:GetRoomShape(),
                doors=#doors>0 and doors or json.EMPTY_ARRAY }
            if live.navigation_grid then
                oracle.navigation.version = 2
                oracle.navigation.grid = navigation_grid(room, grid_size)
            end
        end
    end
    if live.policy_geometry then
        data.combat_geometry = capture_policy_geometry(room,player,result,data.frame)
    end
    if oracle and live.firing_geometry then
        oracle.firing = capture_firing_geometry(room, player,
            oracle.navigation and oracle.navigation.grid, result, firing_handles)
    end
    if oracle then phase_sample(list, result, oracle, phase_policy, phase_oracle) end
    if oracle then tear_sample(list, room, player, result) end
    return {
        type="entity_frame", observation_schema_version=1, provenance="game_api",
        session_id=state.session, game_epoch=state.epoch, room_visit=state.visit,
        frame_id=data.frame, player_position=data.player.position,
        player_velocity=vector(player.Velocity), health=data.player.health,
        entities=#result > 0 and result or json.EMPTY_ARRAY,
        source_overflow=next(overflow) and overflow or json.EMPTY_OBJECT,
    }, oracle
end

local function capture()
    if not state.active then return nil, "not_in_game" end
    local ok, result = pcall(function()
        local game = Game()
        if game:GetNumPlayers() < 1 then return nil end
        local room, player = game:GetRoom(), Isaac.GetPlayer(0)
        if not room or not player then return nil end
        local data = {
            frame = game:GetFrameCount(), paused = game:IsPaused(),
            player = {
                index = 0, character_type = player:GetPlayerType(),
                position = { x = player.Position.X, y = player.Position.Y },
                health = {
                    red_half_hearts = player:GetHearts(),
                    max_red_half_hearts = player:GetMaxHearts(),
                    soul_half_hearts = player:GetSoulHearts(),
                    bone_containers = player:GetBoneHearts(),
                },
            },
        }
        if entities.requested then
            data.entity_frame, data.oracle = capture_entities(room, player, data)
        end
        return data
    end)
    if not ok or not result then return nil, "state_read_failed" end
    return result
end

local function snapshot(now)
    local data, reason = capture()
    state.sequence = state.sequence + 1
    state.pending_frame = data and data.frame or nil
    local message = {
        type = "snapshot", schema_version = 1, session_id = state.session,
        sequence = state.sequence, game_epoch = state.epoch, update_id = state.updates,
        frame_id = data and data.frame or json.null,
        status = data and (data.paused and "paused" or "active") or "unavailable",
        reason = reason or json.null,
        room = data and { visit_id = state.visit } or json.null,
        player = data and data.player or json.null,
    }
    if entities.requested then message.entity_frame = data and data.entity_frame or json.null end
    if live.on then message.oracle = data and data.oracle or json.null end
    if live.policy_geometry then
        message.combat_geometry = data and data.combat_geometry or json.null
    end
    queue(message, now)
end

local function command(raw, now)
    if not actions.armed or not action_authorized() then error("Actions not authorized") end
    if #raw > 1024 or raw:find("\r", 1, true) then error("Invalid command size/delimiter") end
    local c, after = json.decode(raw)
    if type(c) ~= "table" or not after or not raw:sub(after):match("^%s*$") then
        error("Malformed command")
    end
    local function counter(value)
        return type(value) == "number" and value >= 0 and value <= 9007199254740991
            and value % 1 == 0
    end
    for _, key in ipairs({ "sequence", "game_epoch", "room_visit", "frame_id", "frames" }) do
        if not counter(c[key]) then error("Invalid command integer") end
    end
    local directions = { none=true, left=true, right=true, up=true, down=true }
    if c.type ~= "command" or c.protocol_version ~= 1 or c.session_id ~= state.session
        or c.sequence <= actions.sequence
        or not directions[c.move] or not directions[c.shoot]
        or (c.kind ~= "action" and c.kind ~= "heartbeat" and c.kind ~= "release")
        or (c.kind == "action" and (c.frames < 1 or c.frames > 15))
        or (c.kind ~= "action" and (c.frames ~= 0 or c.move ~= "none" or c.shoot ~= "none"))
        then error("Stale or incompatible command") end
    -- The live loop may reference any already-sent frame of this room visit; the
    -- strictly increasing sequence and the 15-frame window below still bound replay.
    local stale = c.game_epoch ~= state.epoch or c.room_visit ~= state.visit
        or (not live.on and c.frame_id ~= state.snapshot_frame)
        or (live.on and (state.snapshot_frame == nil or c.frame_id > state.snapshot_frame))
    if stale and not live.on then error("Stale or incompatible command") end
    local canonical = '{"type":"command","protocol_version":1,"session_id":"'
        .. state.session .. '","sequence":' .. string.format("%.0f", c.sequence)
        .. ',"game_epoch":' .. string.format("%.0f", c.game_epoch)
        .. ',"room_visit":' .. string.format("%.0f", c.room_visit)
        .. ',"frame_id":' .. string.format("%.0f", c.frame_id)
        .. ',"kind":"' .. c.kind .. '","move":"' .. c.move
        .. '","shoot":"' .. c.shoot .. '","frames":' .. string.format("%.0f", c.frames) .. '}'
    if raw:gsub("%s+", "") ~= canonical then error("Noncanonical command") end
    local game, player = Game(), Isaac.GetPlayer(0)
    local frame = game:GetFrameCount()
    if stale or frame < c.frame_id or frame - c.frame_id > 15 or game:IsPaused()
        or game:GetNumPlayers() ~= 1 or not player or player:IsDead() then
        if not live.on then error("Command state unavailable or stale") end
        -- Live loop: races with death, rooms and pauses are expected; refuse without closing.
        actions.sequence, actions.heartbeat = c.sequence, now + 500
        release("rejected")
        queue({ type="command_ack", protocol_version=1, session_id=state.session,
            sequence=c.sequence, game_epoch=c.game_epoch, room_visit=c.room_visit,
            frame_id=c.frame_id, kind=c.kind, status="rejected" }, now)
        return
    end
    actions.sequence, actions.heartbeat = c.sequence, now + 500
    if c.kind == "release" then release("explicit_release")
    elseif c.kind == "action" then
        release("replaced")
        actions.hold = { move=c.move, shoot=c.shoot, frame=frame, epoch=state.epoch,
            visit=state.visit, until_frame=frame+c.frames, deadline=now+250,
            sequence=c.sequence, tears=0 }
        action_note("accepted move=" .. c.move .. " shoot=" .. c.shoot, actions.hold)
        trace_accepted(c, actions.hold)
    end
    queue({ type="command_ack", protocol_version=1, session_id=state.session,
        sequence=c.sequence, game_epoch=state.epoch, room_visit=state.visit,
        frame_id=frame, kind=c.kind, status="accepted" }, now)
end

-- Live loop uses the training approval lease and restart limit; otherwise 3 / 600 s.
restart_budget = function()
    local a = Config.action_authorization
    if live.on and type(a) == "table" and a.profile_mode == "training" then
        return actions.authority_deadline, a.max_restarts
    end
    return restart.deadline, 3
end

local function pump()
    local now = Isaac.GetTime()
    if state.phase == "closed" then
        if now < state.next_retry then return end
        state.next_retry = now + Config.retry_ms
        if not socket then
            local ok, module = pcall(require, "socket.core")
            local json_ok, json_module = pcall(require, "json")
            if not ok or not json_ok then
                note("Bundled socket/json unavailable: " .. tostring(not ok and module or json_module))
                return
            end
            socket, json = module, json_module
        end
        assert(Config.host == "127.0.0.1", "Only loopback is permitted")
        local tcp, err = socket.tcp()
        if not tcp then close("Socket creation failed: " .. tostring(err)); return end
        state.tcp = tcp
        assert(tcp:settimeout(0))
        local connected, connect_error = tcp:connect(Config.host, Config.port)
        if not connected and connect_error ~= "timeout" then
            close("Connection unavailable")
            return
        end
        state.phase, state.since = connected and "hello" or "connecting", now
        return
    end
    if state.phase == "connecting" then
        if state.tcp:getpeername() then
            state.phase, state.since = "hello", now
        elseif now - state.since >= Config.timeout_ms then
            close("Connect deadline expired")
        end
        return
    end
    if (state.phase == "hello" or #state.tx > 0)
        and now - state.since >= Config.timeout_ms then
        close("Handshake/output deadline expired")
        return
    end
    -- Numeric receive bounds work on older LuaSocket; do not depend on new maxsize.
    local received, err, partial = state.tcp:receive(Config.io_bytes)
    local chunk = received or partial or ""
    if #chunk > 0 then
        if state.phase ~= "hello" and not actions.armed then
            close("No requests after hello"); return
        end
        state.rx = state.rx .. chunk
    end
    local limit = state.phase == "hello" and Config.max_bytes or 1024
    local newline = state.rx:find("\n", 1, true)
    if #state.rx > limit + 1 or (not newline and #state.rx > limit) then
        close("Input limit exceeded"); return
    end
    if newline and #state.tx == 0 then
        local raw = state.rx:sub(1, newline - 1)
        state.rx = state.rx:sub(newline + 1)
        if state.phase == "hello" then
            if #state.rx > 0 then close("Only one hello request is supported"); return end
            hello(raw, now)
        else
            command(raw, now)
        end
    end
    if err and err ~= "timeout" then close("Peer disconnected"); return end
    if state.phase == "streaming" and #state.tx == 0
        and now - state.last_sample >= (live.on and Config.live_sample_ms or Config.sample_ms) then
        state.last_sample = now
        snapshot(now)
    end
    if #state.tx > 0 then
        local finish = math.min(#state.tx, state.offset + Config.io_bytes - 1)
        local sent, send_error, last = state.tcp:send(state.tx, state.offset, finish)
        state.offset = (sent or last or (state.offset - 1)) + 1
        if send_error and send_error ~= "timeout" then
            close("Peer stopped receiving"); return
        end
        if state.offset > #state.tx then
            state.tx, state.offset = "", 1
            if state.pending_frame ~= nil then
                state.snapshot_frame, state.pending_frame = state.pending_frame, nil
            end
            if actions.requested then
                if not actions.authority_deadline then
                    local a = Config.action_authorization
                    actions.authority_deadline = training_mode()
                        and now + (a.expires_at - os.time()) * 1000 or now + 120000
                end
                actions.requested, actions.armed, actions.heartbeat = false, true, now + 500
            end
            if restart.requested then
                restart.requested = false
                if not restart.deadline then restart.deadline = now + 600000 end
                local deadline, limit = restart_budget()
                restart.armed = not restart.disabled and deadline ~= nil and now < deadline
                    and restart.attempts < limit
                life_event("restart_arm")
                note(restart.armed and (live.on and "Death restart armed: live loop limit "
                    .. limit .. " attempts" or "Death restart armed: limit 3 attempts / 600 seconds")
                    or "Death restart unavailable: lease/budget/fault")
            end
        end
    end
end

-- No console text comes from the wire. Only a future game-over event can reach
-- this fixed command, after nonblocking transport work has detected disconnects.
local function authorized(now)
    local deadline, limit = restart_budget()
    return restart.armed and not restart.disabled and state.active
        and state.phase == "streaming" and state.session ~= nil
        and deadline ~= nil and now < deadline and restart.attempts < limit
end

local function lifecycle()
    local now = Isaac.GetTime()
    local deadline, limit = restart_budget()
    if restart.armed and (not deadline or now >= deadline or restart.attempts >= limit) then
        restart.armed = false
        life_event("restart_stop")
        note("Death restart stopped: lease or attempt budget exhausted")
    end
    if restart.awaiting and now >= restart.awaiting.deadline then
        restart.awaiting, restart.disabled, restart.armed = nil, true, false
        life_event("restart_timeout")
        note("Death restart fault: fresh game-start confirmation timed out; disabled")
    end
    local pending = restart.pending
    if not pending then return end
    if not authorized(now) or pending.session ~= state.session
        or pending.epoch ~= state.epoch or now - pending.since > 5000 then
        restart.pending = nil
        life_event("restart_cancel")
        note("Death restart cancelled: session/epoch/lease/delay changed")
        return
    end
    if now - pending.since < 1500 then return end
    if live.on and restart.last_dispatch
        and now - restart.last_dispatch < Config.live_restart_interval_ms then return end
    restart.pending = nil
    local ok, dead = pcall(function()
        return Game():GetNumPlayers() == 1 and Isaac.GetPlayer(0):IsDead()
    end)
    if not ok or not dead then
        note("Death restart cancelled: player revived, unavailable or not solo")
        return
    end
    restart.attempts = restart.attempts + 1
    restart.awaiting = { epoch = pending.epoch, deadline = now + 5000 }
    restart.last_dispatch = now
    note("Death restart dispatch session=" .. pending.session .. " epoch="
        .. pending.epoch .. " attempt=" .. restart.attempts)
    life_event("dispatch_before", { "restart_id", restart.attempts })
    local dispatched, err = pcall(Isaac.ExecuteCommand, "restart")
    if not dispatched then
        restart.awaiting, restart.disabled, restart.armed = nil, true, false
        note("Death restart fault: command failed; disabled: " .. tostring(err))
    end
    life_event("dispatch_after", { "restart_id", restart.attempts, "ok", dispatched })
end

mod:AddCallback(ModCallbacks.MC_POST_RENDER, function()
    probe_poll()
    trace_event("render_enter")
    local ok, err = pcall(function() action_guard(Isaac.GetTime()); pump(); lifecycle() end)
    if not ok then close("Observer capability/protocol fault: " .. tostring(err)) end
    trace_event("render_exit")
end)
mod:AddCallback(ModCallbacks.MC_POST_UPDATE, function()
    state.updates = state.updates + 1
    trace_event("update_enter")
    local ok, err = pcall(action_guard, Isaac.GetTime())
    if not ok then close("Action guard fault: " .. tostring(err)) end
    trace_update()
    trace_event("update_exit")
    probe_update()
end)
mod:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, function(_, continued)
    life_event("start_enter", function()
        return { "continued", type(continued) ~= "boolean" and "na" or continued,
            "corr", restart.awaiting and "awaiting" or "uncorrelated" }
    end)
    release()
    entities.ids, entities.next_id = {}, 0
    state.snapshot_frame, state.pending_frame = nil, nil
    state.active, state.epoch, state.visit = true, state.epoch + 1, 0
    restart.pending = nil
    local awaiting = restart.awaiting
    if awaiting then
        restart.awaiting = nil
        if continued == false and state.epoch > awaiting.epoch
            and Isaac.GetTime() < awaiting.deadline then
            note("Death restart confirmed old_epoch=" .. awaiting.epoch
                .. " new_epoch=" .. state.epoch)
        else
            restart.disabled, restart.armed = true, false
            note("Death restart fault: unexpected game-start; disabled")
        end
    end
    trace_event("game_started", " continued=" .. tostring(continued))
    trace_forget()
    probe.ids, probe.pending, probe.post = {}, {}, {}
    probe_event("game_started", function() return " continued=" .. probe_value(continued) end)
    life_event("start_exit")
end)
local function game_end(game_over)
    release()
    trace_event("game_end", " game_over=" .. tostring(game_over))
    trace_forget()
    probe_event("game_end", function() return " game_over=" .. probe_value(game_over) end)
    probe.post = {}
    -- The live loop stays armed so racing commands get refusals rather than a disconnect.
    if not live.on then actions.armed = false end
    if game_over ~= true then restart.pending = nil; return end
    if not authorized(Isaac.GetTime()) or restart.awaiting
        or restart.seen_epoch == state.epoch then return end
    restart.seen_epoch = state.epoch
    restart.pending = {
        session = state.session, epoch = state.epoch, since = Isaac.GetTime(),
    }
    note("Death restart scheduled session=" .. state.session .. " epoch=" .. state.epoch)
end
mod:AddCallback(ModCallbacks.MC_POST_GAME_END, function(_, game_over)
    life_event("game_end_enter", function()
        return { "game_over", type(game_over) ~= "boolean" and "na" or game_over }
    end)
    game_end(game_over)
    life_event("game_end_exit")
end)
mod:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, function()
    release()
    entities.ids = {}
    state.snapshot_frame, state.pending_frame = nil, nil
    state.visit = state.visit + 1
    trace_event("new_room")
    trace_forget()
    probe_event("new_room")
    probe.ids, probe.pending, probe.post = {}, {}, {}
end)
mod:AddCallback(ModCallbacks.MC_PRE_GAME_EXIT, function()
    life_event("exit_enter", function() return { "corr", restart.awaiting and "awaiting" or "uncorrelated" } end)
    -- A normal exit invalidates the operator's selected-profile confirmation.
    if restart.deadline and not restart.awaiting then
        life_event("restart_invalidate")
        restart.disabled = true
    end
    -- A live-loop death restart also exits; only a normal exit drops training approval.
    if not (live.on and restart.awaiting) then
        life_event("approval_drop")
        Config.action_authorization = nil
    else
        life_event("approval_preserve")
    end
    state.active = false
    trace_event("pre_game_exit")
    probe_event("pre_game_exit")
    close("Game exited; observer closed")
    life_event("exit_exit")
end)
mod:AddCallback(ModCallbacks.MC_PRE_MOD_UNLOAD, function(_, unloading)
    if unloading == mod then
        trace_event("pre_mod_unload")
        probe_event("pre_mod_unload")
        close("Observer unloaded")
    end
end)
mod:AddCallback(ModCallbacks.MC_POST_NEW_LEVEL, function()
    release()
    state.snapshot_frame, state.pending_frame = nil, nil
    trace_event("new_level")
    trace_forget()
    probe_event("new_level")
    probe.post = {}
end)
mod:AddCallback(ModCallbacks.MC_INPUT_ACTION, function(_, entity, hook, button)
    local ok, result = pcall(function()
        action_guard(Isaac.GetTime())
        local h = actions.hold
        if not h or not entity then return nil end
        local player = entity:ToPlayer()
        if not player or GetPtrHash(player) ~= GetPtrHash(Isaac.GetPlayer(0)) then return nil end
        local movement = {
            [ButtonAction.ACTION_LEFT]="left", [ButtonAction.ACTION_RIGHT]="right",
            [ButtonAction.ACTION_UP]="up", [ButtonAction.ACTION_DOWN]="down",
        }
        local shooting = {
            [ButtonAction.ACTION_SHOOTLEFT]="left", [ButtonAction.ACTION_SHOOTRIGHT]="right",
            [ButtonAction.ACTION_SHOOTUP]="up", [ButtonAction.ACTION_SHOOTDOWN]="down",
        }
        if not movement[button] and not shooting[button] then return nil end
        local pressed = movement[button] == h.move or shooting[button] == h.shoot
        if hook == InputHook.GET_ACTION_VALUE then return pressed and 1.0 or 0.0 end
        if hook == InputHook.IS_ACTION_PRESSED then return pressed end
        if hook == InputHook.IS_ACTION_TRIGGERED then return false end
        return nil
    end)
    if not ok then close("Native input fault: " .. tostring(result)); return nil end
    if result ~= nil then trace_input(hook, button, result, entity)
    elseif trace.rel then trace_release_input(entity, hook, button) end
    return result
end)
mod:AddCallback(ModCallbacks.MC_POST_FIRE_TEAR, function(_, tear)
    local h = actions.hold
    if not h or h.shoot == "none" or h.tears >= 4 then return end
    local ok, err = pcall(function()
        if not tear.SpawnerEntity then return end
        local player = tear.SpawnerEntity:ToPlayer()
        if not player or GetPtrHash(player) ~= GetPtrHash(Isaac.GetPlayer(0)) then return end
        action_guard(Isaac.GetTime())
        if actions.hold ~= h then return end
        if trace_live() then
            local extra = trace_cooldown(player)
            if extra then trace_event("fire_tear", extra) end
        end
        h.tears = h.tears + 1
        action_note("tear vx=" .. tear.Velocity.X .. " vy=" .. tear.Velocity.Y, h)
    end)
    if not ok then close("Tear evidence fault: " .. tostring(err)) end
end)
note("Observer 0.5.0-dev registered; awaiting render callbacks")
