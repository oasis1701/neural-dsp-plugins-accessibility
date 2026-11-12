# neuralAccess - the Mesa Boogie Mark IIC+ Suite profile.
#
# Everything this particular amplifier knows: its vocabulary, its pixel calibration and its
# layout. The machinery that uses it lives in core.py. Every fact in here was measured against
# the running application; the measurement notes live in handoff.md and are worth reading before
# changing any number.

import time

import api
import controlTypes
import ui
from core import callLater
from keyboardHandler import KeyboardInputGesture
from logHandler import log

from . import core as engine
from . import popups
from .core import (
    CT_BUTTON, CT_COMBOBOX, CT_CUSTOM, CT_SLIDER,
    PROP_BOUNDING_RECT, PROP_CONTROL_TYPE, PROP_HELP_TEXT, PROP_RANGE_VALUE,
    TREESCOPE_DESCENDANTS,
    _prop,
)

# ---- views and modules (0.11.0) ----
#
# Worked out from the plug-in's own file with nothing on screen (2026-11-10): its layout
# document (probe-results\mesa-layout\raw\005-layout.xml, written by
# tools\probe\Extract-EmbeddedXml.py) gives every widget's rectangle, and the names of its
# settings are in the file as text. The Amp view, the top bar and the bottom bar are also known
# from the real tree (probe-results\vst3-tab-order.txt, vst3-host.txt). The other four views
# have never been dumped, so that their controls carry these names as HelpText is ASSUMED - the
# one name seen so far, "Overdrive 2 Pedal HP/LP", fits. Everything below is written to fall
# back to what the Mesa did before 0.11.0 when a view is not recognised, and the view keys log
# what they found (see _logView), so the first use of each view settles it.

# The five views, in the order of their buttons (sectionNames).
VIEW_KEYS = ("pedals", "amp", "cab", "eq", "postfx")

# A view is told by the names of the controls in the tree, tried in this order. The Cab view
# also shows a miniature of the amp, so it has to be asked about before the Amp view, which is
# any tree with controls that carry an amp model's prefix.
VIEW_FAMILIES = (
    ("pedals", ("Compressor Pedal", "Overdrive 1 Pedal", "Overdrive 2 Pedal", "Chorus Pedal")),
    ("cab", ("Cab L ", "Cab R ")),
    ("eq", ("EQ C+ ", "EQ C++ ")),
    ("postfx", ("Delay ", "Reverb ")),
)

# The modules of each view, left to right: (name, the x a control's centre must be left of), x
# as a fraction of the client area. From the layout: the four pedals' rectangles meet at 25.4,
# 49.8 and 74.6 percent; the two microphone columns are the outer 21 percent each side; the
# delay ends at 60.6 percent and the reverb starts at 62.9.
VIEW_MODULES = {
    "pedals": (("Compressor", 0.2544), ("Overdrive 1", 0.4980), ("Overdrive 2", 0.7456), ("Chorus", 1.01)),
    "amp": (("Amplifier", 1.01),),
    "cab": (("Left microphone", 0.2105), ("Amplifier", 0.7895), ("Right microphone", 1.01)),
    "eq": (("Equaliser", 1.01),),
    "postfx": (("Delay", 0.618), ("Reverb", 1.01)),
}
# A view that is not recognised is one module, so the bracket keys still reach it.
UNKNOWN_VIEW_MODULES = (("View", 1.01),)
TOP_BAR_MODULE = "Top bar"

# Bands of the client area, as fractions of its height, for a control's centre. The top bar's
# lowest controls (the value boxes) have theirs at 0.224 and the highest control of any view
# has its at 0.31. The row of view buttons and the "developed by" strip are above 0.085.
TOP_BAR_MAX_Y = 0.26
SECTION_ROW_MAX_Y = 0.085
# The bottom bar cannot be told by height: the Cab view's microphone switches reach down beside
# the button that flips the amp round. Its controls are told by name, and what has no name
# there (a container, the standalone's tempo box) by lying below this.
TOOLS_MIN_Y = 0.90
BOTTOM_HELP = frozenset((
    "Amp View", "Open MIDI Mappings", "Tuner", "Resize the editor",
    "Open audio settings", "Metronome", "Tap tempo", "Tempo",
))

# What a view key or a bracket key may land on. The amp's graphic EQ bands are Custom controls
# with nothing to adjust yet, which keeps them out.
LANDING_TYPES = (CT_SLIDER, CT_BUTTON, CT_COMBOBOX)
# For this long after a landing, the control landed on says where it is ("Pedals view, ...").
LANDING_PREFIX_S = 2.0

# The view keys: the first look for the new view, the looks after it, and how many. The click
# itself goes down 150 ms after the key and comes up at 230 (core.clickElement).
SECTION_LAND_FIRST_MS = 450
SECTION_LAND_POLL_MS = 150
SECTION_LAND_POLLS = 10
# A view's button takes focus when it is clicked; that is not announced, the landing is.
SECTION_HUSH_S = 2.0
# The same view's button is never clicked twice within this long. Two clicks inside the double
# click time are a double click, which on the Petrucci X switches the whole section off; this
# plug-in has a "Section Active" setting per view too, so it is taken to do the same.
SECTION_CLICK_GUARD_S = 1.0

# The amp key (A). A press straight after another goes on from the amp just asked for.
AMP_PRESS_GUARD_S = 1.0
AMP_SWITCH_HUSH_S = 1.5
AMP_FIRST_MS = 400
AMP_POLL_MS = 200
AMP_POLLS = 8
# Focus sent back where it was after a key that had to move it; not announced.
QUICK_HUSH_S = 1.2
QUICK_HOME_S = 1.5

# The doubler key (D): when the new value is first read back, how often again, how many times.
DOUBLER_FIRST_MS = 150
DOUBLER_POLL_MS = 100
DOUBLER_POLLS = 5

# The preset key (P): how often the menu's window is looked for, how long it may take to
# appear, and how long it may stay open.
PRESET_MENU_POLL_MS = 120
PRESET_MENU_APPEAR_POLLS = 25
PRESET_MENU_MAX_S = 600.0

# ---- sections (0.11.3) ----
#
# Each view is a section of the signal chain, and the plug-in can switch a section off whole.
# Its view button is then drawn at half strength (the layout's section_selector_inactive_colour
# is 80F0F0F0) and its view is dimmed to about 0.55 of its brightness. PRESSING ENTER ON A VIEW
# BUTTON IS HOW THE PLUG-IN SWITCHES A SECTION; it does not show the view, a click does. Found
# 2026-11-10 in the add-on's own captures: with 0.11.0 sending Enter, capture 19 has the
# Pedals, Cab, EQ and Post FX buttons at 120 and capture 20, after one Cab key, has Cab at 255;
# two Pedals keys left Pedals where it was. Every view key before 0.11.1 therefore switched its
# section instead of showing it.
#
# A view button's brightest point: 255 with its section on, 120 with it off. The outer seventh
# of the button is left out of the look, in case the plug-in ever draws a focus outline there.
SECTION_ON_PEAK = 190
SECTION_BUTTON_INSET = 0.15
# What a dimmed view's readings are of an undimmed one's (panel 0.60, sliders 0.55, lamp 0.545).
SECTION_DIMMING = 0.55
SECTION_CACHE_S = 0.4
# After Enter on a view button: when the button is first looked at again, how often, how many times.
SECTION_TOGGLE_FIRST_MS = 300
SECTION_TOGGLE_POLL_MS = 150
SECTION_TOGGLE_POLLS = 6

# Enter is turned into a real click on the buttons whose names start with one of these: every
# button of the Pedals, Cab, EQ and Post FX views (see MesaProfile.needsClick).
CLICK_FAMILIES = tuple(family for _view, families in VIEW_FAMILIES for family in families)
CLICK_ROLES = (controlTypes.Role.BUTTON, controlTypes.Role.TOGGLEBUTTON)
# UI Automation's Image control type: the lamps.
CT_IMAGE = 50006
# Where a switch probe is sent when there is nothing to read: core.meanGrey answers None there.
OFF_SCREEN = (-20000, -20000, 0, 0)

# The keys that go somewhere: {what the key asks for: (HelpText of the knob, what to call it)}.
QUICK_JUMPS = {"transpose": ("Transpose Semitones", "Transpose")}
# G on this amplifier: there is a gate knob and no gate switch, so the key goes to the knob.
GATE_KNOB = ("Gate Amount", "Gate")
DOUBLER_SWITCH = "Doubler Active"


