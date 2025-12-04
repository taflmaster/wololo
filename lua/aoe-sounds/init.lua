local M = {}
local player = require("aoe-sounds.player")

-- Initialize random seed once at module load
math.randomseed(os.time())

-- Default configuration
local default_config = {
  enabled = true,
  sounds_dir = nil, -- Will be set to plugin root/sounds by default
  volume = 1.0,
  debug = false, -- Enable debug messages to troubleshoot sound issues
  -- Sound mappings: can be a single file (string) or multiple files (array) for random selection
  -- Example: type = "arrow.mp3" or type = {"arrow1.mp3", "arrow2.mp3", "arrow3.mp3"}
  sounds = {
    yank = "wololo.mp3",
    insert_enter = "villager-create.mp3",
    visual_enter = "villager-select.wav",
    save = "castle.mp3",
    error = "villager-killed.mp3",
    buf_enter = "campaign.mp3",
    quit = "drumpapappa.mp3",
    type = "arrow.mp3", -- Can be an array for random sounds: {"arrow.mp3", "arrow2.mp3"}
    delete = "sword.mp3", -- Can be an array for random sounds: {"sword.mp3", "sword2.mp3"}
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
    type = false, -- Disabled by default (very noisy)
    delete = false, -- Disabled by default (noisy)
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
  else
    sounds_path = get_plugin_root() .. "/sounds"
  end

  -- Check if directory exists and warn user
  if vim.fn.isdirectory(sounds_path) == 0 then
    vim.notify(
      string.format(
        "AoE Sounds: Sounds directory not found: %s\n" ..
        "Please create this directory and add your sound files, or set 'sounds_dir' in your config.\n" ..
        "Example: sounds_dir = '~/.config/nvim/aoe-sounds'",
        sounds_path
      ),
      vim.log.levels.WARN
    )
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
  if not config.enabled then
    if config.debug then
      vim.notify(string.format("AoE Sounds: Plugin disabled, skipping event '%s'", event_name), vim.log.levels.DEBUG)
    end
    return
  end

  if not config.events[event_name] then
    if config.debug then
      vim.notify(string.format("AoE Sounds: Event '%s' is disabled in config", event_name), vim.log.levels.DEBUG)
    end
    return
  end

  local sound_file = config.sounds[event_name]
  if sound_file then
    -- Support both single sound file (string) and multiple sound files (array)
    local selected_sound
    if type(sound_file) == "table" then
      -- Randomly select one sound from the array
      local index = math.random(#sound_file)
      selected_sound = sound_file[index]
      if config.debug then
        vim.notify(
          string.format("AoE Sounds: Event '%s' - selected sound %d/%d: %s",
            event_name, index, #sound_file, selected_sound),
          vim.log.levels.INFO
        )
      end
    else
      -- Single sound file
      selected_sound = sound_file
      if config.debug then
        vim.notify(string.format("AoE Sounds: Event '%s' - playing: %s", event_name, selected_sound), vim.log.levels.INFO)
      end
    end

    local full_path = get_sound_path(selected_sound)
    player.play(full_path)
  elseif config.debug then
    vim.notify(string.format("AoE Sounds: No sound configured for event '%s'", event_name), vim.log.levels.WARN)
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

  -- Typing (arrow sound for each character typed)
  if config.events.type then
    vim.api.nvim_create_autocmd("InsertCharPre", {
      group = augroup,
      callback = function()
        play_sound("type")
      end,
    })
  end

  -- Deletion (sword sound when deleting characters)
  if config.events.delete then
    -- Map backspace and delete keys to play sound
    vim.keymap.set("i", "<BS>", function()
      play_sound("delete")
      -- Use vim.api.nvim_feedkeys to properly send the key
      local key = vim.api.nvim_replace_termcodes("<BS>", true, false, true)
      vim.api.nvim_feedkeys(key, "n", false)
    end, { noremap = true, desc = "AoE: Delete with sword sound" })

    vim.keymap.set("i", "<Del>", function()
      play_sound("delete")
      -- Use vim.api.nvim_feedkeys to properly send the key
      local key = vim.api.nvim_replace_termcodes("<Del>", true, false, true)
      vim.api.nvim_feedkeys(key, "n", false)
    end, { noremap = true, desc = "AoE: Delete with sword sound" })
  end
end

-- Setup function
function M.setup(user_config)
  -- Merge user config with defaults
  config = vim.tbl_deep_extend("force", default_config, user_config or {})

  -- Initialize sounds path
  init_sounds_path()

  -- Setup autocommands
  setup_autocommands()
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
