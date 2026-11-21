# neuralAccess - the Fortin Nameless Suite X profile.
#
# What is the Fortin's own: the landmark tables of its five sections (the Nolly X's five), its
# one amplifier, whose panel has its power switch at the left with a lamp beside it, and the
# names its manual gives. Everything it has in common with the other X plug-ins is in
# archetypex.py (ArchetypeXProfile).
#
# Where it comes from, none of it measured by hand:
#   * the plug-in's own layout, read out of the VST3 (probe-results\fortin-layout), from which
#     tools\probe\Draft-XProfile.py drafted the centres below;
#   * a driven run of 2026-11-20 in REAPER, tools\probe\Probe-XViews.py --plugin fortin, which
#     showed each section once, on the Original skin, and saved the tree and a picture at every
#     stop (probe-results\fortin-views). Every control of its five stops falls within the
#     landmarks' tolerance (tools\dev\Check-FortinNames.py);
#   * the manual, Fortin Nameless Suite X v1.0.0.pdf, pages 10 to 15, for the words.
#
# How it differs from the Nolly X:
#   * one amplifier and no selectors, so there is no link, no cabinet row, and A says so;
#   * the amp's POWER switch is the left-most button of its panel, with STANDBY beside it, and
#     the headlight left of both is a slider while lit (its brightness, which changes only the
#     look) and, by the layout, a button with no name while unlit (HEADLIGHTS);
#   * MVC is drawn as one of two knobs, pushed or pulled. Both are the same slider in the tree,
#     and no reading of the picture tells them apart through every position of the knob
#     (notes\fortin-nameless.md), so the knob is MVC either way and says nothing of the pull;
#   * the plug-in goes through Post Effects' reverb before its delay, the reverb pedal standing
#     higher; Tab here goes delay first, as the bracket keys do.

import controlTypes

from .archetypex import (
    ArchetypeXProfile, CAB_PANEL_SWITCH_PROBES, KNOB_UNITS, NOTE_VALUE_NAMES, ROOM_SEND_CAB_SIDED_NAMES,
    ROOM_SEND_CAPTION_STATE_KEYS, ROOM_SEND_SIDED_CAPTIONS, TOP_BAR_SWITCH_PROBES, TOP_BAR_TIP_PROBES,
    TUNER_HELP,
)
from .core import PROP_BOUNDING_RECT, PROP_NAME, PROP_RANGE_MAX, _prop

# The five sections in button order, as viewOf names their views.
VIEW_KEYS = ("prefx", "amp", "cab", "eq", "postfx")

# The amp's knobs left to right as printed on the panel, in the manual's words (page 11), the
# numerals of GAIN II and GAIN I as figures for speech. The Cab view's miniature has the same.
AMP_KNOBS = ("MVC", "Presence", "Bass", "Middle", "Treble", "Gain 2", "Gain 1")
# The panel's buttons right of the power switch, left to right: STANDBY, the pull gain button
# under MVC, and the input, an invisible button over the cable (HIGH I or LOW I). The Cab view's
# miniature has only the standby switch in its row; its other two are found by landmark.
AMP_SWITCHES = ("Standby switch", "Pull gain switch", "Amp input")

# Where the headlight stands, (centre y, centre x) as fractions of the editor: on the Amp view
# and on the Cab view's miniature. Lit, it is a slider (onLed); unlit, an image button with no
# name (offLed), which the tree is taken to hold while the amp is off, as it holds the pedals'
# lamps while they show. Either is left out of the panel before its power switch is found.
HEADLIGHTS = ((0.6535, 0.1885), (0.4655, 0.3398))

# The EQ's nine bands, as the layout names them ("EQ 65 Hz" to "EQ 16 kHz"), worded for speech.
EQ_BANDS = ("65 hertz", "125 hertz", "250 hertz", "500 hertz", "1 kilohertz",
            "2 kilohertz", "4 kilohertz", "8 kilohertz", "16 kilohertz")

