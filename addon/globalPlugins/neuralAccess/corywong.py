# neuralAccess - the Archetype Cory Wong X profile.
#
# What is the Cory Wong's own: its six sections (a Wah section before the Nolly X's five), the
# landmark tables of their views, its three amplifiers (the D.I. Funk Console, The Clean Machine and
# The Amp Snob), the words their panels print, and its light look. The amplifier selectors, the
# row of cabinet selectors while unlinked, the amp and cab link and the C and Control+A keys it
# shares with the Nolly X (archetypex.LinkedAmpsXProfile), and what every X plug-in has in common
# is in ArchetypeXProfile there.
#
# Where it comes from, none of it measured by hand:
#   * the plug-in's own layout, read out of the VST3 (probe-results\corywong-layout), from which
#     tools\probe\Draft-XProfile.py drafted the centres below;
#   * a driven run of 2026-11-21 in REAPER, tools\probe\Probe-XViews.py --plugin corywong, which
#     showed each section on each amplifier and the link off and on, and saved the tree and a
#     picture at every stop (probe-results\corywong-views);
#   * the words the panels print, from their labels drawings (probe-results\corywong-art\svg), and
#     the manual, Archetype Cory Wong X v1.0.0.pdf, pages 10 to 18, where the panel prints none.
#
# How it differs from the Nolly X:
#   * it is drawn light: a pale pink background (255, 220, 212) with dark captions, where every
#     other X plug-in is near black. Every reading of the top bar, of the Cab view's side panels and
#     of the section buttons is the Cory Wong's own, measured on its run (notes\corywong.md, "The
#     light look on the run's pictures"); taken over from the Nolly, each would say the opposite;
#   * each amp's power lamp, a 7 pixel button in the tree, stands right of the power switch's left
#     edge, and is left out of the panel by its width (PANEL_BUTTON_MIN_WIDTH);
#   * the power switches, the EQ's power switch and the stomps are drawn alike whatever their state
#     (alwaysDrawToggleState false in the skin), so their state is read off their lamps.

import controlTypes

from . import core as engine
from .archetypex import (
    AMP_BAND_Y, CAB_PANEL_SWITCH_PROBES, KNOB_UNITS, LinkedAmpsXProfile, NOTE_VALUE_NAMES,
    ROOM_SEND_CAB_SIDED_NAMES, ROOM_SEND_CAPTION_STATE_KEYS, ROOM_SEND_SIDED_CAPTIONS, TUNER_HELP,
)
from .core import CT_BUTTON, PROP_BOUNDING_RECT, PROP_HELP_TEXT, PROP_NAME, PROP_RANGE_MAX, _prop

# The six sections in button order, as viewOf names their views.
VIEW_KEYS = ("wah", "prefx", "amp", "cab", "eq", "postfx")

# Per amplifier, its knobs and its small switches left to right, in the words the panel prints
# (the Amp view's labels drawings). The amp's own OUTPUT knob is "Amp output", as on the Nolly X, so
# that it cannot be mistaken for the Output of the top bar. Clean's first knob prints "volume"
# where the manual says GAIN.
AMP_KNOB_TABLES = (
    ("Comp", "Tube sat", "High pass", "Low pass", "Lows", "Mids", "Highs", "Amp output"),   # Funk
    ("Volume", "Bass", "Middle", "Treble", "Presence", "Amp output"),                        # Clean
    ("Volume", "Bass", "Middle", "Treble", "Master", "Presence", "Amp output"),              # Snob
)
AMP_SWITCH_TABLES = (
    ("Comp attack", "Lows frequency", "Mids frequency", "Highs frequency"),                  # Funk
    ("Bright switch",),                                                                      # Clean
    ("Bright switch", "Drive switch"),                                                       # Snob
)

# The EQ's nine bands, as the plug-in names its settings and prints them (the EQ's labels drawing).
EQ_BANDS = ("65 hertz", "125 hertz", "250 hertz", "500 hertz", "1 kilohertz",
            "2 kilohertz", "4 kilohertz", "8 kilohertz", "16 kilohertz")

# What each knob is counted in, for a knob with no display of its own.
CORY_KNOB_UNITS = dict(KNOB_UNITS, **{
    "Left mic level": "decibels",
    "Right mic level": "decibels",
    "Left room level": "decibels",
    "Right room level": "decibels",
    "High pass filter": "hertz",
    "Low pass filter": "hertz",
    # The Funk console's filters and tone stack.
    "High pass": "hertz",
    "Low pass": "hertz",
    "Lows": "decibels",
    "Mids": "decibels",
    "Highs": "decibels",
    "Postal Service range": "hertz",
    "Postal Service sensitivity": "decibels",
    "Postal Service attack": "milliseconds",
    "Postal Service decay": "milliseconds",
    "Chorus rate": "hertz",
    "Delay low cut": "hertz",
    "Delay high cut": "hertz",
    "Delay time left": "milliseconds",
    "Delay time right": "milliseconds",
    "Delay tempo": "beats per minute",
})
for _band in EQ_BANDS:
    CORY_KNOB_UNITS["Band %s" % _band] = "decibels"

