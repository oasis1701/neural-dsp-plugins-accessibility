# neuralAccess - the machinery shared by every Neural DSP amplifier.
#
# One add-on, one body of machinery, one PROFILE per amplifier. A profile carries everything a
# particular amplifier knows - its vocabulary, its pixel calibration, its layout tables - while
# this module carries everything that is true of all of them: how an editor window is recognised,
# how focus is dropped into it, how sliders are adjusted, how switch pixels are sampled, and the
# overlay classes NVDA puts in front of the controls.
#
# This module is deliberately independent of HOW NVDA reached the amplifier. The same editor is
# reachable two completely different ways:
#
#   * the standalone application, which is a process of its own and so has an app module, and
#   * the VST3 plug-in, which has no executable at all - it is a DLL living inside whatever host
#     loaded it, so there is nothing for an app module to key to and it is reached through the
#     global plugin's overlay hook instead.
#
# Both routes end up applying the same overlay classes to the same controls, so all of the
# knowledge is written once.
#
# Findings this module is built on (verified against the running applications):
#   * The amps are JUCE applications exposing genuine UI Automation trees with native providers.
#   * The Mesa generation leaves every Name empty with the label in HelpText; the X generation
#     names some controls, HelpTexts others, and leaves its sliders anonymous. The name pipeline
#     therefore asks the profile whenever the tree itself has nothing to say.
#   * Sliders expose RangeValue with IsReadOnly false, so values can be read AND written.
#   * The editors take keyboard focus without giving any component focus, and JUCE's own Tab
#     handling needs a focused component to traverse from. Everything under "keyboard focus
#     entry" exists to put focus on a real control inside the editor.
#
# UIA constants are spelled out numerically so this module never depends on which names a
# particular NVDA build re-exports from UIAHandler.

import ctypes
import time

import api
import braille
import controlTypes
import core
import queueHandler
import screenBitmap
import speech
import ui
import UIAHandler
from NVDAObjects.UIA import UIA
from keyboardHandler import KeyboardInputGesture
from scriptHandler import script
from logHandler import log

from . import tuning

# --- UIA property ids ---
PROP_BOUNDING_RECT = 30001
PROP_PROCESS_ID = 30002
PROP_CONTROL_TYPE = 30003
PROP_NAME = 30005
PROP_IS_ENABLED = 30010
PROP_HELP_TEXT = 30013
PROP_IS_KEYBOARD_FOCUSABLE = 30009
PROP_NATIVE_WINDOW_HANDLE = 30020
PROP_VALUE_VALUE = 30045
PROP_RANGE_VALUE = 30047
PROP_RANGE_MIN = 30049
PROP_RANGE_MAX = 30050
PROP_RANGE_SMALL_CHANGE = 30052
PROP_PROVIDER_DESCRIPTION = 30107

# --- UIA control type ids ---
CT_BUTTON = 50000
CT_CHECKBOX = 50002
CT_COMBOBOX = 50003
CT_EDIT = 50004
CT_LISTITEM = 50007
CT_LIST = 50008
CT_RADIOBUTTON = 50013
CT_SLIDER = 50015
CT_TABITEM = 50019
CT_TEXT = 50020
CT_CUSTOM = 50025
CT_WINDOW = 50032
CT_PANE = 50033

# --- UIA pattern ids ---
PATTERN_INVOKE = 10000
PATTERN_RANGE_VALUE = 10003
PATTERN_TEXT = 10014

TREESCOPE_DESCENDANTS = 4

CATEGORY = "Neural DSP Plugins Accessibility"

# JUCE registers a window class per build, so the exact class name is a hash that changes when
# the vendor ships an update - it is only good enough as a cheap first filter. The reliable test
# is UIA's provider description, which names the module the provider came from, with the root
# element's Name as a second witness. Each profile supplies the marker strings that identify its
# own editor; the class prefix below settles the question for everything that is not JUCE, which
# is very nearly everything, before a single UI Automation call is spent.
JUCE_CLASS_PREFIX = "JUCE_"

# Control types worth landing on when focus has to be dropped into a window, in the order they
# are searched for.
ENTRY_CONTROL_TYPES = (CT_BUTTON, CT_SLIDER, CT_COMBOBOX, CT_CHECKBOX, CT_LISTITEM, CT_EDIT)

# Roles that mean the focus is on a window rather than on anything you can operate.
DEAD_END_ROLES = frozenset((controlTypes.Role.WINDOW, controlTypes.Role.PANE))

# Roles worth returning to when the plugin is brought forward again.
RESUMABLE_ROLES = frozenset((
    controlTypes.Role.BUTTON, controlTypes.Role.SLIDER, controlTypes.Role.EDITABLETEXT,
    controlTypes.Role.CHECKBOX, controlTypes.Role.COMBOBOX, controlTypes.Role.RADIOBUTTON,
    controlTypes.Role.LISTITEM, controlTypes.Role.TAB, controlTypes.Role.TOGGLEBUTTON,
))

# Let the window finish activating before taking focus off it, then confirm it worked.
FOCUS_ENTRY_DELAY_MS = 250
FOCUS_RETRY_DELAY_MS = 500
FOCUS_ENTRY_ATTEMPTS = 3

# A ticked channel row draws a bright indicator; an unticked one stays at the panel's background
# level. Measured on the Mesa Boogie: ticked peaks around 224, unticked around 40.
TICK_BRIGHTNESS = 120
TICK_INDICATOR_INSET = 4
TICK_INDICATOR_WIDTH = 18

# How far to magnify a channel list before asking Windows to recognise it. The row text is about
# eleven pixels tall and light on dark, which reads badly at its natural size.
OCR_RESIZE_FACTOR = 4

# How long a switch reading may be reused. NVDA asks a focused control for its name and role
# several times per focus event and a screen capture is far too expensive to repeat; this is also
# short enough that a reading never survives long enough to be believed after a change.
STATE_CACHE_TTL = 0.4

# After activating a switch the plugin repaints a moment later, so reading the pixels straight
# back returns the old position. Poll until it moves, then say what it moved to. The first poll
# waits for the click to finish and the cursor to be put back - a reading taken while the cursor
# still hovers the switch is off by up to 77 grey levels - and a change must hold for two
# consecutive polls before it is spoken, or the focus events a click sets off cancel the
# announcement mid-queue.
STATE_SETTLE_POLLS = 8
STATE_SETTLE_MS = 150
STATE_SETTLE_FIRST_MS = 600

# A tip reading needs one spot clearly brighter than the other. Measured on the Petrucci's
# screenshots the gaps run 55 to 163 grey levels; anything closer is reported as unknown.
TIP_MIN_GAP = 20

# A sixth entry of a switch probe: its threshold is then not a grey level but a share of the
# brightest point of the control's own rectangle (see AmpController.switchPosition). For a
# switch that always has something near white in it, such as the Nolly X's little rockers,
# whose outline or filling is white in either position. A control whose brightest point is
# under PROBE_PEAK_MIN is a window that is covered or not drawn, and gives no reading.
PROBE_OF_PEAK = "of peak"
PROBE_PEAK_MIN = 40.0


def STATE_LOG(message):
    """Switch readings go to the log at info level while the 0.9.0 switches are being checked by
    hand, so a wrong threshold can be corrected from Hadi's normal log. Turn back to log.debug
    once they are confirmed."""
    log.info(message)


SLOW_CALL_S = 0.3


class ScreenBox(object):
    """A box of the screen as AmpController.screenBox read it."""

    def __init__(self, pixels, width, height):
        self._pixels = pixels
        self.width = width
        self.height = height

    def at(self, x, y):
        """(red, green, blue) of the point x across and y down from the box's corner."""
        pixel = self._pixels[y][x]
        return (pixel.rgbRed, pixel.rgbGreen, pixel.rgbBlue)


class Timed(object):
    """Writes "slow: <what> took N s" to the log at info level when the wrapped work takes
    longer than SLOW_CALL_S.

    On 2026-11-09 NVDA froze six times for 2.2 seconds each in one session (its watchdog said
    so) and nothing in the log said what it was waiting for. Every call this add-on makes into
    the plug-in happens on NVDA's main thread, so a call that hangs there freezes NVDA. With
    this around the add-on's entry points, a freeze with no "slow:" line beside it was not
    spent in the add-on."""

    def __init__(self, what):
        self.what = what

    def __enter__(self):
        self.started = time.time()
        return self

    def __exit__(self, excType, excValue, traceback):
        elapsed = time.time() - self.started
        if elapsed >= SLOW_CALL_S:
            log.info("neuralAccess: slow: %s took %.2f s" % (self.what, elapsed))
        return False


def FOCUS_LOG(obj):
    """What NVDA is about to say for an amplifier control that has just taken focus, at info
    level. Hadi tests by hand and his log is at info level, which carries no speech; with this
    line a Tab pass through a view can be read back afterwards (asked for 2026-11-09: "I went
    over the tab ring so you can read it in the log"). Turn off together with STATE_LOG."""
    try:
        # The rectangle says WHICH control it was when the name says nothing: "focus '',
        # UNKNOWN" on 2026-11-10 could have been the tuner's frame or a passing container.
        location = getattr(obj, "location", None)
        log.info("neuralAccess: focus %r, %s, value %r, at %s" % (
            obj.name, getattr(obj.role, "name", obj.role), obj.value,
            tuple(location) if location else None))
    except Exception:
        # At info level on purpose: this cannot be tried outside NVDA, and a debug warning
        # would be invisible in the very log it is meant to fill.
        log.info("neuralAccess: focus log failed", exc_info=True)


# ---------- buttons that ask before they act ----------
#
# A button in AmpProfile.confirmActions is warned about on the first Enter and pressed on the
# second. The second used to count only inside NVDA's double press time (half a second unless
# changed), and the warning takes longer than that to hear: pressed after listening, Enter only
# repeated the warning, for ever (Hadi on DELETE, 2026-11-10). Now the warned button stays armed
# for CONFIRM_WINDOW_S. Focus landing on another control disarms it, and so does any key that is
# not Enter. Everything here logs at info level: it cannot be tried outside NVDA, and a press
# that does nothing has to be readable in Hadi's log afterwards.
CONFIRM_WINDOW_S = 10.0
_armedConfirm = None    # (editor window, confirmActions key, the button's rectangle, armed until)


def _objRect(obj):
    try:
        location = obj.location
        return (location.left, location.top, location.width, location.height)
    except Exception:
        return None


def _sameRect(a, b, tolerance=2):
    if a is None or b is None:
        return a is None and b is None
    return all(abs(x - y) <= tolerance for x, y in zip(a[:4], b[:4]))


def armConfirm(hwnd, key, rect):
    """The warning for this button has just been spoken; the next Enter on it presses it."""
    global _armedConfirm
    _armedConfirm = (hwnd, key, tuple(rect[:4]) if rect else None, time.time() + CONFIRM_WINDOW_S)
    log.info("neuralAccess: %s: warned, waiting %d seconds for Enter again" % (key, CONFIRM_WINDOW_S))


def disarmConfirm(reason):
    global _armedConfirm
    if _armedConfirm is not None:
        log.info("neuralAccess: %s: no longer waiting for Enter, %s" % (_armedConfirm[1], reason))
        _armedConfirm = None


def takeConfirm(hwnd, key, rect):
    """True when this Enter is the confirming one: the same button was warned about and nothing
    has cancelled it since. The answer is given once."""
    global _armedConfirm
    armed = _armedConfirm
    if armed is None:
        return False
    armedWindow, armedKey, armedRect, deadline = armed
    if time.time() > deadline:
        disarmConfirm("the time ran out")
        return False
    if armedWindow != hwnd or armedKey != key or not _sameRect(armedRect, rect):
        disarmConfirm("Enter was pressed on something else")
        return False
    _armedConfirm = None
    return True


def noteFocusForConfirm(obj, controller):
    """Every focus change passes through here. Focus on another control cancels a warning.

    controller is the amplifier obj belongs to, None for anything outside one. The editor's own
    root is let pass: when its window comes back to the front it takes focus for a few
    milliseconds on the way back to the control that had it, and that is not the user moving.
    """
    armed = _armedConfirm
    if armed is None:
        return
    if controller is None:
        disarmConfirm("focus left the amplifier")
        return
    if _sameRect(armed[2], _objRect(obj)):
        return
    try:
        deadEnd = bool(obj.ampIsDeadEnd)
    except Exception:
        deadEnd = False
    if not deadEnd:
        disarmConfirm("focus moved to another control")


def gestureIsKey(gesture, *names):
    """True when the gesture is one of these keys, named as in a binding: "enter", "shift+tab"."""
    wanted = set("kb:" + name for name in names)
    return any(str(identifier).lower() in wanted
               for identifier in (getattr(gesture, "identifiers", None) or ()))


def noteGestureForConfirm(gesture):
    """Any key but Enter cancels a warning - except a modifier by itself, because Control is
    how the warning is silenced."""
    if _armedConfirm is None:
        return
    if getattr(gesture, "isModifier", False) or gestureIsKey(gesture, "enter"):
        return
    disarmConfirm("another key was pressed")


def noteGesture(gesture):
    """Every key NVDA is about to act on, anywhere on the system, passes through here on its
    way to being acted on. Everything it reaches must cost nothing when it has nothing to do."""
    noteGestureForConfirm(gesture)
    for profile in PROFILES:
        try:
            profile.noteGesture(gesture)
        except Exception:
            log.debugWarning("neuralAccess: a profile could not look at a key", exc_info=True)


# A knob moved with the arrow keys was spoken twice ("49 percent. 49 percent.", Hadi,
# 2026-11-10). The key's script says the new value at once. The plug-in then reports the change
# to UI Automation, and NVDA speaks a value change on the control that has focus. For this long
# after the script has spoken, a report of that same value is not spoken again (see
# AmpSlider.event_valueChange). The first few are logged, at info level because Hadi's log is.
VALUE_ECHO_S = 1.0
_valueEchoesLogged = 0


def clockPosition(fraction, sweepDegrees=270.0):
    """Where a rotary knob's pointer points, in the words a tutorial uses: "2 o'clock",
    "half past 1".

    fraction is how far along its travel the knob is, 0.0 to 1.0. The pointer is straight up at
    the middle of the travel, and the travel is sweepDegrees wide: 270, from half past 7 round
    to half past 4, is the usual. Said to the nearest half hour, which is as exactly as anyone
    reads a small knob by eye. A value half way between two marks goes to the one further from
    12 o'clock, so that the two sides of the dial behave alike.
    """
    fraction = min(1.0, max(0.0, float(fraction)))
    halfHours = (fraction - 0.5) * sweepDegrees / 15.0
    steps = int(abs(halfHours) + 0.5 + 1e-9)
    if halfHours < 0:
        steps = -steps
    hour, half = divmod(steps, 2)
    hour = hour % 12 or 12
    return ("half past %d" if half else "%d o'clock") % hour


# After Tab or Shift+Tab, a decorative stop that receives focus within this long is passed over
# by sending the same key again. A chain of them is followed at most this many times. It was 6
# until 0.12.3. The Nolly X's EQ has 13 in a row between EQ voicing and the first band, HPF :,
# eleven value boxes and LPF :, and Tab gave up on the seventh (Hadi, 2026-11-11: "Band 1.5
# kilohertz readout"). His log has three of them passed in 112 milliseconds.
DECORATIVE_SKIP_S = 1.0
DECORATIVE_SKIP_MAX = 16

# How long a positional lookup's tree sweep may be reused. Each sweep is a FindAll plus a
# cross-process property read per element, which measures at about 100 ms, and NVDA asks a
# focused control for its name and its role three separate times. The cache is also keyed on the
# window geometry, so moving or resizing the window drops it at once rather than after the
# timeout.
POSITIONAL_CACHE_TTL = 2.0

