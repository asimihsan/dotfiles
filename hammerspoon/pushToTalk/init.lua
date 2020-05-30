--
-- Simple Hammerspoon script to create Push-To-Talk functionality
-- Press and hold fn key to talk
--
local log = hs.logger.new('PushToTalk','debug')
local settings = {
  pushToTalk = true
}

local inputVolumes = {}
local muted = false
local menubarIcon = nil
local icons = {
  microphone = nil,
  mutedMicrophone = nil
}

function updateInputVolumes()
  local activeUids = {}
  for index, device in ipairs(hs.audiodevice.allInputDevices()) do
    activeUids[device:uid()] = true
    if inputVolumes[device:uid()] == nil then
      local inputVolume = device:inputVolume()
      if inputVolume == 0 then
        inputVolume = 100
      end
      inputVolumes[device:uid()] = inputVolume
      log.i("Setting unmuted volume for " .. device:uid() .. ": " .. inputVolumes[device:uid()])
    end
    if not device:watcherIsRunning() then
      device:watcherCallback(onInputDeviceChanged)
      device:watcherStart()
    end
  end
  for uid, volume in pairs(inputVolumes) do
    if activeUids[uid] == nil then
      inputVolumes[uid] = nil
      log.i("Removed unmuted volume for no longer active device " .. uid)
    end
  end
end

function onInputDeviceChanged(uid, name, scope, element)
  if name ~= "vmvc" then
    return
  end

  if scope ~= "inpt" then
    return
  end

  local device = hs.audiodevice.findDeviceByUID(uid)
  local newVolume = device:inputVolume()

  if newVolume == 0 or newVolume == inputVolumes[uid] then
    return
  end

  inputVolumes[uid] = newVolume
  log.i("User changed unmuted volume for " .. uid .. ": " .. newVolume)
end

function onSystemAudioDeviceChanged(name)
  if name ~= "dev#" then
    return
  end

  updateInputVolumes()
  changeMicrophoneState(muted)
end

function installSystemAudioWatcher()
  hs.audiodevice.watcher.setCallback(onSystemAudioDeviceChanged)
  hs.audiodevice.watcher.start()
end

function changeMicrophoneState(mute)
  if mute then
    log.i('Muting audio')
    for index, device in ipairs(hs.audiodevice.allInputDevices()) do
      device:setInputVolume(0)
    end
    -- Hack to really mute the microphone
    hs.applescript('set volume input volume 0')
    menubarIcon:setIcon(icons.mutedMicrophone)
  else
    for index, device in ipairs(hs.audiodevice.allInputDevices()) do
      if inputVolumes[device:uid()] == nil then
        log.i("Device with unknown inputVolume")
      else
        log.i('Unmuting audio: ' .. inputVolumes[device:uid()])
        device:setInputVolume(inputVolumes[device:uid()])
      end
    end
    -- Hack to really unmute the microphone
    local defaultInputDevice = hs.audiodevice.defaultInputDevice()
    local defaultVolumne = inputVolumes[defaultInputDevice:uid()]
    hs.applescript('set volume input volume ' .. defaultVolumne)
    menubarIcon:setIcon(icons.microphone)
  end
end

local leftShiftPressed = false
local rightShiftPressed = false
local hotKeyPressed = false
local modifiersChangedTap = hs.eventtap.new(
  {hs.eventtap.event.types.flagsChanged},
  function(event)
    local anyShiftPressed = event:getFlags().shift
    local keyCode = event:getProperty(hs.eventtap.event.properties.keyboardEventKeycode)

    local stateChanged = false
    local newLeftShiftPressed = false
    local newRightShiftPressed = false

    -- 56 is left shift, 60 is right shift
    if not anyShiftPressed then
      newLeftShiftPressed = false
      newRightShiftPressed = false
      newHotKeyPressed = false
    elseif keyCode == 56 then
      newLeftShiftPressed = not leftShiftPressed
      newHotKeyPressed = newLeftShiftPressed and rightShiftPressed
    elseif keyCode == 60 then
      newRightShiftPressed = not rightShiftPressed
      newHotKeyPressed = leftShiftPressed and newRightShiftPressed
    end

    if hotKeyPressed ~= newHotKeyPressed then
      stateChanged = true
    else
      stateChanged = false
    end

    leftShiftPressed = newLeftShiftPressed
    rightShiftPressed = newRightShiftPressed
    hotKeyPressed = newHotKeyPressed

    if stateChanged then
      if hotKeyPressed then
        muted = not settings.pushToTalk
        changeMicrophoneState(muted)
      else
        muted = settings.pushToTalk
        changeMicrophoneState(muted)
      end
    end
  end
)

function initMenubarIcon()
  menubarIcon = hs.menubar.new()
  menubarIcon:setIcon(icons.microphone)
  menubarIcon:setMenu(function()
    return {
      {title = "Push to talk", checked = settings.pushToTalk, fn = function()
        if settings.pushToTalk == false then
          muted = true
          changeMicrophoneState(true)
          settings.pushToTalk = true
        end
      end},
      {title = "Push to mute", checked = not settings.pushToTalk, fn = function()
        if settings.pushToTalk == true then
          muted = false
          changeMicrophoneState(false)
          settings.pushToTalk = false
        end
      end},
      {title = "-"},
      {title = "Hotkey: lshift + rshift"}
    }
  end)
end

function loadIcons()
  local iconPath = hs.configdir .. "/pushToTalk/icons"
  icons.microphone = hs.image.imageFromPath(iconPath .. "/microphone.pdf"):setSize({w = 16, h = 16})
  icons.mutedMicrophone = hs.image.imageFromPath(iconPath .."/microphone-slash.pdf"):setSize({w = 16, h = 16})
end

function loadSettings()
  local loadedSettings = hs.settings.get('pushToTalk.settings')
  if loadedSettings ~= nil then
    settings = loadedSettings
  end
end

function saveSettings()
  hs.settings.set('pushToTalk.settings', settings)
end

-- Public interface
local pushToTalk = {}
pushToTalk.init = function(modifiers)
  modifierKeys = modifiers or {"fn"}

  loadSettings()
  loadIcons()

  initMenubarIcon()

  updateInputVolumes()
  installSystemAudioWatcher()
  changeMicrophoneState(settings.pushToTalk)

  modifiersChangedTap:start()

  local oldShutdownCallback = hs.shutdownCallback
  hs.shutdownCallback = function()
    if oldShutdownCallback ~= nil then
      oldShutdownCallback()
    end

    saveSettings()
    changeMicrophoneState(false)
  end
end

return pushToTalk