# What each knob is counted in, for a knob with no display of its own.
FORTIN_KNOB_UNITS = dict(KNOB_UNITS, **{
    "Left mic level": "decibels",
    "Right mic level": "decibels",
    "Left room level": "decibels",
    "Right room level": "decibels",
    "High pass filter": "hertz",
    "Low pass filter": "hertz",
    "Delay time": "milliseconds",
    "Delay time display": "milliseconds",
    "Delay tempo": "beats per minute",
    # 0 to 8 seconds (the manual), with no figure on the pedal.
    "Reverb decay": "seconds",
})
for _band in EQ_BANDS:
    FORTIN_KNOB_UNITS["Band %s" % _band] = "decibels"

# Each view's own controls as (centre y fraction, centre x fraction, name), from the layout map
# (probe-results\fortin-layout\draft-tables.py), held against the run's trees. A pedal's
# controls have the pedal's name in front; the Grind's one knob, GRIND, is the pedal's name.
VIEW_SLIDER_LANDMARKS = {
    "prefx": (
        (0.4386, 0.1719, "Zuul threshold"),
        (0.3568, 0.4346, "Hexdrive drive"),
        (0.4258, 0.5000, "Hexdrive tone"),
        (0.3568, 0.5615, "Hexdrive level"),
        (0.4386, 0.8359, "Grind"),
    ),
    # The headlight, left of the power switch (onLed, a film strip of its brightness). The
    # amp's knobs are named from the panel (AMP_KNOBS).
    "amp": (
        (0.6535, 0.1885, "Amp headlight"),
    ),
    "cab": (
        (0.4079, 0.0684, "Left position"),
        (0.4079, 0.1504, "Left distance"),
        (0.4079, 0.8496, "Right position"),
        (0.4079, 0.9316, "Right distance"),
        (0.5550, 0.0684, "Left mic level"),
        (0.5550, 0.1504, "Left pan"),
        (0.5550, 0.8496, "Right mic level"),
        (0.5550, 0.9316, "Right pan"),
        (0.7673, 0.1094, "Left room level"),
        (0.7673, 0.8906, "Right room level"),
        (0.4655, 0.3398, "Amp headlight"),
    ),
    "eq": (
        (0.5486, 0.1875, "High pass filter"),
        (0.5486, 0.8154, "Low pass filter"),
        (0.5895, 0.2715, "Band 65 hertz"),
        (0.5895, 0.3291, "Band 125 hertz"),
        (0.5895, 0.3867, "Band 250 hertz"),
        (0.5895, 0.4434, "Band 500 hertz"),
        (0.5895, 0.5010, "Band 1 kilohertz"),
        (0.5895, 0.5586, "Band 2 kilohertz"),
        (0.5895, 0.6162, "Band 4 kilohertz"),
        (0.5895, 0.6738, "Band 8 kilohertz"),
        (0.5895, 0.7314, "Band 16 kilohertz"),
    ),
    "postfx": (
        (0.3939, 0.2578, "Delay sync"),
        (0.4194, 0.1816, "Delay mix"),
        (0.4194, 0.4902, "Delay feedback"),
        # The delay's display. While the delay is free it shows the time and is a slider (the
        # layout's delayTimeMsEditor); synced, a text with the note stands there (DELAY_DISPLAYS).
        (0.4680, 0.2783, "Delay time display"),
        # The tempo beside it: the host's while on DAW (globalTempoEditor, as in the run) or the
        # tapped one while on TAP (delayTempoEditor), whose centres are 2.5 pixels apart.
        (0.4687, 0.3853, "Delay tempo"),
        # While the delay is synced a note-value knob stands here instead (NOTE_KNOB_NAMES).
        (0.5665, 0.2529, "Delay time"),
        (0.5665, 0.4209, "Delay tone"),
        (0.3478, 0.6875, "Reverb mix"),
        (0.3478, 0.8203, "Reverb decay"),
        (0.4450, 0.7520, "Reverb tone"),
    ),
}
VIEW_BUTTON_LANDMARKS = {
    # Each pedal's on/off is its stomp, "<pedal> pedal". The lamps ignore clicks. The Zuul has
    # two lamps at one place, green and red, of which the tree holds the one showing.
    "prefx": (
        (0.5505, 0.1724, "Zuul pedal lamp"),
        (0.6905, 0.1729, "Zuul pedal"),
        (0.5288, 0.5005, "Hexdrive pedal lamp"),
        (0.6931, 0.5000, "Hexdrive pedal"),
        (0.5556, 0.8345, "Grind pedal lamp"),
        (0.6918, 0.8350, "Grind pedal"),
    ),
    # The Fortin logo, which changes the amp's skin, and the cable, a picture that ignores
    # clicks; the input itself is the invisible button over the cable (AMP_SWITCHES).
    "amp": (
        (0.3581, 0.8745, "Amp skin"),
        (0.7020, 0.8530, "Amp input cable"),
        (0.6535, 0.1885, "Amp headlight"),
    ),
    "cab": (
        (0.2749, 0.0430, "Left previous microphone"),
        (0.2749, 0.0752, "Left next microphone"),
        (0.2749, 0.8242, "Right previous microphone"),
        (0.2749, 0.8564, "Right next microphone"),
        (0.3184, 0.1719, "Left microphone switch"),
        (0.3184, 0.9531, "Right microphone switch"),
        (0.7097, 0.1455, "Left room switch"),
        (0.7097, 0.9268, "Right room switch"),
        (0.3114, 0.6914, "Amp skin"),
        (0.4904, 0.6816, "Amp input cable"),
        (0.4629, 0.6387, "Amp input"),
        (0.4910, 0.4053, "Pull gain switch"),
        (0.4655, 0.3398, "Amp headlight"),
    ),
    "eq": (
        (0.6777, 0.1875, "EQ power"),
    ),
    "postfx": (
        (0.3939, 0.4141, "Delay ping pong"),
        (0.7046, 0.1680, "Delay pedal"),
        (0.7097, 0.2246, "Delay pedal lamp"),
        (0.7097, 0.4482, "Tap tempo light"),
        # The Tap tempo stomp, not in the tree with the delay on DAW (the run).
        (0.7046, 0.5059, "Tap tempo"),
        (0.5543, 0.7515, "Reverb pedal lamp"),
        (0.7315, 0.7520, "Reverb pedal"),
    ),
}

