# neuralAccess - an amplifier's popup windows.
#
# A JUCE combo box's open list, or a menu, is a top level window of its own in the plugin's
# process - not a child of the editor. With one open, keyboard focus and the foreground are that
# window, which holds no editor. These helpers find the editor anyway, and find controls inside
# the popups. Nothing here knows about any particular amplifier.

import ctypes
import ctypes.wintypes as wintypes

from . import core as engine
from .core import PROP_CONTROL_TYPE, PROP_NAME, TREESCOPE_DESCENDANTS

_user32 = ctypes.WinDLL("user32")
_ENUM_PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_user32.EnumWindows.argtypes = (_ENUM_PROC, wintypes.LPARAM)
_user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
_user32.IsWindowVisible.argtypes = (wintypes.HWND,)
_user32.GetWindowRect.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))


def topLevelWindows(processID):
    """Visible top level windows of one process."""
    found = []

    def callback(hwnd, _lParam):
        pid = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == processID and _user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    _user32.EnumWindows(_ENUM_PROC(callback), 0)
    return found


def windowRect(hwnd):
    """(left, top, width, height) of a window on screen, or None."""
    rect = wintypes.RECT()
    if not _user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)


def popupWindows(processID, excludeRoot=None):
    """Visible top level JUCE windows of the process other than excludeRoot - the window holding
    the editor - with a real size."""
    out = []
    for hwnd in topLevelWindows(processID) if processID else ():
        if hwnd == excludeRoot or not engine._className(hwnd).startswith("JUCE_"):
            continue
        rect = windowRect(hwnd)
        if rect and rect[2] > 1 and rect[3] > 1:
            out.append(hwnd)
    return out


def findInPopups(processID, name, controlType, excludeRoot=None):
    """(window, element) for the first element with this name and control type inside any of
    the process's popups, or None."""
    client = engine._uiaClient()
    if client is None:
        return None
    for hwnd in popupWindows(processID, excludeRoot):
        try:
            root = client.ElementFromHandle(hwnd)
            condition = client.CreateAndCondition(
                client.CreatePropertyCondition(PROP_NAME, name),
                client.CreatePropertyCondition(PROP_CONTROL_TYPE, controlType))
            element = root.FindFirst(TREESCOPE_DESCENDANTS, condition)
        except Exception:
            continue
        if element:  # a miss is a null COM pointer, which is falsy but not None
            return (hwnd, element)
    return None


def findEditorInProcess(processID):
    """An amplifier editor window anywhere in the process, or None."""
    for hwnd in topLevelWindows(processID):
        found = engine.findAmpWindow(hwnd)
        if found:
            return found
    return None