# Each view's own controls as (centre y fraction, centre x fraction, name), from the layout map,
# which the run's tree matches to the pixel but for the delay's tempo box (below). The names are the
# ones printed on the pedals, with the pedal's name in front.
VIEW_SLIDER_LANDMARKS = {
    "wah": (
        # The treadle and the POSITION knob are both wired to Wah Position, as on the Petrucci X.
        (0.5448, 0.4907, "Wah pedal"),
        (0.3696, 0.8906, "Wah position"),
        (0.6023, 0.8496, "Wah attack"),
        (0.6023, 0.9316, "Wah release"),
        (0.7340, 0.8906, "Wah sensitivity"),
    ),
    "prefx": (
        (0.4003, 0.0781, "Postal Service range"),
        (0.4003, 0.1904, "Postal Service sensitivity"),
        (0.4808, 0.0781, "Postal Service attack"),
        (0.4808, 0.1904, "Postal Service decay"),
        (0.4003, 0.3232, "Compressor blend"),
        (0.4003, 0.4355, "Compressor tone"),
        (0.4808, 0.3232, "Compression"),
        (0.4808, 0.4355, "Compressor volume"),
        (0.4003, 0.6230, "Tuber tone"),
        (0.4808, 0.5674, "Tuber drive"),
        (0.4808, 0.6797, "Tuber level"),
        (0.4003, 0.8652, "Big Rig tone"),
        (0.4808, 0.8096, "Big Rig drive"),
        (0.4808, 0.9219, "Big Rig level"),
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
    ),
    "eq": (
        (0.5384, 0.1924, "High pass filter"),
        (0.5384, 0.8027, "Low pass filter"),
        (0.5435, 0.2686, "Band 65 hertz"),
        (0.5435, 0.3262, "Band 125 hertz"),
        (0.5435, 0.3828, "Band 250 hertz"),
        (0.5435, 0.4404, "Band 500 hertz"),
        (0.5435, 0.4971, "Band 1 kilohertz"),
        (0.5435, 0.5547, "Band 2 kilohertz"),
        (0.5435, 0.6123, "Band 4 kilohertz"),
        (0.5435, 0.6689, "Band 8 kilohertz"),
        (0.5435, 0.7256, "Band 16 kilohertz"),
    ),
    "postfx": (
        (0.3990, 0.1699, "Chorus mix"),
        (0.4795, 0.1143, "Chorus rate"),
        (0.4795, 0.2266, "Chorus width"),
        (0.3798, 0.4307, "Delay sync"),
        (0.4271, 0.3623, "Delay mix"),
        (0.4271, 0.6406, "Delay feedback"),
        # The display. While the delay is free each side's time is a read-only number display (the
        # layout's timeLNumberEditor and timeRNumberEditor), a slider in the tree; synced, a text
        # with the note stands there (DELAY_DISPLAYS). The tempo box between them is at 471,340 80
        # by 20 in the run's tree, on DAW and DUAL, where the layout puts it at 516.
        (0.4476, 0.4497, "Delay time left display"),
        (0.4476, 0.4990, "Delay tempo"),
        (0.4476, 0.5522, "Delay time right display"),
        (0.5256, 0.3623, "Delay low cut"),
        # While the delay is synced a note-value knob stands at each time knob's place.
        (0.5256, 0.4551, "Delay time left"),
        (0.5256, 0.5479, "Delay time right"),
        (0.5256, 0.6406, "Delay high cut"),
        (0.3977, 0.7744, "Wash mix"),
        (0.3977, 0.8916, "Wash decay"),
        (0.4821, 0.7744, "Wash low cut"),
        (0.4821, 0.8916, "Wash high cut"),
    ),
}
VIEW_BUTTON_LANDMARKS = {
    # WAH and AUTO-WAH are named buttons, the switches themselves; their little rockers, 0.014
    # right of each caption's centre, are passed over.
    "wah": (
        (0.3120, 0.9062, "Wah switch"),
        (0.5448, 0.9229, "Auto wah switch"),
    ),
    # Each pedal's on/off is its stomp, "<pedal> pedal", which says its state from the pedal's
    # lamp. The lamps ignore clicks (the layout's activeLed).
    "prefx": (
        (0.5345, 0.1348, "Postal Service pedal lamp"),
        (0.6829, 0.1348, "Postal Service pedal"),
        (0.5345, 0.3789, "Compressor pedal lamp"),
        (0.6829, 0.3770, "Compressor pedal"),
        (0.5345, 0.6230, "Tuber pedal lamp"),
        (0.6829, 0.6221, "Tuber pedal"),
        (0.5332, 0.8662, "Big Rig pedal lamp"),
        (0.6829, 0.8652, "Big Rig pedal"),
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
    ),
    # EQ power is the switch at the left; its lamp, at the right, says its state (CORY_SWITCH_PROBES).
    "eq": (
        (0.6330, 0.1924, "EQ power"),
        (0.6330, 0.8018, "EQ power lamp"),
    ),
    "postfx": (
        (0.5332, 0.1699, "Chorus pedal lamp"),
        (0.7136, 0.1699, "Chorus pedal"),
        (0.3798, 0.5742, "Delay mode"),
        (0.6061, 0.3623, "Delay pedal lamp"),
        (0.6509, 0.3623, "Delay pedal"),
        # The tempo light is in the tree in every sync mode; the Tap tempo stomp (tempoSwitch) was
        # not, with the delay on DAW, as on the Fortin.
        (0.6061, 0.6406, "Tap tempo light"),
        (0.6509, 0.6396, "Tap tempo"),
        (0.3990, 0.8340, "Wash shimmer"),
        (0.5320, 0.8340, "Wash pedal lamp"),
        (0.7110, 0.8340, "Wash pedal"),
    ),
}

