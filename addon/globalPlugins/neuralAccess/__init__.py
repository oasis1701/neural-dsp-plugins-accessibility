# neuralAccess - the global plugin.
#
# This is how neuralAccess reaches an amplifier when it is loaded as a VST3 plug-in. A plug-in
# has no executable of its own - it is a DLL inside whatever host loaded it - so there is nothing
# for an app module to be keyed to, and keying one to reaper.exe would claim bare arrow keys,
# Tab, Enter and the space bar across the whole of REAPER and fight OSARA the entire way.
#
# A global plugin's chooseNVDAObjectOverlayClasses is called for every object NVDA builds in
# every process, which is exactly the reach that is needed. The gestures then live on the overlay
# classes themselves (see core.AmpObject), where NVDA only makes them live while one of the
# amplifier's controls actually has focus. Inside the amplifier they are ours; one Tab outside it
# they are the host's again.
#
# It also registers the standalones' executable names against the shared "neuraldsp" app module,
# which exists only to tell NVDA to use UI Automation for those applications' windows.

import os
import time

import appModuleHandler
import api
import controlTypes
import globalPluginHandler
import globalVars
import inputCore
import ui
from core import callLater
from scriptHandler import script
from logHandler import log

from . import capture
from . import core as engine
from . import mesa
from . import nolly
from . import petrucci
from . import popups

engine.registerProfile(mesa.PROFILE)
engine.registerProfile(petrucci.PROFILE)
engine.registerProfile(nolly.PROFILE)

APP_MODULE = "neuraldsp"

# The developer switch. Captures write pictures to the Temp folder, which is for working on
# the add-on and not for its users (Hadi, 2026-11-12: "auto capture needs to be disabled for
# public release, so it wouldn't create images for users", and the capture key "should only be
# enabled as a developer setting"). The automatic captures and the capture key exist only on a
# computer whose NVDA settings folder holds a file of this name. The file lives outside
# the add-on, so no package ever carries it and an update leaves it in place. Read once;
# creating or deleting the file takes effect when NVDA restarts.
DEVELOPER_SWITCH = "neuralAccess-developer"
_developerSwitchOn = None


def developerSwitchOn():
    global _developerSwitchOn
    if _developerSwitchOn is None:
        try:
            _developerSwitchOn = os.path.isfile(
                os.path.join(globalVars.appArgs.configPath, DEVELOPER_SWITCH))
        except Exception:
            _developerSwitchOn = False
        log.info("neuralAccess: developer switch %s" % ("on" if _developerSwitchOn else "off"))
    return _developerSwitchOn


