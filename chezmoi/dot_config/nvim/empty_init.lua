-- Set up autocmds for Git commit messages
vim.api.nvim_create_autocmd("FileType", {
    pattern = "gitcommit",
    callback = function()
      -- Set textwidth for Git commit messages
      vim.opt_local.textwidth = 72
      -- Highlight the 51st column (for subject line)
      vim.opt_local.colorcolumn = "51,73"
      -- Enable spell checking
      vim.opt_local.spell = true
    end,
  })
  