# A tuner display repaints many times a second and raises no events, so an open tuner is read by
# polling. What gets said is decided in tuning.py; this is only how often to look. While the
# editor is not the foreground window nothing is spoken, and the poll slows to just noticing
# that the tuner has been closed.
TUNER_POLL_MS = 150
TUNER_IDLE_POLL_MS = 1000

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

GA_ROOT = 2

# A private handle on user32 so that setting argument types here can never disturb the prototypes
# NVDA's own winUser module has set on ctypes.windll.user32.
_user32 = ctypes.WinDLL("user32")
_user32.GetAncestor.restype = ctypes.c_void_p
_user32.GetAncestor.argtypes = (ctypes.c_void_p, ctypes.c_uint)
_user32.IsWindow.restype = ctypes.c_bool
_user32.IsWindow.argtypes = (ctypes.c_void_p,)
_user32.GetClassNameW.restype = ctypes.c_int
_user32.GetClassNameW.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int)
_user32.SetForegroundWindow.restype = ctypes.c_bool
_user32.SetForegroundWindow.argtypes = (ctypes.c_void_p,)
_user32.GetForegroundWindow.restype = ctypes.c_void_p
_user32.GetForegroundWindow.argtypes = ()
_user32.IsWindowVisible.restype = ctypes.c_bool
_user32.IsWindowVisible.argtypes = (ctypes.c_void_p,)
_user32.GetWindowTextW.restype = ctypes.c_int
_user32.GetWindowTextW.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int)

CT_MENU = 50009


def windowTitle(hwnd):
    buffer = ctypes.create_unicode_buffer(256)
    try:
        _user32.GetWindowTextW(hwnd, buffer, 256)
    except Exception:
        return ""
    return buffer.value


class _Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


_user32.WindowFromPoint.restype = ctypes.c_void_p
_user32.WindowFromPoint.argtypes = (_Point,)
# The callback returns a Win32 BOOL, which is a full int - a one byte c_bool would leave the rest
# of the register undefined and EnumChildWindows reads all of it.
_ENUM_CHILD_PROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
_user32.EnumChildWindows.restype = ctypes.c_bool
_user32.EnumChildWindows.argtypes = (ctypes.c_void_p, _ENUM_CHILD_PROC, ctypes.c_void_p)


def _cursorPos():
    point = _Point()
    if ctypes.windll.user32.GetCursorPos(ctypes.byref(point)):
        return point.x, point.y
    return None


_user32.GetAsyncKeyState.restype = ctypes.c_short
_user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
# Shift, Control, Alt, both Windows keys, and the two keys NVDA can use as its own modifier.
_HELD_KEYS = (0x10, 0x11, 0x12, 0x5B, 0x5C, 0x2D, 0x14)


def modifiersDown():
    """True while a modifier key is physically held down.

    A command on a chord such as NVDA+shift+E runs while its keys are still down, and a key it
    sends then reaches the plug-in with them attached. JUCE answers a plain Enter and ignores
    shift+Enter, which is how NVDA+shift+I, the same command until 0.13.0, failed to open the
    microphone list (2026-11-09)."""
    try:
        return any(_user32.GetAsyncKeyState(key) & 0x8000 for key in _HELD_KEYS)
    except Exception:
        return False


def _setCursorPos(x, y):
    ctypes.windll.user32.SetCursorPos(int(x), int(y))


def _mouseEvent(flags):
    ctypes.windll.user32.mouse_event(flags, 0, 0, 0, 0)


def _pause(seconds):
    """A wait of a few hundredths of a second, inside one step of a double click. Everything
    else here waits on a timer; see AmpController.doubleClickElement for why this does not."""
    time.sleep(seconds)


# A double click, in seconds: how long each press lasts and how long the button is up between
# the two. The X generation counts two presses as a double click when they start within its own
# doubleClickTimeout, 200 ms (configuration.xml inside the Petrucci's VST3); these start 90 ms
# apart.
DOUBLE_CLICK_PRESS_S = 0.03
DOUBLE_CLICK_GAP_S = 0.06


def _windowAtPoint(x, y):
    try:
        hwnd = _user32.WindowFromPoint(_Point(int(x), int(y)))
        return int(hwnd) if hwnd else None
    except Exception:
        return None


def _nearestCaption(captions, rect):
    """The caption printed immediately to the left of a control, if there is one."""
    best = None
    bestDistance = None
    for name, left, top in captions:
        if left >= rect[0]:
            continue
        distance = abs(top - rect[1])
        if distance > 40 or (bestDistance is not None and distance >= bestDistance):
            continue
        bestDistance, best = distance, name
    return best


def _uiaClient():
    try:
        return UIAHandler.handler.clientObject
    except Exception:
        return None


def _rangeValueInterface():
    iface = getattr(UIAHandler, "IUIAutomationRangeValuePattern", None)
    if iface is not None:
        return iface
    try:
        from comInterfaces.UIAutomationClient import IUIAutomationRangeValuePattern
        return IUIAutomationRangeValuePattern
    except Exception:
        return None


def setRangeValue(element, newValue):
    """Sets a slider's value through its RangeValue pattern, for a control that does not have
    focus (AmpSlider.ampSetValue does the same for the one that has). True when the call went
    through; the caller clamps."""
    interface = _rangeValueInterface()
    if interface is None or element is None:
        return False
    try:
        pattern = element.GetCurrentPattern(PATTERN_RANGE_VALUE)
        if not pattern:
            return False
        pattern.QueryInterface(interface).SetValue(float(newValue))
        return True
    except Exception:
        log.debugWarning("neuralAccess: SetValue failed", exc_info=True)
        return False


def _prop(element, propertyId, default=None):
    try:
        value = element.GetCurrentPropertyValue(propertyId)
    except Exception:
        return default
    return default if value is None else value


def focusedElement():
    """The UI Automation element holding keyboard focus, anywhere on the system."""
    client = _uiaClient()
    if client is None:
        return None
    try:
        return client.GetFocusedElement()
    except Exception:
        return None


def textPatternText(element):
    """The text a control exposes through the Text pattern, or None.

    The X generation's readout displays are Edit controls that carry their display text only
    here - no Value pattern, no Name.
    """
    if element is None:
        return None
    interface = getattr(UIAHandler, "IUIAutomationTextPattern", None)
    try:
        pattern = element.GetCurrentPattern(PATTERN_TEXT)
        if not pattern:
            return None
        if interface is not None:
            pattern = pattern.QueryInterface(interface)
        text = pattern.DocumentRange.GetText(-1)
        return text.strip() if text else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# The profile: everything one amplifier knows
# ---------------------------------------------------------------------------

class AmpProfile(object):
    """The vocabulary, calibration and layout of one amplifier.

    The base class answers every question with "nothing special", so a new amplifier can start
    as nothing but a marker string and grow hooks as its quirks are discovered. Every method that
    needs to ask the editor something receives the controller, which owns the tree searches and
    the caches.
    """

    # A short identifier used in log lines.
    id = "amp"
    # How the amplifier is spoken of in messages.
    displayName = "amplifier"
    # Strings that identify this editor's window: matched against the UIA provider description
    # and the root element's Name. Exact and survives a rebuild, unlike the window class hash.
    markers = ()
    # Spellings of the standalone's executable name, registered against the shared app module.
    executableNames = ()
    # Model prefixes stripped from HelpText labels; the prefix in use also identifies the model.
    ampPrefixes = ()
    # Rewrites that make a raw label read naturally in speech.
    friendlyNames = {}
    # Spoken after the plugin's own display text, which carries a number but rarely its unit.
    unitSuffixes = {}
    # Sliders whose value is a short list of named positions.
    enumValues = {}
    # Knobs voiced on the amplifier's own 0 to 10 dial scale rather than as a percentage.
    ampDialKnobs = frozenset()
    # Buttons that ignore Enter, Space and UIA Invoke and need a real cursor click.
    clickOnlyButtons = frozenset()
    # Buttons whose action cannot be undone and which the plugin fires with no confirmation of
    # its own: {identifier: (what it does, what to say once it has been done)}. Enter on one of
    # these warns; Enter on it again within CONFIRM_WINDOW_S carries it out. A button the plugin
    # does ask about does not belong here - that would be two questions. They are NOT blocked - a
    # sighted user can click them in one motion, so refusing the keyboard entirely would leave
    # this add-on's user with less access than everyone else, which is the opposite of the job.
    confirmActions = {}
    # Labels shared by several controls, with the distinct names to use, left to right.
    duplicateHelpNames = {}
    # Pixel calibration for switches whose position the tree does not expose:
    # label -> (dx, dy, threshold, (lowWord, highWord)[, (boxW, boxH)[, PROBE_OF_PEAK]]), offsets
    # and the optional sample box as client fractions. With PROBE_OF_PEAK the threshold is a
    # share, 0 to 1, of the brightest point of the control's own rectangle.
    switchProbes = {}
    # The sample box, as client fractions.
    switchProbeSize = (0.0120, 0.0163)
    # Switches read by where the handle's bright metal tip is, which needs no threshold:
    # label -> ((x0, y0), (x1, y1), box, (word0, word1)). The two spots and the box size are
    # fractions of the switch's own rectangle; word0 is said when spot 0 is the brighter one.
    tipProbes = {}
    # Stops in the application's own Tab ring that do nothing - lamps, dimming layers. Tab and
    # Shift+Tab move straight past them, silently, and focus never lands on them on purpose.
    decorativeNames = frozenset()
    # What a menu is called, by the heading printed at its top, in capitals as the amplifier
    # prints it: {"PRESETS": "Presets"}. See menuName.
    menuNames = {}

    def menuName(self, heading):
        """What to call one of this amplifier's menus when its window takes focus.

        The window is named after the plug-in ("Archetype Petrucci X, window"), which says
        nothing about what has just opened. heading is the name of the menu's first item, which
        is the heading where the menu has one. A menu that starts with anything else - a
        folder's list of presets starts with a preset - gets no name and is announced as a
        bare "menu".
        """
        return self.menuNames.get((heading or "").strip().upper(), "")

    def readsSwitchState(self, label):
        """True when this amp knows how to read the switch with this label off the screen."""
        return bool(label) and (label in self.switchProbes or label in self.tipProbes)
    # HelpText prefixes marking one-of-N button groups (amp type, cab type).
    groupPrefixes = ()
    # The section views, in the order their buttons appear.
    sectionNames = ()
    # HelpText of the audio settings button in the standalone, or None when the amp has none.
    audioSettingsButtonHelp = None

    # ---------- vocabulary ----------

    def stripPrefix(self, text):
        """Returns (labelWithoutAmpPrefix, ampPrefixOrNone)."""
        for prefix in self.ampPrefixes:
            if text.startswith(prefix):
                return text[len(prefix):], prefix.strip()
        return text, None

    def friendlyLabel(self, helpText):
        label, _amp = self.stripPrefix(helpText)
        return self.friendlyNames.get(label, label)

    def positionalLabel(self, obj, controller):
        """Names a control that carries neither a Name nor a HelpText. Profile layout knowledge."""
        return ""

    def roleOverride(self, obj):
        """A better role for a control NVDA would otherwise call unknown, or None."""
        return None

    def needsClick(self, obj):
        """True for controls that only respond to a real cursor click."""
        return False

    def confirmKey(self, obj):
        """The confirmActions entry this control matches, or None.

        Matched against the application's own Name first and the positional label second, so it
        covers both generations: the X generation names these buttons itself, the Mesa
        generation leaves them unnamed and this add-on supplies the label.
        """
        if not self.confirmActions:
            return None
        native = (_prop(obj.UIAElement, PROP_NAME, "") or "").strip().upper()
        if native in self.confirmActions:
            return native
        label = obj.ampLabel or ""
        return label if label in self.confirmActions else None

    def decorateName(self, obj, base):
        """A final chance to dress a control's spoken name with context."""
        return base

    def dropPressedState(self, obj):
        """True when the control's UIA toggle state must not be spoken.

        The X generation's buttons expose a Toggle pattern whose state is a latch that flips on
        every activation and never reflects the actual selection - announcing it would tell the
        user the opposite of the truth half the time.
        """
        return False

    def suppressValue(self, obj):
        """True when the control's UIA Value string must not be spoken.

        The X generation's buttons mirror their toggle latch as a Value of "Off" or "On", which
        is as meaningless as the latch itself.
        """
        return False

    # ---------- values ----------

    def formatValue(self, label, raw, minimum, maximum, unitText=None):
        """Turns a slider value into something worth listening to."""
        if unitText:
            return unitText
        enum = self.enumValues.get(label)
        if enum:
            index = int(round(raw))
            if 0 <= index < len(enum):
                return enum[index]
            return str(index)
        span = (maximum - minimum) or 1.0
        if maximum <= 1.0 and minimum >= 0.0:
            if label.endswith("Active"):
                return "on" if raw >= 0.5 else "off"
            if label in self.ampDialKnobs:
                return "%.1f" % (raw * 10.0)
            return "%d percent" % int(round(raw * 100.0))
        # Small integer ranges are positional switches.
        if span <= 4 and float(maximum).is_integer():
            return str(int(round(raw)))
        return "%.2f" % raw

    def dialPosition(self, obj, raw, minimum, maximum):
        """Where this knob's pointer points, in words ("2 o'clock"), or "" for a control that
        has no pointer worth reading.

        A knob with nothing printed round it and no display shows a sighted user its pointer
        and nothing else, and that is what a tutorial quotes: "gain at 2 o'clock". The words
        are said after the knob's value when focus lands on it, and after an arrow key only
        when they have changed (AmpSlider._get_value, AmpObject._adjustFocused). The value
        itself stays what formatValue makes of it. See clockPosition.
        """
        return ""

    # ---------- selections and states ----------

    def isSelected(self, obj, controller, prefix):
        """For a one-of-N button: is this the live one? None when it cannot be determined."""
        winner = controller.selectedInGroup(prefix)
        return None if winner is None else (winner == obj.ampHelpText)

    def selectedState(self, obj, controller):
        """Selected state for a one-of-N control that carries no group HelpText, or None.

        Lets a profile present controls like amp model selectors as radio buttons even when the
        tree gives them no vocabulary at all.
        """
        return None

    def stateLabel(self, obj):
        """The key a control's switch probe is registered under, or an empty string.

        The Mesa generation keys probes on the HelpText label; amps whose switches carry no
        HelpText at all key them on the positional name instead.
        """
        helpText = obj.ampHelpText
        if helpText:
            return self.stripPrefix(helpText)[0]
        return ""

    def readoutText(self, controller, obj):
        """The display text mirroring a slider, if the amp draws one."""
        return controller.readoutFor(obj.ampHelpText)

    def activeAmpModel(self, controller):
        """Which amplifier model is live, or None when it cannot be determined."""
        return None

    def switchAnchor(self, controller, label, rect):
        """The rectangle a switch's pixel probe is measured from. Usually the control's own."""
        return rect

    def probeDimming(self, controller, label):
        """What a switch probe's threshold is multiplied by before the reading is held against
        it: 1.0, or less where the amplifier is drawing this switch darker than usual - the
        Mesa Boogie dims a whole view while its section is switched off, and a lit lamp there
        reads darker than an unlit one does elsewhere."""
        return 1.0

    # ---------- navigation and actions ----------

    def entryElement(self, controller, hwnd):
        """The control to land on when the editor is handed keyboard focus, or None for the
        generic topmost leftmost search."""
        return None

    def switchSection(self, controller, index):
        """Shows the numbered section view."""
        ui.message("View switching is not available on this amplifier.")

    def switchAmpModel(self, controller, direction):
        """Moves to the previous or next amplifier model, if the amp has more than one."""
        ui.message("Amp switching is not available on this amplifier.")

    def tabPatch(self, obj, controller, backwards):
        """A chance to splice controls the application leaves out of its own Tab ring.

        Returns True when focus was moved; False passes the key to the application.
        """
        return False

    def passedOver(self, obj):
        """True for a stop that Tab and Shift+Tab move straight past (see
        AmpController.skipDecorative). By default the stops named in decorativeNames."""
        return (getattr(obj, "ampLabel", "") or "") in self.decorativeNames

    def enterPatch(self, obj, controller):
        """A chance to take Enter over before anything else is done with it.

        Returns True when the profile has dealt with the press; False leaves it to the usual
        handling of the focused control.
        """
        return False

    def noteGesture(self, gesture):
        """Told every key NVDA is about to act on, in any application (see core.noteGesture).
        Only for dropping state a key press makes stale; it must return at once otherwise."""
        pass

    def presetStep(self, controller, direction):
        """Loads the previous or next preset. Returns True when the action was taken (any
        speech is the profile's job), False when the preset controls cannot be reached."""
        return False

    def tuner(self, controller):
        """Toggles the tuner.

        Returns True when the button was pressed and a generic confirmation should be spoken,
        False when it could not be reached, or a string when the profile speaks for itself - the
        string is said if it is not empty.
        """
        return False

    def tunerReading(self, controller):
        """What an open tuner shows, for the tuner watcher.

        None when no tuner display is open, which also ends the watch. Otherwise a tuple
        (note, display, inTune): the note as printed or None while nothing rings, the readout
        text, and the amplifier's own in-tune verdict as True, False or None for unknown.
        """
        return None

    def onFocus(self, controller, obj):
        """Called whenever one of this amplifier's controls gains focus."""
        pass

    def afterClick(self, controller, obj):
        """Called once Enter has been turned into a click on a control, before the click lands.

        Anything read here still describes the state before the press.
        """
        pass

    # The single keys. Each hook answers True when it took the key - whatever is then said is
    # the profile's job - and False when the amplifier has no such thing, which the key says.

    def quickToggle(self, controller, which):
        """G and D: flips the named switch ("gate", "doubler") and says its new state, leaving
        focus where it is."""
        return False

    def jumpTo(self, controller, which):
        """R: puts focus on the named control ("transpose") and leaves it there."""
        return False

    def openPresetList(self, controller):
        """P: puts focus on the preset button and presses it."""
        return False

    def stepModule(self, controller, direction):
        """The brackets: puts focus on the first control of the previous or next module of the
        view that is showing."""
        return False

    def midiMappings(self, controller):
        """Control+M: opens or closes the amplifier's MIDI mappings window."""
        return False

    def contextMenu(self, controller):
        """M: opens the menu the amplifier has for the control that has focus, the one a
        mouse user gets with a right click."""
        return False

    def levelCheck(self, controller):
        """L: starts a level check, or ends the one that is running and says what the input
        and output meters showed."""
        return False

    def switchCabModel(self, controller, direction):
        """C: selects the next cabinet, going round, on an amplifier whose cabinet can be
        chosen apart from its amp."""
        return False

    def ampCabLink(self, controller):
        """Control+A: links or unlinks the amplifier and the cabinet and says which it is now,
        leaving focus where it is."""
        return False

    def sectionState(self, controller, index):
        """Shift+number: says the section of that number and whether it is switched on."""
        return False

    def sectionToggle(self, controller, index):
        """Control+number: switches the section of that number off or on and says its new
        state, leaving focus and the view where they are."""
        return False

    def loadImpulseResponse(self, controller, focus, processID):
        """The NVDA+shift+E command: start loading a custom impulse response file. Returns a
        message to speak, or None when the profile has started something that speaks for
        itself."""
        return "Loading impulse responses is not available on this amplifier."


