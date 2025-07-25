return { -- Existing plugins
    {
        "folke/which-key.nvim",
        opts = {}
    }, {
    "nvim-telescope/telescope.nvim",
    dependencies = { "nvim-lua/plenary.nvim" }
}, {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate"
}, -- Add nvim-cmp and its dependencies
    {
        "hrsh7th/nvim-cmp",
        dependencies = { "hrsh7th/cmp-buffer", "hrsh7th/cmp-path", "hrsh7th/cmp-cmdline",
            "davidsierradz/cmp-conventionalcommits" },
        config = function()
            local cmp = require("cmp")
            cmp.setup({
                snippet = {
                    expand = function(args)
                        vim.fn["vsnip#anonymous"](args.body)
                    end
                },
                mapping = cmp.mapping.preset.insert({
                    ['<C-b>'] = cmp.mapping.scroll_docs(-4),
                    ['<C-f>'] = cmp.mapping.scroll_docs(4),
                    ['<C-Space>'] = cmp.mapping.complete(),
                    ['<C-e>'] = cmp.mapping.abort(),
                    ['<CR>'] = cmp.mapping.confirm({
                        select = true
                    }),
                    ['<Tab>'] = cmp.mapping(function(fallback)
                        if cmp.visible() then
                            cmp.select_next_item()
                        else
                            fallback()
                        end
                    end, { 'i', 's' }),
                    ['<S-Tab>'] = cmp.mapping(function(fallback)
                        if cmp.visible() then
                            cmp.select_prev_item()
                        else
                            fallback()
                        end
                    end, { 'i', 's' })
                }),
                sources = cmp.config.sources({ {
                    name = 'conventionalcommits'
                }, {
                    name = 'buffer'
                }, {
                    name = 'path'
                } })
            })

            -- Use buffer source for `/` and `?` (if you enabled `native_menu`, this won't work anymore).
            cmp.setup.cmdline({ '/', '?' }, {
                mapping = cmp.mapping.preset.cmdline(),
                sources = { {
                    name = 'buffer'
                } }
            })

            -- Use cmdline & path source for ':' (if you enabled `native_menu`, this won't work anymore).
            cmp.setup.cmdline(':', {
                mapping = cmp.mapping.preset.cmdline(),
                sources = cmp.config.sources({ {
                    name = 'path'
                } }, { {
                    name = 'cmdline'
                } })
            })
        end
    },
    -- Add vim-vsnip for snippet support
    { "hrsh7th/vim-vsnip" },
    -- Add vim-fugitive for Git integration
    { "tpope/vim-fugitive" },
    {
        "nvim-tree/nvim-web-devicons",
        lazy = true
    },
    {
        'echasnovski/mini.nvim',
        version = '*',
        config = function()
            require('mini.icons').setup()
        end
    },
    {
        'nvim-lualine/lualine.nvim',
        dependencies = { 'nvim-tree/nvim-web-devicons' },
        config = function()
            require('lualine').setup {
                options = {
                    icons_enabled = true,
                    theme = 'auto',
                    component_separators = { left = '', right = '' },
                    section_separators = { left = '', right = '' },
                    globalstatus = true,
                },
                sections = {
                    lualine_a = { 'mode' }, -- This will show VISUAL/NORMAL etc. in a nicer way
                }
            }
        end
    },
    {
        "rafikdraoui/jj-diffconflicts",
        config = function()
            -- No additional configuration is strictly necessary.
            -- This plugin provides the JJDiffConflicts command which your merge tool config calls.
        end
    },
}