# The note-value knob that takes the time knob's place while the delay follows a tempo.
NOTE_KNOB_NAMES = {"Delay time": "Delay note"}
# The text box standing on the delay's display: (centre y, centre x, its name while free, its
# name while synced). Synced, it is the layout's delayTimeNoteEditor, a text with no name that
# takes focus, at 252,357 70x17 (the run, "1/4").
DELAY_DISPLAYS = {
    "postfx": ((0.4674, 0.2803, "Delay time readout", "Delay note readout"),),
}

# Stops that do nothing, or (the skin button) nothing yet: lamps, backgrounds, the little
# rockers whose captions are the switches, the cable picture. Tab passes over them and a
# landing never picks them. The headlight's brightness changes only the look.
DECORATIVE_NAMES = frozenset((
    "Zuul pedal lamp", "Hexdrive pedal lamp", "Grind pedal lamp",
    "Delay pedal lamp", "Tap tempo light", "Reverb pedal lamp",
    "Gate switch", "Doubler switch", "Left room switch", "Right room switch",
    "View background", "Pedal background", "Microphone panel background", "Microphone picture",
    "Amp headlight", "Amp input cable", "Amp skin",
    # The delay's time display while it is free: a read-only number display of the time the knob
    # under it sets (layout delayTimeMsEditor, readonly). Hadi heard it in 0.14.0 (2026-11-20)
    # as a second slider of the same time, as he did the Petrucci X's two in 0.13.8.
    "Delay time display",
))

