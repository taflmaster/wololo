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

-- Play a sound file
function M.play(sound_file)
  local player = find_audio_player()

  if not player then
    -- Only show warning once
    if not M.warned then
      vim.notify("No audio player found. Install ffmpeg, mpv, or pulseaudio.", vim.log.levels.WARN)
      M.warned = true
    end
    return
  end

  -- Check if file exists
  if vim.fn.filereadable(sound_file) == 0 then
    return
  end

  -- Play sound in background
  local cmd = string.format("%s %s %s &", player.cmd, player.args, vim.fn.shellescape(sound_file))
  vim.fn.system(cmd)
end

return M