# ---------------------------------------------------------------------------
# Recognising an editor's window, wherever it turns up
# ---------------------------------------------------------------------------

# Registered amplifier profiles, in the order they are tried.
PROFILES = []


def registerProfile(profile):
    if profile not in PROFILES:
        PROFILES.append(profile)
        log.info("neuralAccess: registered profile %r (%s)" % (profile.id, profile.displayName))


# Window handle -> profile, or False for "looked, not one of ours". Consulted for every object
# NVDA builds anywhere, so it has to stay a dictionary lookup.
_windowProfiles = {}
_amps = {}
# Menu and open list windows, which are no editor: window -> the profile of their amplifier.
_menuProfiles = {}
CT_MENUITEM = 50011


def _className(hwnd):
    try:
        buffer = ctypes.create_unicode_buffer(256)
        _user32.GetClassNameW(hwnd, buffer, 256)
        return buffer.value or ""
    except Exception:
        return ""


def _pruneWindowCache():
    if len(_windowProfiles) < 64:
        return
    for hwnd in [h for h in _windowProfiles if not _user32.IsWindow(h)]:
        _windowProfiles.pop(hwnd, None)
        _amps.pop(hwnd, None)
        _menuProfiles.pop(hwnd, None)


def profileForWindow(hwnd):
    """The profile of the amplifier this window belongs to, or None.

    Answered from a per window cache, because it is consulted for every object NVDA builds. The
    cheap window class test comes first and settles the question for everything that is not JUCE,
    which is very nearly everything; only a JUCE window costs a UI Automation call, and only once.
    """
    if not hwnd:
        return None
    known = _windowProfiles.get(hwnd)
    if known is not None:
        return known or None
    result = None
    if _className(hwnd).startswith(JUCE_CLASS_PREFIX):
        client = _uiaClient()
        if client is not None:
            try:
                element = client.ElementFromHandle(hwnd)
            except Exception:
                element = None
            if element is not None:
                description = _prop(element, PROP_PROVIDER_DESCRIPTION, "") or ""
                name = _prop(element, PROP_NAME, "") or ""
                for profile in PROFILES:
                    if any((marker in description) or (marker in name)
                           for marker in profile.markers):
                        result = profile
                        break
                # A combo box's open list or a menu is a top level window of its own, from the
                # same plug-in module, so the provider description matches it too. Taken for an
                # editor it became a second, "standalone" amplifier (Petrucci X, 2026-11-08).
                # JUCE titles these windows "menu" and gives them a menu root.
                if result is not None and (windowTitle(hwnd) == "menu"
                                           or _prop(element, PROP_CONTROL_TYPE) == CT_MENU):
                    # Remembered as that amplifier's menu, so its window can be given a name.
                    _menuProfiles[hwnd] = result
                    result = None
    _pruneWindowCache()
    _windowProfiles[hwnd] = result if result is not None else False
    if result is not None:
        log.debug("neuralAccess: window %r is a %s editor (hosted=%r)"
                  % (hwnd, result.displayName, isHostedWindow(hwnd)))
    return result


def isAmpWindow(hwnd):
    """True when this window is one of our amplifiers' editors, standalone or hosted."""
    return profileForWindow(hwnd) is not None


def menuProfileForWindow(hwnd):
    """The profile of the amplifier whose menu or open list this window is, or None.

    Windows hands a closed menu's handle to the next window that asks for one, so the title is
    looked at again each time rather than trusted from the first look.
    """
    if not hwnd:
        return None
    profileForWindow(hwnd)
    profile = _menuProfiles.get(hwnd)
    if profile is not None and windowTitle(hwnd) != "menu":
        _menuProfiles.pop(hwnd, None)
        _windowProfiles.pop(hwnd, None)
        return None
    return profile


def firstMenuItemName(element):
    """The Name of the first menu item under a menu window's root element, or ""."""
    client = _uiaClient()
    if client is None or element is None:
        return ""
    try:
        item = element.FindFirst(TREESCOPE_DESCENDANTS,
                                 client.CreatePropertyCondition(PROP_CONTROL_TYPE, CT_MENUITEM))
    except Exception:
        return ""
    # A miss is a null COM pointer, which is falsy but not None.
    return (_prop(item, PROP_NAME, "") or "") if item else ""


def rootWindow(hwnd):
    """The top level window a window belongs to, or None."""
    if not hwnd:
        return None
    try:
        root = _user32.GetAncestor(hwnd, GA_ROOT)
    except Exception:
        return None
    return int(root) if root else None


def childWindows(root):
    """Every descendant window of a window, in enumeration order."""
    found = []

    def visit(hwnd, _lparam):
        if hwnd:
            found.append(int(hwnd))
        return 1

    if not root:
        return found
    try:
        _user32.EnumChildWindows(root, _ENUM_CHILD_PROC(visit), None)
    except Exception:
        log.debugWarning("neuralAccess: could not enumerate child windows", exc_info=True)
    return found


def isHostedWindow(hwnd):
    """True when the editor is a child window inside a DAW rather than an application of its own.

    The standalone's editor is its own top level window. Inside a host it is a child, wrapped by
    whatever window the host parents plug-in editors into - in REAPER a reaperPluginHostWrapProc
    inside the FX dialog. That difference is what decides whether focus may be taken automatically
    when the window comes forward: in the standalone the whole window is the amplifier, but in a
    host the user legitimately wants to reach the host's own controls.
    """
    root = rootWindow(hwnd)
    return root is not None and root != int(hwnd)


def findAmpWindow(root):
    """An editor window at or inside the given top level window, or None."""
    if not root:
        return None
    if isAmpWindow(root):
        return root
    for child in childWindows(root):
        if isAmpWindow(child):
            return child
    return None


def focusFirstHostControl(hostHwnd, ampHwnd):
    """Hands focus to the first ordinary control of the host window.

    The last resort way out of an editor, used only when there is nothing remembered to go back
    to. The editor's own Tab ring is cyclic and has no exit, so without something like this a
    plug-in window can be entered and never left from the keyboard.
    """
    client = _uiaClient()
    if client is None or not hostHwnd:
        return False
    for child in childWindows(hostHwnd):
        if child == ampHwnd or not _user32.IsWindowVisible(child):
            continue
        if _className(child).startswith(JUCE_CLASS_PREFIX):
            continue
        try:
            element = client.ElementFromHandle(child)
        except Exception:
            continue
        if element is None or not _prop(element, PROP_IS_KEYBOARD_FOCUSABLE, False):
            continue
        try:
            element.SetFocus()
        except Exception:
            continue
        log.debug("neuralAccess: stepped out to the host's window %r" % (child,))
        return True
    return False


# ---------------------------------------------------------------------------
# One controller per editor window
# ---------------------------------------------------------------------------

def ampForWindow(hwnd, processID=0):
    """The controller for an editor window, created on first use.

    Keyed on the window rather than on the process, so two instances of the plug-in loaded into
    one host each get their own caches and their own geometry instead of quietly sharing one.
    """
    if not hwnd:
        return None
    controller = _amps.get(hwnd)
    if controller is None:
        profile = profileForWindow(hwnd)
        if profile is None:
            return None
        controller = AmpController(hwnd, profile, processID)
        _amps[hwnd] = controller
    return controller


def ampForObject(obj):
    try:
        return ampForWindow(obj.windowHandle, obj.processID)
    except Exception:
        return None