# The note-value knobs that take the time knobs' places while the delay follows a tempo.
NOTE_KNOB_NAMES = {"Delay time left": "Delay note left", "Delay time right": "Delay note right"}
# The text boxes standing on the delay's display: (centre y, centre x, name while free, name while
# synced). Synced, each is the layout's noteLTextEditor or noteRTextEditor, a nameless text that
# takes focus (430,340 and 540,340, 61 by 20, "1/4" and "1/8" in the run).
DELAY_DISPLAYS = {
    "postfx": ((0.4476, 0.4497, "Delay time left readout", "Delay note left readout"),
               (0.4476, 0.5571, "Delay time right readout", "Delay note right readout")),
}

# The amps' lamps and the Cab miniatures' are named by their size, not by a place: the miniature's
# 3 pixel lamp stands within 0.015 of the editor's height of its 10 pixel power switch.
AMP_POWER_LAMP = "Amp power lamp"

# Stops that do nothing: lamps, backgrounds, the little rockers whose captions are the switches,
# and the delay's two read-only time displays (Hadi heard the Fortin's as a second slider of the
# same time in 0.14.0). Tab passes over them and a landing never picks them.
DECORATIVE_NAMES = frozenset((
    "Postal Service pedal lamp", "Compressor pedal lamp", "Tuber pedal lamp", "Big Rig pedal lamp",
    "Chorus pedal lamp", "Delay pedal lamp", "Tap tempo light", "Wash pedal lamp", "EQ power lamp",
    AMP_POWER_LAMP,
    "Gate switch", "Doubler switch", "Wah switch", "Auto wah switch", "Left room switch", "Right room switch",
    "View background", "Pedal background", "Microphone panel background", "Microphone picture",
    "Delay time left display", "Delay time right display",
))

# The EQ's two captions in the plug-in's Tab ring, hpfLabel and lpfLabel, text stops in the run.
EQ_CAPTIONS = frozenset(("HPF :", "LPF :"))

# The modules the bracket keys step through, left to right but for the Cab section: (name, axis,
# low, high). The pedals stand at 35 to 240, 288 to 489, 536 to 741 and 786 to 987 pixels of 1024 in
# Pre Effects, and at 73 to 263, 334 to 693 and 756 to 951 in Post Effects.
VIEW_MODULES = {
    "wah": (("Wah", "x", 0.0, 1.0),),
    "prefx": (("Postal Service", "x", 0.0, 0.258), ("Compressor", "x", 0.258, 0.500),
              ("Tuber", "x", 0.500, 0.746), ("Big Rig", "x", 0.746, 1.0)),
    "amp": (("Amplifier", "x", 0.0, 1.0),),
    # Left microphone, right microphone, then the amp, as on the Nolly X (Hadi, 2026-11-15).
    "cab": (("Left microphone", "x", 0.0, 0.25), ("Right microphone", "x", 0.75, 1.0),
            ("Amplifier", "x", 0.25, 0.75)),
    "eq": (("EQ", "x", 0.0, 1.0),),
    "postfx": (("Chorus", "x", 0.0, 0.292), ("Delay", "x", 0.292, 0.708), ("Wash", "x", 0.708, 1.0)),
}
# Each module's on/off switch, first in its Tab order (see RING_TYPES in archetypex.py).
MODULE_SWITCHES = frozenset((
    "WAH",
    "Postal Service pedal", "Compressor pedal", "Tuber pedal", "Big Rig pedal",
    "Amp power switch",
    "Left microphone switch", "Right microphone switch",
    "EQ power",
    "Chorus pedal", "Delay pedal", "Wash pedal",
))
# The plug-in's Post Effects tree goes Wash, Chorus, Delay; Pre Effects goes pedal by pedal.
TAB_IN_MODULE_ORDER = frozenset(("cab", "postfx"))
# The Funk panel's tree has its eight knobs, then its four switches; Tab takes the panel as it reads.
TAB_LEFT_TO_RIGHT_MODULES = frozenset(("Amplifier",))

# The pedals' knobs that say where their pointer points: the round knobs whose value is a
# percentage and is shown nowhere. Left out: the knobs with a unit (CORY_KNOB_UNITS) and the delay's
# time and note knobs, which have the display.
VIEW_POINTER_KNOBS = {
    "prefx": frozenset((
        "Compressor blend", "Compressor tone", "Compression", "Compressor volume",
        "Tuber tone", "Tuber drive", "Tuber level", "Big Rig tone", "Big Rig drive", "Big Rig level")),
    "postfx": frozenset((
        "Chorus mix", "Chorus width", "Delay mix", "Delay feedback",
        "Wash mix", "Wash decay", "Wash low cut", "Wash high cut")),
}

# The delay's Time R is disabled on SINGLE (the manual's page 16), and says "inactive" while the
# Delay mode switch reads single.
DISABLED_ON_SINGLE = frozenset(("Delay time right", "Delay note right"))

# ---- reading switch positions off the screen ----
#
# No switch of the Cory Wong says its state in the tree. Every reading below was measured on the
# run of 2026-11-21 or on rebuilds from the plug-in's own pictures (tools\probe\Find-XSwitchSpots.py,
# probe-results\corywong-switch-spots.txt, notes\corywong.md).
#
# 1. The top bar's, the wah's and the Cab side panels' little rockers and their captions, one box
#    at the places the Nolly's are read (archetypex._rocker). On this look a rocker that is on is a
#    dark filled pill, and one that is off an outline with pink inside, so the dark word comes
#    first. The box is held against the way from the control's darkest point to its brightest
#    (core.PROBE_OF_RANGE): on, it reads 0.08 of that way at every size from 0.5 to 2 times, and
#    about 0 on a panel the plug-in dims; off, 1.00 at full size, 0.60 or more at 0.75, 1.25 and
#    1.5 times, and 0.29 at the plug-in's Small size (0.715), where the box catches some outline.
#    Against the brightest point alone, as on the dark plug-ins, an off rocker read 0.84 at 1.5
#    times, under any line that would still have said "on" for a dimmed one.
_ROCKER_BOX = (2 / 1024.0, 4 / 782.0)
_ROCKER_LINE = 0.2