class MesaProfile(engine.AmpProfile):
    """The Neural DSP Mesa Boogie Mark IIC+ Suite, standalone and VST3."""

    id = "mesa"
    displayName = "Mesa Boogie Mark IIC+"

    # The provider description names the module the provider came from -
    #   Unidentified Provider (unmanaged:Mesa Boogie Mark IIC+ Suite.vst3)
    # - and the root element carries the same words as its Name. Exact, survives a rebuild, and
    # tells this amplifier apart from any other JUCE plug-in in the same host.
    markers = ("Mesa Boogie Mark IIC+ Suite",)

    # The standalone's executable name is not a valid Python module name (spaces and a plus
    # sign), so NVDA cannot find an app module for it by the usual naming convention; the global
    # plugin maps these spellings onto the shared app module instead.
    executableNames = (
        "mesa boogie mark iic+ suite",
        "Mesa Boogie Mark IIC+ Suite",
        "MESA BOOGIE MARK IIC+ SUITE",
    )

    # Amp model prefixes stripped from control labels. The prefix in use also tells us which of
    # the two amps is currently selected.
    ampPrefixes = ("Mark II C++ ", "Mark II C+ ")

    # Rewrites that make a raw HelpText read naturally in speech.
    friendlyNames = {
        "Mid": "Middle",
        "EQ Switch": "Graphic EQ mode",
        "Bright": "Bright pull switch",
        "Pull Shift Treble": "Treble shift pull switch",
        "Pull Shift Bass": "Bass shift pull switch",
        "Pull Deep": "Deep pull switch",
        "Pull Lead": "Lead channel pull switch",
        "Lead Bright": "Lead bright pull switch",
        "Amp Section Active": "Amp power switch",
        "Amp View": "Flip amp front or rear",
        "Input Gain": "Input",
        "Output Gain": "Output",
        "Gate Amount": "Gate",
        "Transpose Semitones": "Transpose",
        "Channel Mode": "Input mode",
        "Doubler Active": "Doubler",
        "Doubler Delay": "Doubler spread",
        "Open audio settings": "Audio settings",
        "Open MIDI Mappings": "MIDI mappings",
        "Resize the editor": "Resize window",
        "Preset Previous": "Previous preset",
        "Preset Next": "Next preset",
        "Tap tempo": "Tap tempo",
        "Delay Dry/Wet": "Delay mix",
        "Reverb Dry/Wet": "Reverb mix",
        "Overdrive 2 Pedal HP/LP": "Overdrive 2 peak switch",
        # The names below are the plug-in's own, as its controls carry them (Hadi's log of
        # 2026-11-10), said the way the Petrucci X's are: a pedal's footswitch is "the pedal",
        # and nothing says "Pedal" or "Cab L" in front of every knob.
        "Compressor Pedal Compression": "Compression",
        "Compressor Pedal Level": "Compressor level",
        "Compressor Pedal Attack": "Compressor attack",
        "Compressor Pedal Active": "Compressor pedal",
        "Overdrive 1 Pedal Drive": "Overdrive 1 drive",
        "Overdrive 1 Pedal Level": "Overdrive 1 level",
        "Overdrive 1 Pedal Tone": "Overdrive 1 tone",
        "Overdrive 1 Pedal Active": "Overdrive 1 pedal",
        "Overdrive 2 Pedal Drive": "Overdrive 2 drive",
        "Overdrive 2 Pedal Level": "Overdrive 2 level",
        "Overdrive 2 Pedal Tone": "Overdrive 2 tone",
        "Overdrive 2 Pedal Active": "Overdrive 2 pedal",
        "Chorus Pedal Rate": "Chorus rate",
        "Chorus Pedal Depth": "Chorus depth",
        "Chorus Pedal Mix": "Chorus mix",
        "Chorus Pedal Active": "Chorus pedal",
        "Delay Active": "Delay pedal",
        "Delay Mode": "Delay mode",
        "Delay Note/ms Display": "Delay time type",
        "Delay Sync": "Delay sync",
        "Delay Feedback": "Delay feedback",
        "Delay High Pass": "Delay high pass",
        "Delay Low Pass": "Delay low pass",
        "Delay Time L": "Delay time left",
        "Delay Time R": "Delay time right",
        "Delay Sync Note L": "Delay note left",
        "Delay Sync Note R": "Delay note right",
        "Delay Tempo": "Delay tempo",
        "Delay Tap Tempo": "Delay tap tempo",
        "Reverb Active": "Reverb pedal",
        "Reverb Decay": "Reverb decay",
        "Reverb Pre-Delay": "Reverb pre-delay",
        "Reverb Low Cut": "Reverb low cut",
        "Reverb High Cut": "Reverb high cut",
        "Cab L Active": "Left microphone",
        "Cab L Phase": "Left microphone phase",
        "Cab L Position": "Left microphone position",
        "Cab L Distance": "Left microphone distance",
        "Cab L Level": "Left microphone level",
        "Cab L Pan": "Left microphone pan",
        "Cab L Room Active": "Left room",
        "Cab L Room IR Level": "Left room level",
        "Cab R Active": "Right microphone",
        "Cab R Phase": "Right microphone phase",
        "Cab R Position": "Right microphone position",
        "Cab R Distance": "Right microphone distance",
        "Cab R Level": "Right microphone level",
        "Cab R Pan": "Right microphone pan",
        "Cab R Room Active": "Right room",
        "Cab R Room IR Level": "Right room level",
        "EQ C+ Active": "EQ",
        "EQ C++ Active": "EQ",
    }

    # Spoken after the plugin's own display text, which carries a number but rarely its unit.
    unitSuffixes = {
        "Input Gain": "decibels",
        "Output Gain": "decibels",
        "Gate Amount": "decibels",
        "Transpose Semitones": "semitones",
        "Tempo": "beats per minute",
    }

    # Sliders whose value is a short list of named positions.
    enumValues = {
        "EQ Switch": ("EQ auto, graphic EQ on lead only", "centre, graphic EQ on both channels",
                      "EQ out, graphic EQ bypassed"),
        "Channel Mode": ("stereo", "mono"),
    }

    # Knobs voiced on the amplifier's own 0 to 10 dial scale rather than as a percentage.
    ampDialKnobs = frozenset((
        "Volume 1", "Treble", "Bass", "Mid", "Middle", "Master 1",
        "Lead Drive", "Lead Master", "Presence", "Reverb",
    ))

    # Buttons that ignore Enter, the space bar and UI Automation's Invoke alike. Pressing these
    # takes a real cursor click.
    clickOnlyButtons = frozenset(("Open audio settings",))
    audioSettingsButtonHelp = "Open audio settings"

    # The amp panel draws a standby lever and a power lever, and both carry the HelpText "Amp
    # Section Active". They are NOT two switches: they are two clickable hotspots for the one
    # parameter that switches the whole amp block in and out. Clicking either one flips both
    # levers and puts out the power lamp, and the resulting screen is pixel-identical whichever
    # you click (verified 2026-08-08). So they share a leading name to say they do the same
    # thing, and differ only in which lever you are standing on. Named left to right.
    duplicateHelpNames = {
        "Amp Section Active": ("Amp on off switch, standby lever", "Amp on off switch, power lever"),
    }

    # The five view buttons in the top icon bar, in left to right order.
    sectionNames = ("Pedals", "Amp", "Cab", "EQ", "Post FX")

    # One-of-N button groups: the selected one is read off the screen (or, for amp type, out of
    # the tree - see isSelected).
    groupPrefixes = ("Amp Type: ", "Cab Type: ")
    AMP_TYPE_PREFIX = "Amp Type: "

    # ---- reading switch positions off the screen ----
    #
    # No button in this application exposes its state: the only pattern is Invoke, ItemStatus is
    # empty, and there is no Toggle, SelectionItem, Value or legacy MSAA state (established by
    # Probe-ButtonState.ps1 - do not go looking again). Pixels are the only route.
    #
    # A pull switch is drawn as the KNOB BEING PULLED OUT - the knob renders larger with a raised
    # collar, so its bright numbered ring expands outward. Nothing about the label strip above it
    # changes, which is where a first guess would sample and find nothing.
    #
    # Each entry is (dx, dy, threshold, (lowWord, highWord)). dx and dy offset the sample box from
    # the control's own rectangle and are fractions of the client area, so they survive the
    # plugin's four window sizes. The reading is the MEAN grey over the box, and grey is
    # 0.299R + 0.587G + 0.114B. Below the threshold speaks lowWord, at or above it highWord.
    # Calibrated 2026-08-08 by tools\probe\Probe-SwitchPixels.ps1 and Find-SwitchProbe.py; the
    # measured figures behind every threshold are in handoff.md. Every separation is 56 grey
    # levels or more. Re-checked unchanged against the VST3 inside REAPER by Probe-Vst3Pixels.ps1.
    switchProbeSize = (0.0120, 0.0163)
    PUSHED_PULLED = ("pushed", "pulled")
    switchProbes = {
        "Bright": (-0.0020, 0.0680, 75, PUSHED_PULLED),
        "Pull Shift Treble": (0.0040, 0.0707, 70, PUSHED_PULLED),
        "Pull Shift Bass": (0.0060, 0.0735, 69, PUSHED_PULLED),
        "Pull Deep": (0.0080, 0.0707, 60, PUSHED_PULLED),
        "Pull Lead": (0.0040, 0.0544, 79, PUSHED_PULLED),
        "Lead Bright": (0.0060, 0.0762, 70, PUSHED_PULLED),
        # Standby and power are one parameter with two levers. The box is anchored on the
        # LEFTMOST of the pair whichever of them is focused, and the polarity is inverted from
        # intuition: lever up, amp on, reads about 92; lever down, amp off, reads about 184,
        # because dropping the lever swings a bright chrome face into the box. Hence "amp on" is
        # the LOW word.
        "Amp Section Active": (0.0179, 0.0163, 138, ("amp on", "amp off")),
        # ---- the pedals, the EQ and the Cab view (0.11.2) ----
        #
        # Worked out with nothing on screen by tools\probe\Measure-MesaSwitches.py, from the
        # plug-in's own pictures (probe-results\mesa-art) laid over the screens saved in August
        # at the rectangles Hadi's log of 2026-11-10 gives. Where a saved screen already shows
        # a state, the picture and the screen agree to a tenth of a grey level.
        #
        # A pedal's footswitch looks the same on and off; its lamp says which. The box is
        # measured from the LAMP's rectangle, not the switch's (see switchAnchor): 6 pixels
        # square on the lamp's centre, which reads 84 to 95 unlit and 167 to 169 lit on all six
        # pedals. A bigger box takes in the dark rim and the gap shrinks to 34 at 12 pixels.
        "Compressor Pedal Active": (0.02742, 0.03741, 130, ("off", "on"), (0.00598, 0.00816)),
        "Overdrive 1 Pedal Active": (0.02742, 0.03741, 130, ("off", "on"), (0.00598, 0.00816)),
        "Overdrive 2 Pedal Active": (0.02742, 0.03741, 130, ("off", "on"), (0.00598, 0.00816)),
        "Chorus Pedal Active": (0.02742, 0.03741, 130, ("off", "on"), (0.00598, 0.00816)),
        "Delay Active": (0.02742, 0.03741, 130, ("off", "on"), (0.00598, 0.00816)),
        "Reverb Active": (0.02742, 0.03741, 130, ("off", "on"), (0.00598, 0.00816)),
        # The EQ's lamp is smaller, 38 pixels, and the usual 12 pixel box on its centre reads 21
        # (C++ panel) or 35 (C+ panel) unlit and 115 or 120 lit.
        "EQ C+ Active": (0.01296, 0.01769, 70, ("off", "on")),
        "EQ C++ Active": (0.01296, 0.01769, 70, ("off", "on")),
        # The Cab view's switches are a picture 62 by 37 drawn across the button's width in the
        # middle of its height: filled white when on, an outline when off. The box is the
        # middle half of the drawn part. On reads 198; off reads 67, and 90 on the phase
        # switch, whose sign has more lines in it.
        "Cab L Active": (0.00773, 0.02639, 144, ("off", "on"), (0.01496, 0.01224)),
        "Cab R Active": (0.00773, 0.02639, 144, ("off", "on"), (0.01496, 0.01224)),
        "Cab L Phase": (0.00773, 0.02639, 144, ("normal", "inverted"), (0.01496, 0.01224)),
        "Cab R Phase": (0.00773, 0.02639, 144, ("normal", "inverted"), (0.01496, 0.01224)),
        "Cab L Room Active": (0.00623, 0.02204, 140, ("off", "on"), (0.01196, 0.00952)),
        "Cab R Room Active": (0.00623, 0.02204, 140, ("off", "on"), (0.01196, 0.00952)),
    }

    # The small lever switches on the pedals, read by where the lever's bright tip is: the two
    # spots and the box as fractions of the switch's own rectangle (see core tipProbes). The
    # lever is one of two pictures, to the left or to the right, and each lights its own spot
    # to 160 and leaves the other at 0 to 26. The first word is said when the lever is to the
    # left, and the words are the ones printed either side of the switch. The overdrive's
    # switch has two signs printed there and no words, so it says where the lever is.
    LEVER_LEFT = (0.098, 0.255)
    LEVER_RIGHT = (0.745, 0.2365)
    LEVER_BOX = 0.157
    tipProbes = {
        "Compressor Pedal Attack": (LEVER_LEFT, LEVER_RIGHT, LEVER_BOX, ("slow", "fast")),
        "Overdrive 2 Pedal HP/LP": (LEVER_LEFT, LEVER_RIGHT, LEVER_BOX, ("left", "right")),
        "Delay Mode": (LEVER_LEFT, LEVER_RIGHT, LEVER_BOX, ("single", "dual")),
        "Delay Note/ms Display": (LEVER_LEFT, LEVER_RIGHT, LEVER_BOX, ("milliseconds", "note")),
    }

    # The switches whose state is their lamp's, and how far from the switch a lamp may be and
    # still be its own, as a fraction of the client area's width (the pedals' are 0.11 away).
    LAMP_SWITCHES = frozenset((
        "Compressor Pedal Active", "Overdrive 1 Pedal Active", "Overdrive 2 Pedal Active",
        "Chorus Pedal Active", "Delay Active", "Reverb Active", "EQ C+ Active", "EQ C++ Active",
    ))
    LAMP_MAX_DISTANCE = 0.16
    LAMP_MAX_SIZE = 0.10

    # ---- the unnamed controls, located by where they sit ----
    #
    # Bands of the client area, as fractions, so these survive the plugin's four window sizes.
    # Measured with the client area 1003 by 735, at (459,149) standalone and (330,244) inside
    # REAPER - the offsets within the client area are identical in both.
    CAPTION_Y_RANGE = (0.05, 0.10)      # the row of section captions; the DOUBLER rules live here
    DECORATIVE_MAX_HEIGHT = 0.03        # 16 of 735; no working control in the top bar is this short
    PRESET_TOOL_Y_RANGE = (0.09, 0.13)  # the icon row, 31 tall at y fraction 0.109
    PRESET_MENU_Y_RANGE = (0.13, 0.19)  # the name display, 25 tall at y fraction 0.154
    PRESET_MENU_MIN_WIDTH = 0.15        # 254 of 1003; the previous and next arrows are 35
    PRESET_BLOCK_MIN_X = 0.45           # the whole preset block sits in the right half of the bar
    METER_Y_RANGE = (0.05, 0.12)        # 101 tall bars starting at y fraction 0.082
    METER_MAX_WIDTH = 0.02              # 11 of 1003
    METER_MIN_HEIGHT = 0.10             # 101 of 735

    # The amp's five band graphic EQ is drawn as pattern-less Custom controls, located by their
    # proportional position inside the client area.
    AMP_EQ_BANDS = ("80 hertz", "240 hertz", "750 hertz", "2200 hertz", "6600 hertz")
    AMP_EQ_Y_RANGE = (0.30, 0.36)
    AMP_EQ_MAX_WIDTH = 0.04             # 29 of 1003; was an absolute 40 pixels and broke on a resize
    AMP_EQ_MIN_HEIGHT = 0.068           # 89 of 735; likewise, was an absolute 50

    # The preset toolbar's four icon slots, left to right: diskette, trash bin, arrow into a
    # bracket, magnifying glass. The magnifying glass is not a search - it opens Explorer on the
    # preset folder. The trash bin is drawn between Save and Import but is ABSENT FROM THE
    # ACCESSIBILITY TREE whenever the loaded preset cannot be deleted, so a button's slot is
    # worked out from where it sits in the row, never from its index in the list.
    PRESET_TOOL_NAMES = ("Save preset", "Delete preset", "Import preset", "Open presets folder")

    # Of those, the ones Enter clicks outright. Delete goes through the confirmation path
    # instead - it cannot be undone, and on this amplifier the loaded preset's name still
    # cannot be read, so a stray Enter would throw away something you could not even name.
    PRESET_CLICKABLE = frozenset(("Save preset", "Import preset", "Open presets folder"))

    confirmActions = {
        "Delete preset": ("deletes the loaded preset, and this amplifier cannot tell you which "
                          "preset that is", "preset deleted"),
    }

    # The preset name display. A pattern-less Custom control; clicking it opens the preset menu.
    PRESET_MENU_NAME = "Preset menu"

    # The two thin vertical bars flanking the top bar. Not in the app's tab ring.
    METER_NAMES = ("Input level meter", "Output level meter")

    # Two unnamed buttons flank the DOUBLER caption: the short grey rules drawn either side of
    # the word. Real buttons in the app's own tab ring that do nothing whatsoever - verified with
    # Invoke, hover, click, double-click, right-click and Enter, against a positive control.
    DECORATIVE_NAME = "decorative divider"

    # ---- positional lookups, cached per controller ----

    def navButtonElements(self, controller):
        return controller._positionalSweep("nav", lambda: self._navButtonElements(controller))

    def _navButtonElements(self, controller):
        """The unlabelled view selector buttons in the top icon bar, ordered left to right."""
        geometry = controller.clientGeometry()
        if not geometry:
            return []
        _left, top, _width, height = geometry
        candidates = []
        for element in controller.findElements(controlType=CT_BUTTON):
            if _prop(element, PROP_HELP_TEXT, ""):
                continue
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4:
                continue
            if (rect[1] - top) / height < 0.05:
                candidates.append(element)
        return controller._sortedByX(candidates)

    def navButtonIndex(self, controller, obj):
        """Position of an unlabelled top bar button within that row."""
        ordered = self.navButtonElements(controller)
        try:
            targetLeft = obj.location.left
        except Exception:
            return None
        for index, (left, _element) in enumerate(ordered):
            if abs(left - targetLeft) < 3:
                return index
        return None

    def presetRowCentre(self, controller):
        """Screen x of the middle of the preset block.

        Taken from the Previous and Next preset buttons, which the application does label, so it
        survives a window resize and does not care which icons are currently present.
        """
        return controller._positionalSweep("presetCentre", lambda: self._presetRowCentre(controller))

    def _presetRowCentre(self, controller):
        centres = []
        for helpText in ("Preset Previous", "Preset Next"):
            for element in controller.findElements(controlType=CT_BUTTON, helpText=helpText):
                rect = _prop(element, PROP_BOUNDING_RECT)
                if rect and len(rect) >= 4 and rect[2] > 0:
                    centres.append(rect[0] + rect[2] / 2.0)
                    break
        return (sum(centres) / 2.0) if len(centres) == 2 else None

    def presetToolSlot(self, controller, rect):
        """Which of the four preset toolbar icons a button is.

        Worked out from the button's offset either side of the row's centre, in units of one
        button width, because the icons are drawn edge to edge. Deliberately not the button's
        index in the list: the delete trash bin drops out of the tree whenever the loaded preset
        cannot be deleted, and an index would then name every remaining button wrongly.
        """
        centre = self.presetRowCentre(controller)
        if centre is None or rect.width <= 0:
            return None
        offset = (rect.left + rect.width / 2.0 - centre) / float(rect.width)
        slot = int(round(offset + (len(self.PRESET_TOOL_NAMES) - 1) / 2.0))
        return slot if 0 <= slot < len(self.PRESET_TOOL_NAMES) else None

    def eqBandElements(self, controller):
        """The amp's five graphic EQ bands, ordered left to right."""
        return controller._positionalSweep("eq", lambda: self._eqBandElements(controller))

    def _eqBandElements(self, controller):
        geometry = controller.clientGeometry()
        if not geometry:
            return []
        _left, top, width, height = geometry
        ordered = []
        for element in controller.findElements(controlType=CT_CUSTOM):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4:
                continue
            yFraction = (rect[1] - top) / height
            if (self.AMP_EQ_Y_RANGE[0] <= yFraction <= self.AMP_EQ_Y_RANGE[1]
                    and (rect[2] / width) < self.AMP_EQ_MAX_WIDTH
                    and (rect[3] / height) > self.AMP_EQ_MIN_HEIGHT):
                # Keep the rectangle from this read rather than asking for it a second time in
                # _sortedByX: that doubled the cross-process calls in the hottest lookup here.
                ordered.append((rect[0], element))
        ordered.sort(key=lambda pair: pair[0])
        return ordered

    def eqBandIndex(self, controller, obj):
        try:
            targetLeft = obj.location.left
        except Exception:
            return None
        for index, (left, _element) in enumerate(self.eqBandElements(controller)):
            if abs(left - targetLeft) < 3:
                return index
        return None

    # ---- profile hooks ----

    def entryElement(self, controller, hwnd):
        """Entering always lands on the leftmost view selector, a familiar place."""
        navButtons = self.navButtonElements(controller)
        if navButtons:
            return navButtons[0][1]
        return None

    def positionalLabel(self, obj, controller):
        """Names the handful of controls that carry no HelpText at all."""
        try:
            geometry = controller.clientGeometry(obj.windowHandle)
            if not geometry:
                return ""
            left, top, width, height = geometry
            rect = obj.location
            if not rect:
                return ""
            xFraction = (rect.left - left) / float(width)
            yFraction = (rect.top - top) / float(height)
        except Exception:
            return ""
        widthFraction = rect.width / float(width)
        heightFraction = rect.height / float(height)
        role = obj.ampNativeRole
        # Top icon bar: the five view selectors.
        if role == controlTypes.Role.BUTTON and yFraction < 0.05:
            index = self.navButtonIndex(controller, obj)
            if index is not None and index < len(self.sectionNames):
                return "%s view" % self.sectionNames[index]
            return "view selector"
        # The two grey rules either side of the DOUBLER caption. Real buttons with a place in the
        # app's tab ring, but pressing them does nothing at all.
        if (role == controlTypes.Role.BUTTON
                and self.CAPTION_Y_RANGE[0] <= yFraction <= self.CAPTION_Y_RANGE[1]
                and heightFraction < self.DECORATIVE_MAX_HEIGHT):
            return self.DECORATIVE_NAME
        # The preset toolbar icons: save, delete, import, open presets folder.
        if (role == controlTypes.Role.BUTTON
                and self.PRESET_TOOL_Y_RANGE[0] <= yFraction <= self.PRESET_TOOL_Y_RANGE[1]
                and xFraction > self.PRESET_BLOCK_MIN_X):
            slot = self.presetToolSlot(controller, rect)
            if slot is not None:
                return self.PRESET_TOOL_NAMES[slot]
            return "preset button"
        # The preset name display, which opens the preset menu when it is clicked. It is centred
        # exactly on the preset row, which keeps this from catching a container in the audio
        # settings overlay - that is drawn over the plugin and shares these coordinates.
        if (self.PRESET_MENU_Y_RANGE[0] <= yFraction <= self.PRESET_MENU_Y_RANGE[1]
                and xFraction > self.PRESET_BLOCK_MIN_X
                and widthFraction > self.PRESET_MENU_MIN_WIDTH):
            rowCentre = self.presetRowCentre(controller)
            if rowCentre is not None and abs(rect.left + rect.width / 2.0 - rowCentre) <= rect.width * 0.25:
                return self.PRESET_MENU_NAME
        # The input and output level meters flanking the top bar. The plugin's only clipping
        # feedback, and the only controls here that are tall and hair thin.
        if (self.METER_Y_RANGE[0] <= yFraction <= self.METER_Y_RANGE[1]
                and widthFraction < self.METER_MAX_WIDTH
                and heightFraction > self.METER_MIN_HEIGHT):
            return self.METER_NAMES[0] if xFraction < 0.5 else self.METER_NAMES[1]
        # The amp's five band graphic EQ, drawn as unnamed Custom controls.
        if (self.AMP_EQ_Y_RANGE[0] <= yFraction <= self.AMP_EQ_Y_RANGE[1]
                and widthFraction < self.AMP_EQ_MAX_WIDTH
                and heightFraction > self.AMP_EQ_MIN_HEIGHT):
            index = self.eqBandIndex(controller, obj)
            if index is not None and index < len(self.AMP_EQ_BANDS):
                return "Graphic EQ %s" % self.AMP_EQ_BANDS[index]
            return "Graphic EQ band"
        return ""

    def roleOverride(self, obj):
        # The preset name display is a Custom control, so NVDA announces it as "unknown". It
        # behaves like a button - clicking it opens the preset menu - so say so.
        if obj.ampNativeRole == controlTypes.Role.UNKNOWN and not obj.ampHelpText:
            if obj.ampLabel == self.PRESET_MENU_NAME:
                return controlTypes.Role.BUTTON
        return None

    def needsClick(self, obj):
        """The preset toolbar buttons and the preset name display ignore Enter, Space and UIA
        Invoke alike; only a real cursor click reaches them. Confirmed with NVDA quit outright so
        nothing could intercept.

        So does every button of the Pedals, Cab, EQ and Post FX views. Hadi, 2026-11-10, on
        Compressor Pedal Active: "When I press enter on that, it makes an error sound on
        windows" - the plug-in did not take the key and Windows rang its bell. Only that one
        was heard; the others are taken to be the same, being the same kind of drawn switch,
        and a click is what a sighted user gives all of them. The amp panel's own buttons, the
        amp and cab selectors and the tuner button do take Enter and are left alone."""
        helpText = obj.ampHelpText
        if helpText:
            return obj.ampNativeRole in CLICK_ROLES and helpText.startswith(CLICK_FAMILIES)
        label = obj.ampLabel
        return label == self.PRESET_MENU_NAME or label in self.PRESET_CLICKABLE

    def isSelected(self, obj, controller, prefix):
        if prefix == self.AMP_TYPE_PREFIX:
            # The tree already knows this one, so do not read the screen for it.
            model = self.activeAmpModel(controller)
            if not model:
                return None
            return obj.ampHelpText[len(prefix):].strip() == model
        return super(MesaProfile, self).isSelected(obj, controller, prefix)

    def activeAmpModel(self, controller):
        """Which amplifier is live, straight from the tree - no screen reading needed.

        Every amp control's HelpText is prefixed with the model in use, so the answer is already
        being carried around by controls that have nothing to do with the Amp Type buttons.
        """
        for element in controller.findElements(controlType=CT_SLIDER):
            _label, amp = self.stripPrefix(_prop(element, PROP_HELP_TEXT, ""))
            if amp:
                return amp
        return None

    def _lampRects(self, controller):
        """The rectangle of every lamp in the view: the small pictures in the tree."""
        geometry = controller.clientGeometry()
        if not geometry:
            return []
        rects = []
        for element in controller.findElements(controlType=CT_IMAGE):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4 and 0 < rect[2] < geometry[2] * self.LAMP_MAX_SIZE:
                rects.append(tuple(rect[:4]))
        return rects

    def _lampFor(self, controller, rect):
        """The lamp that belongs to a switch: the nearest one, if it is near enough. None when
        there is none, and then the switch says no state at all."""
        geometry = controller.clientGeometry()
        if not geometry:
            return None
        cx = rect[0] + rect[2] / 2.0
        cy = rect[1] + rect[3] / 2.0
        best = None
        for lamp in controller._positionalSweep("mesaLamps", lambda: self._lampRects(controller)):
            distance = ((lamp[0] + lamp[2] / 2.0 - cx) ** 2 + (lamp[1] + lamp[3] / 2.0 - cy) ** 2) ** 0.5
            if distance <= geometry[2] * self.LAMP_MAX_DISTANCE and (best is None or distance < best[0]):
                best = (distance, lamp)
        return best[1] if best else None

    def switchAnchor(self, controller, label, rect):
        """The amp on/off pair is always measured from its left-hand lever, so both levers
        report the same parameter rather than two halves of it. A pedal's footswitch and the
        EQ's switch are measured from their lamp."""
        if label in self.LAMP_SWITCHES:
            # With no lamp to read, a place off the screen: the reading is then "cannot be
            # seen" and nothing is said, where the switch's own rectangle would give a guess.
            return self._lampFor(controller, rect) or OFF_SCREEN
        if label != "Amp Section Active":
            return rect
        # Cached: finding the left-hand lever is a tree search, and doing it per focus event put
        # 200 ms on both of these stops.
        anchor = controller._positionalSweep("ampPowerAnchor",
                                             lambda: self._ampPowerAnchor(controller))
        return anchor if anchor else rect

    def _ampPowerAnchor(self, controller):
        ordered = controller._sortedByX(
            controller.findElements(controlType=CT_BUTTON, helpText="Amp Section Active"))
        if not ordered:
            return None
        anchor = _prop(ordered[0][1], PROP_BOUNDING_RECT)
        return anchor if anchor and len(anchor) >= 4 else None

    # ---- reading the whole editor at once ----

    def _sweep(self, controller):
        """Every element of the editor as (controlType, helpText, rect, element), in the tree's
        own order and in one cross-process call, or None when the editor cannot be read.

        The tree's order is the plug-in's Tab order: JUCE builds both from the same walk of its
        components (probe-results\\tab-order.txt against controls-dump.txt). So "the first
        control of a module in this list" is the stop Tab would reach first.
        """
        client = engine._uiaClient()
        root = controller._mainElement()
        if client is None or root is None:
            return None
        try:
            request = client.CreateCacheRequest()
            for propertyId in (PROP_CONTROL_TYPE, PROP_HELP_TEXT, PROP_BOUNDING_RECT):
                request.AddProperty(propertyId)
        except Exception:
            log.info("neuralAccess: mesa: could not build the request to read the editor", exc_info=True)
            return None
        try:
            # Nothing may be filtered out for not being a "control" element.
            request.TreeFilter = client.RawViewCondition
        except Exception:
            pass
        try:
            found = root.FindAllBuildCache(TREESCOPE_DESCENDANTS, client.CreateTrueCondition(), request)
        except Exception:
            log.info("neuralAccess: mesa: the editor could not be read", exc_info=True)
            return None
        out = []
        for index in range(found.Length if found else 0):
            try:
                element = found.GetElement(index)
                controlType = element.GetCachedPropertyValue(PROP_CONTROL_TYPE)
                helpText = element.GetCachedPropertyValue(PROP_HELP_TEXT) or ""
                rect = element.GetCachedPropertyValue(PROP_BOUNDING_RECT)
            except Exception:
                continue
            if not rect or len(rect) < 4 or rect[2] <= 0 or rect[3] <= 0:
                continue
            out.append((controlType, helpText, tuple(rect[:4]), element))
        return out

    # ---- which view is showing, and the modules in it ----

    def viewOf(self, controller, items=None):
        """Which of the five views is showing ("pedals", "amp", "cab", "eq", "postfx"), told
        from the names of the controls in the tree (see VIEW_FAMILIES), or None."""
        if items is None:
            items = self._sweep(controller)
        names = [helpText for _type, helpText, _rect, _element in (items or ()) if helpText]
        for view, families in VIEW_FAMILIES:
            if any(name.startswith(families) for name in names):
                return view
        if any(self.stripPrefix(name)[1] for name in names):
            return "amp"
        return None

    def _centre(self, controller, rect):
        """A rectangle's centre as fractions of the client area, or None."""
        geometry = controller.clientGeometry()
        if not geometry or not rect or len(rect) < 4:
            return None
        left, top, width, height = geometry
        return ((rect[0] + rect[2] / 2.0 - left) / float(width),
                (rect[1] + rect[3] / 2.0 - top) / float(height))

    def _moduleAt(self, controller, view, helpText, rect):
        """The module a control belongs to: the top bar, one of the view's own, or None for the
        bottom bar (the amp and cab selectors, MIDI, the tuner button)."""
        centre = self._centre(controller, rect)
        if centre is None:
            return None
        cx, cy = centre
        if cy < TOP_BAR_MAX_Y:
            return TOP_BAR_MODULE
        helpText = helpText or ""
        if helpText in BOTTOM_HELP or helpText.startswith(self.groupPrefixes) or cy >= TOOLS_MIN_Y:
            return None
        for name, limit in VIEW_MODULES.get(view, UNKNOWN_VIEW_MODULES):
            if cx < limit:
                return name
        return None

    def _moduleStops(self, controller, view, items):
        """[(module name, element)] in the order the bracket keys step through them: the top
        bar, then the view's own modules left to right.

        The element is the module's first control in the plug-in's Tab order that has a name,
        which passes over the two decorative dividers in the top bar and anything else the
        plug-in leaves nameless; a module with no named control at all gives its first control.
        The row of view buttons is not part of the top bar here - it has the number keys.
        """
        named = {}
        nameless = {}
        for controlType, helpText, rect, element in items or ():
            if controlType not in LANDING_TYPES:
                continue
            module = self._moduleAt(controller, view, helpText, rect)
            if module is None:
                continue
            if module == TOP_BAR_MODULE and self._centre(controller, rect)[1] < SECTION_ROW_MAX_Y:
                continue
            (named if helpText else nameless).setdefault(module, element)
        order = (TOP_BAR_MODULE,) + tuple(name for name, _limit in VIEW_MODULES.get(view, UNKNOWN_VIEW_MODULES))
        return [(name, named.get(name) or nameless[name]) for name in order
                if name in named or name in nameless]

    def moduleStops(self, controller):
        items = self._sweep(controller)
        return self._moduleStops(controller, self.viewOf(controller, items), items)

    def _firstContentStop(self, controller, view, items):
        """The first stop of the view itself: of its first module in the plug-in's Tab order."""
        nameless = None
        for controlType, helpText, rect, element in items or ():
            if controlType not in LANDING_TYPES:
                continue
            if self._moduleAt(controller, view, helpText, rect) in (None, TOP_BAR_MODULE):
                continue
            if helpText:
                return element
            if nameless is None:
                nameless = element
        return nameless

    def _logView(self, controller, view, items):
        """Writes what a view holds to the log, once per view and NVDA run.

        Four of the five views were built from the plug-in's file and not from the screen, so
        the first time each is shown its real controls go on record: Hadi's ordinary use is
        then the capture nobody has to ask him for.
        """
        logged = self.__dict__.setdefault("_loggedViews", set())
        if view in logged:
            return
        logged.add(view)
        lines = []
        for controlType, helpText, rect, _element in items or ():
            module = self._moduleAt(controller, view, helpText, rect)
            if module in (None, TOP_BAR_MODULE):
                continue
            lines.append("%s %r at %d,%d %dx%d in %s" % (
                controlType, helpText, rect[0], rect[1], rect[2], rect[3], module))
        log.info("neuralAccess: mesa: the %s view holds %d controls: %s" % (view, len(lines), "; ".join(lines)))

    # ---- landing: putting focus somewhere on purpose ----

    @staticmethod
    def _rectMatches(a, b, tolerance=2):
        return all(abs(x - y) <= tolerance for x, y in zip(a, b))

    @staticmethod
    def _isLandingTarget(obj, rect, controlType):
        """True when obj is the landing element itself: whole rectangle and control type."""
        if not rect:
            return False
        try:
            location = obj.location
            if any(abs(a - b) >= 3 for a, b in zip(
                    (location.left, location.top, location.width, location.height), rect)):
                return False
            return _prop(obj.UIAElement, PROP_CONTROL_TYPE) == controlType
        except Exception:
            return False

    def _landOn(self, controller, element, prefix):
        """Puts focus on element, its announcement led by prefix. True when that was done."""
        rect = _prop(element, PROP_BOUNDING_RECT)
        if not rect or len(rect) < 4:
            return False
        rect = tuple(rect[:4])
        controlType = _prop(element, PROP_CONTROL_TYPE)
        if self._isLandingTarget(api.getFocusObject(), rect, controlType):
            # Already standing on it: SetFocus would raise no event and nothing would be said.
            ui.message(prefix)
            return True
        controller._mesaLanding = (rect, controlType, prefix, time.time() + LANDING_PREFIX_S)
        # Focus is moving on purpose: a Tab pressed a moment ago must not skip what it lands on.
        controller._lastTab = None
        if controller.trySetFocus(element):
            return True
        controller._mesaLanding = None
        return False

    def _arriveOn(self, controller, element, spoken):
        """Puts focus on element, whose own announcement then says everything. When focus is
        already there nothing would be said, so spoken is."""
        rect = _prop(element, PROP_BOUNDING_RECT)
        controlType = _prop(element, PROP_CONTROL_TYPE)
        if rect and len(rect) >= 4 \
                and self._isLandingTarget(api.getFocusObject(), tuple(rect[:4]), controlType):
            ui.message(spoken)
            return
        controller._lastTab = None
        if not controller.trySetFocus(element):
            ui.message(spoken)

    def decorateName(self, obj, base):
        """Straight after a view key or a bracket key, the control focus landed on also says
        where it is: "Pedals view, ...", "Left microphone, ...". Not when its own name already
        starts with that, as "Delay mix" does in the Delay module."""
        controller = obj.ampController
        if controller is None:
            return base
        # A view button whose section is switched off says so; nothing is added when it is on.
        index = self._viewButtonIndex(obj, base)
        if index is not None and self.sectionActive(controller, index) is False:
            base = "%s, section off" % base
        landing = getattr(controller, "_mesaLanding", None)
        if not landing:
            return base
        rect, controlType, prefix, expiry = landing
        if time.time() > expiry:
            controller._mesaLanding = None
            return base
        if not self._isLandingTarget(obj, rect, controlType):
            return base
        if not base:
            return prefix
        if base.lower().startswith(prefix.lower()):
            return base
        return "%s, %s" % (prefix, base)

    # ---- the view keys ----

    def switchSection(self, controller, index):
        """1 to 5: shows the view and puts focus on its first control, which says the view's
        name in front of its own ("Pedals view, ...").

        The view's button is clicked with the real cursor. THE VIEW BUTTONS IGNORE ENTER, like
        the preset buttons and the audio settings cogwheel. Until 0.11.1 this gave the button
        focus and sent Enter, NVDA said "Pedals view" because the button had taken focus, and
        the view never changed: on 2026-11-10 three view keys in a row each left the Amp view
        showing two seconds later, and Hadi could not open a view with Enter on the buttons
        either. The August checks only ever listened for the button's name. A real click is what
        opened the five views when their screens were saved (tools\\probe\\Probe-Sections.ps1).

        Focus goes on to the first control of the view once the view is seen to have changed.
        If the view is not recognised, focus stays on the button and the view's name is said.
        """
        ordered = self.navButtonElements(controller)
        if not ordered:
            ui.message("Cannot locate the amplifier window.")
            return
        # The row holds a sixth unnamed button, the "developed by" strip, so the count of
        # buttons found says nothing about how many views there are.
        if index >= len(self.sectionNames) or index >= len(ordered):
            ui.message("View not available.")
            return
        element = ordered[index][1]
        controller._lastTab = None
        now = time.time()
        lastIndex, lastTime = getattr(controller, "_mesaSectionClick", (None, 0.0))
        repeated = lastIndex == index and now - lastTime < SECTION_CLICK_GUARD_S
        # No click when the view is already showing, or when its button was clicked a moment
        # ago (see SECTION_CLICK_GUARD_S).
        if not repeated and self.viewOf(controller) != VIEW_KEYS[index]:
            rect = _prop(element, PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4:
                controller.hushFocus([rect], SECTION_HUSH_S)
            controller._mesaSectionClick = (index, now)
            if not controller.clickElement(element):
                ui.message("Could not switch view.")
                return
            # Switching a view repopulates the upper display area, so anything cached about
            # where unnamed controls sit is now potentially about a control that no longer exists.
            controller.invalidatePositional()
            controller.invalidateReadouts()
            controller.invalidateStates()
        # A newer key press supersedes this one: its landing stops quietly.
        serial = getattr(controller, "_mesaSwitchSerial", 0) + 1
        controller._mesaSwitchSerial = serial
        callLater(SECTION_LAND_FIRST_MS, self._landAfterSwitch, controller, index, SECTION_LAND_POLLS, serial)

    # ---- sections: on, off, and what that does to the readings ----

    def _viewButtonIndex(self, obj, label=None):
        """Which view's button a control is, 0 to 4, or None for anything else."""
        if getattr(obj, "ampHelpText", ""):
            return None
        if label is None:
            label = getattr(obj, "ampLabel", "") or ""
        if not label.endswith(" view") or label[:-len(" view")] not in self.sectionNames:
            return None
        return self.sectionNames.index(label[:-len(" view")])

    def sectionActive(self, controller, index):
        """True when the view's section is switched on, False when it is off, None when the
        view's button cannot be seen. Read off the button: see SECTION_ON_PEAK."""
        cache = controller.__dict__.setdefault("_mesaSections", {})
        now = time.time()
        cached = cache.get(index)
        if cached is not None and now - cached[0] < SECTION_CACHE_S:
            return cached[1]
        active = None
        ordered = self.navButtonElements(controller)
        if 0 <= index < len(self.sectionNames) and index < len(ordered):
            rect = _prop(ordered[index][1], PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4:
                insetX = rect[2] * SECTION_BUTTON_INSET
                insetY = rect[3] * SECTION_BUTTON_INSET
                peak = controller.peakGrey(rect[0] + insetX, rect[1] + insetY,
                                           rect[2] - 2 * insetX, rect[3] - 2 * insetY)
                if peak is not None:
                    active = peak >= SECTION_ON_PEAK
        cache[index] = (now, active)
        return active

    def probeDimming(self, controller, label):
        """A switch in a view whose section is off is read against a threshold scaled down by
        the dimming. Told by the switch's name, which starts with its view's family."""
        for view, families in VIEW_FAMILIES:
            if (label or "").startswith(families):
                if self.sectionActive(controller, VIEW_KEYS.index(view)) is False:
                    return SECTION_DIMMING
                return 1.0
        return 1.0

    def enterPatch(self, obj, controller):
        """Enter on a view button goes to the plug-in, which switches that section on or off,
        and the add-on says what the section is once the button has been redrawn: "EQ section,
        on". In 0.11.1 and 0.11.2 Enter here was turned into the view's number key, before it
        was known what Enter does."""
        index = self._viewButtonIndex(obj)
        if index is None:
            return False
        name = self.sectionNames[index]
        controller.__dict__.pop("_mesaSections", None)
        before = self.sectionActive(controller, index)
        try:
            KeyboardInputGesture.fromName("enter").send()
        except Exception:
            ui.message("Could not switch the %s section." % name)
            return True
        serial = getattr(controller, "_mesaSectionSerial", 0) + 1
        controller._mesaSectionSerial = serial

        def report(remaining):
            if getattr(controller, "_mesaSectionSerial", serial) != serial:
                return
            controller.__dict__.pop("_mesaSections", None)
            now = self.sectionActive(controller, index)
            if (now is not None and now != before) or remaining <= 0:
                log.info("neuralAccess: mesa: Enter on the %s view button: section %r before, %r after"
                         % (name, before, now))
                # A switched section dims or lights its whole view: every reading is stale.
                controller.invalidateStates()
                ui.message("%s section" % name if now is None
                           else "%s section, %s" % (name, "on" if now else "off"))
                return
            callLater(SECTION_TOGGLE_POLL_MS, report, remaining - 1)

        callLater(SECTION_TOGGLE_FIRST_MS, report, SECTION_TOGGLE_POLLS)
        return True

    def _landAfterSwitch(self, controller, index, remaining, serial):
        if getattr(controller, "_mesaSwitchSerial", serial) != serial:
            return
        controller.invalidatePositional()
        name = self.sectionNames[index]
        prefix = "%s view" % name
        if self.sectionActive(controller, index) is False:
            # Nothing in this view is in the signal chain; he should hear that before any knob.
            prefix = "%s, section off" % prefix
        items = self._sweep(controller)
        view = self.viewOf(controller, items)
        if view == VIEW_KEYS[index]:
            self._logView(controller, view, items)
            stop = self._firstContentStop(controller, view, items)
            if stop is not None and self._landOn(controller, stop, prefix):
                log.info("neuralAccess: mesa: view key: the %s view shows; focus to %r"
                         % (name, _prop(stop, PROP_HELP_TEXT, "")))
                return
        if remaining > 0:
            callLater(SECTION_LAND_POLL_MS, self._landAfterSwitch, controller, index, remaining - 1, serial)
            return
        if view is not None and view != VIEW_KEYS[index]:
            log.info("neuralAccess: mesa: view key: the %s view never appeared; the %s view is showing"
                     % (name, view))
            ui.message("%s view did not open" % name)
            return
        # Not recognised, or nothing in it to land on. Focus is on the view's button, whose own
        # announcement was kept quiet, so the view's name is said here.
        self._logView(controller, "unrecognised after the %s key" % name, items)
        log.info("neuralAccess: mesa: view key: the %s view %s; focus left on its button" % (
            name, "has no control to land on" if view is not None else "was not recognised"))
        ui.message(prefix)

    # ---- the single keys: A, D, G, R, P and the brackets ----

    def stepModule(self, controller, direction):
        """The bracket keys: focus on the previous or next module's first stop, round and round,
        the module's name said in front of the control's own."""
        items = self._sweep(controller)
        view = self.viewOf(controller, items)
        stops = self._moduleStops(controller, view, items)
        if not stops:
            ui.message("No modules to move between here.")
            return True
        names = [name for name, _element in stops]
        focus = engine.focusedElement()
        rect = _prop(focus, PROP_BOUNDING_RECT) if focus is not None else None
        current = None
        if rect and len(rect) >= 4:
            current = self._moduleAt(controller, view, _prop(focus, PROP_HELP_TEXT, ""), tuple(rect[:4]))
        if current in names:
            index = (names.index(current) + direction) % len(names)
        else:
            # In the bottom bar, or nowhere: that counts as past the last module.
            index = 0 if direction > 0 else len(names) - 1
        name, element = stops[index]
        log.info("neuralAccess: mesa: module key: %s view, from %r to %r, focus to %r"
                 % (view, current, name, _prop(element, PROP_HELP_TEXT, "")))
        if not self._landOn(controller, element, name):
            ui.message(name)
        return True

    def _jump(self, controller, helpText, spoken):
        elements = controller.findElements(controlType=CT_SLIDER, helpText=helpText)
        if not elements:
            return False
        self._arriveOn(controller, elements[0], spoken)
        return True

    def jumpTo(self, controller, which):
        """R: focus on the Transpose knob, and nothing else."""
        entry = QUICK_JUMPS.get(which)
        return self._jump(controller, *entry) if entry else False

    def quickToggle(self, controller, which):
        """D flips the doubler and says "Doubler, on", focus staying where it is. G goes to the
        Gate knob: this amplifier has no gate switch to flip.

        The doubler's switch is a slider with two positions in the tree, so it is set and read
        back there. No click, and nothing read off the screen.
        """
        if which == "gate":
            return self._jump(controller, *GATE_KNOB)
        if which != "doubler":
            return False
        elements = controller.findElements(controlType=CT_SLIDER, helpText=DOUBLER_SWITCH)
        if not elements:
            return False
        element = elements[0]
        before = _prop(element, PROP_RANGE_VALUE)
        if before is None:
            ui.message("Cannot read the doubler.")
            return True
        wanted = 0.0 if float(before) >= 0.5 else 1.0
        if not engine.setRangeValue(element, wanted):
            ui.message("Could not switch the doubler.")
            return True
        # A newer press takes over the reporting, so a quick double press says where the
        # switch ended up once.
        serial = getattr(controller, "_mesaDoublerSerial", 0) + 1
        controller._mesaDoublerSerial = serial

        def report(remaining):
            if getattr(controller, "_mesaDoublerSerial", serial) != serial:
                return
            now = _prop(element, PROP_RANGE_VALUE)
            isOn = None if now is None else float(now) >= 0.5
            if isOn == (wanted >= 0.5) or remaining <= 0:
                log.info("neuralAccess: mesa: doubler key: %r before, set to %r, reads %r" % (before, wanted, now))
                ui.message("Doubler" if isOn is None else "Doubler, %s" % ("on" if isOn else "off"))
                return
            callLater(DOUBLER_POLL_MS, report, remaining - 1)

        callLater(DOUBLER_FIRST_MS, report, DOUBLER_POLLS)
        return True

    def ampTypeElements(self, controller):
        """The amp type selectors, left to right, as (helpText, rect, element)."""
        found = []
        for element in controller.findElements(controlType=CT_BUTTON):
            helpText = _prop(element, PROP_HELP_TEXT, "")
            rect = _prop(element, PROP_BOUNDING_RECT)
            if helpText.startswith(self.AMP_TYPE_PREFIX) and rect and len(rect) >= 4 and rect[2] > 0:
                found.append((helpText, tuple(rect[:4]), element))
        found.sort(key=lambda entry: entry[1][0])
        return found

    def liveAmpType(self, controller, selectors):
        """Which of the selectors is the live amp, as an index, or None.

        The Amp view and the Cab view say it in the tree: every amp control's name starts with
        the model. In the other views nothing in the tree does, and it is read off the screen
        the way the cab selectors are, the live selector being the one drawn filled in.
        """
        model = self.activeAmpModel(controller)
        live = (self.AMP_TYPE_PREFIX + model) if model else controller.selectedInGroup(self.AMP_TYPE_PREFIX)
        for index, (helpText, _rect, _element) in enumerate(selectors):
            if helpText == live:
                return index
        return None

    def _quickHome(self, controller, selectorRects):
        """(element, rect) of the control focus goes back to after the amp key, or None.

        That is the control that has focus as the key is pressed. A second press may come while
        focus still sits on the selector the first one pressed; the place remembered from the
        first press is used then. With focus on a selector and nothing remembered, the user is
        standing on the selectors and focus stays with them.
        """
        now = time.time()
        focus = engine.focusedElement()
        rect = _prop(focus, PROP_BOUNDING_RECT) if focus is not None else None
        rect = tuple(rect[:4]) if rect and len(rect) >= 4 else None
        remembered = getattr(controller, "_mesaQuickHome", None)
        if remembered is not None and now > remembered[2]:
            remembered = controller._mesaQuickHome = None
        if rect is not None and any(self._rectMatches(rect, other) for other in selectorRects):
            if remembered is None:
                return None
            controller._mesaQuickHome = (remembered[0], remembered[1], now + QUICK_HOME_S)
            return remembered[:2]
        if rect is None or controller.isFocusDeadEnd(focus) or not controller.elementIsInside(focus):
            return None
        controller._mesaQuickHome = (focus, rect, now + QUICK_HOME_S)
        return (focus, rect)

    def switchAmpModel(self, controller, direction):
        """A: the other amp type, the IIC+ or the IIC++, and "Mark II C++ amplifier" said once
        it is live.

        The selector is pressed by giving it focus and sending Enter, which this generation
        honours. Focus then goes back where it was, unannounced. When the control it was on has
        gone with the old amp's panel - in the Amp view, and on the miniature in the Cab view -
        focus goes to the first control of the view, which says the amplifier's name first.
        """
        selectors = self.ampTypeElements(controller)
        if len(selectors) < 2:
            ui.message("Cannot locate the amplifier selectors.")
            return
        pressedAt = time.time()
        lastTarget, lastTime = getattr(controller, "_mesaAmpPress", (None, 0.0))
        if lastTarget is not None and pressedAt - lastTime < AMP_PRESS_GUARD_S:
            # The tree may not show the amp just asked for yet; step on from it all the same.
            base = lastTarget
        else:
            controller.invalidateStates()
            base = self.liveAmpType(controller, selectors)
            if base is None:
                log.info("neuralAccess: mesa: amp key: neither the tree nor the selectors' pictures say which amplifier is live")
                ui.message("Cannot tell which amplifier is live.")
                return
        target = (base + direction) % len(selectors)
        helpText, rect, element = selectors[target]
        model = helpText[len(self.AMP_TYPE_PREFIX):].strip()
        home = self._quickHome(controller, [entry[1] for entry in selectors])
        controller._mesaAmpPress = (target, pressedAt)
        controller._lastTab = None
        controller.hushFocus([rect] + ([home[1]] if home else []), AMP_SWITCH_HUSH_S)
        try:
            element.SetFocus()
            KeyboardInputGesture.fromName("enter").send()
        except Exception:
            ui.message("Could not switch amplifier.")
            return
        controller.invalidatePositional()
        controller.invalidateReadouts()
        controller.invalidateStates()
        log.info("neuralAccess: mesa: amp key: %s was live; pressed the selector for %s; focus was %s"
                 % (selectors[base][0][len(self.AMP_TYPE_PREFIX):], model,
                    "on %r" % (_prop(home[0], PROP_HELP_TEXT, ""),) if home else "on the selectors or outside"))
        serial = getattr(controller, "_mesaSwitchSerial", 0) + 1
        controller._mesaSwitchSerial = serial

        def poll(remaining):
            if getattr(controller, "_mesaSwitchSerial", serial) != serial:
                return
            controller.invalidatePositional()
            controller.invalidateStates()
            if self.liveAmpType(controller, self.ampTypeElements(controller)) == target:
                controller.invalidateReadouts()
                prefix = "%s amplifier" % model
                if home is None:
                    # He was on the selectors; focus stays on the one just pressed.
                    ui.message(prefix)
                    return
                if controller._stillUsable(home[0]):
                    controller._lastTab = None
                    controller.hushFocus([home[1]], QUICK_HUSH_S)
                    controller.trySetFocus(home[0])
                    ui.message(prefix)
                    return
                items = self._sweep(controller)
                stop = self._firstContentStop(controller, self.viewOf(controller, items), items)
                if stop is None or not self._landOn(controller, stop, prefix):
                    ui.message(prefix)
                return
            if remaining > 0:
                callLater(AMP_POLL_MS, poll, remaining - 1)
            else:
                log.info("neuralAccess: mesa: amp key: %s never showed as live" % model)
                ui.message("Could not switch amplifier.")

        callLater(AMP_FIRST_MS, poll, AMP_POLLS)

    # ---- the preset menu ----

    def presetMenuElement(self, controller):
        """The preset name display, which opens the preset menu when it is clicked, or None."""
        return controller._positionalSweep("presetMenu", lambda: self._presetMenuElement(controller))

    def _presetMenuElement(self, controller):
        geometry = controller.clientGeometry()
        centre = self.presetRowCentre(controller)
        if not geometry or centre is None:
            return None
        left, top, width, height = geometry
        for element in controller.findElements(controlType=CT_CUSTOM):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4:
                continue
            yFraction = (rect[1] - top) / float(height)
            if (self.PRESET_MENU_Y_RANGE[0] <= yFraction <= self.PRESET_MENU_Y_RANGE[1]
                    and (rect[0] - left) / float(width) > self.PRESET_BLOCK_MIN_X
                    and rect[2] / float(width) > self.PRESET_MENU_MIN_WIDTH
                    and abs(rect[0] + rect[2] / 2.0 - centre) <= rect[2] * 0.25):
                return element
        return None

    def openPresetList(self, controller):
        """P: focus on the preset display, then the click it needs, which opens the plug-in's
        preset menu. Focus goes to the display first so that he is on it, and can press Enter,
        if the click does not take."""
        element = self.presetMenuElement(controller)
        if element is None:
            return False
        controller._lastTab = None
        controller.trySetFocus(element)
        pressed = controller.clickElement(element)
        log.info("neuralAccess: mesa: preset key: click %s" % ("sent" if pressed else "could not be sent"))
        if not pressed:
            ui.message("Could not press the preset menu.")
        else:
            self._followPresetMenu(controller)
        return True

    def afterClick(self, controller, obj):
        # Enter on the preset display opens the same menu as the P key.
        if (getattr(obj, "ampLabel", "") or "") == self.PRESET_MENU_NAME:
            self._followPresetMenu(controller)

    def _menuWindows(self, controller):
        """The amplifier's open menus: top level windows of its process titled "menu"."""
        editorRoot = engine.rootWindow(controller.hwnd)
        return [hwnd for hwnd in popups.popupWindows(controller.processID, editorRoot)
                if engine.windowTitle(hwnd) == "menu"]

    def _followPresetMenu(self, controller):
        """After a click on the preset display: waits for the menu to open and then to close,
        and puts focus back on the display if it has ended up outside the amplifier.

        The menu is a window of its own. On the Petrucci X, closing such a menu inside REAPER
        hands focus to the host's FX window and not to the plug-in (2026-11-10). Whether the
        Mesa does the same has not been seen, so this only acts when focus is found outside.
        """
        serial = getattr(controller, "_mesaMenuSerial", 0) + 1
        controller._mesaMenuSerial = serial
        started = time.time()

        def poll(opened, remaining):
            if getattr(controller, "_mesaMenuSerial", serial) != serial:
                return
            isOpen = bool(self._menuWindows(controller))
            if not opened and not isOpen:
                if remaining > 0:
                    callLater(PRESET_MENU_POLL_MS, poll, False, remaining - 1)
                else:
                    log.info("neuralAccess: mesa: preset menu: no menu window appeared")
                return
            if isOpen:
                if time.time() - started < PRESET_MENU_MAX_S:
                    callLater(PRESET_MENU_POLL_MS, poll, True, 0)
                return
            # A moment for the plug-in and the host to settle where focus goes.
            callLater(150, self._returnFromPresetMenu, controller, serial)

        callLater(PRESET_MENU_POLL_MS, poll, False, PRESET_MENU_APPEAR_POLLS)

    def _returnFromPresetMenu(self, controller, serial):
        if getattr(controller, "_mesaMenuSerial", serial) != serial:
            return
        controller.invalidatePositional()
        display = self.presetMenuElement(controller)
        focus = engine.focusedElement()
        inside = focus is not None and controller.elementIsInside(focus) \
            and not controller.isFocusDeadEnd(focus)
        foreground = controller.editorIsForeground()
        log.info("neuralAccess: mesa: preset menu: closed; focus %s the amplifier, its window %s in front"
                 % ("inside" if inside else "outside", "is" if foreground else "is not"))
        if inside or not foreground or display is None:
            # Focus came back by itself, or the user has gone to another window.
            return
        controller._lastTab = None
        controller.trySetFocus(display)

    def presetStep(self, controller, direction):
        helpText = "Preset Previous" if direction < 0 else "Preset Next"
        if controller.pressByHelpText(helpText):
            ui.message("previous preset" if direction < 0 else "next preset")
            return True
        return False

    def tuner(self, controller):
        return controller.pressByHelpText("Tuner")

    def leadToggle(self, controller):
        for prefix in self.ampPrefixes:
            if controller.pressByHelpText("%sPull Lead" % prefix):
                return "lead channel switch toggled"
        return "Lead switch not available. Switch to the amp view first."


PROFILE = MesaProfile()
