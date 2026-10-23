-- Default read-only observer; opt-in lifecycle and explicitly authorized native actions.
local mod = RegisterMod("Isaac Future Observer", 1)
local Config = {
    host = "127.0.0.1", port = 9528, max_bytes = 49152, hello_bytes = 16384, io_bytes = 4096,
    timeout_ms = 3000, retry_ms = 1000, sample_ms = 200,
    -- Operator-supplied metadata is optional; never pretend it is runtime detection.
    game_version = nil, steam_build = nil,
    -- Default disabled; optional private expiring approval is loaded once per mod load.
    action_authorization = nil,
    action_authorization_path = "mods/isaac_threrisaifuture_observer/action_authorization.json",
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
-- Live loop: entity observation, actions and restarts in one approved session.
local live = { on = false }
local diagnostic = nil

-- Opt-in read-only entity export; these tables never contain oracle/reward data.
local entities = { requested = false, ids = {}, next_id = 0 }
local entity_caps = { enemy=12, projectile=20, obstacle=24, pickup=8, own_attack=16, bomb=4 }
-- Held collectibles change rarely, so the scan is cached and refreshed on a short cadence.
local collectible_cap, collectible_max_id, collectible_period = 256, 1024, 30
-- Oracle metrics: cumulative per game epoch, reset on game start. Never policy input.
local HIT_CLASSES = { "enemy", "projectile", "own_bomb", "explosion", "spikes", "fire",
    "creep", "other" }
local metrics = { kills = 0, hits = {} }
for _, name in ipairs(HIT_CLASSES) do metrics.hits[name] = 0 end
local function reset_metrics()
    metrics.kills = 0
    for _, name in ipairs(HIT_CLASSES) do metrics.hits[name] = 0 end
end
-- Grid types by GridEntityType name (no numeric assumptions); absent names are skipped.
local OBSTACLE_NAMES = {
    GRID_ROCK="rock", GRID_ROCK_ALT="rock", GRID_ROCK_ALT2="rock", GRID_ROCK_SPIKED="rock",
    GRID_ROCK_GOLD="rock", GRID_ROCKT="marked_rock", GRID_ROCK_SS="marked_rock",
    GRID_ROCK_BOMB="bomb_rock", GRID_ROCKB="block", GRID_PIT="pit", GRID_SPIKES="spikes",
    GRID_SPIKES_ONOFF="spikes", GRID_POOP="poop", GRID_TNT="tnt", GRID_WALL="wall",
}
local MAX_MAP_ROOMS = 64
local collectible_cache = { dirty = true, frame = nil, ids = {}, overflow = 0 }

local function entity_capable()
    return type(Isaac.GetRoomEntities) == "function" and type(GetPtrHash) == "function"
        and EntityType ~= nil and GridEntityType ~= nil
end

local action_note
local function release(reason)
    local h = actions.hold
    actions.hold = nil
    if h and action_note then action_note("release reason=" .. (reason or "transition"), h) end
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
            or a.max_restarts < 0 or a.max_restarts > 5000 then return false end
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

local close, restart_budget, authorized
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
    release(reason or "closed")
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
    if action_authorized() then
        advertised[#advertised + 1] = "safe_actions_v1"
        if training_mode() and entity_capable() then
            advertised[#advertised + 1] = "live_loop_v1"
        end
    end
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
            or seen.entity_action_v1 then
            error("Live loop requires exactly entity, action and restart modes")
        end
    else
        if seen.safe_actions_v1 and training_mode() then
            error("Training approval requires the live loop")
        end
        if seen.safe_actions_v1 and seen.death_restart_v1 then error("Incompatible modes") end
        if seen.entity_observation_v1 and (seen.safe_actions_v1 or seen.death_restart_v1) then
            error("Entity observations require read-only mode")
        end
    end
    live.on = seen.live_loop_v1 == true
    entities.requested = seen.entity_observation_v1 == true
    actions.requested = seen.safe_actions_v1 == true
    restart.requested = seen.death_restart_v1 == true
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

-- Raw API values are floored and clamped into the declared wire ranges. Counters can
-- legitimately exceed them (e.g. 999+ coins with mods, battery overcharge, modded IDs).
local function clamp_int(value, low, high)
    value = tonumber(value)
    if not value or value ~= value then return low end
    return math.max(low, math.min(high, math.floor(value)))
end

local function collectible_list(player, frame)
    local cache = collectible_cache
    if cache.dirty or cache.frame == nil or frame < cache.frame
        or frame - cache.frame >= collectible_period then
        local ids, overflow = {}, 0
        local size = Isaac.GetItemConfig():GetCollectibles().Size
        for id = 1, math.min(collectible_max_id, size - 1) do
            if player:HasCollectible(id, true) then
                if #ids >= collectible_cap then overflow = overflow + 1
                else ids[#ids + 1] = id end
            end
        end
        cache.ids, cache.overflow, cache.frame, cache.dirty = ids, overflow, frame, false
    end
    return cache.ids, cache.overflow
end

-- Like clamp_int but keeps fractions (3 decimals). Declared wire ranges are in entities.py
-- STAT_RANGES; infinite or NaN raw values (e.g. MaxFireDelay of -1) land on the bounds.
local function clamp_num(value, low, high)
    value = tonumber(value)
    if not value or value ~= value then return low end
    return math.floor(math.max(low, math.min(high, value)) * 1000 + 0.5) / 1000
end

local function player_stats(player)
    local delay = tonumber(player.MaxFireDelay) or 0
    return {
        damage = clamp_num(player.Damage, 0, 1000),
        tears_per_second = clamp_num(30 / (delay + 1), 0, 60),
        range = clamp_num(player.TearRange, 0, 10000),
        shot_speed = clamp_num(player.ShotSpeed, 0, 10),
        move_speed = clamp_num(player.MoveSpeed, 0, 10),
        luck = clamp_num(player.Luck, -100, 100),
    }
end

-- Fixed wire order; keep in sync with TEAR_FLAG_NAMES and WEAPON_NAMES in entities.py.
local tear_flag_names = { "TEAR_SPECTRAL", "TEAR_PIERCING", "TEAR_HOMING", "TEAR_SLOW",
    "TEAR_POISON", "TEAR_FREEZE", "TEAR_SPLIT", "TEAR_GROW", "TEAR_BOOMERANG",
    "TEAR_PERSISTENT", "TEAR_WIGGLE", "TEAR_EXPLOSIVE", "TEAR_CHARM", "TEAR_CONFUSION",
    "TEAR_BURN", "TEAR_BOUNCE" }
local weapon_names = { "WEAPON_TEARS", "WEAPON_BRIMSTONE", "WEAPON_LASER", "WEAPON_KNIFE",
    "WEAPON_BOMBS", "WEAPON_ROCKETS", "WEAPON_MONSTROS_LUNGS", "WEAPON_LUDOVICO_TECHNIQUE",
    "WEAPON_TECH_X", "WEAPON_BONE", "WEAPON_NOTCHED_AXE", "WEAPON_URN_OF_SOULS",
    "WEAPON_SPIRIT_SWORD", "WEAPON_FETUS", "WEAPON_UMBILICAL_WHIP" }

-- Repentance tear flags are 128-bit sets: `player.TearFlags & TearFlags.X` is a set that
-- equals TearFlags.TEAR_NORMAL (empty) when the flag is off. Any API surprise reads false.
local function has_tear_flag(player, name)
    local ok, result = pcall(function()
        local flag = TearFlags and TearFlags[name]
        if flag == nil then return false end
        local both = player.TearFlags & flag
        if type(both) == "number" then return both ~= 0 end
        if type(both) == "table" or type(both) == "userdata" then
            if both.l ~= nil and both.h ~= nil then return both.l ~= 0 or both.h ~= 0 end
            return both ~= TearFlags.TEAR_NORMAL
        end
        return false
    end)
    return ok and result == true
end

local function has_weapon(player, name)
    local ok, result = pcall(function()
        local kind = WeaponType and WeaponType[name]
        if kind == nil then return false end
        return player:HasWeaponType(kind)
    end)
    return ok and result == true
end

local function flag_list(names, test, player)
    local list = {}
    for i, name in ipairs(names) do list[i] = test(player, name) end
    return list
end

local function inventory_facts(player)
    local slot = ActiveSlot.SLOT_PRIMARY
    local active = clamp_int(player:GetActiveItem(slot), 0, collectible_max_id)
    local charge, max_charge = 0, 0
    if active > 0 then
        charge = clamp_int(player:GetActiveCharge(slot), 0, 24)
        local config = Isaac.GetItemConfig():GetCollectible(active)
        if config then max_charge = clamp_int(config.MaxCharges, 0, 24) end
    end
    return {
        coins = clamp_int(player:GetNumCoins(), 0, 999),
        bombs = clamp_int(player:GetNumBombs(), 0, 999),
        keys = clamp_int(player:GetNumKeys(), 0, 999),
        active_item = active, active_charge = charge, active_max_charge = max_charge,
        card = clamp_int(player:GetCard(0), 0, 65535),
        pill = clamp_int(player:GetPill(0), 0, 65535),
        trinket = clamp_int(player:GetTrinket(0), 0, 65535),
    }
end

local function room_facts(room)
    local level = Game():GetLevel()
    local doors = {}
    for slot = 0, 7 do
        local door = room:GetDoor(slot)
        doors[slot + 1] = door ~= nil and door:IsOpen() == true
    end
    return {
        type = clamp_int(room:GetType(), 0, 31), stage = clamp_int(level:GetStage(), 0, 15),
        stage_type = clamp_int(level:GetStageType(), 0, 7),
        clear = room:IsClear() == true, doors = doors,
        shape = clamp_int(room:GetRoomShape(), 1, 12),
    }
end

-- Only rooms the in-game minimap shows or the player visited are exported (no hidden
-- map data). A room type is exported only once visited or when its icon is displayed.
local function minimap()
    local level = Game():GetLevel()
    local rooms = level:GetRooms()
    assert(type(rooms.Size) == "number" and rooms.Size >= 0 and rooms.Size <= 512,
        "Level room scan exceeds 512")
    local current_desc = level:GetCurrentRoomDesc()
    local current_grid = current_desc and tonumber(current_desc.GridIndex)
        or tonumber(level:GetCurrentRoomIndex()) or -1
    local result, seen = {}, {}
    for i = 0, rooms.Size - 1 do
        if #result >= MAX_MAP_ROOMS then break end
        local desc = rooms:Get(i)
        local data = desc and desc.Data
        local grid = desc and tonumber(desc.GridIndex)
        if data and grid and grid >= 0 and grid <= 168 and grid % 1 == 0 and not seen[grid] then
            local visited = (tonumber(desc.VisitedCount) or 0) > 0
            local flags = clamp_int(desc.DisplayFlags or 0, 0, 0x7fffffff)
            if visited or flags ~= 0 then
                seen[grid] = true
                result[#result+1] = { grid_index = grid, shape = clamp_int(data.Shape, 1, 12),
                    visited = visited, current = grid == current_grid,
                    room_type = (visited or (flags & 4) ~= 0)
                        and clamp_int(data.Type, 0, 31) or json.null }
            end
        end
    end
    return result, current_grid < 0
end

local function capture_entities(room, player, data)
    local list = Isaac.GetRoomEntities()
    assert(type(list) == "table" and #list <= 1024, "Room entity scan exceeds 1024")
    local grid_size = room:GetGridSize()
    assert(type(grid_size) == "number" and grid_size % 1 == 0
        and grid_size >= 0 and grid_size <= 2048, "Room grid scan exceeds 2048")
    local groups = { enemy={}, projectile={}, obstacle={}, pickup={}, own_attack={}, bomb={} }
    local retained = {}
    local oracle_enemies, oracle_overflow = {}, 0
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
    local player_hash = GetPtrHash(player)
    -- Attacks of the player or its familiars; the Parent link covers spawners left unset.
    local function own_attack(entity)
        local spawner = entity.SpawnerType
        if spawner == EntityType.ENTITY_PLAYER or spawner == EntityType.ENTITY_FAMILIAR then
            return true
        end
        local parent = entity.Parent
        return parent ~= nil and GetPtrHash(parent) == player_hash
    end
    local function add(kind, key, position, velocity, pickup, age, class, hp, max_hp)
        local relative = vector({ X=position.X-player.Position.X, Y=position.Y-player.Position.Y })
        local item = { kind=kind, entity_id=identity(key), spawn_generation=0,
            position=relative, velocity=vector(velocity), hp=json.null, max_hp=json.null,
            variant=json.null, subtype=json.null, price=json.null, age_frames=json.null,
            obstacle_class=class or json.null }
        if class and type(max_hp) == "number" and type(hp) == "number" and max_hp > 0
            and max_hp <= 1000000 and hp == hp then
            hp = math.max(0, math.min(hp, max_hp))
            item.hp = math.floor(hp * 1000 + 0.5) / 1000
            item.max_hp = math.max(0.001, math.floor(max_hp * 1000 + 0.5) / 1000)
        end
        if age then item.age_frames = clamp_int(age, 0, 10000) end
        if pickup then
            -- Price: 0 free; non-zero shop or devil deal. Modded values are clamped.
            local native = pickup:ToPickup()
            item.variant = clamp_int(pickup.Variant, 0, 1023)
            item.subtype = clamp_int(pickup.SubType, 0, 1024)
            item.price = clamp_int(native and native.Price or 0, -1000, 999)
        end
        groups[kind][#groups[kind]+1] = item
    end
    for _, entity in ipairs(list) do
        -- Seeds and pointers are internal lifetime keys, never policy features.
        local key = "e:" .. tostring(GetPtrHash(entity)) .. ":" .. tostring(entity.InitSeed)
        if entities.ids[key] then retained[key] = entities.ids[key] end
        if entity:Exists() and entity.Visible and not entity:IsDead() then
            local kind, class
            -- Fireplaces first: they must never be classified as enemies.
            if entity.Type == EntityType.ENTITY_FIREPLACE then
                kind, class = "obstacle", "fire"
            elseif entity:IsActiveEnemy(false) then kind = "enemy"
            elseif entity.Type == EntityType.ENTITY_PROJECTILE then kind = "projectile"
            elseif entity.Type == EntityType.ENTITY_PICKUP then kind = "pickup"
            elseif entity.Type == EntityType.ENTITY_BOMB then kind = "bomb"
            elseif (entity.Type == EntityType.ENTITY_TEAR or entity.Type == EntityType.ENTITY_LASER
                or entity.Type == EntityType.ENTITY_KNIFE) and own_attack(entity) then
                kind = "own_attack"
            end
            if kind then
                add(kind, key, entity.Position, entity.Velocity,
                    kind == "pickup" and entity or nil,
                    kind == "bomb" and entity.FrameCount or nil,
                    class, entity.HitPoints, entity.MaxHitPoints)
            end
        end
        -- Live-loop reward labels only; leaves through the separate oracle block.
        -- Invisible (e.g. burrowed) enemies stay listed so hiding is not a kill.
        if live.on and entity:Exists() and not entity:IsDead()
            and entity.Type ~= EntityType.ENTITY_FIREPLACE and entity:IsActiveEnemy(false) then
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
                end
            end
        end
    end
    -- Only ordinary visible geometry; no doors, hidden rooms, rock subtype or contents.
    local class_by_type = {}
    for name, class in pairs(OBSTACLE_NAMES) do
        local kind = GridEntityType[name]
        if kind then class_by_type[kind] = class end
    end
    local width, height = room:GetGridWidth(), room:GetGridHeight()
    assert(type(width) == "number" and type(height) == "number" and width % 1 == 0
        and height % 1 == 0 and width >= 1 and height >= 1, "Invalid room grid size")
    for index=0,grid_size-1 do
        local grid = room:GetGridEntity(index)
        local column = index % width
        -- The outer border ring is walls and door frames, never useful geometry.
        local border = column == 0 or column == width - 1 or index < width
            or index >= (height - 1) * width
        if grid and not border and grid.CollisionClass ~= 0 then
            local class = class_by_type[grid:GetType()]
            if class then
                add("obstacle", "g:" .. index .. ":" .. grid:GetType(), grid.Position, nil,
                    nil, nil, class)
            end
        end
    end
    entities.ids = retained
    local result, overflow = {}, {}
    for _, kind in ipairs({ "enemy", "projectile", "obstacle", "pickup", "own_attack", "bomb" }) do
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
            enemy_overflow = oracle_overflow,
            room_index = clamp_int(Game():GetLevel():GetCurrentRoomIndex(), -64, 255),
            kills = metrics.kills, player_hits = {} }
        for _, name in ipairs(HIT_CLASSES) do oracle.player_hits[name] = metrics.hits[name] end
    end
    local map, off_grid = minimap()
    local held, held_overflow = collectible_list(player, data.frame)
    return {
        type="entity_frame", observation_schema_version=5, provenance="game_api",
        session_id=state.session, game_epoch=state.epoch, room_visit=state.visit,
        frame_id=data.frame, player_position=data.player.position,
        player_velocity=vector(player.Velocity), health=data.player.health,
        entities=#result > 0 and result or json.EMPTY_ARRAY,
        source_overflow=next(overflow) and overflow or json.EMPTY_OBJECT,
        inventory=inventory_facts(player), stats=player_stats(player),
        tear_flags=flag_list(tear_flag_names, has_tear_flag, player),
        weapons=flag_list(weapon_names, has_weapon, player),
        collectibles=#held > 0 and held or json.EMPTY_ARRAY,
        collectible_overflow=held_overflow, room=room_facts(room),
        map=#map > 0 and map or json.EMPTY_ARRAY, map_current_off_grid=off_grid,
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
    local uses = { none=true, bomb=true, active=true, pillcard=true }
    if c.type ~= "command" or c.protocol_version ~= 1 or c.session_id ~= state.session
        or c.sequence <= actions.sequence
        or not directions[c.move] or not directions[c.shoot] or not uses[c.use]
        or (c.kind ~= "action" and c.kind ~= "heartbeat" and c.kind ~= "release"
            and not (c.kind == "restart" and live.on))
        or (c.kind == "action" and (c.frames < 1 or c.frames > 15))
        or (c.kind ~= "action" and (c.frames ~= 0 or c.move ~= "none" or c.shoot ~= "none"
            or c.use ~= "none"))
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
        .. '","shoot":"' .. c.shoot .. '","use":"' .. c.use .. '","frames":' .. string.format("%.0f", c.frames) .. '}'
    if raw:gsub("%s+", "") ~= canonical then error("Noncanonical command") end
    local game, player = Game(), Isaac.GetPlayer(0)
    local frame = game:GetFrameCount()
    -- A restart also needs training authority, pacing and budget (shared with death restarts).
    local refuse_restart = c.kind == "restart" and (not training_mode() or restart.pending
        or restart.awaiting or not authorized(now)
        or (restart.last_dispatch
            and now - restart.last_dispatch < Config.live_restart_interval_ms))
    if stale or frame < c.frame_id or frame - c.frame_id > 15 or game:IsPaused()
        or game:GetNumPlayers() ~= 1 or not player or player:IsDead() or refuse_restart then
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
    if c.kind == "restart" then
        -- Dispatched by lifecycle() after the ack has left the buffer.
        release("restart")
        restart.pending = { session = state.session, epoch = state.epoch, since = now,
            source = "command" }
        note("Command restart accepted session=" .. state.session .. " epoch=" .. state.epoch)
    elseif c.kind == "release" then release("explicit_release")
    elseif c.kind == "action" then
        release("replaced")
        actions.hold = { move=c.move, shoot=c.shoot, use=c.use, use_pending=true, frame=frame, epoch=state.epoch,
            visit=state.visit, until_frame=frame+c.frames, deadline=now+250,
            sequence=c.sequence }
        action_note("accepted move=" .. c.move .. " shoot=" .. c.shoot .. " use=" .. c.use,
            actions.hold)
    end
    queue({ type="command_ack", protocol_version=1, session_id=state.session,
        sequence=c.sequence, game_epoch=state.epoch, room_visit=state.visit,
        frame_id=frame, kind=c.kind, status="accepted" }, now)
end

-- Live loop uses the training approval lease and restart limit; otherwise 3 / 600 s.
restart_budget = function()
    local a = Config.action_authorization
    if live.on and type(a) == "table" and a.profile_mode == "training" then
        -- Approval max_restarts 0 means unlimited; the lease deadline still bounds the session.
        return actions.authority_deadline, a.max_restarts == 0 and math.huge or a.max_restarts
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
    local limit = state.phase == "hello" and Config.hello_bytes or 1024
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
                note(restart.armed and (live.on and "Death restart armed: live loop limit "
                    .. (limit == math.huge and "unlimited" or limit) .. " attempts" or "Death restart armed: limit 3 attempts / 600 seconds")
                    or "Death restart unavailable: lease/budget/fault")
            end
        end
    end
end

-- No console text comes from the wire. Only a future game-over event can reach
-- this fixed command, after nonblocking transport work has detected disconnects.
authorized = function(now)
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
        note("Death restart stopped: lease or attempt budget exhausted")
    end
    if restart.awaiting and now >= restart.awaiting.deadline then
        restart.awaiting, restart.disabled, restart.armed = nil, true, false
        note("Death restart fault: fresh game-start confirmation timed out; disabled")
    end
    local pending = restart.pending
    if not pending then return end
    if not authorized(now) or pending.session ~= state.session
        or pending.epoch ~= state.epoch or now - pending.since > 5000 then
        restart.pending = nil
        note("Death restart cancelled: session/epoch/lease/delay changed")
        return
    end
    local by_command = pending.source == "command"
    if by_command then
        -- Let the accepted ack reach the wire first; the restart closes the connection.
        if #state.tx > 0 and now - pending.since < 500 then return end
    elseif now - pending.since < 1500 then return end
    if live.on and restart.last_dispatch
        and now - restart.last_dispatch < Config.live_restart_interval_ms then return end
    restart.pending = nil
    if not by_command then
        local ok, dead = pcall(function()
            return Game():GetNumPlayers() == 1 and Isaac.GetPlayer(0):IsDead()
        end)
        if not ok or not dead then
            note("Death restart cancelled: player revived, unavailable or not solo")
            return
        end
    end
    restart.attempts = restart.attempts + 1
    restart.awaiting = { epoch = pending.epoch, deadline = now + 5000 }
    restart.last_dispatch = now
    note("Death restart dispatch session=" .. pending.session .. " epoch="
        .. pending.epoch .. " attempt=" .. restart.attempts
        .. " source=" .. (pending.source or "death"))
    local dispatched, err = pcall(Isaac.ExecuteCommand, "restart")
    if not dispatched then
        restart.awaiting, restart.disabled, restart.armed = nil, true, false
        note("Death restart fault: command failed; disabled: " .. tostring(err))
    end
end

mod:AddCallback(ModCallbacks.MC_POST_RENDER, function()
    local ok, err = pcall(function() action_guard(Isaac.GetTime()); pump(); lifecycle() end)
    if not ok then close("Observer capability/protocol fault: " .. tostring(err)) end
end)
mod:AddCallback(ModCallbacks.MC_POST_UPDATE, function()
    state.updates = state.updates + 1
    local ok, err = pcall(action_guard, Isaac.GetTime())
    if not ok then close("Action guard fault: " .. tostring(err)) end
end)
mod:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, function(_, continued)
    release()
    reset_metrics()
    collectible_cache.dirty = true
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
end)
local function game_end(game_over)
    release()
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
    game_end(game_over)
end)
-- Oracle metrics only. Both callbacks are bounded, read-only and never alter the game.
mod:AddCallback(ModCallbacks.MC_POST_NPC_DEATH, function(_, npc)
    pcall(function()
        if npc:IsEnemy() == true and not npc:HasEntityFlags(EntityFlag.FLAG_FRIENDLY) then
            metrics.kills = math.min(metrics.kills + 1, 9007199254740991)
        end
    end)
end)
local function damage_class(player_hash, flags, source)
    local function has(name)
        local flag = DamageFlag and DamageFlag[name]
        return flag ~= nil and flags & flag ~= 0
    end
    local ref = source and source.Entity
    if has("DAMAGE_EXPLOSION") then
        if source and source.Type == EntityType.ENTITY_BOMB and ref ~= nil
            and (ref.SpawnerType == EntityType.ENTITY_PLAYER
                or (ref.Spawner ~= nil and GetPtrHash(ref.Spawner) == player_hash)) then
            return "own_bomb"
        end
        return "explosion"
    elseif has("DAMAGE_SPIKES") or has("DAMAGE_CURSED_DOOR") then return "spikes"
    elseif has("DAMAGE_FIRE") then return "fire"
    elseif has("DAMAGE_ACID") then return "creep"
    end
    local kind = source and source.Type
    if kind == EntityType.ENTITY_PROJECTILE then return "projectile" end
    if type(kind) == "number" and kind >= 10 and kind < 1000 then return "enemy" end
    return "other"
end
-- Counts hits on player 0 only; the observer supports a single player. Returns nil always.
mod:AddCallback(ModCallbacks.MC_ENTITY_TAKE_DMG, function(_, entity, amount, flags, source)
    pcall(function()
        local hash = GetPtrHash(Isaac.GetPlayer(0))
        if GetPtrHash(entity) ~= hash then return end
        local class = damage_class(hash, flags or 0, source)
        metrics.hits[class] = math.min(metrics.hits[class] + 1, 9007199254740991)
    end)
    return nil
end, EntityType.ENTITY_PLAYER)
mod:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, function()
    release()
    collectible_cache.dirty = true
    entities.ids = {}
    state.snapshot_frame, state.pending_frame = nil, nil
    state.visit = state.visit + 1
end)
mod:AddCallback(ModCallbacks.MC_PRE_GAME_EXIT, function()
    -- A normal exit invalidates the operator's selected-profile confirmation.
    if restart.deadline and not restart.awaiting then
        restart.disabled = true
    end
    -- A live-loop death restart also exits; only a normal exit drops training approval.
    if not (live.on and restart.awaiting) then
        Config.action_authorization = nil
    end
    state.active = false
    close("Game exited; observer closed")
end)
mod:AddCallback(ModCallbacks.MC_PRE_MOD_UNLOAD, function(_, unloading)
    if unloading == mod then
        close("Observer unloaded")
    end
end)
mod:AddCallback(ModCallbacks.MC_POST_NEW_LEVEL, function()
    release()
    state.snapshot_frame, state.pending_frame = nil, nil
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
        local use_buttons = {
            bomb=ButtonAction.ACTION_BOMB, active=ButtonAction.ACTION_ITEM,
            pillcard=ButtonAction.ACTION_PILLCARD,
        }
        if h.use ~= "none" and button == use_buttons[h.use] then
            -- Triggered fires once per accepted command; pressed lasts while the hold is live.
            if hook == InputHook.GET_ACTION_VALUE then return 1.0 end
            if hook == InputHook.IS_ACTION_PRESSED then return true end
            if hook == InputHook.IS_ACTION_TRIGGERED then
                local first = h.use_pending
                h.use_pending = false
                return first
            end
            return nil
        end
        if not movement[button] and not shooting[button] then return nil end
        local pressed = movement[button] == h.move or shooting[button] == h.shoot
        if hook == InputHook.GET_ACTION_VALUE then return pressed and 1.0 or 0.0 end
        if hook == InputHook.IS_ACTION_PRESSED then return pressed end
        if hook == InputHook.IS_ACTION_TRIGGERED then return false end
        return nil
    end)
    if not ok then close("Native input fault: " .. tostring(result)); return nil end
    return result
end)
note("Observer 0.5.0-dev registered; awaiting render callbacks")
