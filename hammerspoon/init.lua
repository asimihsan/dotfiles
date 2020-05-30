hs.logger.defaultLogLevel = "info"
local reload_watcher = hs.pathwatcher.new(hs.configdir, hs.reload):start()

-- This opens up local ports that allow a local CLI tool to communicate to the Hammerspoon process.
require("hs.ipc")

-- Note: to get started you need to install SpoonInstall.spoon first by getting the ZIP and installing it
-- https://github.com/Hammerspoon/Spoons
-- Once manually installed other Spoon extensions are synchronously auto-installed.
hs.loadSpoon("SpoonInstall")
spoon.SpoonInstall.repos.asimihsan = {
  url = "https://github.com/asimihsan/Spoons",
  desc = "asimihsan's spoon repository",
}
spoon.SpoonInstall.use_syncinstall = true

-- I'm using a local copy of [1]
--
-- [1] https://github.com/semperos/hammerspoon-push-to-talk
local pushToTalk = require("pushToTalk")
pushToTalk.init{}