def _executableNames():
    """Every spelling of every registered standalone's executable name.

    NVDA derives the executable name in a way we do not want to depend on exactly, so several
    plausible spellings are registered per amplifier; extra registrations are harmless dictionary
    entries.
    """
    names = []
    for profile in engine.PROFILES:
        names.extend(profile.executableNames)
    return names


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    def __init__(self, *args, **kwargs):
        super(GlobalPlugin, self).__init__(*args, **kwargs)
        # Where focus was in the host when we stepped into the amplifier, so stepping back out
        # returns you to the control you came from rather than somewhere arbitrary. The element
        # is captured on a deliberate step-in; the object is whatever was last focused outside an
        # amplifier, which covers the case where neuralAccess never saw the step-in - after an
        # NVDA restart with focus already inside, say.
        self._hostFocusElement = None
        self._hostFocusObject = None
        self._registered = []
        for name in _executableNames():
            try:
                appModuleHandler.registerExecutableWithAppModule(name, APP_MODULE)
                self._registered.append(name)
            except Exception:
                log.exception("neuralAccess: could not register executable %r" % name)
        log.info("neuralAccess: registered %d executable spellings for app module %r"
                 % (len(self._registered), APP_MODULE))
        if developerSwitchOn():
            self.bindGesture("kb:NVDA+shift+c", "capture")
        # Every key NVDA is about to act on, so that a key other than Enter cancels a button's
        # "Press Enter again to confirm" (see core.armConfirm and core.noteGesture).
        self._gestureHook = getattr(inputCore, "decide_executeGesture", None)
        if self._gestureHook is not None:
            try:
                self._gestureHook.register(self._beforeGesture)
            except Exception:
                log.info("neuralAccess: could not watch the keys", exc_info=True)
                self._gestureHook = None
        self._adoptRunningInstances()

    def _beforeGesture(self, gesture=None, **kwargs):
        """Always True: this only looks at the key, and must never be why a key does nothing."""
        try:
            engine.noteGesture(gesture)
        except Exception:
            log.debugWarning("neuralAccess: could not look at a key", exc_info=True)
        return True

    def terminate(self, *args, **kwargs):
        hook = getattr(self, "_gestureHook", None)
        if hook is not None:
            try:
                hook.unregister(self._beforeGesture)
            except Exception:
                pass
            self._gestureHook = None
        for name in self._registered:
            try:
                appModuleHandler.unregisterExecutable(name)
            except Exception:
                pass
        self._registered = []
        super(GlobalPlugin, self).terminate(*args, **kwargs)

    def _adoptRunningInstances(self):
        """Applies the shared app module to a standalone already running when NVDA started.

        NVDA keeps one app module per process and fetches it only once. When a standalone is
        already running as NVDA starts, that fetch happens before this plugin has registered the
        executable name, so NVDA caches a plain app module and keeps it for the life of that
        process. Dropping those entries makes NVDA build ours instead.

        This matters much less than it used to: the control overlays now come from this global
        plugin, which has no such caching, so a stale app module can no longer stop neuralAccess
        working. It is kept because the app module still asks NVDA to use UI Automation.
        """
        table = getattr(appModuleHandler, "runningTable", None)
        if table is None:
            log.debugWarning("neuralAccess: appModuleHandler exposes no runningTable to refresh")
            return
        wanted = set(name.lower() for name in _executableNames())
        adopted = []
        for processID, appModule in list(table.items()):
            appName = (getattr(appModule, "appName", "") or "").lower()
            if appName not in wanted or type(appModule).__module__.endswith(APP_MODULE):
                continue
            try:
                appModule.terminate()
            except Exception:
                log.debugWarning("neuralAccess: could not end the stale app module", exc_info=True)
            table.pop(processID, None)
            adopted.append(processID)
        if not adopted:
            return
        log.info("neuralAccess: adopting already running process(es) %r" % adopted)
        for processID in adopted:
            try:
                appModuleHandler.getAppModuleFromProcessID(processID)
            except Exception:
                log.debugWarning("neuralAccess: could not build the app module", exc_info=True)
        # The focused object still carries the old app module. Moving focus onto a control makes
        # NVDA build a fresh one, and from that point on everything is normal.
        hwnd = self._foregroundAmpWindow()
        if hwnd:
            controller = engine.ampForWindow(hwnd, self._foregroundProcessID())
            if controller is not None:
                controller.scheduleFocusEntry()

    # ---------- putting the overlay classes in front of the amplifiers' controls ----------

    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        try:
            with engine.Timed("recognising an object's window"):
                engine.applyOverlayClasses(obj, clsList)
        except Exception:
            log.debugWarning("neuralAccess: could not classify an object", exc_info=True)

    # ---------- focus tracking ----------

    def event_gainFocus(self, obj, nextHandler):
        # Focus on another control cancels a button's "Press Enter again to confirm".
        try:
            engine.noteFocusForConfirm(obj, self._controllerFor(obj))
        except Exception:
            log.debugWarning("neuralAccess: could not follow focus for a confirmation", exc_info=True)
        # A lamp or dimming layer that Tab has just landed on is passed over before NVDA says a
        # word about it; anything else ends the Tab press.
        try:
            controller = self._controllerFor(obj)
            if controller is not None:
                with engine.Timed("working out a focused control's name and value"):
                    if controller.skipDecorative(obj):
                        return
                    if controller.focusIsHushed(obj):
                        # A focus change a command made itself and speaks for (the gate and
                        # doubler keys click a caption, then send focus back).
                        location = getattr(obj, "location", None)
                        log.info("neuralAccess: focus change kept quiet, at %s"
                                 % (tuple(location) if location else None,))
                        return
                    controller._lastTab = None
                    engine.FOCUS_LOG(obj)
                    self._captureIfNameless(obj, controller)
        except Exception:
            log.debugWarning("neuralAccess: decorative skip failed", exc_info=True)
        try:
            with engine.Timed("focus tracking"):
                self._trackFocus(obj)
        except Exception:
            log.debugWarning("neuralAccess: focus tracking failed", exc_info=True)
        nextHandler()

    def event_foreground(self, obj, nextHandler):
        try:
            controller = self._controllerFor(obj)
            # Only the standalone takes focus by itself. Inside a host the FX window's own
            # controls are somewhere you legitimately want to be, so stepping in is deliberate.
            if controller is not None and not controller.hosted and obj.ampIsDeadEnd:
                controller.scheduleFocusEntry()
        except Exception:
            log.debugWarning("neuralAccess: foreground handling failed", exc_info=True)
        nextHandler()

    def _controllerFor(self, obj):
        if not isinstance(obj, engine.AmpObject):
            return None
        return obj.ampController

    # A control that announces with no name is this add-on failing at its one job, and Hadi
    # should not have to stop and press the capture key to report it (asked 2026-11-09). So the
    # add-on takes the capture itself, silently, a moment after such a stop takes focus: the
    # moment's delay lets NVDA speak first. Rationed, because a capture holds NVDA for a while.
    # Text is in the list since 0.12.2: the Nolly's synced delay displays are text elements in
    # the Tab ring, and one said only "text" with no capture taken (Hadi, 2026-11-11). Captions
    # are text elements too, but each carries its caption as its name. Only with the developer
    # switch on (see DEVELOPER_SWITCH).
    AUTO_CAPTURE_ROLES = (controlTypes.Role.BUTTON, controlTypes.Role.SLIDER,
                          controlTypes.Role.EDITABLETEXT, controlTypes.Role.COMBOBOX,
                          controlTypes.Role.RADIOBUTTON, controlTypes.Role.STATICTEXT)
    AUTO_CAPTURE_GAP_S = 20.0
    AUTO_CAPTURE_MAX = 8

    def _captureIfNameless(self, obj, controller):
        try:
            if obj.name or obj.role not in self.AUTO_CAPTURE_ROLES or not developerSwitchOn():
                return
            taken, last = getattr(self, "_autoCaptures", (0, 0.0))
            now = time.time()
            if taken >= self.AUTO_CAPTURE_MAX or now - last < self.AUTO_CAPTURE_GAP_S:
                return
            self._autoCaptures = (taken + 1, now)
            location = obj.location
            reason = "focus landed on a %s with no name at %s" % (
                getattr(obj.role, "name", obj.role), tuple(location) if location else None)
            log.info("neuralAccess: %s; taking a capture" % reason)
            callLater(400, self._automaticCapture, controller, obj.processID, reason)
        except Exception:
            log.info("neuralAccess: automatic capture could not be arranged", exc_info=True)

    def _automaticCapture(self, controller, processID, reason):
        try:
            capture.capture(controller, processID, automatic=reason)
        except Exception:
            log.info("neuralAccess: automatic capture failed", exc_info=True)

    def _trackFocus(self, obj):
        controller = self._controllerFor(obj)
        if controller is None:
            # Somewhere outside the amplifier. Worth keeping as the way back out of a plug-in
            # window, whose Tab ring is cyclic and has no exit of its own. This is only a
            # reference - nothing is asked of the object, so it costs nothing on a focus change
            # anywhere else on the system.
            self._hostFocusObject = obj
            return
        try:
            controller.profile.onFocus(controller, obj)
        except Exception:
            log.debugWarning("neuralAccess: profile focus hook failed", exc_info=True)
        role = getattr(obj, "role", None)
        if role in engine.RESUMABLE_ROLES:
            controller.rememberFocus(getattr(obj, "UIAElement", None))
        elif not controller.hosted and obj.ampIsDeadEnd:
            controller.scheduleFocusEntry()
        if role == controlTypes.Role.LIST:
            # Start reading the channel names off the screen now, so they are ready by the time
            # the first row is announced.
            element = getattr(obj, "UIAElement", None)
            rect = engine._prop(element, engine.PROP_BOUNDING_RECT) if element is not None else None
            if rect and len(rect) >= 4:
                controller.recogniseRowNames(tuple(rect[:4]))

    # ---------- stepping in and out ----------

    def _foregroundProcessID(self):
        try:
            return api.getForegroundObject().processID
        except Exception:
            return 0

    def _foregroundAmpWindow(self):
        """An editor window at or inside whatever is in front, or None."""
        try:
            root = api.getForegroundObject().windowHandle
        except Exception:
            return None
        return engine.findAmpWindow(root)

    @script(description="Steps keyboard focus into the amplifier, or back out to the host. "
                        "Inside a host the amplifier's own Tab ring is cyclic and never leaves it, "
                        "so this is the way back.",
            gesture="kb:NVDA+shift+f", category=engine.CATEGORY)
    def script_focusPlugin(self, gesture):
        focus = api.getFocusObject()
        controller = self._controllerFor(focus)
        if controller is not None and controller.hosted:
            self._stepOut(controller)
            return
        self._stepIn(controller)

    def _stepIn(self, controller):
        if controller is None:
            hwnd = self._foregroundAmpWindow()
            if not hwnd:
                ui.message("No Neural DSP amplifier window in front.")
                return
            controller = engine.ampForWindow(hwnd, self._foregroundProcessID())
        if controller is None:
            ui.message("Could not move focus into the amplifier.")
            return
        if controller.hosted:
            # Remember where we came from, so stepping back out lands on the host control you
            # were standing on rather than wherever the host happens to put focus. Some hosts
            # hand focus to the editor itself when its window activates - an element inside the
            # editor is no way back out, so it is not worth remembering.
            element = engine.focusedElement()
            self._hostFocusElement = element if not controller.elementIsInside(element) else None
        controller.enterWindow(force=True)

    def _focusLeft(self, controller):
        """True when keyboard focus is genuinely outside the editor.

        trySetFocus only says the SetFocus call did not raise. REAPER's FX dialog accepts the
        call and quietly leaves focus where it was, which once made step-out return early having
        done nothing at all - so every strategy is checked against where focus actually ended up.
        """
        return not controller.elementIsInside(engine.focusedElement())

    def _stepOut(self, controller):
        host = controller.hostWindow()
        target = self._hostFocusElement
        self._hostFocusElement = None
        if target is not None and not controller.elementIsInside(target) \
                and controller.trySetFocus(target) and self._focusLeft(controller):
            return
        # Nothing captured on the way in, or it has gone. Fall back to the last thing focused
        # anywhere outside an amplifier, provided it belongs to this host's window.
        obj = self._hostFocusObject
        if obj is not None and host and engine.rootWindow(getattr(obj, "windowHandle", 0)) == host:
            try:
                obj.setFocus()
                if self._focusLeft(controller):
                    return
            except Exception:
                log.debugWarning("neuralAccess: could not restore the host's focus", exc_info=True)
        # Last resort: any ordinary control of the host window. Focusing the host window itself
        # is no use - it is already the active window, so nothing moves.
        if host and engine.focusFirstHostControl(host, controller.hwnd) and self._focusLeft(controller):
            return
        ui.message("Could not step back out to the host. Alt tab away and back instead.")

    @script(description="Loads your own impulse response file into the focused microphone slot: "
                        "opens the microphone list and presses its LOAD button.",
            gesture="kb:NVDA+shift+i", category=engine.CATEGORY)
    def script_loadImpulseResponse(self, gesture):
        processID = self._foregroundProcessID()
        focus = api.getFocusObject()
        controller = self._controllerFor(focus)
        if controller is None:
            # The microphone list may already be open; it is a window of its own.
            hwnd = self._foregroundAmpWindow() or (popups.findEditorInProcess(processID) if processID else None)
            if hwnd:
                controller = engine.ampForWindow(hwnd, processID)
        if controller is None:
            ui.message("No Neural DSP amplifier found.")
            return
        message = controller.profile.loadImpulseResponse(controller, focus, processID)
        if message:
            ui.message(message)

    # Saves a picture and a list of every control of the amplifier as it is now, including any
    # list or menu it has open, for working on this add-on. Bound to NVDA+Shift+C only with the
    # developer switch on (Hadi, 2026-11-12), and given no description, so that nobody else has
    # it in the Input Gestures dialog or loses NVDA's own NVDA+Shift+C (set column headers).
    def script_capture(self, gesture):
        processID = self._foregroundProcessID()
        controller = self._controllerFor(api.getFocusObject())
        if controller is None:
            # With a combo box's list open, focus and the foreground are the list's own window,
            # which holds no editor - so look through the whole process.
            hwnd = self._foregroundAmpWindow() or (popups.findEditorInProcess(processID) if processID else None)
            if hwnd:
                controller = engine.ampForWindow(hwnd, processID)
        try:
            capture.capture(controller, processID)
        except Exception:
            log.info("neuralAccess: capture failed", exc_info=True)
            ui.message("Capture failed. The reason is in NVDA's log.")
