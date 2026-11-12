# neuralAccess - the capture key (NVDA+shift+C, from anywhere).
#
# Saves what an amplifier looks like right now, for whoever is working on this add-on: a picture
# of the editor and of every popup the amplifier has open (a combo box's list, a menu), and a
# text file listing every UI Automation element in each with its type, names, rectangle and
# value - including the name this add-on gives it. Hadi can then stay inside the plug-in, press
# the key, change something, press it again, and the developer reads the folder afterwards, with
# no switching back and forth to a terminal.
#
# Files go to %TEMP%\neuralAccess-captures as capture-NNN.txt plus capture-NNN-<window>.bmp.
# Nothing here knows about any particular amplifier.

import ctypes
import os
import struct
import tempfile
import time

import api
import screenBitmap
import ui
import UIAHandler
from logHandler import log
from NVDAObjects.UIA import UIA

from . import core as engine
from . import popups
from .core import (
    PROP_BOUNDING_RECT, PROP_CONTROL_TYPE, PROP_HELP_TEXT, PROP_IS_ENABLED,
    PROP_IS_KEYBOARD_FOCUSABLE, PROP_NAME, PROP_RANGE_MAX, PROP_RANGE_MIN, PROP_RANGE_VALUE,
    PROP_VALUE_VALUE, TREESCOPE_DESCENDANTS, _prop,
)

FOLDER = os.path.join(tempfile.gettempdir(), "neuralAccess-captures")

CONTROL_TYPE_NAMES = {
    50000: "Button", 50002: "CheckBox", 50003: "ComboBox", 50004: "Edit", 50005: "Hyperlink",
    50006: "Image", 50007: "ListItem", 50008: "List", 50009: "Menu", 50010: "MenuBar",
    50011: "MenuItem", 50012: "ProgressBar", 50013: "RadioButton", 50014: "ScrollBar",
    50015: "Slider", 50016: "Spinner", 50018: "Tab", 50019: "TabItem", 50020: "Text",
    50021: "ToolBar", 50022: "ToolTip", 50023: "Tree", 50024: "TreeItem", 50025: "Custom",
    50026: "Group", 50032: "Window", 50033: "Pane", 50037: "TitleBar", 50038: "Separator",
}
CACHED_PROPERTIES = (
    PROP_CONTROL_TYPE, PROP_NAME, PROP_HELP_TEXT, PROP_BOUNDING_RECT, PROP_IS_KEYBOARD_FOCUSABLE,
    PROP_IS_ENABLED, PROP_VALUE_VALUE, PROP_RANGE_VALUE, PROP_RANGE_MIN, PROP_RANGE_MAX,
)


def _saveBitmap(path, rect):
    """Writes the screen inside rect as a 32 bit top-down BMP. False if it could not be read."""
    left, top, width, height = (int(v) for v in rect)
    if width <= 0 or height <= 0 or left < -10000 or top < -10000:
        return False
    bitmap = screenBitmap.ScreenBitmap(width, height)
    pixels = bitmap.captureImage(left, top, width, height)
    raw = ctypes.string_at(ctypes.addressof(pixels), ctypes.sizeof(pixels))
    fileHeader = struct.pack("<2sIHHI", b"BM", 14 + 40 + len(raw), 0, 0, 14 + 40)
    infoHeader = struct.pack("<IiiHHIIiiII", 40, width, -height, 1, 32, 0, len(raw), 2835, 2835, 0, 0)
    with open(path, "wb") as handle:
        handle.write(fileHeader + infoHeader + raw)
    return True


def _cached(element, propertyId):
    try:
        return element.GetCachedPropertyValue(propertyId)
    except Exception:
        return None


