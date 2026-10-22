-- Passive timing evidence ledger (experimental, unshipped).
-- Records caller-supplied facts only. It calls no engine, clock, socket, logger or
-- filesystem API, grants no input authority, and never labels anything completed or
-- applied. Query counts are observations, never proof of engine consumption.

local Ledger = {}
Ledger.__index = Ledger

local MAX = 9007199254740991 -- 2^53 - 1
local MAX_REPEAT = 15
local CALL_BUDGET = 4096
local HOOKS = { "GET_ACTION_VALUE", "IS_ACTION_PRESSED", "IS_ACTION_TRIGGERED" }
local KNOWN_HOOK = {}
for _, name in ipairs(HOOKS) do KNOWN_HOOK[name] = true end

local function counter(value, name, min)
    min = min or 0
    if type(value) ~= "number" or value ~= value or value % 1 ~= 0
        or value < min or value > MAX then
        error(name .. " must be an integer in " .. min .. "..2^53-1", 3)
    end
    return math.tointeger(value)
end

local function check_hook_value(hook, button, value)
    if type(hook) ~= "string" or not KNOWN_HOOK[hook] then
        error("unknown input hook", 3)
    end
    button = counter(button, "button")
    if button > 7 then error("button must be an integer in 0..7", 2) end
    if hook == "GET_ACTION_VALUE" then
        if type(value) ~= "number" or value ~= value or value < 0 or value > 1 then
            error("GET_ACTION_VALUE value must be a finite number in 0..1", 3)
        end
    elseif type(value) ~= "boolean" then
        error(hook .. " value must be a boolean", 3)
    end
    return button
end

local function spend(self)
    if self.calls >= CALL_BUDGET then error("observation call budget exhausted", 3) end
    self.calls = self.calls + 1
end

function Ledger.new(sequence, accepted_frame, requested_frames)
    sequence = counter(sequence, "sequence", 1)
    accepted_frame = counter(accepted_frame, "accepted_frame")
    requested_frames = counter(requested_frames, "requested_frames", 1)
    if requested_frames > MAX_REPEAT then error("requested_frames must be 1..15", 2) end
    if accepted_frame + requested_frames > MAX then error("end frame exceeds 2^53-1", 2) end
    local self = setmetatable({
        sequence = sequence, accepted = accepted_frame, requested = requested_frames,
        calls = 0, release = nil,
        dropped = { query_out_of_window = 0, query_after_close = 0,
            post_update_out_of_window = 0 },
        queries = {}, posts = {},
    }, Ledger)
    for i = 1, requested_frames do
        local cells = {}
        for _, hook in ipairs(HOOKS) do
            cells[hook] = {}
            for button = 0, 7 do cells[hook][button] = { count = 0 } end
        end
        self.queries[i] = cells
    end
    for i = 1, requested_frames + 1 do self.posts[i] = { count = 0, after_release = 0 } end
    return self
end

-- Returns true when the query fell inside the window and the ledger was still open.
function Ledger:observe_query(frame, update_counter, hook, button, value)
    frame = counter(frame, "frame")
    update_counter = counter(update_counter, "update_counter")
    button = check_hook_value(hook, button, value)
    spend(self)
    if self.release then
        self.dropped.query_after_close = self.dropped.query_after_close + 1
        return false
    end
    local offset = frame - self.accepted
    if offset < 0 or offset >= self.requested then
        self.dropped.query_out_of_window = self.dropped.query_out_of_window + 1
        return false
    end
    local cell = self.queries[offset + 1][hook][button]
    cell.count = cell.count + 1
    if cell.count == 1 then
        cell.first_update, cell.first_value = update_counter, value
    end
    cell.last_update, cell.last_value = update_counter, value
    return true
end

-- The endpoint frame (accepted + requested) is observable, also after close.
function Ledger:observe_post_update(frame, update_counter)
    frame = counter(frame, "frame")
    update_counter = counter(update_counter, "update_counter")
    spend(self)
    local offset = frame - self.accepted
    if offset < 0 or offset > self.requested then
        self.dropped.post_update_out_of_window = self.dropped.post_update_out_of_window + 1
        return false
    end
    local slot = self.posts[offset + 1]
    slot.count = slot.count + 1
    if slot.count == 1 then slot.first_update = update_counter end
    slot.last_update = update_counter
    if self.release then slot.after_release = slot.after_release + 1 end
    return true
end

-- Records the first release cause only; the reason is opaque and never interpreted.
function Ledger:close(reason, frame, update_counter)
    if type(reason) ~= "string" or #reason < 1 or #reason > 64
        or not reason:find("%S") or reason:find("%c") then
        error("reason must be a nonblank string of at most 64 bytes without control characters", 2)
    end
    frame = counter(frame, "frame")
    update_counter = counter(update_counter, "update_counter")
    if self.release then return false end
    self.release = { reason = reason, frame = frame, update_counter = update_counter }
    return true
end

local function copy_fields(source, keys)
    local out = {}
    for _, key in ipairs(keys) do out[key] = source[key] end
    return out
end

local CELL_KEYS = { "count", "first_update", "last_update", "first_value", "last_value" }
local POST_KEYS = { "count", "first_update", "last_update", "after_release" }

-- Detached deep copy; only observed cells are listed. No immutability is claimed.
function Ledger:snapshot()
    local snap = {
        sequence = self.sequence, accepted_frame = self.accepted,
        requested_frames = self.requested, calls = self.calls,
        limits = { query_slots = self.requested, post_update_slots = self.requested + 1,
            hooks = #HOOKS, buttons = 8, call_budget = CALL_BUDGET },
        dropped = copy_fields(self.dropped,
            { "query_out_of_window", "query_after_close", "post_update_out_of_window" }),
        query_window = {}, post_updates = {},
    }
    for i = 1, self.requested do
        local slot = { frame = self.accepted + i - 1, cells = {} }
        for _, hook in ipairs(HOOKS) do
            slot.cells[hook] = {}
            for button = 0, 7 do
                local cell = self.queries[i][hook][button]
                if cell.count > 0 then slot.cells[hook][button] = copy_fields(cell, CELL_KEYS) end
            end
        end
        snap.query_window[i] = slot
    end
    for i = 1, self.requested + 1 do
        local slot = copy_fields(self.posts[i], POST_KEYS)
        slot.frame = self.accepted + i - 1
        snap.post_updates[i] = slot
    end
    if self.release then snap.release = copy_fields(self.release,
        { "reason", "frame", "update_counter" }) end
    return snap
end

return Ledger
