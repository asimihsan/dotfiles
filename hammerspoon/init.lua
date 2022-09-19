require "string"

logger = hs.logger.new('logger', 'debug')
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
local powerWatcher = nil
local lastPowerSource = hs.battery.powerSource()

function powerSourceChangedCallback()
    local currentPowerSource = hs.battery.powerSource()
    if lastPowerSource == "AC Power" and currentPowerSource == "Battery Power" then
        -- Prevent displayIdle from happening, and apply this rule to both AC and battery power
        hs.caffeinate.set("displayIdle", true, true)
        setCaffeineDisplay(hs.caffeinate.get("displayIdle"))
    elseif lastPowerSource == "Battery Power" and currentPowerSource == "AC Power" then
        -- Allow displayIdle to happen, and apply this rule to both AC and battery power
        hs.caffeinate.set("displayIdle", false, true)
        setCaffeineDisplay(hs.caffeinate.get("displayIdle"))
    end
    lastPowerSource = currentPowerSource
end
powerWatcher = hs.battery.watcher.new(powerSourceChangedCallback)
powerWatcher:start()
-- ----------------------------------------------------------------------------
--  If not on home Wifi then mute audio
-- ----------------------------------------------------------------------------
local wifiWatcher = nil
local homeSSID = "Onset Roost"
local lastSSID = hs.wifi.currentNetwork()

function ssidChangedCallback()
    newSSID = hs.wifi.currentNetwork()
    if newSSID == homeSSID and lastSSID ~= homeSSID then
        -- We just joined our home WiFi network
        hs.audiodevice.defaultOutputDevice():setVolume(25)
    elseif newSSID ~= homeSSID and lastSSID == homeSSID then
        -- We just departed our home WiFi network
        hs.audiodevice.defaultOutputDevice():setVolume(0)
    end
    lastSSID = newSSID
end
wifiWatcher = hs.wifi.watcher.new(ssidChangedCallback)
wifiWatcher:start()
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
--  Attempt to wake up NAS when waking up
-- ----------------------------------------------------------------------------
function checkWakeUpNasResult(rc, stderr, stderr)
    if rc ~= 0 then
        print(string.format("Unexpected result waking up NAS: rc=%d stderr=%s stdout=%s", rc, stderr, stdout))
    end
end

function checkMountResult(rc, stderr, stderr)
    if rc ~= 0 then
        print(string.format("Unexpected result running mount: rc=%d stderr=%s stdout=%s", rc, stderr, stdout))
    end
end

function wakeUpNas()
    print("Waking up NAS...")
    local t = hs.task.new("/usr/local/bin/wakeonlan", checkWakeUpNasResult, {"00:11:32:EC:EF:A7"})
    t:start()
end

function mountSharedFolders()
    print("Running mount...")
    local t = hs.task.new("/Users/asimi/bin/mount.sh", checkMountResult)
    t:start()
end

hs.network.reachability.internet():setCallback(function(self, flags)
    if (flags & hs.network.reachability.flags.reachable) > 0 then
        logger.i("internet is reachable, so do mounting")
        mountSharedFolders()
    end
end):start()

hs.timer.doEvery(60, mountSharedFolders)