def _dumpWindow(hwnd, origin, lines, withAddonNames):
    """Every element under one window, in document order, positions relative to origin."""
    client = engine._uiaClient()
    if client is None:
        lines.append("  (no UI Automation client)")
        return
    try:
        root = client.ElementFromHandle(hwnd)
        request = client.CreateCacheRequest()
        for propertyId in CACHED_PROPERTIES:
            request.AddProperty(propertyId)
        request.TreeFilter = client.RawViewCondition
        found = root.FindAllBuildCache(TREESCOPE_DESCENDANTS, client.CreateTrueCondition(), request)
    except Exception:
        log.info("neuralAccess capture: could not read the tree of %r" % hwnd, exc_info=True)
        lines.append("  (tree could not be read)")
        return
    lines.append("  root: type %s name %r" % (
        CONTROL_TYPE_NAMES.get(_prop(root, PROP_CONTROL_TYPE), "?"), _prop(root, PROP_NAME, "")))
    count = found.Length if found else 0
    lines.append("  elements: %d" % count)
    nameFailures = []
    for index in range(count):
        element = found.GetElement(index)
        controlType = _cached(element, PROP_CONTROL_TYPE)
        rect = _cached(element, PROP_BOUNDING_RECT) or (0, 0, 0, 0)
        parts = [
            "%3d" % index,
            CONTROL_TYPE_NAMES.get(controlType, str(controlType)),
            "at %d,%d %dx%d" % (rect[0] - origin[0], rect[1] - origin[1], rect[2], rect[3]),
            "name=%r" % (_cached(element, PROP_NAME) or ""),
        ]
        helpText = _cached(element, PROP_HELP_TEXT)
        if helpText:
            parts.append("help=%r" % helpText)
        if _cached(element, PROP_IS_KEYBOARD_FOCUSABLE):
            parts.append("focusable")
        if _cached(element, PROP_IS_ENABLED) is False:
            parts.append("disabled")
        value = _cached(element, PROP_VALUE_VALUE)
        if value:
            parts.append("value=%r" % value)
        rangeValue = _cached(element, PROP_RANGE_VALUE)
        if controlType == engine.CT_SLIDER and rangeValue is not None:
            parts.append("range=%s [%s..%s]" % (rangeValue, _cached(element, PROP_RANGE_MIN),
                                                 _cached(element, PROP_RANGE_MAX)))
        if withAddonNames:
            # Building the NVDA object runs this add-on's overlay classes, so this is the name
            # NVDA would actually speak. NVDA expects its own cached properties on the element
            # (the native window handle among them); without them the first capture build
            # failed on every element and wrote "speaks=?".
            try:
                nvdaElement = element.BuildUpdatedCache(UIAHandler.handler.baseCacheRequest)
                parts.append("speaks=%r" % (UIA(UIAElement=nvdaElement).name or ""))
            except Exception:
                if not nameFailures:
                    log.info("neuralAccess capture: could not build an NVDA object", exc_info=True)
                nameFailures.append(index)
                parts.append("speaks=?")
        lines.append("  " + " | ".join(parts))


def _nextNumber():
    highest = 0
    for name in os.listdir(FOLDER):
        if name.startswith("capture-") and name[8:11].isdigit():
            highest = max(highest, int(name[8:11]))
    return highest + 1


def capture(controller, processID, automatic=None):
    """Saves pictures and control lists; speaks how it went.

    With `automatic` (a sentence saying why) the add-on is taking the capture by itself: it
    says nothing, and the reason goes on the file's second line."""
    def say(message):
        if not automatic:
            ui.message(message)

    try:
        os.makedirs(FOLDER, exist_ok=True)
        number = _nextNumber()
    except Exception:
        log.info("neuralAccess capture: cannot use %s" % FOLDER, exc_info=True)
        say("Capture failed: cannot write the capture folder.")
        return
    stem = os.path.join(FOLDER, "capture-%03d" % number)
    lines = ["neuralAccess capture %d, %s" % (number, time.strftime("%Y-%m-%d %H:%M:%S"))]
    if automatic:
        lines.append("AUTOMATIC: %s" % automatic)
    focus = api.getFocusObject()
    try:
        location = focus.location
        lines.append("NVDA focus: name=%r role=%s at %s" % (focus.name, focus.role, tuple(location) if location else None))
    except Exception:
        lines.append("NVDA focus: could not be read")
    focused = engine.focusedElement()
    lines.append("UIA focus: %s" % (_prop(focused, PROP_BOUNDING_RECT) if focused is not None else None,))

    windows = []
    editorRoot = None
    if controller is not None:
        geometry = controller.clientGeometry()
        if geometry:
            windows.append(("editor", controller.hwnd, tuple(geometry), True))
        editorRoot = engine.rootWindow(controller.hwnd)
        lines.append("amplifier: %s, %s" % (controller.profile.displayName,
                                             "plug-in" if controller.hosted else "standalone"))
    popupCount = 0
    for hwnd in popups.popupWindows(processID, editorRoot):
        popupCount += 1
        windows.append(("popup%d" % popupCount, hwnd, popups.windowRect(hwnd), True))
    if not windows:
        foreground = api.getForegroundObject()
        rect = popups.windowRect(foreground.windowHandle)
        if rect:
            windows.append(("foreground", foreground.windowHandle, rect, False))

    saved = 0
    for label, hwnd, rect, addonNames in windows:
        lines.append("")
        lines.append("=== %s: window %r class %r title %r at %s ===" % (
            label, hwnd, engine._className(hwnd), engine.windowTitle(hwnd), rect))
        picture = "%s-%s.bmp" % (stem, label)
        try:
            if _saveBitmap(picture, rect):
                saved += 1
                lines.append("  picture: %s" % os.path.basename(picture))
            else:
                lines.append("  picture: window not on screen")
        except Exception:
            log.info("neuralAccess capture: picture of %s failed" % label, exc_info=True)
            lines.append("  picture: failed")
        _dumpWindow(hwnd, rect[:2], lines, addonNames)
    with open(stem + ".txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    log.info("neuralAccess: %scapture %d saved to %s (%d pictures)" % (
        "automatic " if automatic else "", number, FOLDER, saved))
    if popupCount:
        say("Capture %d saved, with %d popup%s" % (number, popupCount, "" if popupCount == 1 else "s"))
    elif controller is None:
        say("Capture %d saved. No amplifier found, so only the window in front." % number)
    else:
        say("Capture %d saved" % number)