def _rocker(x, y, words):
    return (x / 1024.0 + 0.00001, y / 782.0 + 0.00001, _ROCKER_LINE, words, _ROCKER_BOX, engine.PROBE_OF_RANGE)


CORY_SWITCH_PROBES = {
    "Gate switch": _rocker(9, 4, ("gate on", "gate off")),
    "Doubler switch": _rocker(9, 4, ("doubler on", "doubler off")),
    # A caption that is itself the switch (GATE, DOUBLER, WAH, AUTO-WAH, ROOM SEND) is read at its
    # rocker's own rectangle (switchAnchor), not at an offset from the caption's corner: at 0.75
    # times the two round differently, and AUTO-WAH on read "off" (the final review, 2026-11-21).
    "Gate": _rocker(9, 4, ("on", "off")),
    "Doubler": _rocker(9, 4, ("on", "off")),
    "Wah switch": _rocker(9, 4, ("wah on", "wah off")),
    "Auto wah switch": _rocker(9, 4, ("auto wah on", "auto wah off")),
    "Wah": _rocker(9, 4, ("on", "off")),
    "Auto wah": _rocker(9, 4, ("on", "off")),
    "Left room switch": _rocker(9, 4, ("room send on", "room send off")),
    "Right room switch": _rocker(9, 4, ("room send on", "room send off")),
    "Left room send": _rocker(9, 4, ("on", "off")),
    "Right room send": _rocker(9, 4, ("on", "off")),
    # A microphone's on/off button, at the Nolly's place. Its background is light while the
    # microphone is on and filled with a darker grey, its symbol light, while it is off, so the box
    # stands at the button's brightest point on (1.00 of the way from its darkest, the symbol's
    # stroke, on the run's left side) and at its darkest off (0.00 on the right side): the mirror of
    # the Nolly's.
    "Left microphone switch": (0.01367, 0.03325, 0.5, ("off", "on"), (0.00391, 0.00512), engine.PROBE_OF_RANGE),
    "Right microphone switch": (0.01367, 0.03325, 0.5, ("off", "on"), (0.00391, 0.00512), engine.PROBE_OF_RANGE),
    # PHASE, at the Nolly's place: the symbol is dark here, so the dot it gains when inverted is
    # dark too. Both sides read 0.92 and 0.82 of the way, normal, in the run (the right side faded,
    # its microphone off). Against the brightest point alone, as until the final review, a dot on a
    # faded side stayed above the line and said "normal" (2026-11-21).
    "Left phase": (0.05176, 0.00639, 0.5, ("inverted", "normal"), (0.00293, 0.00384), engine.PROBE_OF_RANGE),
    "Right phase": (0.05176, 0.00639, 0.5, ("inverted", "normal"), (0.00293, 0.00384), engine.PROBE_OF_RANGE),
    # 2. Lamps read where they stand (switchAnchor gives the lamp's own rectangle): the mean of a
    #    box in the lamp against the way from the lamp's darkest point to its brightest. Rebuilt lit
    #    and unlit in four ways of scaling, with the box a pixel off every way, the EQ's lamp reads
    #    0.82 to 0.91 lit and 0.13 to 0.36 unlit with a box of 6 pixels at its middle; the Funk's
    #    and the Snob's power lamps 0.68 to 1.00 lit and 0.00 to 0.53 unlit with the one pixel at
    #    their middle (probe-results\corywong-measures\measure_lamps.py --range). That way, unlike
    #    the brightest point alone, is the same however the plug-in fades a section that is off,
    #    towards black or towards its pink. The Clean's unlit lamp, on its green panel, can read as
    #    bright as a lit one, and the Cab miniatures' lamps are 3 pixels: those power switches have
    #    no reading.
    "EQ power": (7 / 1024.0, 7 / 782.0, 0.6, ("off", "on"), (6 / 1024.0, 6 / 782.0), engine.PROBE_OF_RANGE),
    "Funk amp power switch": (3 / 1024.0, 3 / 782.0, 0.6, ("amp off", "amp on"), (1 / 1024.0, 1 / 782.0),
                              engine.PROBE_OF_RANGE),
    "Snob amp power switch": (3 / 1024.0, 3 / 782.0, 0.6, ("amp off", "amp on"), (1 / 1024.0, 1 / 782.0),
                              engine.PROBE_OF_RANGE),
}
# The tuner window's mute button has no reading here: the run did not open the tuner, and the
# reading every other X plug-in shares was measured on a dark window.


def _lampSpots(lamp, a, b, stomp, words, gap=None):
    """A stomp's two spots, found on its 16 pixel lamp (each spot's corner in the lamp, a box of 5
    pixels), carried into the stomp's own rectangle, 70 pixels square: the stomps spring back, so
    their own pictures say nothing. gap, when given, is how far apart the spots must stand for a
    word to be said, in place of core's 20."""
    (lx, ly), (sx, sy) = lamp, stomp
    probe = (((lx + a[0] - sx) / 70.0 + 0.0001, (ly + a[1] - sy) / 70.0 + 0.0001),
             ((lx + b[0] - sx) / 70.0 + 0.0001, (ly + b[1] - sy) / 70.0 + 0.0001), 5 / 70.0, words)
    return probe if gap is None else probe + (gap,)