class AmpController(object):
    """Everything that has to ask the editor a question or read it off the screen.

    One of these exists per editor window. It holds no NVDA plumbing at all, so the app module and
    the global plugin can both drive it. Amp-specific questions are put to self.profile.
    """

    def __init__(self, hwnd, profile, processID=0):
        self._hwnd = hwnd
        self.profile = profile
        self.processID = processID
        self._geometryCache = {}
        self._readoutCache = None
        self._readoutStamp = 0.0
        self._lastGoodReadouts = {}
        self._positionalCache = {}
        self._stateCache = {}
        self._lastFocusElement = None
        self._entryPending = False
        self._rowNames = {}
        self._ocrPending = set()
        self._panelCache = None
        self._panelStamp = 0.0
        self._tunerWatching = False
        self._tunerAnnouncer = tuning.TunerAnnouncer()
        # (backwards, when, how many decorative stops passed over since the key was pressed)
        self._lastTab = None
        # (until when, rectangles): focus changes the add-on makes itself and speaks for
        self._hushedFocus = None
        log.info("neuralAccess: attached %s to editor window %r in process %s (hosted=%r)"
                 % (profile.id, hwnd, processID, isHostedWindow(hwnd)))

    def noteTab(self, backwards):
        """Remembers a Tab or Shift+Tab the user pressed inside the editor."""
        self._lastTab = (backwards, time.time(), 0)

    def skipDecorative(self, obj):
        """Passes over a decorative stop that Tab has just landed on, in the same direction.

        True when the stop was skipped - the caller then announces nothing. Focus arriving any
        other way (a click, a view switch) is left alone, so a lamp is never jumped over unasked.
        """
        if self._lastTab is None or not self.profile.passedOver(obj):
            return False
        backwards, when, skipped = self._lastTab
        gap = time.time() - when
        if gap > DECORATIVE_SKIP_S or skipped >= DECORATIVE_SKIP_MAX:
            # Said in the log, so that a stop Tab should have passed over can be explained
            # (Hadi's EQ, 2026-11-11: Shift+Tab stopped on value boxes and on HPF :).
            log.info("neuralAccess: a passed-over stop is stopped on, %r: %s" % (
                getattr(obj, "ampLabel", None) or getattr(obj, "name", None),
                "%.2f s since the last Tab" % gap if gap > DECORATIVE_SKIP_S
                else "%d passed over in a row" % skipped))
            return False
        self._lastTab = (backwards, time.time(), skipped + 1)
        # As if Tab had been pressed again on this stop: the profile's own splices in the ring
        # come before the application's Tab, as they do for a key the user presses. Without
        # that, a stop spliced in after a passed-over one could no longer be reached.
        try:
            if self.profile.tabPatch(obj, self, backwards):
                return True
        except Exception:
            log.debugWarning("neuralAccess: the ring's splices failed on a passed-over stop", exc_info=True)
        KeyboardInputGesture.fromName("shift+tab" if backwards else "tab").send()
        return True

    def hushFocus(self, rects, seconds, everything=False):
        """For this many seconds, a focus change onto a control at one of these rectangles is
        not announced.

        For commands that have to move focus to get their work done and then put it back: a
        click hands keyboard focus to the button clicked (seen 2026-11-10: "focus 'GATE, on'"
        0.19 s after the gate key). The command says what it did; hearing the button and then
        the control focus went back to would bury that. Anything else that takes focus in the
        meantime is announced as usual.

        everything keeps every focus change in this amplifier quiet, for a command that has to
        go through another view and come back: what takes focus on the way cannot be named
        beforehand. Each call takes the place of the one before, so a call that names
        rectangles ends it.
        """
        self._hushedFocus = (time.time() + seconds,
                             [tuple(rect[:4]) for rect in rects if rect and len(rect) >= 4],
                             bool(everything))

    def focusIsHushed(self, obj):
        """True when this focus change is one hushFocus asked to keep quiet."""
        hushed = getattr(self, "_hushedFocus", None)
        if not hushed:
            return False
        deadline, rects, everything = hushed
        if time.time() > deadline:
            self._hushedFocus = None
            return False
        if everything:
            return True
        try:
            location = obj.location
            rect = (location.left, location.top, location.width, location.height)
        except Exception:
            return False
        return any(all(abs(a - b) <= 2 for a, b in zip(rect, wanted)) for wanted in rects)

    @property
    def hwnd(self):
        return self._hwnd

    @property
    def hosted(self):
        return isHostedWindow(self._hwnd)

    def hostWindow(self):
        """The host's top level window, or None when this is the standalone."""
        return rootWindow(self._hwnd) if self.hosted else None

    # ---------- the tree ----------

    def _mainElement(self, hwnd=None):
        client = _uiaClient()
        if client is None:
            return None
        if not hwnd:
            hwnd = self._hwnd
        if not hwnd:
            try:
                hwnd = api.getFocusObject().windowHandle
            except Exception:
                hwnd = None
        if not hwnd:
            return None
        try:
            return client.ElementFromHandle(hwnd)
        except Exception:
            return None

    def clientGeometry(self, hwnd=None):
        """(left, top, width, height) of an editor window, in screen coordinates.

        Cached per window: the audio settings dialog and the main window are both asked about.
        """
        now = time.time()
        key = hwnd or self._hwnd
        cached = self._geometryCache.get(key)
        if cached and (now - cached[0]) < 2.0:
            return cached[1]
        element = self._mainElement(hwnd)
        if element is None:
            return None
        try:
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4:
                return None
            left, top, width, height = rect[0], rect[1], rect[2], rect[3]
            if width <= 0 or height <= 0:
                return None
            geometry = (float(left), float(top), float(width), float(height))
            self._geometryCache[key] = (now, geometry)
            return geometry
        except Exception:
            return None

    def findElements(self, controlType=None, helpText=None, name=None, hwnd=None, root=None):
        client = _uiaClient()
        if root is None:
            root = self._mainElement(hwnd)
        if client is None or root is None:
            return []
        try:
            conditions = []
            if controlType is not None:
                conditions.append(client.CreatePropertyCondition(PROP_CONTROL_TYPE, controlType))
            if helpText is not None:
                conditions.append(client.CreatePropertyCondition(PROP_HELP_TEXT, helpText))
            if name is not None:
                conditions.append(client.CreatePropertyCondition(PROP_NAME, name))
            if not conditions:
                condition = client.CreateTrueCondition()
            else:
                condition = conditions[0]
                for extra in conditions[1:]:
                    condition = client.CreateAndCondition(condition, extra)
            with Timed("a search of the editor (type %r, help %r, name %r)" % (controlType, helpText, name)):
                found = root.FindAll(TREESCOPE_DESCENDANTS, condition)
                return [found.GetElement(i) for i in range(found.Length)]
        except Exception:
            # At info level while the view-recognition glitch of 2026-11-09 is open: a search
            # that fails here returns nothing, and "nothing found" reads as the wrong view.
            log.info("neuralAccess: findElements failed", exc_info=True)
            return []

    def _collectReadouts(self):
        """Every unit-bearing display value in one tree search, keyed by the knob it mirrors.

        These Edit controls are volatile: the Value property intermittently comes back empty
        even though the control is alive, so Name is used as a second source.
        """
        readouts = {}
        elements = self.findElements(controlType=CT_EDIT)
        for element in elements:
            helpText = _prop(element, PROP_HELP_TEXT, "")
            if not helpText:
                continue
            # These displays are volatile: a control that is alive and on screen intermittently
            # answers with an empty string. Asking twice clears up most of it.
            text = None
            for _attempt in range(2):
                for propertyId in (PROP_VALUE_VALUE, PROP_NAME):
                    text = _prop(element, propertyId)
                    if text:
                        break
                if text:
                    break
            if not text:
                continue
            suffix = self.profile.unitSuffixes.get(helpText)
            readouts[helpText] = "%s %s" % (text, suffix) if suffix else text
        log.debug("neuralAccess: %d edit controls gave %d readouts" % (len(elements), len(readouts)))
        # Anything still missing keeps its last known reading. A moment-old value in the right
        # units beats falling back to speaking a bare percentage of the knob's travel.
        self._lastGoodReadouts.update(readouts)
        return dict(self._lastGoodReadouts)

    def readoutFor(self, helpText):
        """The unit-bearing display text that mirrors a knob, if the app draws one.

        Backed by a short-lived cache. Every cross-process UI Automation call happens on NVDA's
        main thread, so searching the tree once per knob is enough to trip NVDA's freeze
        watchdog; one search per refresh keeps announcements instant.
        """
        if not helpText:
            return None
        now = time.time()
        if self._readoutCache is None or (now - self._readoutStamp) > 0.5:
            self._readoutCache = self._collectReadouts()
            self._readoutStamp = now
        return self._readoutCache.get(helpText)

    def invalidateReadouts(self):
        self._readoutCache = None

    def _sortedByX(self, elements):
        decorated = []
        for element in elements:
            rect = _prop(element, PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4:
                decorated.append((rect[0], element))
        decorated.sort(key=lambda pair: pair[0])
        return decorated

    def _positionalSweep(self, key, builder):
        """A short-lived cache in front of a positional lookup.

        Every one of these is a full tree search plus a cross-process property read per element,
        all of it on NVDA's main thread, and NVDA asks for a control's name and role several
        times per focus event. Caching the sweep rather than the answer means neighbouring
        controls of the same kind share one search between them. Keyed on the client geometry so
        a resize or a move invalidates it immediately.
        """
        now = time.time()
        geometry = self.clientGeometry()
        cached = self._positionalCache.get(key)
        if cached is not None and cached[0] == geometry and (now - cached[1]) < POSITIONAL_CACHE_TTL:
            return cached[2]
        value = builder()
        self._positionalCache[key] = (geometry, now, value)
        return value

    def invalidatePositional(self):
        self._positionalCache = {}

    def forgetPositional(self, key):
        """Drops one positional lookup, so the next call for it searches the tree afresh."""
        self._positionalCache.pop(key, None)

    def duplicateHelpIndex(self, obj, helpText):
        """Where a control sits, left to right, among the controls sharing its HelpText."""
        ordered = self._sortedByX(self.findElements(controlType=CT_BUTTON, helpText=helpText))
        try:
            targetLeft = obj.location.left
        except Exception:
            return None
        for index, (left, _element) in enumerate(ordered):
            if abs(left - targetLeft) < 3:
                return index
        return None

    # ---------- keyboard focus entry ----------
    #
    # The editor takes keyboard focus without handing it to any component, and its own Tab
    # handling needs a focused component to traverse from. Until something inside is focused, the
    # standalone's Tab does nothing at all and a host's Tab walks the host's own controls instead.
    # Everything below exists to put focus on a real control inside the editor.

    def _focusedElement(self):
        return focusedElement()

    def isFocusDeadEnd(self, element):
        """True when focus is on one of this editor's windows, or a container filling one."""
        if element is None:
            return False
        if self.processID and _prop(element, PROP_PROCESS_ID) != self.processID:
            return False
        controlType = _prop(element, PROP_CONTROL_TYPE)
        if controlType in (CT_WINDOW, CT_PANE):
            return True
        if controlType in ENTRY_CONTROL_TYPES:
            return False
        # The root component covers the whole client area, and landing there is just as dead: it
        # has no siblings, so the app has nothing to move focus to. Inside a host this is the
        # usual case rather than the exotic one - the editor's root is a Custom control named
        # after the amplifier, so a check on the role alone would never catch it.
        geometry = self.clientGeometry(_prop(element, PROP_NATIVE_WINDOW_HANDLE) or self._hwnd)
        rect = _prop(element, PROP_BOUNDING_RECT)
        if not geometry or not rect or len(rect) < 4:
            return False
        return rect[2] >= geometry[2] * 0.9 and rect[3] >= geometry[3] * 0.9

    def elementIsInside(self, element):
        """True when a UIA element sits within this editor's client area.

        A control reports no native window handle of its own, so there is nothing to compare
        against the editor's window; geometry containment is the honest test. Host controls do
        not overlap the editor's client area - a DAW's FX chrome sits above and beside it.
        """
        if element is None:
            return False
        geometry = self.clientGeometry()
        rect = _prop(element, PROP_BOUNDING_RECT)
        if not geometry or not rect or len(rect) < 4:
            return False
        left, top, width, height = geometry
        return (rect[0] >= left - 2 and rect[1] >= top - 2
                and (rect[0] + rect[2]) <= (left + width + 2)
                and (rect[1] + rect[3]) <= (top + height + 2))

    def focusIsInside(self):
        """True when whatever holds keyboard focus is one of this editor's own controls.

        Used to confirm a deliberate step-in worked, where "focus is no longer on a dead end" is
        no use - before stepping in, focus was on one of the host's controls, which is not a dead
        end of ours either.
        """
        element = focusedElement()
        if element is None:
            return False
        if self.processID and _prop(element, PROP_PROCESS_ID) != self.processID:
            return False
        return self.elementIsInside(element)

    def _stillUsable(self, element):
        """A control destroyed by a view change stops answering; that is how we spot one."""
        if element is None:
            return False
        try:
            if _prop(element, PROP_CONTROL_TYPE) is None:
                return False
            rect = _prop(element, PROP_BOUNDING_RECT)
            return bool(rect) and len(rect) >= 4 and rect[2] > 0 and rect[3] > 0
        except Exception:
            return False

    def entryElement(self, hwnd=None):
        """The control to land on when a window has to be handed keyboard focus.

        The profile chooses for the editor itself, so entering always announces the same familiar
        place. Dialogs get their topmost, leftmost control.
        """
        if not hwnd or hwnd == self._hwnd:
            element = self.profile.entryElement(self, self._hwnd)
            if element is not None:
                return element
        best = None
        bestKey = None
        for controlType in ENTRY_CONTROL_TYPES:
            for element in self.findElements(controlType=controlType, hwnd=hwnd):
                rect = _prop(element, PROP_BOUNDING_RECT)
                if not rect or len(rect) < 4 or rect[2] <= 0:
                    continue
                key = (round(rect[1]), round(rect[0]))
                if bestKey is None or key < bestKey:
                    bestKey, best = key, element
        return best

    def trySetFocus(self, element):
        if element is None:
            log.debug("neuralAccess: focus entry found no control to land on")
            return False
        try:
            element.SetFocus()
            log.debug("neuralAccess: focus entry moved to %r at %r"
                      % (_prop(element, PROP_HELP_TEXT, ""), _prop(element, PROP_BOUNDING_RECT)))
            return True
        except Exception:
            log.debugWarning("neuralAccess: SetFocus failed", exc_info=True)
            return False

    def scheduleFocusEntry(self, attempt=0, force=False):
        if self._entryPending:
            return
        self._entryPending = True
        core.callLater(FOCUS_ENTRY_DELAY_MS, self.enterWindow, attempt, force)

    def enterWindow(self, attempt=0, force=False):
        """Puts focus on a real control inside the editor.

        Returns True when it took the job on, and False when entry was not needed because a
        control inside the editor already holds keyboard focus. Callers rely on that answer:
        NVDA's idea of the focused object lags behind the editor's, because activating the window
        raises a focus event for the editor's root and NVDA keeps it, so "the object NVDA is
        standing on is a dead end" is not the same question as "the editor cannot traverse".

        force is used by the deliberate step-in gesture: focus is then sitting on one of the
        host's own controls rather than on a dead end of ours, so the usual guard would refuse.
        """
        self._entryPending = False
        focused = self._focusedElement()
        if not force and not self.isFocusDeadEnd(focused):
            log.debug("neuralAccess: focus entry not needed, focus is already on a control")
            return False
        hwnd = self._hwnd
        if not force:
            hwnd = _prop(focused, PROP_NATIVE_WINDOW_HANDLE) or self._hwnd
        log.debug("neuralAccess: focus entry attempt %d, window %r, editor window %r"
                  % (attempt, hwnd, self._hwnd))
        remembered = self._lastFocusElement if self._stillUsable(self._lastFocusElement) else None
        if remembered is not None:
            self.trySetFocus(remembered)
            # Focus can be refused by a control that outlived its section, so check once more.
            core.callLater(FOCUS_RETRY_DELAY_MS, self._confirmEntry, hwnd, attempt, force)
            return True
        if self.trySetFocus(self.entryElement(hwnd)):
            return True
        if attempt + 1 < FOCUS_ENTRY_ATTEMPTS:
            # Straight after launch the tree can still be filling in; give it another moment.
            core.callLater(FOCUS_RETRY_DELAY_MS, self.scheduleFocusEntry, attempt + 1, force)
            return True
        return False

    def _confirmEntry(self, hwnd, attempt, force=False):
        if force:
            if self.focusIsInside():
                return
        elif not self.isFocusDeadEnd(self._focusedElement()):
            return
        self._lastFocusElement = None
        if not self.trySetFocus(self.entryElement(hwnd)) and attempt + 1 < FOCUS_ENTRY_ATTEMPTS:
            core.callLater(FOCUS_RETRY_DELAY_MS, self.scheduleFocusEntry, attempt + 1, force)

    def rememberFocus(self, element):
        self._lastFocusElement = element

    # ---------- audio settings channel lists ----------
    #
    # The standalone's audio settings hold the input and output channel lists, the least
    # accessible thing in the Mesa generation: rows named "Row 1" to "Row 4", channel names
    # absent from the tree, no readable tick, arrow keys ignored. Everything below supplies
    # those missing pieces. None of it runs in a plug-in, where there is no audio settings
    # panel at all because the host owns the audio device - the lookups simply find nothing,
    # which is the same answer by a shorter route.

    def channelLists(self):
        """The settings panel's lists, each with its caption and its rows.

        This is one cached sweep on purpose. Naming a row, saying which row it is and moving
        between rows all need the same information, and every one of these lookups is a
        cross-process tree search on NVDA's main thread - doing them per focus event was slow
        enough to make injected keystrokes go missing.
        """
        now = time.time()
        if self._panelCache is not None and (now - self._panelStamp) < 2.0:
            return self._panelCache
        lists = []
        for element in self.findElements(controlType=CT_LIST):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4 or rect[2] <= 0:
                continue
            lists.append({"element": element, "rect": tuple(rect[:4]), "label": None, "rows": []})
        if lists:
            captions = self._panelCaptions()
            for entry in lists:
                entry["label"] = _nearestCaption(captions, entry["rect"])
                entry["rows"] = self.channelRows(entry["element"])
        self._panelCache = lists
        self._panelStamp = now
        return lists

    def invalidatePanel(self):
        self._panelCache = None

    def _panelCaptions(self):
        """Every "Something:" caption in the panel, as (name, left, top)."""
        captions = []
        for element in self.findElements(controlType=CT_TEXT):
            name = _prop(element, PROP_NAME, "")
            if not name or not name.rstrip().endswith(":"):
                continue
            rect = _prop(element, PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4:
                captions.append((name.rstrip().rstrip(":").strip(), rect[0], rect[1]))
        return captions

    def panelLabelFor(self, rect):
        """The caption sitting to the left of a row of the settings panel."""
        return _nearestCaption(self._panelCaptions(), rect)

    def panelControls(self):
        """The settings panel's combo boxes and lists, top to bottom then left to right.

        That is the order the application's own traversal uses, which is how we can step out of a
        channel list and land somewhere sensible.

        Buttons are deliberately left out. The panel is drawn over the top of the plugin, so the
        amplifier's own controls are still sitting underneath it in the tree, at the very same
        coordinates - and any test based on the panel's outline picks them up. Landing on one of
        those is what threw focus clear across the plugin. The panel's own two buttons are still
        reachable with Tab from the neighbouring combo box.
        """
        controls = []
        for controlType in (CT_COMBOBOX, CT_LIST):
            for element in self.findElements(controlType=controlType):
                rect = _prop(element, PROP_BOUNDING_RECT)
                if not rect or len(rect) < 4 or rect[2] <= 0 or rect[0] < -10000:
                    continue
                controls.append((tuple(rect[:4]), element))
        controls.sort(key=lambda item: (item[0][1], item[0][0]))
        return controls

    def channelRows(self, listElement):
        """A list's rows, ordered top to bottom, as (element, rect) pairs."""
        rows = []
        for element in self.findElements(controlType=CT_LISTITEM, root=listElement):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4 and rect[2] > 0:
                rows.append((element, tuple(rect[:4])))
        rows.sort(key=lambda pair: pair[1][1])
        return rows

    def listContaining(self, rowRect):
        """The channel list a row belongs to, or None."""
        if not rowRect:
            return None
        for entry in self.channelLists():
            rect = entry["rect"]
            if (rect[1] - 2) <= rowRect[1] and (rowRect[1] + rowRect[3]) <= (rect[1] + rect[3] + 2) \
                    and (rect[0] - 2) <= rowRect[0] <= (rect[0] + rect[2] + 2):
                return entry
        return None

    def rowIndexIn(self, entry, rowRect):
        for index, (_element, rect) in enumerate(entry["rows"]):
            if abs(rect[1] - rowRect[1]) < 3:
                return index
        return None

    def rowIsTicked(self, rowRect):
        """Reads the row's tick from the screen, because nothing in the tree reports it.

        Returns None when the row cannot be seen at all - a minimised window parks its controls
        at around minus 32000, and a capture of nothing comes back uniformly black. Saying
        "not ticked" in that situation would be a plain lie, so the caller treats None as unknown.
        """
        if not rowRect or rowRect[0] < -10000 or rowRect[1] < -10000:
            return None
        brightest = self.peakBrightness(
            int(rowRect[0]) + TICK_INDICATOR_INSET, int(rowRect[1]) + TICK_INDICATOR_INSET,
            TICK_INDICATOR_WIDTH, int(rowRect[3]) - (TICK_INDICATOR_INSET * 2))
        if brightest is None:
            return None
        return brightest >= TICK_BRIGHTNESS

    def peakBrightness(self, left, top, width, height):
        """The brightest pixel in a box of the screen, as the mean of its channels, or None.

        The peak rather than the mean, for indicators drawn as a small bright mark on a dark
        ground. None when the box cannot be seen: a capture of nothing comes back all black.
        """
        left, top, width, height = int(left), int(top), int(width), int(height)
        if width <= 0 or height <= 0 or left < -10000 or top < -10000:
            return None
        try:
            bitmap = screenBitmap.ScreenBitmap(width, height)
            pixels = bitmap.captureImage(left, top, width, height)
        except Exception:
            log.debugWarning("neuralAccess: could not sample the screen", exc_info=True)
            return None
        brightest = 0
        for y in range(height):
            scanline = pixels[y]
            for x in range(width):
                pixel = scanline[x]
                value = (pixel.rgbRed + pixel.rgbGreen + pixel.rgbBlue) // 3
                if value > brightest:
                    brightest = value
        return brightest or None

    def meanGrey(self, left, top, width, height):
        """Mean grey over a box of the screen, or None if it cannot be seen.

        None means unknown, and callers must keep it unknown. A minimised or covered window parks
        its controls at around minus 32000 and a capture of nothing comes back uniformly black;
        announcing a switch position from that would be inventing one.
        """
        left, top, width, height = int(left), int(top), int(width), int(height)
        if width <= 0 or height <= 0 or left < -10000 or top < -10000:
            return None
        try:
            bitmap = screenBitmap.ScreenBitmap(width, height)
            pixels = bitmap.captureImage(left, top, width, height)
        except Exception:
            log.debugWarning("neuralAccess: could not sample the screen", exc_info=True)
            return None
        total = 0.0
        count = 0
        allBlack = True
        for y in range(height):
            scanline = pixels[y]
            for x in range(width):
                pixel = scanline[x]
                if pixel.rgbRed or pixel.rgbGreen or pixel.rgbBlue:
                    allBlack = False
                total += 0.299 * pixel.rgbRed + 0.587 * pixel.rgbGreen + 0.114 * pixel.rgbBlue
                count += 1
        if not count or allBlack:
            return None
        return total / count

    def screenBox(self, left, top, width, height):
        """A box of the screen read once, to be asked about one point at a time: an object with
        width, height and at(x, y), which gives (red, green, blue). None if it cannot be read.

        For something watched many times a second, such as a level meter, where a look needs a
        few dozen points out of a box of a thousand. meanGrey and peakGrey visit every pixel,
        and the visiting is what costs the time.
        """
        left, top, width, height = int(left), int(top), int(width), int(height)
        if width <= 0 or height <= 0 or left < -10000 or top < -10000:
            return None
        try:
            bitmap = screenBitmap.ScreenBitmap(width, height)
            pixels = bitmap.captureImage(left, top, width, height)
        except Exception:
            log.debugWarning("neuralAccess: could not read a box of the screen", exc_info=True)
            return None
        return ScreenBox(pixels, width, height)

    def peakGrey(self, left, top, width, height):
        """The grey of the brightest point in a box of the screen, or None if it cannot be seen.

        For telling a mark drawn at full strength from the same mark drawn fainter, where the
        mean would say more about the background than about the mark. None as for meanGrey.
        """
        left, top, width, height = int(left), int(top), int(width), int(height)
        if width <= 0 or height <= 0 or left < -10000 or top < -10000:
            return None
        try:
            bitmap = screenBitmap.ScreenBitmap(width, height)
            pixels = bitmap.captureImage(left, top, width, height)
        except Exception:
            log.debugWarning("neuralAccess: could not sample the screen", exc_info=True)
            return None
        peak = 0.0
        for y in range(height):
            scanline = pixels[y]
            for x in range(width):
                pixel = scanline[x]
                grey = 0.299 * pixel.rgbRed + 0.587 * pixel.rgbGreen + 0.114 * pixel.rgbBlue
                if grey > peak:
                    peak = grey
        return peak or None

    def switchPosition(self, label, rect):
        """The word for a switch's current position, or None when it cannot be read."""
        probe = self.profile.switchProbes.get(label)
        tip = self.profile.tipProbes.get(label)
        if (probe is None and tip is None) or not rect or len(rect) < 4:
            return None
        geometry = self.clientGeometry()
        if not geometry:
            return None
        key = (label, int(rect[0]), int(rect[1]))
        now = time.time()
        cached = self._stateCache.get(key)
        if cached is not None and (now - cached[0]) < STATE_CACHE_TTL:
            return cached[1]
        if tip is not None:
            word = self._tipPosition(label, rect, tip)
        else:
            _left, _top, width, height = geometry
            dx, dy, threshold, words = probe[:4]
            # A fifth entry overrides the sample box, for lamps smaller than the usual box.
            boxSize = probe[4] if len(probe) > 4 else self.profile.switchProbeSize
            anchor = self.profile.switchAnchor(self, label, rect)
            boxW = max(1, int(round(boxSize[0] * width)))
            boxH = max(1, int(round(boxSize[1] * height)))
            grey = self.meanGrey(anchor[0] + dx * width, anchor[1] + dy * height, boxW, boxH)
            if len(probe) > 5 and probe[5] == PROBE_OF_PEAK:
                # The threshold is a share of the brightest point of the control itself, so
                # the reading holds however the amplifier dims the control: under a window
                # drawn over the view, or on a panel that is switched off.
                peak = self.peakGrey(anchor[0], anchor[1], anchor[2], anchor[3])
                threshold = None if peak is None or peak < PROBE_PEAK_MIN else threshold * peak
            else:
                threshold = threshold * self.profile.probeDimming(self, label)
            word = None if grey is None or threshold is None \
                else (words[1] if grey >= threshold else words[0])
            STATE_LOG("neuralAccess: %s sampled %s against %s -> %r"
                      % (label, "None" if grey is None else "%.1f" % grey,
                         threshold if threshold is None else "%.1f" % threshold, word))
        self._stateCache[key] = (now, word)
        return word

    def _tipPosition(self, label, rect, tip):
        """Which of two spots holds the handle's bright tip. None when neither clearly does."""
        (x0, y0), (x1, y1), box, words = tip
        left, top, width, height = rect[:4]
        boxW = max(1, int(round(box * width)))
        boxH = max(1, int(round(box * height)))
        grey0 = self.meanGrey(left + x0 * width, top + y0 * height, boxW, boxH)
        grey1 = self.meanGrey(left + x1 * width, top + y1 * height, boxW, boxH)
        if grey0 is None or grey1 is None or abs(grey0 - grey1) < TIP_MIN_GAP:
            word = None
        else:
            word = words[0] if grey0 > grey1 else words[1]
        STATE_LOG("neuralAccess: %s tip spots %s / %s -> %r" % (
            label, "None" if grey0 is None else "%.1f" % grey0,
            "None" if grey1 is None else "%.1f" % grey1, word))
        return word

    def selectedInGroup(self, prefix):
        """Which button of a one-of-N group is live: the brightest of them.

        Returns its HelpText, or None if the group cannot be read. No threshold is involved, so
        this does not care that the members have different baselines.
        """
        now = time.time()
        cached = self._stateCache.get(prefix)
        if cached is not None and (now - cached[0]) < STATE_CACHE_TTL:
            return cached[1]
        best = None
        for element in self.findElements(controlType=CT_BUTTON):
            helpText = _prop(element, PROP_HELP_TEXT, "")
            if not helpText.startswith(prefix):
                continue
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4 or rect[2] <= 0:
                continue
            grey = self.meanGrey(rect[0], rect[1], rect[2], rect[3])
            if grey is None:
                self._stateCache[prefix] = (now, None)
                return None
            if best is None or grey > best[0]:
                best = (grey, helpText)
        winner = best[1] if best else None
        self._stateCache[prefix] = (now, winner)
        log.debug("neuralAccess: selected in %r -> %r" % (prefix, winner))
        return winner

    def activeAmpModel(self):
        """Which amplifier model is live. The profile knows where that answer lives."""
        return self.profile.activeAmpModel(self)

    def invalidateStates(self):
        self._stateCache = {}

    def announceStateChange(self, obj):
        """Speaks a switch's new position once the plugin has finished repainting.

        Reading straight back after activating one returns the old position - the repaint lands a
        moment later. This polls until the reading moves, and says nothing if it never does.
        """
        label = self.profile.stateLabel(obj)
        if not self.profile.readsSwitchState(label):
            return
        before = getattr(obj, "ampStateWord", None)
        rect = _prop(obj.UIAElement, PROP_BOUNDING_RECT)

        def poll(remaining, pending):
            self.invalidateStates()
            now = self.switchPosition(label, rect)
            if now is not None and now != before:
                if pending == now:
                    ui.message(now)
                    return
                # Seen once; confirm on the next poll before speaking, so the announcement
                # lands after the click's focus events instead of being cancelled by them.
                if remaining > 0:
                    core.callLater(STATE_SETTLE_MS, poll, remaining - 1, now)
                return
            if remaining > 0:
                core.callLater(STATE_SETTLE_MS, poll, remaining - 1, None)

        core.callLater(STATE_SETTLE_FIRST_MS, poll, STATE_SETTLE_POLLS, None)

    def channelRowLabel(self, rowRect):
        """The channel's printed name, recovered by recognising the list on screen."""
        entry = self.listContaining(rowRect)
        if entry is None:
            return None
        listRect = entry["rect"]
        recognised = self._rowNames.get(listRect)
        if recognised is None:
            self.recogniseRowNames(listRect)
            return None
        centre = rowRect[1] + (rowRect[3] / 2.0)
        for top, bottom, text in recognised:
            if top <= centre <= bottom:
                return text
        return None

    def recogniseRowNames(self, listRect):
        """Runs Windows character recognition over a channel list, once per list."""
        if listRect in self._ocrPending or listRect in self._rowNames:
            return
        try:
            from contentRecog import RecogImageInfo
            from contentRecog.uwpOcr import UwpOcr
        except Exception:
            log.debugWarning("neuralAccess: character recognition is unavailable", exc_info=True)
            self._rowNames[listRect] = []
            return
        left, top, width, height = (int(value) for value in listRect)
        try:
            recognizer = UwpOcr()
            imageInfo = RecogImageInfo(left, top, width, height, OCR_RESIZE_FACTOR)
            bitmap = screenBitmap.ScreenBitmap(imageInfo.recogWidth, imageInfo.recogHeight)
            pixels = bitmap.captureImage(left, top, width, height)
        except Exception:
            log.debugWarning("neuralAccess: could not capture the channel list", exc_info=True)
            return
        self._ocrPending.add(listRect)

        def onResult(result):
            queueHandler.queueFunction(queueHandler.eventQueue,
                                       self._rowNamesRecognised, listRect, imageInfo, result)

        try:
            recognizer.recognize(pixels, imageInfo, onResult)
        except Exception:
            self._ocrPending.discard(listRect)
            log.debugWarning("neuralAccess: recognition failed to start", exc_info=True)

    def _rowNamesRecognised(self, listRect, imageInfo, result):
        self._ocrPending.discard(listRect)
        if isinstance(result, Exception):
            log.debugWarning("neuralAccess: recognition failed: %r" % result)
            self._rowNames[listRect] = []
            return
        lines = []
        for line in getattr(result, "data", None) or []:
            words = [word.get("text", "").strip() for word in line]
            words = [word for word in words if word]
            # A ticked row's indicator sits just left of the text and is sometimes recognised as
            # a stray character of its own. Drop a leading lone symbol.
            while words and len(words[0]) == 1 and not words[0].isalnum():
                words.pop(0)
            text = " ".join(words).strip(" .,:;|_")
            if not text:
                continue
            tops = [word.get("y", 0) for word in line]
            heights = [word.get("height", 0) for word in line]
            top = imageInfo.convertYToScreen(min(tops))
            bottom = imageInfo.convertYToScreen(max(t + h for t, h in zip(tops, heights)))
            lines.append((top, bottom, text))
        lines.sort()
        self._rowNames[listRect] = lines
        log.debug("neuralAccess: recognised %d channel names" % len(lines))

    def forgetRowNames(self):
        self._rowNames = {}

    def moveChannelRow(self, obj, gesture, size):
        """Arrow key movement through a channel list, which the application does not implement.

        The direction comes from the key itself rather than from the slider sense of "increase",
        because in a list Down has to mean the next row down, not a smaller value.

        Returns True when the keystroke belonged to a list and has been dealt with.
        """
        keyName = (getattr(gesture, "mainKeyName", "") or "").lower()
        if keyName in ("uparrow", "leftarrow", "pageup"):
            step = -1
        elif keyName in ("downarrow", "rightarrow", "pagedown"):
            step = 1
        else:
            step = 0
        role = getattr(obj, "role", None)
        if role == controlTypes.Role.LIST:
            rows = self.channelRows(getattr(obj, "UIAElement", None))
            if not rows:
                return False
            self.trySetFocus(rows[-1 if (size == "max" or step < 0) else 0][0])
            return True
        if not isinstance(obj, AmpChannelRow):
            return False
        entry = self.listContaining(obj.ampRect)
        if entry is None:
            return False
        rows = entry["rows"]
        current = self.rowIndexIn(entry, obj.ampRect)
        if current is None:
            return False
        if size == "min":
            target = 0
        elif size == "max":
            target = len(rows) - 1
        elif step == 0:
            return False
        else:
            target = current + step
        if target < 0 or target >= len(rows):
            # Staying put is better than silently falling out of the list.
            ui.message("edge of list")
            return True
        self.trySetFocus(rows[target][0])
        return True

    def leaveChannelList(self, obj, gesture):
        """Tab out of a channel list.

        The application never gave a row keyboard focus itself, so its own Tab handling has no
        idea where it is and just leaves you stuck among the rows. Handing focus back to the list
        does not help either - the list bounces it straight into a row again. So move to the
        neighbouring control in the panel directly.
        """
        rect = obj.ampRect
        if not rect:
            return False
        # Find the list geometrically, from freshly read positions. Matching against the cached
        # sweep meant that a slightly stale rectangle silently found nothing, and Tab then fell
        # through to the application - which, not knowing where it was, threw focus clear across
        # the plugin.
        controls = self.panelControls()
        index = None
        for position, (controlRect, _element) in enumerate(controls):
            if controlRect[0] - 4 <= rect[0] and controlRect[1] - 4 <= rect[1] \
                    and (rect[0] + rect[2]) <= (controlRect[0] + controlRect[2] + 4) \
                    and (rect[1] + rect[3]) <= (controlRect[1] + controlRect[3] + 4):
                index = position
                break
        if index is None:
            return False
        backwards = any("shift" in identifier for identifier in (gesture.identifiers or ()))
        target = index - 1 if backwards else index + 1
        # Never leave the user stranded among rows the application cannot navigate.
        if target >= len(controls):
            target = index - 1
        if target < 0:
            target = index + 1
        if target < 0 or target >= len(controls):
            return False
        return self.trySetFocus(controls[target][1])

    def toggleChannelRow(self, obj):
        """Ticks or unticks a channel. Invoke is the only thing these rows answer to."""
        element = getattr(obj, "UIAElement", None)
        if element is None:
            return False
        rect = getattr(obj, "ampRect", None)
        before = self.rowIsTicked(rect) if rect else None
        interface = getattr(UIAHandler, "IUIAutomationInvokePattern", None)
        try:
            pattern = element.GetCurrentPattern(PATTERN_INVOKE)
            if not pattern:
                return False
            if interface is not None:
                pattern = pattern.QueryInterface(interface)
            pattern.Invoke()
        except Exception:
            log.debugWarning("neuralAccess: could not invoke the channel row", exc_info=True)
            return False
        # NVDA has already cached this row's checked state; drop it so the next look is honest.
        try:
            obj.invalidateCache()
        except Exception:
            pass
        core.callLater(120, self._announceRowState, rect, before, 0)
        return True

    def _announceRowState(self, rect, before, attempt):
        """Waits for the list to repaint before saying what the channel is now.

        The tick is read from the screen, and the list redraws a little after the row is invoked.
        Announcing straight away reported the state the row had a moment ago, so pressing Space
        repeatedly kept saying the same thing.
        """
        ticked = self.rowIsTicked(rect)
        if ticked is None:
            ui.message("toggled, but the state cannot be read")
            return
        if ticked == before and attempt < 8:
            core.callLater(120, self._announceRowState, rect, before, attempt + 1)
            return
        if ticked != before:
            ui.message("ticked" if ticked else "not ticked")
            return
        # The plugin ignored the press. It will not leave itself with no channel at all, so the
        # last one switched on cannot be switched off - say that rather than repeating the state.
        if ticked and self._tickedCount(rect) <= 1:
            ui.message("still ticked. The plugin keeps one channel switched on, "
                       "so switch another one on before switching this one off.")
            return
        ui.message("unchanged, still ticked" if ticked else "unchanged, still not ticked")

    def _tickedCount(self, rowRect):
        entry = self.listContaining(rowRect)
        if entry is None:
            return 0
        return sum(1 for _element, rect in entry["rows"] if self.rowIsTicked(rect))

    # ---------- pressing things ----------

    def clickElement(self, element, window=None, right=False):
        """Clicks a control with the real cursor, then puts the cursor back. right makes it a
        click of the right button, which is how this generation opens a control's own menu.

        window is for a control in one of the editor's popups, such as a combo box's open list:
        nothing is brought forward - that would close the popup - and the point must belong to
        that window instead of the editor.

        The Mesa generation has a few buttons that ignore Enter and UIA Invoke; in the X
        generation that is every button there is. Only a genuine click reaches them. The steps
        are spread over timers rather than sleeping, so NVDA is never blocked.

        Before the button goes down, the editor's window is brought forward and the point is
        checked to actually belong to it - otherwise the press would land on whatever happens to
        cover the editor at that moment, which is how a verification console once swallowed a
        whole run of clicks.
        """
        rect = _prop(element, PROP_BOUNDING_RECT)
        if not rect or len(rect) < 4 or rect[2] <= 0:
            return False
        x = rect[0] + rect[2] / 2
        y = rect[1] + rect[3] / 2
        origin = _cursorPos()
        # What stands under the pointer's resting place now; see restore below.
        beneath = _windowAtPoint(origin[0], origin[1]) if origin else None
        target = window or self._hwnd
        targetRoot = rootWindow(target) or target
        if window is None:
            try:
                _user32.SetForegroundWindow(targetRoot)
            except Exception:
                pass
        try:
            _setCursorPos(x, y)
        except Exception:
            log.debugWarning("neuralAccess: could not place the cursor", exc_info=True)
            return False
        pressed = {"down": False}

        def down():
            under = _windowAtPoint(x, y)
            underRoot = rootWindow(under) if under else None
            if under != target and underRoot != targetRoot:
                log.info("neuralAccess: click abandoned, window %r covers the target" % (under,))
                return
            pressed["down"] = True
            _mouseEvent(MOUSEEVENTF_RIGHTDOWN if right else MOUSEEVENTF_LEFTDOWN)

        def up():
            if pressed["down"]:
                _mouseEvent(MOUSEEVENTF_RIGHTUP if right else MOUSEEVENTF_LEFTUP)

        def restore(late):
            """Puts the pointer back where it rested, unless the click has opened something
            right there.

            Hadi's pointer rests at the middle of the screen. The Petrucci's preset menu opens
            over that spot, and with the pointer put back the plug-in saw the mouse hovering
            over the fifth row: the list came up with "Neural DSP" chosen and the first arrow
            key opened that folder (2026-11-10, capture 15). A window under the resting place
            that was not there before the click is something the click opened, so the pointer
            stays on the control that was clicked. The late look catches a menu that came up
            after the pointer was already back.
            """
            if _windowAtPoint(origin[0], origin[1]) == beneath:
                if not late:
                    _setCursorPos(origin[0], origin[1])
                return
            if late and _cursorPos() != origin:
                return
            if late:
                _setCursorPos(x, y)
            log.info("neuralAccess: the click opened a window where the pointer rested, %r; "
                     "pointer left on the control at (%d, %d)" % (origin, x, y))

        core.callLater(150, down)
        core.callLater(230, up)
        if origin:
            core.callLater(360, restore, False)
            core.callLater(800, restore, True)
        return True

    def doubleClickElement(self, element):
        """Double-clicks a control with the real cursor, then puts the cursor back. True when
        the clicks were set going.

        In the X generation a double click on a section button switches that whole section off
        or on. The two presses have to start within the plug-in's own double click time, 200
        ms, and NVDA's timers are not exact enough to promise that: a busy moment between two
        timers would turn the double click into two single ones. So the four mouse events go
        out from one step, with a few hundredths of a second between them, which holds NVDA for
        about an eighth of a second. The guards are clickElement's: the editor is brought
        forward, and nothing is pressed when another window covers the point.
        """
        rect = _prop(element, PROP_BOUNDING_RECT)
        if not rect or len(rect) < 4 or rect[2] <= 0:
            return False
        x = rect[0] + rect[2] / 2
        y = rect[1] + rect[3] / 2
        origin = _cursorPos()
        target = self._hwnd
        targetRoot = rootWindow(target) or target
        try:
            _user32.SetForegroundWindow(targetRoot)
        except Exception:
            pass
        try:
            _setCursorPos(x, y)
        except Exception:
            log.debugWarning("neuralAccess: could not place the cursor", exc_info=True)
            return False

        def press():
            under = _windowAtPoint(x, y)
            underRoot = rootWindow(under) if under else None
            if under != target and underRoot != targetRoot:
                log.info("neuralAccess: double click abandoned, window %r covers the target" % (under,))
                return
            _mouseEvent(MOUSEEVENTF_LEFTDOWN)
            _pause(DOUBLE_CLICK_PRESS_S)
            _mouseEvent(MOUSEEVENTF_LEFTUP)
            _pause(DOUBLE_CLICK_GAP_S)
            _mouseEvent(MOUSEEVENTF_LEFTDOWN)
            _pause(DOUBLE_CLICK_PRESS_S)
            _mouseEvent(MOUSEEVENTF_LEFTUP)

        def restore():
            _setCursorPos(origin[0], origin[1])

        core.callLater(150, press)
        if origin:
            # The four events are over about 270 ms after the call.
            core.callLater(330, restore)
        return True

    def pressByHelpText(self, helpText, click=False):
        """Presses a button by focusing it and sending Enter, which the Mesa generation honours."""
        for element in self.findElements(controlType=CT_BUTTON, helpText=helpText):
            if click:
                if self.clickElement(element):
                    return True
                continue
            try:
                element.SetFocus()
            except Exception:
                continue
            try:
                KeyboardInputGesture.fromName("enter").send()
                return True
            except Exception:
                log.debugWarning("neuralAccess: could not send Enter", exc_info=True)
        return False

    # ---------- the tuner ----------
    #
    # An open tuner is narrated while a string rings: the note, how far off it is, and when it is
    # in tune. The profile reads the display; tuning.py decides what is worth saying; this loop
    # only keeps looking until the tuner is closed or the editor goes away.

    def watchTuner(self):
        """Starts narrating the tuner, unless it is already being watched."""
        if self._tunerWatching:
            return
        self._tunerWatching = True
        self._tunerAnnouncer.reset()
        log.debug("neuralAccess: tuner watch started")
        core.callLater(TUNER_POLL_MS, self._tunerPoll)

    def editorIsForeground(self):
        """True when the window holding the editor is the one the user is working in.

        Inside REAPER the foreground window is sometimes the FX window and sometimes the editor's
        own JUCE window inside it (seen 2026-10-02: GetForegroundWindow returned the editor
        itself), so the question is whether the foreground window belongs to the same top level
        window as the editor.
        """
        try:
            foreground = _user32.GetForegroundWindow()
        except Exception:
            return False
        if not foreground:
            return False
        foreground = int(foreground)
        if foreground == int(self._hwnd):
            return True
        root = rootWindow(self._hwnd) or self._hwnd
        return (rootWindow(foreground) or foreground) == int(root)

    def _tunerPoll(self):
        reading = None
        try:
            if _user32.IsWindow(self._hwnd):
                reading = self.profile.tunerReading(self)
        except Exception:
            log.debugWarning("neuralAccess: tuner reading failed", exc_info=True)
        if reading is None:
            self._tunerWatching = False
            log.debug("neuralAccess: tuner watch ended")
            return
        if self.editorIsForeground():
            note, display, inTune = reading
            text = self._tunerAnnouncer.feed(note, display, inTune, time.monotonic())
            if text:
                # The newest reading is the only one worth hearing; anything still queued from
                # the last one is already out of date.
                speech.cancelSpeech()
                ui.message(text)
            delay = TUNER_POLL_MS
        else:
            # The user is in another window: say nothing, and announce the next note in full
            # when they come back.
            self._tunerAnnouncer.reset()
            delay = TUNER_IDLE_POLL_MS
        core.callLater(delay, self._tunerPoll)

    # ---------- the audio settings overlay ----------

    def settingsPanelOpen(self):
        """The audio settings panel is drawn inside the main window rather than in a window of
        its own, so it is recognised by its combo boxes appearing in the tree."""
        return len(self.findElements(controlType=CT_COMBOBOX)) >= 3

    def toggleAudioSettings(self):
        # The settings button ignores Enter and ignores Invoke, so it takes a real click.
        # Clicking it a second time closes the panel again, which matters because Escape does
        # not. The Mesa generation labels its button through HelpText, the X generation through
        # a real Name.
        wasOpen = self.settingsPanelOpen()
        pressed = False
        buttonHelp = self.profile.audioSettingsButtonHelp
        buttonName = getattr(self.profile, "audioSettingsButtonName", None)
        if buttonHelp:
            pressed = self.pressByHelpText(buttonHelp, click=True)
        elif buttonName:
            for element in self.findElements(controlType=CT_BUTTON, name=buttonName):
                pressed = self.clickElement(element)
                break
        if not pressed:
            if self.hosted:
                # Not a failure. The plug-in has no audio settings at all, because choosing the
                # device is the host's job.
                ui.message("No audio settings here. The host owns the audio device.")
            else:
                ui.message("Could not reach the audio settings button.")
            return
        if wasOpen:
            self.forgetRowNames()
            self.invalidatePanel()
            ui.message("audio settings closed")
            return
        # Nothing is announced here: the click puts focus on the cogwheel, which NVDA names, and
        # the panel's first row is announced a moment later. A third message would just be noise.
        core.callLater(600, self._focusSettingsPanel)

    def _focusSettingsPanel(self):
        """Lands on the panel's first row so it can be worked through with Tab."""
        best = None
        bestKey = None
        for element in self.findElements(controlType=CT_COMBOBOX):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4:
                continue
            key = (round(rect[1]), round(rect[0]))
            if bestKey is None or key < bestKey:
                bestKey, best = key, element
        self.trySetFocus(best)
        # Read the channel names off the screen now, so they are ready before you Tab to them.
        self.invalidatePanel()
        for entry in self.channelLists():
            self.recogniseRowNames(entry["rect"])


# ---------------------------------------------------------------------------
# The overlay classes NVDA puts in front of the editors' controls
# ---------------------------------------------------------------------------

class AmpObject(UIA):
    """Supplies the name the application leaves blank, and carries the editor's key bindings.

    The gestures live here rather than on an app module on purpose. An object's bindings are only
    live while that object has focus, so inside a host every one of these keys belongs to the
    amplifier while you are standing on one of its controls and belongs to the host the instant
    you are not. Bound to an app module they would have been claimed across the whole of REAPER.
    """

    def _get_ampController(self):
        return ampForObject(self)

    def _get_ampProfile(self):
        controller = self.ampController
        return controller.profile if controller is not None else None

    def _get_ampHelpText(self):
        try:
            return self.UIAElement.CurrentHelpText or ""
        except Exception:
            return ""

    def _get_ampLabel(self):
        controller = self.ampController
        profile = self.ampProfile
        helpText = self.ampHelpText
        if not helpText:
            if controller is None or profile is None:
                return ""
            if self.ampNativeRole == controlTypes.Role.LIST:
                # The settings panel prints each row's caption to the left of its control.
                rect = _prop(self.UIAElement, PROP_BOUNDING_RECT)
                return (controller.panelLabelFor(rect) if rect else "") or ""
            return profile.positionalLabel(self, controller) or ""
        label, _amp = profile.stripPrefix(helpText) if profile else (helpText, None)
        # A couple of controls share one HelpText, so the app's own label cannot tell them apart.
        names = profile.duplicateHelpNames.get(label) if profile else None
        if names:
            index = controller.duplicateHelpIndex(self, helpText) if controller is not None else None
            if index is not None and index < len(names):
                return names[index]
        return profile.friendlyLabel(helpText) if profile else helpText

    def _get_ampNeedsClick(self):
        """True for controls the app exposes with no pattern that Enter or Invoke can reach."""
        profile = self.ampProfile
        return profile.needsClick(self) if profile is not None else False

    def _get_ampIsDeadEnd(self):
        """True when this object is a window of the editor, or the root filling one.

        Inside a host the editor's root is a Custom control named after the amplifier, which NVDA
        reports with the role "unknown" - so the role alone would miss it, and other Custom
        controls are real operable things. The size is what separates them: only the root fills
        the client area.
        """
        if self.ampNativeRole in DEAD_END_ROLES:
            return True
        if self.ampHelpText:
            return False
        amp = self.ampController
        if amp is None:
            return False
        geometry = amp.clientGeometry(self.windowHandle)
        rect = self.location
        if not geometry or not rect:
            return False
        return rect.width >= geometry[2] * 0.9 and rect.height >= geometry[3] * 0.9

    def _get_ampStateWord(self):
        """The switch position word for a switch the profile can read, else None."""
        profile = self.ampProfile
        controller = self.ampController
        if profile is None or controller is None:
            return None
        label = profile.stateLabel(self)
        if not profile.readsSwitchState(label):
            return None
        rect = _prop(self.UIAElement, PROP_BOUNDING_RECT)
        return controller.switchPosition(label, rect)

    def _get_ampGroupPrefix(self):
        """The one-of-N group this button belongs to, if any."""
        profile = self.ampProfile
        if profile is None:
            return None
        helpText = self.ampHelpText
        for prefix in profile.groupPrefixes:
            if helpText.startswith(prefix):
                return prefix
        return None

    def _get_ampIsSelected(self):
        """For a one-of-N button: is this the live one? None when it cannot be determined."""
        controller = self.ampController
        if controller is None:
            return None
        prefix = self.ampGroupPrefix
        if prefix is not None:
            return controller.profile.isSelected(self, controller, prefix)
        return controller.profile.selectedState(self, controller)

    def _get_states(self):
        try:
            states = super(AmpObject, self)._get_states()
        except Exception:
            states = set()
        profile = self.ampProfile
        if profile is not None and profile.dropPressedState(self):
            # The latch behind the UIA toggle state does not reflect the control, so nothing
            # NVDA derived from it may be spoken - not "pressed", and not "checked" either.
            # Every selector read "checked" from its latch after one sweep through the amps.
            states.discard(controlTypes.State.PRESSED)
            states.discard(controlTypes.State.CHECKED)
            states.discard(controlTypes.State.CHECKABLE)
            states.discard(controlTypes.State.HALFCHECKED)
        if self.ampIsSelected:
            states.add(controlTypes.State.CHECKED)
        return states

    def _get_value(self):
        profile = self.ampProfile
        if profile is not None and profile.suppressValue(self):
            return ""
        try:
            return super(AmpObject, self)._get_value()
        except Exception:
            return ""

    def _get_role(self):
        # A button that picks one of a set is a radio button, and saying so lets NVDA and braille
        # report "selected" in their own words. Only claim it when the selection can actually be
        # determined - a radio button that never reports selected is worse than a plain button.
        if self.ampIsSelected is not None:
            return controlTypes.Role.RADIOBUTTON
        role = self.ampNativeRole
        profile = self.ampProfile
        if profile is not None:
            override = profile.roleOverride(self)
            if override is not None:
                return override
        return role

    def _get_ampNativeRole(self):
        """The role NVDA would report on its own.

        Read through the base class rather than through self.role, because _get_role consults
        the positional label and the positional label consults the role.
        """
        try:
            return super(AmpObject, self)._get_role()
        except Exception:
            return controlTypes.Role.UNKNOWN

    def _get_name(self):
        try:
            existing = super(AmpObject, self)._get_name()
        except Exception:
            existing = ""
        base = existing or self.ampLabel
        profile = self.ampProfile
        if profile is not None:
            base = profile.decorateName(self, base)
        # A pull switch's position goes in the name rather than into a check box state - these
        # are two-position switches on a guitar amplifier and the words printed on the panel are
        # the right domain language. One-of-N buttons do use a real state; see _get_role.
        state = self.ampStateWord
        return "%s, %s" % (base, state) if state else base

    def _get_description(self):
        # NVDA maps UIA HelpText to the description. Once it has been promoted to the name,
        # repeating it verbatim just makes every announcement twice as long.
        try:
            existing = super(AmpObject, self)._get_description()
        except Exception:
            return ""
        if existing and existing == self.ampHelpText:
            return ""
        return existing

    # ---------- scripts ----------

    # Controls that do nothing with an arrow key, by the role the plug-in itself gives them. Sent
    # on, the key went through the plug-in to the host's window, and in REAPER's FX window the
    # dialog's own arrow handling then moved focus out of the plug-in: Down Arrow on any button
    # landed on REAPER's Add button (Hadi, 2026-11-12, who chose to stop it). On these the
    # arrows, Page Up and Down, Home and End now do nothing. Knobs, combo boxes, text boxes,
    # lists and the audio channel rows keep theirs.
    NO_ARROW_ROLES = (controlTypes.Role.BUTTON, controlTypes.Role.TOGGLEBUTTON,
                      controlTypes.Role.STATICTEXT)

    def _adjustFocused(self, direction, size, gesture):
        amp = self.ampController
        obj = api.getFocusObject()
        if amp is not None and amp.moveChannelRow(obj, gesture, size):
            return
        if amp is None or not isinstance(obj, AmpSlider):
            if amp is not None and getattr(obj, "ampNativeRole", None) in self.NO_ARROW_ROLES:
                return
            gesture.send()
            return
        rangeInfo = obj.ampRange
        if rangeInfo is None:
            gesture.send()
            return
        raw, minimum, maximum, _small = rangeInfo
        step = obj.ampStep(size)
        if size == "min":
            target = minimum
        elif size == "max":
            target = maximum
        else:
            target = raw + (step * direction)
        dialBefore = obj.ampDial
        if obj.ampSetValue(target):
            amp.invalidateReadouts()
            obj.invalidateCache()
            spoken = obj.value or ""
            # So that the plug-in's own report of this change is not spoken as well.
            obj._ampSaidValue = (spoken, time.time())
            # A knob with a pointer says where it points only when that has changed: each press
            # is one percent and the pointer takes five or six of them to reach the next half
            # hour, so most presses say the percent and nothing else.
            dial = obj.ampDial
            if dial and dial == dialBefore:
                spoken = obj.ampPlainValue or ""
            ui.message(spoken)
        else:
            ui.message("could not change %s" % (obj.name or "control"))

    @script(description="Moves to the next or previous control, first stepping into the amplifier "
                        "if nothing inside it holds keyboard focus.",
            gestures=["kb:tab", "kb:shift+tab"], category=CATEGORY)
    def script_tab(self, gesture):
        amp = self.ampController
        # Tab is dead while the window itself holds focus, so use it to step inside instead - but
        # only when the editor genuinely has nothing focused. NVDA's focused object lags behind:
        # activating the window raises a focus event for the editor's root and NVDA stays on it
        # while a real control still holds keyboard focus underneath. enterWindow answers the
        # question that actually matters, and says False when the editor can traverse perfectly
        # well. Swallowing Tab in that state made it look completely dead.
        if self.ampIsDeadEnd and amp is not None and amp.enterWindow():
            return
        if isinstance(self, AmpChannelRow) and amp is not None and amp.leaveChannelList(self, gesture):
            return
        if amp is not None:
            backwards = any("shift" in identifier for identifier in (gesture.identifiers or ()))
            amp.noteTab(backwards)
            if amp.profile.tabPatch(self, amp, backwards):
                return
        gesture.send()

    @script(description="Presses the focused control, clicking the few buttons that ignore Enter.",
            gesture="kb:enter", category=CATEGORY)
    def script_enter(self, gesture):
        amp = self.ampController
        profile = self.ampProfile
        obj = api.getFocusObject()
        if isinstance(obj, AmpChannelRow) and amp is not None and amp.toggleChannelRow(obj):
            return
        if profile is not None and amp is not None and profile.enterPatch(obj, amp):
            return
        # Tabbing to the audio settings cogwheel and pressing Enter is the obvious thing to do,
        # and the application simply ignores it. Turn that press into the click it needs.
        helpText = getattr(obj, "ampHelpText", "") or ""
        if profile is not None:
            helpText, _amp = profile.stripPrefix(helpText)
        if amp is not None and profile is not None and helpText \
                and helpText == profile.audioSettingsButtonHelp:
            amp.toggleAudioSettings()
            return
        if profile is not None and helpText in profile.clickOnlyButtons and amp is not None:
            element = getattr(obj, "UIAElement", None)
            if element is not None and amp.clickElement(element):
                return
        # Anything that cannot be undone and that the plugin itself does not ask about: say what
        # it would do, and carry it out only when Enter is pressed on it again (see armConfirm).
        # This must come before the ordinary click handling, or the first press would already
        # have fired it.
        confirmKey = profile.confirmKey(obj) if profile is not None else None
        if confirmKey is not None and amp is not None:
            warning, done = profile.confirmActions[confirmKey]
            rect = _objRect(obj)
            if not takeConfirm(amp.hwnd, confirmKey, rect):
                armConfirm(amp.hwnd, confirmKey, rect)
                ui.message("%s %s. Press Enter again to confirm." % (obj.name or confirmKey, warning))
                return
            element = getattr(obj, "UIAElement", None)
            if element is not None and amp.clickElement(element):
                log.info("neuralAccess: %s: confirmed, click sent" % (confirmKey,))
                core.callLater(700, ui.message, done)
                return
            log.info("neuralAccess: %s: confirmed, but the click could not be sent" % (confirmKey,))
            ui.message("Could not press %s." % (obj.name or confirmKey))
            return
        # Some buttons ignore Enter, the space bar and UI Automation's Invoke alike, and only
        # respond to a real cursor click.
        if getattr(obj, "ampNeedsClick", False) and amp is not None:
            element = getattr(obj, "UIAElement", None)
            if element is not None and amp.clickElement(element):
                log.debug("neuralAccess: Enter turned into a click on %r" % (obj.name,))
                profile.afterClick(amp, obj)
                # If the clicked control is a switch whose position is read off the screen,
                # say where it landed once the plugin has repainted.
                amp.invalidateStates()
                amp.announceStateChange(obj)
                return
        # Pressing a switch changes something this module had to read off the screen, so anything
        # cached about it is now stale, and the new position is worth saying out loud.
        if amp is not None:
            amp.invalidateStates()
            amp.announceStateChange(obj)
        gesture.send()

    @script(description="Ticks or unticks the focused audio channel.",
            gesture="kb:space", category=CATEGORY)
    def script_space(self, gesture):
        amp = self.ampController
        obj = api.getFocusObject()
        if isinstance(obj, AmpChannelRow) and amp is not None and amp.toggleChannelRow(obj):
            return
        gesture.send()

    @script(description="Increases the focused knob or switch.",
            gestures=["kb:rightArrow", "kb:upArrow"], category=CATEGORY)
    def script_increase(self, gesture):
        self._adjustFocused(1, "small", gesture)

    @script(description="Decreases the focused knob or switch.",
            gestures=["kb:leftArrow", "kb:downArrow"], category=CATEGORY)
    def script_decrease(self, gesture):
        self._adjustFocused(-1, "small", gesture)

    @script(description="Increases the focused knob in larger steps.",
            gesture="kb:pageUp", category=CATEGORY)
    def script_increaseLarge(self, gesture):
        self._adjustFocused(1, "large", gesture)

    @script(description="Decreases the focused knob in larger steps.",
            gesture="kb:pageDown", category=CATEGORY)
    def script_decreaseLarge(self, gesture):
        self._adjustFocused(-1, "large", gesture)

    @script(description="Increases the focused knob by the smallest possible amount.",
            gestures=["kb:control+rightArrow", "kb:control+upArrow"], category=CATEGORY)
    def script_increaseFine(self, gesture):
        self._adjustFocused(1, "fine", gesture)

    @script(description="Decreases the focused knob by the smallest possible amount.",
            gestures=["kb:control+leftArrow", "kb:control+downArrow"], category=CATEGORY)
    def script_decreaseFine(self, gesture):
        self._adjustFocused(-1, "fine", gesture)

    @script(description="Sets the focused knob to its minimum.",
            gesture="kb:home", category=CATEGORY)
    def script_minimum(self, gesture):
        self._adjustFocused(-1, "min", gesture)

    @script(description="Sets the focused knob to its maximum.",
            gesture="kb:end", category=CATEGORY)
    def script_maximum(self, gesture):
        self._adjustFocused(1, "max", gesture)

    @staticmethod
    def _typingIntoText(gesture):
        """True when a plain key was pressed while a text box has focus.

        The number keys switch views, but the plugins' value readouts are real text boxes wired
        to their settings, and the tuner's reference pitch has one too - a digit typed there is
        meant for the box.
        """
        if getattr(gesture, "modifiers", None):
            return False
        obj = api.getFocusObject()
        return getattr(obj, "role", None) == controlTypes.Role.EDITABLETEXT

    def _switchSection(self, index, gesture):
        if self._typingIntoText(gesture):
            gesture.send()
            return
        amp = self.ampController
        if amp is None:
            return
        with Timed("view key %d" % (index + 1)):
            amp.profile.switchSection(amp, index)

    @script(description="Shows the first section view.",
            gesture="kb:1", category=CATEGORY)
    def script_section1(self, gesture):
        self._switchSection(0, gesture)

    @script(description="Shows the second section view.",
            gesture="kb:2", category=CATEGORY)
    def script_section2(self, gesture):
        self._switchSection(1, gesture)

    @script(description="Shows the third section view.",
            gesture="kb:3", category=CATEGORY)
    def script_section3(self, gesture):
        self._switchSection(2, gesture)

    @script(description="Shows the fourth section view.",
            gesture="kb:4", category=CATEGORY)
    def script_section4(self, gesture):
        self._switchSection(3, gesture)

    @script(description="Shows the fifth section view.",
            gesture="kb:5", category=CATEGORY)
    def script_section5(self, gesture):
        self._switchSection(4, gesture)

    @script(description="Shows the sixth section view.",
            gesture="kb:6", category=CATEGORY)
    def script_section6(self, gesture):
        self._switchSection(5, gesture)

    @script(description="Shows the seventh section view.",
            gesture="kb:7", category=CATEGORY)
    def script_section7(self, gesture):
        self._switchSection(6, gesture)

    # A whole section on or off (Hadi, 2026-11-11: "shift+number keys reports section names and
    # their on/off state. and ctrl+number keys to toggle them on and off. hotkeys are good for
    # this, no need to add any controls to the tab ring"). The number is the view key's. One
    # command for each of the two, with seven keys, so that NVDA's Input gestures dialog gets
    # two entries and not fourteen.

    @staticmethod
    def _numberOf(gesture):
        """Which of the keys 1 to 7 on the number row a gesture was made with, counted from 0,
        or None. NVDA names a digit key by the key itself, whatever the keyboard layout."""
        name = getattr(gesture, "mainKeyName", None)
        if isinstance(name, str) and len(name) == 1 and name in "1234567":
            return int(name) - 1
        return None

    def _sectionKey(self, gesture, hook):
        index = self._numberOf(gesture)
        amp = self.ampController
        if amp is None or index is None:
            return
        with Timed("the %s key" % hook):
            if not getattr(amp.profile, hook)(amp, index):
                ui.message("Not available on this amplifier.")

    @script(description="Says the section of that number and whether it is switched on.",
            gestures=["kb:shift+1", "kb:shift+2", "kb:shift+3", "kb:shift+4", "kb:shift+5",
                      "kb:shift+6", "kb:shift+7"], category=CATEGORY)
    def script_sectionState(self, gesture):
        # Shift with a digit types a character, so in a text box it is typing, like a plain key.
        if getattr(api.getFocusObject(), "role", None) == controlTypes.Role.EDITABLETEXT:
            gesture.send()
            return
        self._sectionKey(gesture, "sectionState")

    @script(description="Switches the section of that number off or on and says its new state. "
                        "Focus and the view stay where they are.",
            gestures=["kb:control+1", "kb:control+2", "kb:control+3", "kb:control+4", "kb:control+5",
                      "kb:control+6", "kb:control+7"], category=CATEGORY)
    def script_sectionToggle(self, gesture):
        # Control with a digit types nothing, so this acts in a text box too.
        self._sectionKey(gesture, "sectionToggle")

    def _switchAmpModel(self, direction, gesture):
        if self._typingIntoText(gesture):
            gesture.send()
            return
        amp = self.ampController
        if amp is not None:
            with Timed("amp model key"):
                amp.profile.switchAmpModel(amp, direction)

    # One key, going round forwards (Hadi, 2026-11-10: "let's change this to only one key, A to
    # cycle through them"). Until 0.10.13 it was 8 and 9, back and forward, each with an
    # NVDA+Shift twin. In a text box A is typing, like every single key.
    @script(description="Selects the next amplifier model, going round, on amps that have several.",
            gesture="kb:a", category=CATEGORY)
    def script_ampNext(self, gesture):
        self._switchAmpModel(1, gesture)

    # The Nolly X can pair any amplifier with any cabinet (Hadi, 2026-11-11, took these two
    # keys as proposed): C goes round the cabinets as A goes round the amplifiers, and the
    # rarer command, the link itself, is Control on the amp key, as Control+M is on M.
    @script(description="Selects the next cabinet, going round, on amps whose cabinet can be "
                        "chosen apart from the amplifier.",
            gesture="kb:c", category=CATEGORY)
    def script_cabNext(self, gesture):
        self._singleKey(gesture, "switchCabModel", 1)

    @script(description="Links or unlinks the amplifier and the cabinet and says which it is now. "
                        "Focus stays where it is.",
            gesture="kb:control+a", category=CATEGORY)
    def script_ampCabLink(self, gesture):
        # Control+A selects everything in a text box, and there it still does.
        if getattr(api.getFocusObject(), "role", None) == controlTypes.Role.EDITABLETEXT:
            gesture.send()
            return
        self._singleKey(gesture, "ampCabLink")

    def _presetStep(self, direction, gesture):
        obj = api.getFocusObject()
        if getattr(obj, "role", None) == controlTypes.Role.EDITABLETEXT:
            gesture.send()
            return
        amp = self.ampController
        if amp is None or not amp.profile.presetStep(amp, direction):
            ui.message("Preset control not available.")

    # The single keys (Hadi, 2026-11-10): one key each, reachable with one finger, and no
    # NVDA+shift twin to remember. In a text box a plain key is typing, so there it goes to the
    # amplifier untouched; his rule is to Tab away from the box and then use the key.
    #
    # Letters and digits are named by the key itself. A punctuation key is named by the
    # character the keyboard layout in use gives it (NVDA asks MapVirtualKeyEx with the focused
    # window's layout), and Hadi has a Persian layout beside the English one. So each of those
    # keys is bound under both names: the left bracket key gives U+062C in Persian, the right
    # bracket U+0686, the comma key U+0648; the period key gives a period in both.

    @script(description="Loads the previous preset and says its name.",
            gestures=["kb:,", "kb:\u0648"], category=CATEGORY)
    def script_presetPrevious(self, gesture):
        self._presetStep(-1, gesture)

    @script(description="Loads the next preset and says its name.",
            gestures=["kb:."], category=CATEGORY)
    def script_presetNext(self, gesture):
        self._presetStep(1, gesture)

    # Comma and period by the key itself, on any keyboard layout (Hadi, 2026-11-12: "make so
    # period and comma keys work for all keyboard layouts"). The bindings above go by the
    # character the layout types, so on a layout whose comma key types a letter (Russian б, for
    # one) they never match. Windows names keys by virtual key code as well, and keyboard
    # layouts give these two keys VK_OEM_COMMA and VK_OEM_PERIOD whatever they type on them (how
    # far that holds was not checked layout by layout), so a plain press of either is taken by
    # its code when no binding answered. NVDA asks the user's own Input Gestures settings before this, so
    # a key assigned elsewhere there still goes where the user sent it.
    KEYS_BY_CODE = {0xBC: "presetPrevious", 0xBE: "presetNext"}
    # The brackets by where they sit, the two keys to the right of P (scan codes 0x1A and 0x1B),
    # asked for the same day. Their virtual key codes do not stay with them: the German layout
    # gives VK_OEM_4 and VK_OEM_6 to ß and the accent key on the top row, and puts Ü and + to the
    # right of P. The place is what an English-keyboard habit, and the Persian bindings above,
    # go by.
    KEYS_BY_POSITION = {0x1A: "modulePrevious", 0x1B: "moduleNext"}

    def getScript(self, gesture):
        found = super(AmpObject, self).getScript(gesture)
        if found is None and not getattr(gesture, "modifiers", None):
            name = self.KEYS_BY_CODE.get(getattr(gesture, "vkCode", None))
            if name is None and not getattr(gesture, "isExtended", False):
                name = self.KEYS_BY_POSITION.get(getattr(gesture, "scanCode", None))
            if name:
                found = getattr(self, "script_" + name, None)
        return found

    def _singleKey(self, gesture, hook, *args):
        """Hands one of the single keys to its profile hook, or to the amplifier as typing."""
        if self._typingIntoText(gesture):
            gesture.send()
            return
        amp = self.ampController
        if amp is None:
            return
        with Timed("the %s key" % hook):
            if not getattr(amp.profile, hook)(amp, *args):
                ui.message("Not available on this amplifier.")

    @script(description="Switches the noise gate on or off and says its new state. Focus stays "
                        "where it is. On the Mesa Boogie, which has a gate knob and no switch, "
                        "moves to that knob.",
            gesture="kb:g", category=CATEGORY)
    def script_gate(self, gesture):
        self._singleKey(gesture, "quickToggle", "gate")

    @script(description="Switches the doubler on or off and says its new state. Focus stays "
                        "where it is.",
            gesture="kb:d", category=CATEGORY)
    def script_doubler(self, gesture):
        self._singleKey(gesture, "quickToggle", "doubler")

    @script(description="Moves to the transpose control.",
            gesture="kb:r", category=CATEGORY)
    def script_transpose(self, gesture):
        self._singleKey(gesture, "jumpTo", "transpose")

    @script(description="Moves to the preset button and presses it, which opens the list of presets.",
            gesture="kb:p", category=CATEGORY)
    def script_presetList(self, gesture):
        self._singleKey(gesture, "openPresetList")

    @script(description="Moves to the previous module of the view: a pedal, a rack unit, a microphone, "
                        "or the top bar.",
            gestures=["kb:[", "kb:\u062c"], category=CATEGORY)
    def script_modulePrevious(self, gesture):
        self._singleKey(gesture, "stepModule", -1)

    @script(description="Moves to the next module of the view: a pedal, a rack unit, a microphone, "
                        "or the top bar.",
            gestures=["kb:]", "kb:\u0686"], category=CATEGORY)
    def script_moduleNext(self, gesture):
        self._singleKey(gesture, "stepModule", 1)

    @script(description="Opens the menu of the control that has focus, the one a mouse user gets "
                        "with a right click. It holds Reset parameter and MIDI learn.",
            gestures=["kb:m", "kb:applications"], category=CATEGORY)
    def script_contextMenu(self, gesture):
        self._singleKey(gesture, "contextMenu")

    @script(description="Opens or closes the MIDI mappings window.",
            gesture="kb:control+m", category=CATEGORY)
    def script_midiMappings(self, gesture):
        self._singleKey(gesture, "midiMappings")

    # Until 0.13.0 this was NVDA+Shift+I on the global plugin, so that it also worked with the
    # microphone list already open. A global key beats NVDA's own commands in every program, and
    # NVDA+Shift+I is the magnifier's colour filter in NVDA 2026. Hadi chose NVDA+Shift+E
    # (2026-11-12; I sits too far into the middle of the keyboard, and NVDA+Alt opens REAPER's
    # menu). Here, on the amplifier's controls, it takes nothing from any other program, and
    # NVDA itself does not use it.
    @script(description="Loads your own impulse response file into the focused microphone slot: "
                        "opens the microphone list and presses its LOAD button.",
            gesture="kb:NVDA+shift+e", category=CATEGORY)
    def script_loadImpulseResponse(self, gesture):
        amp = self.ampController
        if amp is None:
            return
        message = amp.profile.loadImpulseResponse(amp, api.getFocusObject(),
                                                  getattr(self, "processID", 0))
        if message:
            ui.message(message)

    # Start and stop on one key (Hadi, 2026-11-11, asked which of the two it should be).
    @script(description="Starts a level check. Pressed again, ends it and says the highest and "
                        "the usual level of the input and output meters while it ran.",
            gesture="kb:l", category=CATEGORY)
    def script_levelCheck(self, gesture):
        self._singleKey(gesture, "levelCheck")

    @script(description="Opens or closes the tuner.", gesture="kb:t", category=CATEGORY)
    def script_tuner(self, gesture):
        if self._typingIntoText(gesture):
            # The tuner's reference pitch is a text box; a letter typed there is for the box.
            gesture.send()
            return
        amp = self.ampController
        if amp is None:
            return
        result = amp.profile.tuner(amp)
        if result is True:
            ui.message("tuner toggled")
        elif isinstance(result, str) and result:
            ui.message(result)


class AmpChannelRow(AmpObject):
    """One row of the audio settings input or output channel list.

    The application gives these away as "Row 1" to "Row 4" with no channel name, no ticked state
    and no keyboard handling whatsoever - the names are not in the accessibility tree even in its
    raw view, and the rows carry no Toggle pattern. So the name comes from reading the screen,
    the ticked state from the brightness of the row's indicator, and the navigation from this
    module. They behave exactly like check boxes, so that is how they are presented.
    """

    def _get_ampRect(self):
        return _prop(self.UIAElement, PROP_BOUNDING_RECT)

    def _get_ampTicked(self):
        controller = self.ampController
        return controller.rowIsTicked(self.ampRect) if controller is not None else None

    def _get_role(self):
        # Only claim to be a check box when the tick can actually be read. Otherwise NVDA would
        # announce "not checked" for a state nobody knows.
        if self.ampTicked is None:
            return controlTypes.Role.LISTITEM
        return controlTypes.Role.CHECKBOX

    def _get_name(self):
        rect = self.ampRect
        controller = self.ampController
        if rect and controller is not None:
            label = controller.channelRowLabel(rect)
            if label:
                return label
        try:
            return super(AmpChannelRow, self)._get_name() or ""
        except Exception:
            return ""

    def _get_states(self):
        try:
            states = super(AmpChannelRow, self)._get_states()
        except Exception:
            states = set()
        if self.ampTicked:
            states.add(controlTypes.State.CHECKED)
        return states

    def _get_positionInfo(self):
        # Reading the name off the screen is never perfectly reliable, so always say which row
        # this is as well - that way a misread name still leaves you knowing where you are.
        amp = self.ampController
        entry = amp.listContaining(self.ampRect) if amp is not None else None
        if entry is None:
            return {}
        index = amp.rowIndexIn(entry, self.ampRect)
        if index is None:
            return {}
        return {"indexInGroup": index + 1, "similarItemsInGroup": len(entry["rows"])}


class AmpSlider(AmpObject):
    """A knob, switch position or fader: readable and writable through RangeValue."""

    def _get_ampRange(self):
        element = self.UIAElement
        raw = _prop(element, PROP_RANGE_VALUE)
        if raw is None:
            return None
        minimum = _prop(element, PROP_RANGE_MIN, 0.0)
        maximum = _prop(element, PROP_RANGE_MAX, 1.0)
        smallChange = _prop(element, PROP_RANGE_SMALL_CHANGE, 0.0)
        return float(raw), float(minimum), float(maximum), float(smallChange)

    def _get_value(self):
        # The value, and for a knob with a pointer where that points: "72 percent, 2 o'clock".
        plain = self.ampPlainValue
        dial = self.ampDial
        return "%s, %s" % (plain, dial) if plain and dial else plain

    def _get_ampDial(self):
        """Where this knob's pointer points ("2 o'clock"), or "" (see AmpProfile.dialPosition)."""
        rangeInfo = self.ampRange
        profile = self.ampProfile
        if rangeInfo is None or profile is None:
            return ""
        raw, minimum, maximum, _small = rangeInfo
        return profile.dialPosition(self, raw, minimum, maximum) or ""

    def _get_ampPlainValue(self):
        """The value by itself, without the clock position."""
        rangeInfo = self.ampRange
        if rangeInfo is None:
            try:
                return super(AmpSlider, self)._get_value()
            except Exception:
                return ""
        raw, minimum, maximum, _small = rangeInfo
        profile = self.ampProfile
        if profile is None:
            return "%.2f" % raw
        label, _amp = profile.stripPrefix(self.ampHelpText)
        if not label:
            # An anonymous slider's identity comes from its position, and the value formatter
            # needs that identity to pick its units.
            label = self.ampLabel
        amp = self.ampController
        unitText = profile.readoutText(amp, self) if amp is not None else None
        return profile.formatValue(label, raw, minimum, maximum, unitText)

    def event_valueChange(self):
        """The plug-in reporting that this knob's value changed.

        NVDA speaks such a report when the knob has focus. After an arrow key that is the
        second time: the key's script has already said the value (see VALUE_ECHO_S). A report
        of the value just said is therefore kept quiet, and only a braille display is brought
        up to date. A report of any other value - the mouse, the host's automation, a readout
        that settled after the key - goes to NVDA as before.
        """
        global _valueEchoesLogged
        said = getattr(self, "_ampSaidValue", None)
        if said is not None and time.time() - said[1] <= VALUE_ECHO_S:
            try:
                value = self.value or ""
            except Exception:
                value = None
            if value == said[0]:
                if _valueEchoesLogged < 5:
                    _valueEchoesLogged += 1
                    log.info("neuralAccess: value: the plug-in reported %r %.0f ms after the key said it; not spoken again"
                             % (value, (time.time() - said[1]) * 1000))
                try:
                    braille.handler.handleUpdate(self)
                except Exception:
                    log.debugWarning("neuralAccess: could not update braille", exc_info=True)
                return
        super(AmpSlider, self).event_valueChange()

    def ampStep(self, size):
        """Chooses a sensible increment: 'small', 'large' or 'fine'."""
        rangeInfo = self.ampRange
        if rangeInfo is None:
            return 0.0
        _raw, minimum, maximum, smallChange = rangeInfo
        span = maximum - minimum
        # Positional switches step by whole positions.
        if span >= 1.0 and smallChange >= 0.5:
            return smallChange
        # Transpose reports one semitone as its small change; honour it.
        if 0.02 <= smallChange < 0.5:
            return smallChange
        if size == "large":
            return span * 0.05
        if size == "fine":
            return span * 0.001
        return span * 0.01

    def ampSetValue(self, newValue):
        rangeInfo = self.ampRange
        if rangeInfo is None:
            return False
        _raw, minimum, maximum, _small = rangeInfo
        newValue = max(minimum, min(maximum, newValue))
        interface = _rangeValueInterface()
        if interface is None:
            return False
        try:
            pattern = self.UIAElement.GetCurrentPattern(PATTERN_RANGE_VALUE)
            if not pattern:
                return False
            pattern.QueryInterface(interface).SetValue(float(newValue))
            return True
        except Exception:
            log.debugWarning("neuralAccess: SetValue failed", exc_info=True)
            return False


class AmpMenuWindow(UIA):
    """The window of one of an amplifier's menus or open lists.

    It takes focus as the menu opens, before any item does, and the plug-in names it after
    itself with the role of a window: Hadi heard "Archetype Petrucci X, window" each time the
    list of presets opened (2026-11-10). Here it is a menu, called after its heading. Nothing
    else about the menu is touched; its items are read as the plug-in presents them.
    """

    def _get_name(self):
        try:
            profile = menuProfileForWindow(self.windowHandle)
            if profile is not None:
                return profile.menuName(firstMenuItemName(self.UIAElement))
        except Exception:
            log.debugWarning("neuralAccess: could not name a menu window", exc_info=True)
        try:
            return super(AmpMenuWindow, self)._get_name()
        except Exception:
            return ""

    def _get_role(self):
        return controlTypes.Role.POPUPMENU


def applyOverlayClasses(obj, clsList):
    """Puts the amplifier's overlay classes in front of one of its controls.

    Called for every object NVDA builds anywhere on the system, so the cheap tests come first: it
    has to be a UI Automation object, in a JUCE window, before anything is asked of UI Automation.
    Returns True when the object belongs to one of our amplifiers.
    """
    if not isinstance(obj, UIA):
        return False
    try:
        className = obj.windowClassName or ""
    except Exception:
        return False
    if not className.startswith(JUCE_CLASS_PREFIX):
        return False
    try:
        hwnd = obj.windowHandle
    except Exception:
        return False
    if profileForWindow(hwnd) is None:
        # Not an editor. The window of an amplifier's menu still gets a name; see AmpMenuWindow.
        if menuProfileForWindow(hwnd) is not None and obj.role == controlTypes.Role.WINDOW:
            clsList.insert(0, AmpMenuWindow)
        return False
    if obj.role == controlTypes.Role.SLIDER:
        clsList.insert(0, AmpSlider)
    elif obj.role == controlTypes.Role.LISTITEM:
        clsList.insert(0, AmpChannelRow)
    else:
        clsList.insert(0, AmpObject)
    return True


def isAmpObject(obj):
    """True when an NVDA object is one of the amplifiers' controls."""
    return isinstance(obj, AmpObject)
