# 🏰 AoE Sounds - Age of Empires Sound Effects for Neovim

A Neovim plugin that plays Age of Empires sound effects when you perform common actions in Neovim. Wololo your way through code!

## ✨ Features

- 🎵 Plays AoE sounds on various Neovim events
- 🎲 Random sound selection - provide multiple sounds per event for variety!
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

**Important:** You need to specify a custom sounds directory since plugin managers don't expose the plugin's internal directory structure.

1. Create a directory for your sounds (e.g., `~/.config/nvim/aoe-sounds/`)
2. Add your AoE sound files to this directory
3. Add to your `~/.config/nvim/lua/plugins/aoe-sounds.lua`:

```lua
return {
  "taflmaster/wololo",
  config = function()
    require("aoe-sounds").setup({
      -- REQUIRED: Specify where your sound files are located
      sounds_dir = "~/.config/nvim/aoe-sounds",

      -- Optional: customize configuration
      enabled = true,
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
require("aoe-sounds").setup({
  sounds_dir = "~/.config/nvim/aoe-sounds",
})
EOF
```

**packer.nvim:**
```lua
use {
  'taflmaster/wololo',
  config = function()
    require("aoe-sounds").setup({
      sounds_dir = "~/.config/nvim/aoe-sounds",
    })
  end
}
```

## 🎵 Sound Files

### Setting Up Your Sounds Directory

1. **Create a directory** for your sound files:
   ```bash
   mkdir -p ~/.config/nvim/aoe-sounds
   ```

2. **Download or copy** your Age of Empires sound files to this directory

3. **Configure the plugin** to point to this directory (see Installation section above)

### Default Sound Mappings

| Event | Sound File | Description | Default |
|-------|------------|-------------|---------|
| `yank` | `wololo.mp3` | When yanking text | ✅ Enabled |
| `insert_enter` | `villager-create.mp3` | Entering insert mode | ✅ Enabled |
| `visual_enter` | `villager-select.wav` | Entering visual mode | ✅ Enabled |
| `save` | `castle.mp3` | Saving a file | ✅ Enabled |
| `error` | `villager-killed.mp3` | When errors appear | ✅ Enabled |
| `quit` | `drumpapappa.mp3` | Exiting Neovim | ✅ Enabled |
| `type` | `arrow.mp3` | Each character typed (archer attack) | ❌ Disabled (noisy) |
| `delete` | `sword.mp3` | Deleting characters | ❌ Disabled (noisy) |
| `buf_enter` | `campaign.mp3` | Opening a new buffer | ❌ Disabled (can be annoying) |

### Customizing Sound File Names

If your sound files have different names than the defaults, update the config:

```lua
require("aoe-sounds").setup({
  sounds_dir = "~/.config/nvim/aoe-sounds",
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

### Random Sound Effects for Frequent Events

For actions that happen frequently (like typing and deleting), you can provide multiple sound files and the plugin will randomly select one each time the event occurs. This adds variety and makes repetitive actions more interesting!

Simply provide an array of sound file names instead of a single string:

```lua
require("aoe-sounds").setup({
  sounds_dir = "~/.config/nvim/aoe-sounds",
  sounds = {
    -- Single sound (traditional way)
    yank = "wololo.mp3",

    -- Multiple sounds - randomly selected!
    type = {
      "arrow1.mp3",
      "arrow2.mp3",
      "arrow3.mp3",
      "bow-release.mp3",
    },
    delete = {
      "sword1.mp3",
      "sword2.mp3",
      "blade-swing.mp3",
    },
  },
  events = {
    type = true,   -- Enable typing sounds
    delete = true, -- Enable deletion sounds
  },
})
```

**Benefits of random sounds:**
- Reduces repetition fatigue for frequently occurring events
- Makes typing and deletion more dynamic and engaging
- Perfect for `type`, `delete`, and other high-frequency events
- Backward compatible - single strings still work perfectly

### Alternative Sounds Directory Location

You can use any directory you prefer:

```bash
mkdir -p ~/aoe-sounds
```

```lua
require("aoe-sounds").setup({
  sounds_dir = "~/aoe-sounds",
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

  -- REQUIRED: Custom sounds directory
  -- This is where you store your sound files
  sounds_dir = "~/.config/nvim/aoe-sounds",

  -- Sound file mappings (filenames in your sounds_dir)
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
    buf_enter = false, -- Disabled by default (can be annoying)
    quit = true,
    type = false, -- Disabled by default (very noisy, but fun!)
    delete = false, -- Disabled by default (noisy)
  },
})
```

### Enable/Disable Specific Events

Some events are disabled by default because they can be noisy:

```lua
require("aoe-sounds").setup({
  sounds_dir = "~/.config/nvim/aoe-sounds",
  events = {
    -- Enable the noisy but fun events
    type = true,          -- Play arrow sound on each keystroke
    delete = true,        -- Play sword sound when deleting
    buf_enter = true,     -- Play sound when opening buffers

    -- Disable events you find annoying
    insert_enter = false, -- Don't play sound when entering insert mode
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
- **InsertCharPre** - Before each character is inserted (typing sound)
- **Key Mappings** - Custom mappings for `<BS>` and `<Del>` (deletion sound)

## 🐛 Troubleshooting

### No sound playing

1. **Check if an audio player is installed:**
   ```bash
   which ffplay mpv paplay afplay
   ```
   If none are found, install one: `sudo apt install ffmpeg`

2. **Verify your sounds directory exists:**
   ```bash
   ls -la ~/.config/nvim/aoe-sounds
   ```
   If it doesn't exist, create it: `mkdir -p ~/.config/nvim/aoe-sounds`

3. **Test playing a sound manually:**
   ```bash
   ffplay -nodisp -autoexit ~/.config/nvim/aoe-sounds/wololo.mp3
   ```

4. **Check the plugin configuration:**
   ```vim
   :lua print(vim.inspect(require("aoe-sounds").get_config()))
   ```
   Verify that `sounds_dir` points to the correct location.

5. **Check Neovim messages for warnings:**
   ```vim
   :messages
   ```
   The plugin will warn you if the sounds directory or files are not found.

### Sounds directory not found error

If you see a warning about the sounds directory not being found:

1. Make sure you've set `sounds_dir` in your config
2. Create the directory: `mkdir -p ~/.config/nvim/aoe-sounds`
3. Add your sound files to that directory
4. Restart Neovim

## 📝 License

MIT

## 🙏 Credits

- Age of Empires sounds are property of Microsoft/Ensemble Studios
- Plugin inspired by the glorious "Wololo" monk conversion sound

## 💡 Sound Suggestions

Here are some other fun sound ideas you could implement:

### Combat Sounds
- **Archer attack** (`arrow.mp3`) - When typing each character (already implemented!)
- **Sword/melee attack** (`sword.mp3`) - When deleting (already implemented!)
- **Cavalry charge** - When using find/replace across file (`:s/`)
- **Siege weapon** - When deleting large blocks of code

### Building/Economy Sounds
- **Building complete** - When LSP auto-formatting completes
- **Resource collected** - When accepting autocomplete suggestions
- **Trade complete** - When git operations succeed

### Strategy Sounds
- **Town bell** - When compiler warnings appear
- **Trumpet fanfare** - When all tests pass
- **Defeat sound** - When build fails
- **Victory sound** - When successfully merging/deploying

### Social Sounds
- **Taunts** (11, 11, 11) - Custom command for fun
- **"All hail, king of the losers"** - When closing without saving
- **"Nice town, I'll take it"** - When opening a new project

Want me to implement any of these? 🏹⚔️

## 🎊 Contributing

Feel free to open issues or PRs! Add more sound events, improve the plugin, or share your favorite AoE sound combinations!

---

**Wololo!** 🏰⚔️