def _miniSpots(a, b, words, gap):
    """A Cab miniature toggle's two 2 pixel spots, each corner in the 14 pixel switch, the first word
    said when the first spot is the brighter by gap or more."""
    return ((a[0] / 14.0 + 0.0001, a[1] / 14.0 + 0.0001), (b[0] / 14.0 + 0.0001, b[1] / 14.0 + 0.0001), 2 / 14.0,
            words, gap)


# 3. Two spots, the first word said when the first spot is the brighter by 20 or more.
#    * The amps' small toggles, chrome levers on their own pictures: a worst case of 27.2 over four
#      ways of scaling and a pixel's shift. Up is SLOW, BRIGHT on and DRIVE on, and 150 Hz, 600 Hz
#      and 2.5 kHz, as the panels print them and the manual says.
#    * The delay's mode switch, leaning left for SINGLE and right for DUAL: 26.0.
#    * Each stomp, from its pedal's lamp: of the pairs that never lean the wrong way by more than
#      12 over the four ways of scaling and a pixel's shift, the one whose spots stand furthest apart
#      at the plug-in's own size, lit and unlit (30 to 60). So another scaling makes them silent,
#      never wrong. The compressor's lamp, on a blue pedal, stands only 16.8 apart unlit at best, and
#      speaks at 10 apart instead (the fifth entry, as the Soldano's Bright), leaning the wrong way
#      by 8.5 at most. The colour reading the Soldano's lamps use does not tell these lamps apart.
CORY_TIP_PROBES = {
    "Input mode switch": ((1.3637, 0.6042), (1.3637, 0.0834), 0.25, ("stereo", "mono")),
    "Comp attack": ((0.3930, 0.3215), (0.3930, 0.5001), 0.1787, ("slow", "fast")),
    "Lows frequency": ((0.3930, 0.5001), (0.3930, 0.3215), 0.1787, ("225 hertz", "150 hertz")),
    "Mids frequency": ((0.3930, 0.5001), (0.3930, 0.3215), 0.1787, ("900 hertz", "600 hertz")),
    "Highs frequency": ((0.3930, 0.5001), (0.3930, 0.3215), 0.1787, ("4 kilohertz", "2.5 kilohertz")),
    "Bright switch": ((0.3930, 0.3215), (0.3930, 0.5001), 0.1787, ("on", "off")),
    "Drive switch": ((0.3930, 0.3215), (0.3930, 0.5001), 0.1787, ("on", "off")),
    "Delay mode": ((0.1945, 0.3057), (0.7779, 0.2223), 0.1390, ("dual", "single")),
    # The Wash's SHIMMER, a push button: off its cap stands high with a deep shadow below, on it
    # sits pressed in a dark ring. 4 pixel spots below and above the cap stand 55.9 apart on and
    # 47.2 off at the plug-in's own size, and lean the wrong way by 1.7 at most over the four ways
    # of scaling and a pixel's shift (probe-results\corywong-measures\shimmer_pairs.py). The spot
    # finder's 5 pixel pair stood 14.5 apart on Hadi's screen, and 0.16.0 said no position (his
    # report, 2026-11-21).
    "Wash shimmer": ((14 / 34.0 + 0.0001, 24 / 34.0 + 0.0001), (21 / 34.0 + 0.0001, 8 / 34.0 + 0.0001), 4 / 34.0,
                     ("on", "off")),
    "Postal Service pedal": _lampSpots((130, 410), (8, 9), (10, 1), (103, 499), ("on", "off")),
    "Compressor pedal": _lampSpots((380, 410), (7, 10), (10, 1), (351, 499), ("on", "off"), 10),
    "Tuber pedal": _lampSpots((630, 410), (8, 8), (10, 10), (602, 499), ("on", "off")),
    "Big Rig pedal": _lampSpots((879, 409), (4, 10), (10, 1), (851, 499), ("on", "off")),
    "Chorus pedal": _lampSpots((166, 409), (7, 8), (10, 1), (139, 523), ("on", "off")),
    "Delay pedal": _lampSpots((363, 466), (7, 9), (10, 1), (336, 474), ("on", "off")),
    "Wash pedal": _lampSpots((846, 408), (6, 9), (1, 1), (819, 521), ("on", "off")),
    # The Cab view's miniature toggles, 14 pixels: 2 pixel spots, each pair speaking at a distance
    # of its own (the fifth entry), above the furthest it leans the wrong way over the four ways of
    # scaling and a pixel's shift and at most two thirds of how far apart it stands at the
    # plug-in's own size (probe-results\corywong-measures\mini_pairs.py). The Funk's attack: 101.4
    # and 104.3 apart, leaning 41.5 at worst, speaking at 55. Its frequency switches and the Snob's
    # Bright and Drive: 117.2 and 124.7 apart, leaning 53.0, speaking at 65. The Clean's Bright is
    # read at the Snob's spots: the pair the search chose for it (11,1 and 6,8, one spot steady on
    # the panel) said "on" for off with the whole editor drawn at 0.75 times, 57 apart, past any
    # threshold that still lets it speak; the Snob's pair, whose spots move apart, is silent there
    # and right at full size and at 1.5 times. Added after 0.16.1, on Hadi's question whether they
    # could be read (2026-11-21).
    "Mini Comp attack": _miniSpots((5, 11), (6, 8), ("slow", "fast"), 55),
    "Mini Lows frequency": _miniSpots((6, 8), (6, 10), ("225 hertz", "150 hertz"), 65),
    "Mini Mids frequency": _miniSpots((6, 8), (6, 10), ("900 hertz", "600 hertz"), 65),
    "Mini Highs frequency": _miniSpots((6, 8), (6, 10), ("4 kilohertz", "2.5 kilohertz"), 65),
    "Mini Clean bright switch": _miniSpots((6, 10), (6, 8), ("on", "off"), 65),
    "Mini Snob bright switch": _miniSpots((6, 10), (6, 8), ("on", "off"), 65),
    "Mini Drive switch": _miniSpots((6, 10), (6, 8), ("on", "off"), 65),
}

