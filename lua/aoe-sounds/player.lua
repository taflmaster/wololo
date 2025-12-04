local M = {}

-- Cache for available audio players
local audio_player = nil

-- Check which audio player is available
local function find_audio_player()
  if audio_player then
    return audio_player
  end

  local players = {
    { cmd = "ffplay", args = "-nodisp -autoexit -v 0" },
    { cmd = "mpv", args = "--no-video --really-quiet" },
    { cmd = "afplay", args = "" }, -- macOS
    { cmd = "paplay", args = "" }, -- PulseAudio (Linux)
  }

  for _, player in ipairs(players) do
    if vim.fn.executable(player.cmd) == 1 then
      audio_player = player
      return audio_player
    end
  end

  return nil
end

-- Get the current audio player name
function M.get_player_name()
  local player = find_audio_player()
  return player and player.cmd or "none"
end

-- Play a sound file
function M.play(sound_file, debug)
  local player = find_audio_player()

  if not player then
    -- Only show warning once
    if not M.warned_player then
      vim.notify("AoE Sounds: No audio player found. Install ffmpeg, mpv, or pulseaudio.", vim.log.levels.WARN)
      M.warned_player = true
    end
    return
  end

  if debug then
    vim.notify(string.format("AoE Sounds: Using player '%s' for: %s", player.cmd, sound_file), vim.log.levels.DEBUG)
  end

  -- Check if file exists
  if vim.fn.filereadable(sound_file) == 0 then
    -- Only warn once per missing file
    if not M.warned_files then
      M.warned_files = {}
    end
    if not M.warned_files[sound_file] then
      vim.notify(
        string.format("AoE Sounds: Sound file not found: %s", sound_file),
        vim.log.levels.WARN
      )
      M.warned_files[sound_file] = true
    end
    return
  end

  -- Play sound in background using jobstart for true async execution
  local cmd = string.format("%s %s %s", player.cmd, player.args, vim.fn.shellescape(sound_file))
  vim.fn.jobstart(cmd, {
    detach = true,
    on_exit = function() end,
  })
end

return M
