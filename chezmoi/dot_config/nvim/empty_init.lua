vim.g.mapleader = " "

-- Terminal-specific settings
vim.opt.termguicolors = true -- Enable 24-bit RGB colors
vim.opt.laststatus = 3       -- Global status line
vim.opt.fillchars = {
    horiz = '━',
    horizup = '┻',
    horizdown = '┳',
    vert = '┃',
    vertleft = '┫',
    vertright = '┣',
    verthoriz = '╋',
}
vim.opt.encoding = 'utf-8'
vim.opt.guicursor = 'n-v-c-sm:block,i-ci-ve:ver25,r-cr-o:hor20'

-- Prevent screen corruption issues
vim.opt.hidden = true
vim.opt.updatetime = 300
vim.opt.redrawtime = 10000
vim.opt.ttyfast = true

-- Better mouse support
vim.opt.mouse = 'a'                 -- Enable mouse in all modes
vim.opt.mousemodel = 'popup_setpos' -- Right-click positions cursor

-- Add double-click to select word mapping
vim.api.nvim_set_keymap('n', '<2-LeftMouse>', 'viw', { noremap = true, silent = true })
vim.api.nvim_set_keymap('n', '<3-LeftMouse>', 'viW', { noremap = true, silent = true })

-- Enable system clipboard integration
vim.opt.clipboard = 'unnamedplus'

-- Mac-style clipboard mappings
vim.keymap.set('v', '<D-c>', '"+y', { silent = true })    -- Cmd+c in visual mode
vim.keymap.set('n', '<D-v>', '"+p', { silent = true })    -- Cmd+v in normal mode
vim.keymap.set('i', '<D-v>', '<C-r>+', { silent = true }) -- Cmd+v in insert mode
vim.keymap.set('c', '<D-v>', '<C-r>+', { silent = true }) -- Cmd+v in command mode

-- Add visual mode mappings to ensure CMD+c works in visual mode
vim.keymap.set('v', '<D-c>', '"+y', { silent = true })
vim.keymap.set('v', '<D-x>', '"+d', { silent = true })

-- Optional: Add these for Ctrl+c/v as well if you want
vim.keymap.set('v', '<C-c>', '"+y', { silent = true })
vim.keymap.set('n', '<C-v>', '"+p', { silent = true })
vim.keymap.set('i', '<C-v>', '<C-r>+', { silent = true })

local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
    vim.fn.system({ "git", "clone", "--filter=blob:none", "https://github.com/folke/lazy.nvim.git", "--branch=v11.13.1",
        lazypath })
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup("plugins", {
    rocks = {
        enabled = false -- Disable luarocks to remove warnings
    }
})

-- Set up autocmds for Git commit messages
vim.api.nvim_create_autocmd("FileType", {
    pattern = "gitcommit",
    callback = function()
        -- Set textwidth for Git commit messages
        vim.opt_local.textwidth = 72
        -- Highlight the 51st column (for subject line) and 73rd column
        vim.opt_local.colorcolumn = "51,73"
        -- Enable spell checking
        vim.opt_local.spell = true
        -- Set up nvim-cmp for gitcommit filetype
        local cmp = require('cmp')
        cmp.setup.buffer({
            sources = cmp.config.sources({ {
                name = 'conventionalcommits'
            }, {
                name = 'buffer'
            } })
        })
    end
})

-- Add a keybinding to open Git commit message
vim.api.nvim_set_keymap('n', '<leader>gc', ':Git commit<CR>', {
    noremap = true,
    silent = true
})

-- -- LSP setup
-- local lspconfig = require('lspconfig')
-- lspconfig.rust_analyzer.setup({})
-- lspconfig.pyright.setup({})
-- lspconfig.gopls.setup({})

-- -- Treesitter setup
-- require('nvim-treesitter.configs').setup {
--     ensure_installed = {"lua", "vim", "help"},
--     highlight = {
--         enable = true
--     }
-- }

-- -- Telescope setup
-- require('telescope').setup {}
-- require('telescope').load_extension('conventional_commits')

-- -- Add a keybinding to use conventional commits
-- vim.api.nvim_set_keymap('n', '<leader>cc',
--     "<cmd>lua require('telescope').extensions.conventional_commits.conventional_commits()<CR>", {
--         noremap = true,
--         silent = true
--     })
