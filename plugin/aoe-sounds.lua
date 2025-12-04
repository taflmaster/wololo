-- Prevent loading the plugin twice
if vim.g.loaded_aoe_sounds then
  return
end
vim.g.loaded_aoe_sounds = true

-- Create user commands
vim.api.nvim_create_user_command("AoESoundsToggle", function()
  require("aoe-sounds").toggle()
end, {
  desc = "Toggle Age of Empires sounds",
})

vim.api.nvim_create_user_command("AoESoundsEnable", function()
  require("aoe-sounds").enable()
end, {
  desc = "Enable Age of Empires sounds",
})

vim.api.nvim_create_user_command("AoeSoundsDisable", function()
  require("aoe-sounds").disable()
end, {
  desc = "Disable Age of Empires sounds",
})