POWER_STATE_KEYS = {"Funk": "Funk amp power switch", "Clean": "Clean amp power switch",
                    "Snob": "Snob amp power switch"}
# Filed so that the miniature never borrows the full-size reading; nothing is filed under them.
MINI_POWER_STATE_KEYS = {"Funk": "Mini Funk amp power switch", "Clean": "Mini Clean amp power switch",
                         "Snob": "Mini Snob amp power switch"}

# The self-check's boxes (core.AmpProfile.screenReferences), chosen by
# tools\probe\Find-ScreenReferences.py --light from the run's 17 pictures, where each read alike
# within 2: two corners of the flat pink background and the INPUT MODE and OUTPUT captions taken
# whole, which vary 1.4 and 1.9 at 0.75 to 1.5 times the size.
CORY_TOP_BAR_REFERENCES = (
    (1014 / 1024.0, 124 / 782.0, 6 / 1024.0, 6 / 782.0, (255.0, 220.0, 212.0)),
    (4 / 1024.0, 4 / 782.0, 6 / 1024.0, 6 / 782.0, (255.0, 220.0, 212.0)),
    (345 / 1024.0, 84 / 782.0, 80 / 1024.0, 14 / 782.0, (218.9, 186.7, 179.2)),
    (909 / 1024.0, 84 / 782.0, 53 / 1024.0, 14 / 782.0, (222.6, 190.1, 182.6)),
)

# Where the EQ's lamp stands, and how near a power switch's lamp stands to it (fractions of the
# editor): the lamp is 15 pixels above the switch's top and 7 right of its left edge.
EQ_LAMP_CENTRE = (0.6330, 0.8018)
POWER_LAMP_REACH = (0.03, 0.012)
# The captions that are switches, read at the rocker inside each (switchAnchor): the rockers are
# 20 pixels wide (0.0195 of the editor).
CAPTION_SWITCHES = frozenset(("Gate", "Doubler", "Wah", "Auto wah", "Left room send", "Right room send"))
ROCKER_WIDTH = (0.015, 0.025)