# The EQ's two captions in the plug-in's Tab ring, hpfLabel and lpfLabel, the only textLabels its
# layout marks as taking focus. The knob each names is a stop of its own.
EQ_CAPTIONS = frozenset(("HPF :", "LPF :"))

# The modules the bracket keys step through, left to right but for the Cab section: (name, axis,
# low, high). The pedals stand at 68 to 285, 404 to 621 and 747 to 964 pixels of 1024 in Pre
# Effects, and at 124 to 564 and 652 to 888 in Post Effects; the Cab's miniature amp at 336 to
# 766, between the microphone panels at 32 to 192 and 832 to 992.
VIEW_MODULES = {
    "prefx": (("Zuul", "x", 0.0, 0.336), ("Hexdrive", "x", 0.336, 0.668), ("Grind", "x", 0.668, 1.0)),
    "amp": (("Amplifier", "x", 0.0, 1.0),),
    # Left microphone, right microphone, then the amp, as on the Nolly X (Hadi, 2026-11-15).
    "cab": (("Left microphone", "x", 0.0, 0.25), ("Right microphone", "x", 0.75, 1.0),
            ("Amplifier", "x", 0.25, 0.75)),
    "eq": (("EQ", "x", 0.0, 1.0),),
    "postfx": (("Delay", "x", 0.0, 0.594), ("Reverb", "x", 0.594, 1.0)),
}
# Each module's on/off switch, first in its Tab order (see RING_TYPES in archetypex.py).
MODULE_SWITCHES = frozenset((
    "Zuul pedal", "Hexdrive pedal", "Grind pedal",
    "Amp power switch",
    "Left microphone switch", "Right microphone switch",
    "EQ power",
    "Delay pedal", "Reverb pedal",
))
# Tab goes through these views' modules in the bracket keys' order rather than the plug-in's.
TAB_IN_MODULE_ORDER = frozenset(("cab", "postfx"))

# The pedals' knobs that say where their pointer points: those with no figure shown anywhere.
# Left out: the delay's time and note knobs, which have the display.
VIEW_POINTER_KNOBS = {
    "prefx": frozenset(("Zuul threshold", "Hexdrive drive", "Hexdrive tone", "Hexdrive level", "Grind")),
    "postfx": frozenset(("Delay mix", "Delay feedback", "Delay tone", "Reverb mix", "Reverb decay", "Reverb tone")),
}

# ---- reading switch positions off the screen, on the Original skin ----
#
# No switch of the Fortin says its state in the tree. The top bar's and the Cab view's side
# panels' are drawn as the Nolly X draws them and are read the same way (TOP_BAR_SWITCH_PROBES,
# TOP_BAR_TIP_PROBES and CAB_PANEL_SWITCH_PROBES in archetypex.py). The rest are pictures, two per
# switch, and are read at two spots each: the first word is said when the first spot is the
# brighter one by 20 grey levels or more, and nothing is said otherwise. The spots are fractions
# of the switch's own rectangle, with a box of 5 pixels at this size. tools\probe\
# Find-XSwitchSpots.py found them (probe-results\fortin-switch-spots.txt): it rebuilds each
# switch on its panel in both states from the plug-in's own pictures and takes the pair of spots
# with the widest margin over four ways of scaling and a pixel's shift, quoted below as "worst
# case". The run of 2026-11-20 showed each switch in one state, and in that state every spot
# below reads the screen as the picture it matches; the other state rests on the pictures.
# Which picture is which state is the skin's (normalImage for off, downImage for on).
#
# Two read nothing: the Cab view's miniature power and standby switches, 24 pixels, whose
# pictures no pair of spots tells apart (worst case -4.0 and -3.7), and the pull gain button,
# whose picture is the same in both states (its state shows only on the MVC knob, which no
# reading tells either; notes\fortin-nameless.md). These pictures are the Original skin's. The
# Blackout skin's amp pictures differ, and these spots are used on them too until it has its own
# (plan Task 12). On the Blackout pictures rebuilt offline they read true or nothing: the power
# and standby switches "amp on" when on and nothing when off, Amp input true, and the miniature's
# input nothing. The pedals', the EQ's and the delay's pictures are the same in every skin.
POWER_STATE_KEYS = {"Nameless": "Nameless amp power switch"}
# Filed so that the miniature never borrows the full-size reading; nothing is filed under it.
MINI_POWER_STATE_KEYS = {"Nameless": "Mini Nameless amp power switch"}

