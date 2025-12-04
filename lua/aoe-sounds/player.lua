local M = {}

-- Cache for available audio players
local audio_player = nil

-- Check which audio player is available
local function find_audio_player()
  if audio_player then
    print(string.format("[AoE Sounds] Using cached audio player: %s", audio_player.cmd))
    return audio_player
  end

  print("[AoE Sounds] Searching for audio player...")
  local players = {
    { cmd = "ffplay", args = "-nodisp -autoexit -v 0" },
    { cmd = "mpv", args = "--no-video --really-quiet" },
    { cmd = "afplay", args = "" }, -- macOS
    { cmd = "paplay", args = "" }, -- PulseAudio (Linux)
  }

  for _, player in ipairs(players) do
    local is_executable = vim.fn.executable(player.cmd)
    print(string.format("[AoE Sounds] Checking %s: %s", player.cmd, is_executable == 1 and "found" or "not found"))
    if is_executable == 1 then
      audio_player = player
      print(string.format("[AoE Sounds] Selected audio player: %s", audio_player.cmd))
      return audio_player
    end
  end

  print("[AoE Sounds] No audio player found!")
  return nil
end

-- Play a sound file
function M.play(sound_file)
  print(string.format("[AoE Sounds] play() called with: %s", sound_file))

  local player = find_audio_player()

  if not player then
    print("[AoE Sounds] ERROR: No audio player available")
    -- Only show warning once
    if not M.warned then
      vim.notify("No audio player found. Install ffmpeg, mpv, or pulseaudio.", vim.log.levels.WARN)
      M.warned = true
    end
    return
  end

  -- Check if file exists
  local file_exists = vim.fn.filereadable(sound_file)
  print(string.format("[AoE Sounds] File readable check: %s = %s", sound_file, file_exists == 1 and "yes" or "no"))

  if file_exists == 0 then
    print(string.format("[AoE Sounds] ERROR: File not found or not readable: %s", sound_file))
    return
  end

  -- Play sound in background
  local cmd = string.format("%s %s %s &", player.cmd, player.args, vim.fn.shellescape(sound_file))
  print(string.format("[AoE Sounds] Executing command: %s", cmd))
  local result = vim.fn.system(cmd)
  if result and result ~= "" then
    print(string.format("[AoE Sounds] Command output: %s", result))
  end
end

return M
