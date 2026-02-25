require "string"

logger = hs.logger.new('logger', 'debug')
hs.logger.defaultLogLevel = "info"

local reload_watcher = hs.pathwatcher.new(hs.configdir, hs.reload):start()

-- This opens up local ports that allow a local CLI tool to communicate to the Hammerspoon process.
require("hs.ipc")

-- ----------------------------------------------------------------------------
--  caffeine, prevent display from sleeping
-- ----------------------------------------------------------------------------
local caffeine = hs.menubar.new()
function setCaffeineDisplay(state)
    if state then
        caffeine:setTitle("AWAKE")
    else
        caffeine:setTitle("SLEEPY")
    end
end

function caffeineClicked()
    setCaffeineDisplay(hs.caffeinate.toggle("displayIdle"))
end

if caffeine then
    caffeine:setClickCallback(caffeineClicked)
    setCaffeineDisplay(hs.caffeinate.get("displayIdle"))
end
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
--  If go from power cable plugged in to battery then make display AWAKE
-- ----------------------------------------------------------------------------
-- local powerWatcher = nil
-- local lastPowerSource = hs.battery.powerSource()

-- function powerSourceChangedCallback()
--     local currentPowerSource = hs.battery.powerSource()
--     if lastPowerSource == "AC Power" and currentPowerSource == "Battery Power" then
--         -- Prevent displayIdle from happening, and apply this rule to both AC and battery power
--         hs.caffeinate.set("displayIdle", true, true)
--         setCaffeineDisplay(hs.caffeinate.get("displayIdle"))
--     elseif lastPowerSource == "Battery Power" and currentPowerSource == "AC Power" then
--         -- Allow displayIdle to happen, and apply this rule to both AC and battery power
--         hs.caffeinate.set("displayIdle", false, true)
--         setCaffeineDisplay(hs.caffeinate.get("displayIdle"))
--     end
--     lastPowerSource = currentPowerSource
-- end
-- powerWatcher = hs.battery.watcher.new(powerSourceChangedCallback)
-- powerWatcher:start()