FORTIN_TIP_PROBES = dict(TOP_BAR_TIP_PROBES, **{
    # The amp's POWER and STANDBY switches, one picture each, up for off and down for on. Both
    # are the plug-in's Active Amp Section, so both say whether the amp is on. Worst case 27.4
    # and 28.3; on the screen (on) 116.2 against 60.0 and 116.4 against 47.7. Darkened to 0.56,
    # as a section switched off is, off may be under the 20 and say nothing.
    "Nameless amp power switch": ((0.4168, 0.2293), (0.3751, 0.7293), 0.1043, ("amp on", "amp off")),
    "Standby switch": ((0.4168, 0.2293), (0.4376, 0.7501), 0.1043, ("amp on", "amp off")),
    # The input, HIGH I or LOW I, read off the cable picture (CableHigh or CableLow) behind the
    # invisible button that switches it, at the same places of the editor: 790,547 and 790,534
    # on the Amp view, and 651,381 and 654,375 on the Cab view's miniature, below its button.
    # Worst case 98.0 and 43.8; on the screen (high) 132.8 against 24.2 and 138.6 against 56.6.
    "Amp input": ((0.5635, 0.9115), (0.5635, 0.7469), 0.0665, ("high", "low")),
    "Mini Amp input": ((0.4287, 1.0279), (0.5001, 0.8612), 0.1280, ("high", "low")),
    # The EQ's POWER switch. Worst case 73.6; on the screen (on) 151.3 against 19.8.
    "EQ power": ((0.4484, 0.1380), (0.4829, 0.2760), 0.0863, ("on", "off")),
    # The delay's PING PONG toggle, leaning right for on. Worst case 25.4. The plug-in prints the
    # caption above it and two dots below, which the pictures lack; on the screen (on) the spots
    # read 154.3 against 95.0, and 34.6 apart at the worst pixel's shift.
    "Delay ping pong": ((0.5801, 0.3201), (0.3001, 0.3401), 0.1001, ("on", "off")),
    # Each stomp, from its pedal's lamp: the stomps spring back, so their own pictures say
    # nothing. The first spot is on the lamp's middle, the second at its edge or on the pedal
    # beside it, which is why the fractions of the stomp's rectangle are negative or over 1.
    # The Zuul's lamp is green while its gate is open and red while it is closed, two pictures
    # at one place; the red lamp's spots read both (worst case 53.1 red, 91.1 green, 48.4 off).
    # The others: worst case 67.8 (Hexdrive, red), 80.6 (Grind, green), 64.8 (delay, small
    # green) and 71.2 (reverb, green). On the screen the Zuul's and the Grind's were lit.
    "Zuul pedal": ((0.3379, -1.0269), (0.1623, -0.7702), 0.0676, ("on", "off")),
    "Hexdrive pedal": ((0.3650, -1.2837), (0.2298, -1.1891), 0.0676, ("on", "off")),
    "Grind pedal": ((0.3515, -0.9594), (0.2433, -0.6891), 0.0676, ("on", "off")),
    "Delay pedal": ((1.2974, 0.5406), (1.4460, 0.3515), 0.0676, ("on", "off")),
    "Reverb pedal": ((0.3379, -1.4188), (0.7433, -1.3783), 0.0676, ("on", "off")),
})
FORTIN_SWITCH_PROBES = dict(TOP_BAR_SWITCH_PROBES, **CAB_PANEL_SWITCH_PROBES)
# The tuner window's mute button is the framework's own, as on the Petrucci X.
FORTIN_SWITCH_PROBES["Mute while tuning"] = ArchetypeXProfile.switchProbes["Mute while tuning"]


