local M = {}
local player = require("aoe-sounds.player")

-- Default configuration
local default_config = {
  enabled = true,
  sounds_dir = nil, -- Will be set to plugin root/sounds by default
  volume = 1.0,
  sounds = {
    yank = "wololo.mp3",
    insert_enter = "villager-create.mp3",
    visual_enter = "villager-select.wav",
    save = "castle.mp3",
    error = "villager-killed.mp3",
    buf_enter = "campaign.mp3",
    quit = "drumpapappa.mp3",
  },
  -- Events to enable (can be disabled individually)
  events = {
    yank = true,
    insert_enter = true,
    visual_enter = true,
    save = true,
    error = true,
    buf_enter = false, -- Disabled by default (can be annoying)
    quit = true,
  },
}

local config = vim.deepcopy(default_config)
local sounds_path = nil

-- Get the plugin root directory
local function get_plugin_root()
  local str = debug.getinfo(1, "S").source:sub(2)
  return vim.fn.fnamemodify(str, ":h:h:h")
end

-- Initialize sounds directory path
local function init_sounds_path()
  if config.sounds_dir then
    sounds_path = vim.fn.expand(config.sounds_dir)
    print(string.format("[AoE Sounds] Using custom sounds directory: %s", sounds_path))
  else
    sounds_path = get_plugin_root() .. "/sounds"
    print(string.format("[AoE Sounds] Using default sounds directory: %s", sounds_path))
  end

  -- Check if directory exists
  if vim.fn.isdirectory(sounds_path) == 0 then
    print(string.format("[AoE Sounds] WARNING: Sounds directory does not exist: %s", sounds_path))
  else
    print(string.format("[AoE Sounds] Sounds directory exists: %s", sounds_path))
  end
end

-- Get full path to a sound file
local function get_sound_path(sound_name)
  if not sounds_path then
    init_sounds_path()
  end
  return sounds_path .. "/" .. sound_name
end

-- Play a sound by event name
local function play_sound(event_name)
  print(string.format("[AoE Sounds] Event triggered: %s", event_name))

  if not config.enabled then
    print("[AoE Sounds] Plugin is disabled, skipping sound")
    return
  end

  if not config.events[event_name] then
    print(string.format("[AoE Sounds] Event '%s' is disabled in config", event_name))
    return
  end

  local sound_file = config.sounds[event_name]
  if sound_file then
    local full_path = get_sound_path(sound_file)
    print(string.format("[AoE Sounds] Playing sound for event '%s': %s -> %s", event_name, sound_file, full_path))
    player.play(full_path)
  else
    print(string.format("[AoE Sounds] No sound file configured for event: %s", event_name))
  end
end

-- Setup autocommands
local function setup_autocommands()
  local augroup = vim.api.nvim_create_augroup("AoESounds", { clear = true })

  -- Yank sound
  if config.events.yank then
    vim.api.nvim_create_autocmd("TextYankPost", {
      group = augroup,
      callback = function()
        play_sound("yank")
      end,
    })
  end

  -- Insert mode
  if config.events.insert_enter then
    vim.api.nvim_create_autocmd("InsertEnter", {
      group = augroup,
      callback = function()
        play_sound("insert_enter")
      end,
    })
  end

  -- Visual mode
  if config.events.visual_enter then
    vim.api.nvim_create_autocmd("ModeChanged", {
      group = augroup,
      pattern = "*:[vV\x16]*", -- \x16 is Ctrl-V
      callback = function()
        play_sound("visual_enter")
      end,
    })
  end

  -- Save file
  if config.events.save then
    vim.api.nvim_create_autocmd("BufWritePost", {
      group = augroup,
      callback = function()
        play_sound("save")
      end,
    })
  end

  -- Error/diagnostic
  if config.events.error then
    vim.api.nvim_create_autocmd("DiagnosticChanged", {
      group = augroup,
      callback = function()
        local diagnostics = vim.diagnostic.get(0, { severity = vim.diagnostic.severity.ERROR })
        if #diagnostics > 0 then
          play_sound("error")
        end
      end,
    })
  end

  -- Buffer enter (opening files)
  if config.events.buf_enter then
    vim.api.nvim_create_autocmd("BufReadPost", {
      group = augroup,
      callback = function()
        play_sound("buf_enter")
      end,
    })
  end

  -- Quit
  if config.events.quit then
    vim.api.nvim_create_autocmd("VimLeavePre", {
      group = augroup,
      callback = function()
        play_sound("quit")
      end,
    })
  end
end

-- Setup function
function M.setup(user_config)
  print("[AoE Sounds] Setup called")

  -- Merge user config with defaults
  config = vim.tbl_deep_extend("force", default_config, user_config or {})

  print(string.format("[AoE Sounds] Plugin enabled: %s", config.enabled))
  print("[AoE Sounds] Enabled events:")
  for event, enabled in pairs(config.events) do
    if enabled then
      print(string.format("  - %s: %s", event, config.sounds[event] or "no sound file"))
    end
  end

  -- Initialize sounds path
  init_sounds_path()

  -- Setup autocommands
  setup_autocommands()

  print("[AoE Sounds] Setup complete")
end

-- Toggle plugin on/off
function M.toggle()
  config.enabled = not config.enabled
  local status = config.enabled and "enabled" or "disabled"
  vim.notify("AoE Sounds " .. status, vim.log.levels.INFO)
end

-- Enable plugin
function M.enable()
  config.enabled = true
  vim.notify("AoE Sounds enabled", vim.log.levels.INFO)
end

-- Disable plugin
function M.disable()
  config.enabled = false
  vim.notify("AoE Sounds disabled", vim.log.levels.INFO)
end

-- Get current config
function M.get_config()
  return config
end

return M