class CoryWongProfile(LinkedAmpsXProfile):
    """The Neural DSP Archetype Cory Wong X, standalone and VST3."""

    id = "corywong"
    displayName = "Archetype Cory Wong X"

    # The editor's UI Automation name in the run of 2026-11-21.
    markers = ("Archetype Cory Wong X",)

    executableNames = (
        "archetype cory wong x",
        "Archetype Cory Wong X",
        "ARCHETYPE CORY WONG X",
    )

    # The six section buttons at the top, left to right, by their HelpText in the run.
    sectionNames = ("Wah", "Pre FX", "Amp", "Cab", "EQ", "Post FX")
    VIEW_KEYS = VIEW_KEYS

    friendlyNames = {
        "Wah": "Wah section",
        "Pre FX": "Pre FX section",
        "Amp": "Amp section",
        "Cab": "Cab section",
        "EQ": "EQ section",
        "Post FX": "Post FX section",
        TUNER_HELP: "Tuner",
    }

    # The three amplifiers, matching the selectors at the bottom, left to right. Unlinked, the row
    # of cabinet selectors under them goes by the same three names.
    ampModelNames = ("Funk", "Clean", "Snob")

    enumValues = {
        "Delay sync": ("free", "DAW sync", "tap sync"),
        "Delay note left": NOTE_VALUE_NAMES,
        "Delay note right": NOTE_VALUE_NAMES,
    }

    KNOB_UNITS = CORY_KNOB_UNITS
    VIEW_SLIDER_LANDMARKS = VIEW_SLIDER_LANDMARKS
    VIEW_BUTTON_LANDMARKS = VIEW_BUTTON_LANDMARKS
    VIEW_MODULES = VIEW_MODULES
    MODULE_SWITCHES = MODULE_SWITCHES
    TAB_IN_MODULE_ORDER = TAB_IN_MODULE_ORDER
    TAB_LEFT_TO_RIGHT_MODULES = TAB_LEFT_TO_RIGHT_MODULES
    VIEW_POINTER_KNOBS = VIEW_POINTER_KNOBS
    NOTE_KNOB_NAMES = NOTE_KNOB_NAMES
    DELAY_DISPLAYS = DELAY_DISPLAYS
    AMP_KNOB_TABLES = AMP_KNOB_TABLES
    AMP_SWITCH_TABLES = AMP_SWITCH_TABLES
    POWER_STATE_KEYS = POWER_STATE_KEYS
    MINI_POWER_STATE_KEYS = MINI_POWER_STATE_KEYS
    decorativeNames = DECORATIVE_NAMES

    # The Cab view's side panels say ROOM SEND, as the Nolly's do; WAH and AUTO-WAH are captions
    # that are the wah's switches, as GATE is the gate's.
    CAPTION_STATE_KEYS = dict(ROOM_SEND_CAPTION_STATE_KEYS, **{"AUTO-WAH": "Auto wah"})
    SIDED_CAPTIONS = ROOM_SEND_SIDED_CAPTIONS
    CAB_SIDED_NAMES = ROOM_SEND_CAB_SIDED_NAMES

    # The amps' lamps are 7 pixels wide (0.0068 of the editor), the miniatures' power switches 10
    # (0.0098): the lamps are left out of the panels before the power switch is found.
    PANEL_BUTTON_MIN_WIDTH = 0.0083
    # The Cab view's miniature amp row: knobs of 20 and 21 pixels with their tops at 358 and 359,
    # switches of 14 at 361 and 362, the power switch of 10 at 363 to 365 (0.4668, inside the
    # default band's top of 0.47 by 2.5 pixels). No other knob or button of the Cab view has its top
    # between 344 and 375, and the EQ's band sliders, tops at 349, are wider than the panel's limit.
    CAB_MINI_BAND = (0.44, 0.48)
    # The miniature's switches are 14 pixels high (0.0179) and its power switch 10, the Amp view's
    # power switch 20 (0.0256) and its toggles 28.
    MINI_SWITCH_MAX_HEIGHT = 0.022
    FULL_SIZE_STATE_NAMES = frozenset(("Amp power switch", "Bright switch", "Drive switch", "Comp attack",
                                       "Lows frequency", "Mids frequency", "Highs frequency"))

    # The pedals' backgrounds: 201 and 205 by 343 in Pre Effects, 190 and 195 by 318 and the delay's
    # 359 by 265 in Post Effects (0.186 to 0.351 of the width, 0.339 to 0.439 of the height).
    PEDAL_BACKGROUND_WIDTH = (0.17, 0.37)
    PEDAL_BACKGROUND_HEIGHT = (0.32, 0.46)
    EQ_CAPTIONS = EQ_CAPTIONS

    # The selectors' toggle states were true at all 17 stops of the run, as on the Nolly X. Their
    # pictures were not measured on this look, so with no toggle state to go by the amplifier is not
    # guessed.
    SELECTOR_MEAN_MARGIN = None

    # The section buttons' icons are dark on the pink bar, and a section switched off has its icon
    # faded: read the mirror of the dark plug-ins' way (archetypex._sectionLook). On the run the Wah
    # section, off, read 0.27 and the other five 1.00, on every picture.
    SECTION_ICONS_DARK = True

    switchProbes = CORY_SWITCH_PROBES
    tipProbes = CORY_TIP_PROBES
    screenReferences = CORY_TOP_BAR_REFERENCES

    # ---------- telling the views and the amplifiers apart ----------

    def _viewFromSliders(self, sliders, geometry):
        """Each section but the Amp view has a slider maximum no other has (the layout's settings,
        as the run's tree reports them): the low pass filter's 20000 hertz and the high pass
        filter's 500 in the EQ; the chorus's rate (3 hertz), the delay's low cut (800), its free
        times (1100) and its high cut (5000) in Post FX; the Postal Service's sensitivity (54
        decibels) and range (1700 hertz) in Pre FX; the wah's sensitivity (100) in the Wah view.
        1000 is no tell, the wah's attack and the Postal Service's both ending there, and 20 is
        none, the top bar's doubler spread going to 20."""
        found = set()
        for element in sliders:
            try:
                found.add(float(_prop(element, PROP_RANGE_MAX)))
            except (TypeError, ValueError):
                continue
        if found & {20000.0, 500.0}:
            return "eq"
        if found & {3.0, 800.0, 1100.0, 5000.0}:
            return "postfx"
        if found & {54.0, 1700.0}:
            return "prefx"
        if 100.0 in found:
            return "wah"
        return "amp"

    def _ampIndexOf(self, knobs, switches):
        """Funk has eight knobs and four switches, Clean six and one, Snob seven and two."""
        return {(8, 4): 0, (6, 1): 1, (7, 2): 2}.get((len(knobs), len(switches)))

    def stateLabel(self, obj):
        """The Cab view's miniature Bright switch is read at other spots on the Clean amplifier than
        on the Snob, so its reading is filed per amplifier, as the Nolly's is."""
        label = super(CoryWongProfile, self).stateLabel(obj)
        if label == "Mini Bright switch":
            controller = obj.ampController
            mini = self.cabMiniPanel(controller) if controller is not None else None
            return "Mini %s bright switch" % mini["name"] if mini else ""
        return label

    # ---------- the lamps ----------

    def positionalLabel(self, obj, controller):
        """An amp's or a miniature's power lamp, by its width: a nameless button narrower than
        PANEL_BUTTON_MIN_WIDTH in the amp panel's band or the miniature's."""
        if obj.ampNativeRole in (controlTypes.Role.BUTTON, controlTypes.Role.TOGGLEBUTTON):
            fractions = self._objFractions(obj, controller)
            element = getattr(obj, "UIAElement", None)
            if fractions is not None and element is not None and self._isLamp(element, fractions):
                return AMP_POWER_LAMP
        return super(CoryWongProfile, self).positionalLabel(obj, controller)

    def _isLamp(self, element, fractions):
        if _prop(element, PROP_NAME, "") or _prop(element, PROP_HELP_TEXT, ""):
            return False
        return self._lampShaped(fractions)

    def _lampShaped(self, fractions):
        _xF, yF, wF, _hF = fractions
        inBand = AMP_BAND_Y[0] <= yF <= AMP_BAND_Y[1] or self.CAB_MINI_BAND[0] <= yF <= self.CAB_MINI_BAND[1]
        return inBand and 0 < wF < self.PANEL_BUTTON_MIN_WIDTH

    def _landmarkAt(self, controller, view, rect, tables=None):
        """The lamps too, for the Tab ring and a view's landing, which pass over a button by its
        landmark: in the Amp and Cab views a button of a lamp's size in the amp panel's band or the
        miniature's is the amp's power lamp."""
        if tables is None and view in ("amp", "cab"):
            fractions = self._fractions(controller, rect)
            if fractions is not None and self._lampShaped(fractions):
                return AMP_POWER_LAMP
        return super(CoryWongProfile, self)._landmarkAt(controller, view, rect, tables)

    def switchAnchor(self, controller, label, rect):
        """The lamp's own rectangle for a switch read off its lamp (EQ power, the Funk's and the
        Snob's power switches); the switch's own for the rest. None when the lamp is not found,
        and then nothing is said."""
        if label in CAPTION_SWITCHES:
            return controller._positionalSweep("rockerRect:%d,%d" % (int(rect[0]), int(rect[1])),
                                               lambda: self._rockerIn(controller, rect))
        if label == "EQ power":
            return controller._positionalSweep("eqLampRect", lambda: self._lampRect(
                controller, lambda cx, cy, w: abs(cy - EQ_LAMP_CENTRE[0]) <= 0.02
                and abs(cx - EQ_LAMP_CENTRE[1]) <= 0.012 and w >= self.PANEL_BUTTON_MIN_WIDTH))
        if label in ("Funk amp power switch", "Snob amp power switch"):
            fractions = self._fractions(controller, rect)
            if fractions is None:
                return None
            xF, yF, wF, _hF = fractions
            switchX = xF + wF / 2.0

            def near(cx, cy, w):
                return (w < self.PANEL_BUTTON_MIN_WIDTH and abs(cx - switchX) <= POWER_LAMP_REACH[1]
                        and 0 < yF - cy <= POWER_LAMP_REACH[0])
            return controller._positionalSweep("powerLampRect:%d,%d" % (int(rect[0]), int(rect[1])),
                                               lambda: self._lampRect(controller, near))
        return rect

    def _rockerIn(self, controller, rect):
        """The rectangle of the nameless 20 by 12 rocker standing inside a caption switch's own
        rectangle, or None."""
        geometry = controller.clientGeometry()
        if not geometry or not rect or len(rect) < 4:
            return None
        width = geometry[2]
        for element in controller.findElements(controlType=CT_BUTTON):
            if _prop(element, PROP_NAME, "") or _prop(element, PROP_HELP_TEXT, ""):
                continue
            found = _prop(element, PROP_BOUNDING_RECT)
            if not found or len(found) < 4 or found[2] <= 0:
                continue
            if ROCKER_WIDTH[0] <= found[2] / float(width) <= ROCKER_WIDTH[1] \
                    and rect[0] <= found[0] and found[0] + found[2] <= rect[0] + rect[2] + 1 \
                    and rect[1] <= found[1] and found[1] + found[3] <= rect[1] + rect[3] + 1:
                return tuple(found[:4])
        return None

    def _lampRect(self, controller, wanted):
        for element in controller.findElements(controlType=CT_BUTTON):
            if _prop(element, PROP_NAME, "") or _prop(element, PROP_HELP_TEXT, ""):
                continue
            found = _prop(element, PROP_BOUNDING_RECT)
            fractions = self._fractions(controller, found)
            if fractions is None or found[2] <= 0:
                continue
            xF, yF, wF, hF = fractions
            if wanted(xF + wF / 2.0, yF + hF / 2.0, wF):
                return tuple(found[:4])
        return None

    # ---------- what SINGLE disables ----------

    def inactiveWord(self, obj):
        """"inactive" for Time R while the delay is on SINGLE (the manual's page 16), by the Delay
        mode switch's own reading; nothing when that cannot be read."""
        label = obj.ampLabel or ""
        if label not in DISABLED_ON_SINGLE:
            return ""
        controller = obj.ampController
        if controller is None:
            return ""
        mode = controller._positionalSweep("delayModeRect", lambda: self._landmarkRect(controller, "postfx", "Delay mode"))
        if mode is None:
            return ""
        return "inactive" if controller.switchPosition("Delay mode", mode) == "single" else ""

    def _landmarkRect(self, controller, view, name):
        """The rectangle of the button standing at a landmark of VIEW_BUTTON_LANDMARKS, or None."""
        if self.viewOf(controller) != view:
            return None
        for ly, lx, landmark in VIEW_BUTTON_LANDMARKS.get(view, ()):
            if landmark != name:
                continue
            for element in controller.findElements(controlType=CT_BUTTON):
                found = _prop(element, PROP_BOUNDING_RECT)
                fractions = self._fractions(controller, found)
                if fractions is None:
                    continue
                xF, yF, wF, hF = fractions
                if abs(yF + hF / 2.0 - ly) <= 0.02 and abs(xF + wF / 2.0 - lx) <= 0.012:
                    return tuple(found[:4])
        return None

    def formatValue(self, label, raw, minimum, maximum, unitText=None):
        """The chorus's rate runs 0.3 to 3 hertz, where the whole numbers other hertz are said in
        would lose most of the knob."""
        if label == "Chorus rate" and not unitText:
            return "%.2f hertz" % raw
        return super(CoryWongProfile, self).formatValue(label, raw, minimum, maximum, unitText)


PROFILE = CoryWongProfile()