class FortinProfile(ArchetypeXProfile):
    """The Neural DSP Fortin Nameless Suite X, standalone and VST3."""

    id = "fortin"
    displayName = "Fortin Nameless Suite X"

    # The editor's UI Automation name in the run of 2026-11-20.
    markers = ("Fortin Nameless Suite X",)

    executableNames = (
        "fortin nameless suite x",
        "Fortin Nameless Suite X",
        "FORTIN NAMELESS SUITE X",
    )

    # The five section buttons at the top, left to right, by their HelpText in the run.
    sectionNames = ("Pre Effects", "Amp", "Cab", "EQ", "Post Effects")
    VIEW_KEYS = VIEW_KEYS

    friendlyNames = {
        "Pre Effects": "Pre Effects section",
        "Amp": "Amp section",
        "Cab": "Cab section",
        "EQ": "EQ section",
        "Post Effects": "Post Effects section",
        TUNER_HELP: "Tuner",
    }

    # One amplifier, and no selectors.
    ampModelNames = ("Nameless",)

    enumValues = {
        "Delay sync": ("free", "DAW sync", "tap sync"),
        "Delay note": NOTE_VALUE_NAMES,
    }

    KNOB_UNITS = FORTIN_KNOB_UNITS
    VIEW_SLIDER_LANDMARKS = VIEW_SLIDER_LANDMARKS
    VIEW_BUTTON_LANDMARKS = VIEW_BUTTON_LANDMARKS
    VIEW_MODULES = VIEW_MODULES
    MODULE_SWITCHES = MODULE_SWITCHES
    TAB_IN_MODULE_ORDER = TAB_IN_MODULE_ORDER
    VIEW_POINTER_KNOBS = VIEW_POINTER_KNOBS
    NOTE_KNOB_NAMES = NOTE_KNOB_NAMES
    DELAY_DISPLAYS = DELAY_DISPLAYS
    AMP_KNOB_TABLES = (AMP_KNOBS,)
    AMP_SWITCH_TABLES = (AMP_SWITCHES,)
    decorativeNames = DECORATIVE_NAMES

    # The Cab view's side panels are the Nolly's: ROOM SEND and PHASE on each side.
    CAPTION_STATE_KEYS = ROOM_SEND_CAPTION_STATE_KEYS
    SIDED_CAPTIONS = ROOM_SEND_SIDED_CAPTIONS
    CAB_SIDED_NAMES = ROOM_SEND_CAB_SIDED_NAMES

    # See FORTIN_TIP_PROBES and FORTIN_SWITCH_PROBES above. The Cab view's miniature has the
    # amp's switches under the same names, and is read under "Mini <name>" (the power switch
    # under MINI_POWER_STATE_KEYS): its switches are 24 and 36 pixels high (0.031 and 0.046 of
    # the editor), the Amp view's 48 and 79 (0.061 and 0.101).
    POWER_STATE_KEYS = POWER_STATE_KEYS
    MINI_POWER_STATE_KEYS = MINI_POWER_STATE_KEYS
    FULL_SIZE_STATE_NAMES = frozenset(("Amp power switch", "Standby switch", "Amp input"))
    MINI_SWITCH_MAX_HEIGHT = 0.054
    switchProbes = FORTIN_SWITCH_PROBES
    tipProbes = FORTIN_TIP_PROBES

    # ---------- telling the views and the amplifier apart ----------

    def _viewFromSliders(self, sliders, geometry):
        """EQ is the only view with the low pass filter's 20000 hertz, and Post Effects the only
        one with the reverb's decay (to 8 seconds) or the delay's time (to 6000 milliseconds).
        Pre Effects has its pedals' big knobs, 80 and 132 pixels, with their tops between a
        quarter and 0.45 of the way down; the amp's knobs are 45 pixels and the top bar's 60."""
        _left, top, width, height = geometry
        postfx = pedalKnob = False
        for element in sliders:
            maximum = _prop(element, PROP_RANGE_MAX)
            try:
                maximum = float(maximum)
            except (TypeError, ValueError):
                maximum = None
            if maximum == 20000.0:
                return "eq"
            if maximum in (8.0, 6000.0):
                postfx = True
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4:
                continue
            if rect[2] / width >= 0.075 and 0.25 <= (rect[1] - top) / height <= 0.45:
                pedalKnob = True
        if postfx:
            return "postfx"
        return "prefx" if pedalKnob else "amp"

    def _panelIn(self, controller, band, maxWidthFraction):
        """The amp's panel, or the Cab view's miniature of it. The headlight, left of the power
        switch, is neither a knob nor a switch (see HEADLIGHTS); the power switch is the
        left-most button after it (POWER, then STANDBY)."""
        parts = self._panelParts(controller, band, maxWidthFraction)
        if parts is None:
            return None
        knobs, buttons = (self._withoutHeadlight(controller, entries) for entries in parts)
        if not knobs or not buttons:
            return None
        power = buttons[0]
        return self._panel([entry for entry in knobs if entry[0] > power[0]], buttons[1:], power)

    def _withoutHeadlight(self, controller, entries):
        """The (x, rectangle, element) entries but any standing at the headlight's place."""
        kept = []
        for entry in entries:
            fractions = self._fractions(controller, entry[1])
            if fractions is not None:
                xF, yF, wF, hF = fractions
                if any(abs(yF + hF / 2.0 - cy) <= 0.02 and abs(xF + wF / 2.0 - cx) <= 0.012 for cy, cx in HEADLIGHTS):
                    continue
            kept.append(entry)
        return kept

    def _ampIndexOf(self, knobs, switches):
        """The one amplifier, for a panel with its seven knobs; None for anything else, which is
        how a half-built tree is turned away."""
        return 0 if len(knobs) == len(AMP_KNOBS) else None

    # ---------- naming ----------

    def positionalLabel(self, obj, controller):
        if obj.ampNativeRole == controlTypes.Role.UNKNOWN:
            name = self._backgroundName(obj, controller)
            if name:
                return name
        return super(FortinProfile, self).positionalLabel(obj, controller)

    def _backgroundName(self, obj, controller):
        """A name for the backgrounds that are in the tree as controls of their own: a pedal's
        (217 by 430, the delay's 440 by 372, the reverb's 236 by 453), a microphone panel's (160
        by 527) and the two pictures of each microphone in front of its speaker (250 by 250).
        None of them does anything. As the Nolly's, but for the delay pedal's height."""
        if self._tunerControlName(obj, controller) is not None \
                or self._midiControlName(obj, controller) is not None:
            return ""
        fractions = self._objFractions(obj, controller)
        if fractions is None:
            return ""
        _xF, yF, wF, hF = fractions
        view = self.viewOf(controller)
        if view in ("prefx", "postfx") and 0.20 <= wF <= 0.50 and 0.45 <= hF <= 0.60:
            return "Pedal background"
        if view == "cab":
            if 0.14 <= wF <= 0.17 and 0.62 <= hF <= 0.72:
                return "Microphone panel background"
            if 0.22 <= wF <= 0.27 and 0.28 <= hF <= 0.36 and yF > 0.6:
                return "Microphone picture"
        return ""

    def passedOver(self, obj):
        """The EQ's two captions in the Tab ring (see EQ_CAPTIONS) too."""
        if getattr(obj, "ampNativeRole", None) == controlTypes.Role.STATICTEXT:
            element = getattr(obj, "UIAElement", None)
            if element is not None and (_prop(element, PROP_NAME, "") or "").strip() in EQ_CAPTIONS:
                return True
        return super(FortinProfile, self).passedOver(obj)


PROFILE = FortinProfile()
