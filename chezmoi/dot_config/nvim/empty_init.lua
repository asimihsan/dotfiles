local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
    vim.fn.system({"git", "clone", "--filter=blob:none", "https://github.com/folke/lazy.nvim.git", "--branch=v11.13.1",
                   lazypath})
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup("plugins")

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
            sources = cmp.config.sources({{
                name = 'conventionalcommits'
            }, {
                name = 'buffer'
            }})
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
