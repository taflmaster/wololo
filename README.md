# 🏰 AoE Sounds - Age of Empires Sound Effects for Neovim

A Neovim plugin that plays Age of Empires sound effects when you perform common actions in Neovim. Wololo your way through code!

## ✨ Features

- 🎵 Plays AoE sounds on various Neovim events
- ⚙️ Fully configurable sound mappings
- 🎛️ Enable/disable individual events
- 🔇 Easy toggle on/off
- 🚀 LazyVim compatible
- 🎮 Low overhead (sounds play asynchronously)

## 📋 Requirements

One of the following audio players must be installed:
- `ffmpeg` (ffplay) - Recommended, cross-platform
- `mpv` - Popular media player
- `afplay` - macOS built-in
- `paplay` - PulseAudio (most Linux distros)

### Installing ffmpeg

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Arch Linux:**
```bash
sudo pacman -S ffmpeg
```

## 📦 Installation

### With LazyVim / lazy.nvim

Add to your `~/.config/nvim/lua/plugins/aoe-sounds.lua`:

```lua
return {
  "taflmaster/wololo",
  config = function()
    require("aoe-sounds").setup({
      -- Optional: customize configuration
      enabled = true,
      sounds_dir = nil, -- defaults to plugin's sounds directory
      events = {
        yank = true,
        insert_enter = true,
        visual_enter = true,
        save = true,
        error = true,
        buf_enter = false, -- can be annoying
        quit = true,
      },
    })
  end,
}
```

### With other plugin managers

**vim-plug:**
```vim
Plug 'taflmaster/wololo'

lua << EOF
require("aoe-sounds").setup()
EOF
```

**packer.nvim:**
```lua
use {
  'taflmaster/wololo',
  config = function()
    require("aoe-sounds").setup()
  end
}
```

## 🎵 Sound Files

Place your Age of Empires sound files in the `sounds/` directory of the plugin, or specify a custom directory in the config.

### Default Sound Mappings

| Event | Sound File | Description |
|-------|------------|-------------|
| `yank` | `wololo.mp3` | When yanking text |
| `insert_enter` | `villager-create.mp3` | Entering insert mode |
| `visual_enter` | `villager-select.wav` | Entering visual mode |
| `save` | `castle.mp3` | Saving a file |
| `error` | `villager-killed.mp3` | When errors appear |
| `buf_enter` | `campaign.mp3` | Opening a new buffer |
| `quit` | `drumpapappa.mp3` | Exiting Neovim |

### Adding Your Sounds

1. Copy your AoE sound files to the plugin's `sounds/` directory
2. Rename them to match the default names, or update the config:

```lua
require("aoe-sounds").setup({
  sounds = {
    yank = "aoe2-30-wololo.mp3",
    insert_enter = "Voicy_Villager creation SFX.mp3",
    visual_enter = "villager_select3.WAV",
    save = "Voicy_Castle SFX.mp3",
    error = "Voicy_Villager killed SFX.mp3",
    buf_enter = "age-of-empires-2-campa.mp3",
    quit = "aoe2-drumpapappa.mp3",
  },
})
```

### Using a Custom Sounds Directory

```lua
require("aoe-sounds").setup({
  sounds_dir = "~/my-sounds/aoe",
})
```

## 🎮 Usage

### Commands

- `:AoESoundsToggle` - Toggle sounds on/off
- `:AoESoundsEnable` - Enable sounds
- `:AoeSoundsDisable` - Disable sounds

### Keybindings (Example)

Add to your config:

```lua
vim.keymap.set("n", "<leader>ts", "<cmd>AoESoundsToggle<cr>", { desc = "Toggle AoE Sounds" })
```

## ⚙️ Configuration

### Full Configuration Example

```lua
require("aoe-sounds").setup({
  -- Enable/disable the plugin
  enabled = true,

  -- Custom sounds directory (optional)
  sounds_dir = nil,

  -- Sound file mappings
  sounds = {
    yank = "wololo.mp3",
    insert_enter = "villager-create.mp3",
    visual_enter = "villager-select.wav",
    save = "castle.mp3",
    error = "villager-killed.mp3",
    buf_enter = "campaign.mp3",
    quit = "drumpapappa.mp3",
  },

  -- Enable/disable individual events
  events = {
    yank = true,
    insert_enter = true,
    visual_enter = true,
    save = true,
    error = true,
    buf_enter = false, -- Disabled by default
    quit = true,
  },
})
```

### Disable Specific Events

If you find certain sounds annoying:

```lua
require("aoe-sounds").setup({
  events = {
    insert_enter = false, -- Don't play sound when entering insert mode
    buf_enter = false,    -- Don't play sound when opening buffers
  },
})
```

## 🎯 Supported Events

- **TextYankPost** - When you yank/copy text (`y`, `yy`, etc.)
- **InsertEnter** - When entering insert mode (`i`, `a`, `o`, etc.)
- **ModeChanged** (Visual) - When entering visual mode (`v`, `V`, `<C-v>`)
- **BufWritePost** - After saving a file (`:w`)
- **DiagnosticChanged** - When LSP errors appear
- **BufReadPost** - When opening/reading a file
- **VimLeavePre** - Before exiting Neovim

## 🐛 Troubleshooting

### No sound playing

1. Check if an audio player is installed: `which ffplay mpv paplay afplay`
2. Test playing a sound manually: `ffplay -nodisp -autoexit sounds/wololo.mp3`
3. Check if sound files exist in the `sounds/` directory
4. Ensure the plugin is enabled: `:lua print(require("aoe-sounds").get_config().enabled)`

### Sounds not found

Make sure your sound files are in the correct directory. Check with:
```vim
:lua print(vim.inspect(require("aoe-sounds").get_config()))
```

## 📝 License

MIT

## 🙏 Credits

- Age of Empires sounds are property of Microsoft/Ensemble Studios
- Plugin inspired by the glorious "Wololo" monk conversion sound

## 🎊 Contributing

Feel free to open issues or PRs! Add more sound events, improve the plugin, or share your favorite AoE sound combinations!

---

**Wololo!** 🏰⚔️
