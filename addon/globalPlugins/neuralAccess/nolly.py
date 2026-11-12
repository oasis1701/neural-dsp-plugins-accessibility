# neuralAccess - the Archetype Nolly X profile.
#
# What is the Nolly X's own: its five sections, the landmark tables of their views, its four
# amplifiers, the amp and cab link with its two rows of selectors, and the pictures its switches
# are read from. Everything it has in common with the other X plug-ins is in archetypex.py
# (ArchetypeXProfile), where the tables below are looked up under the names they carry here.
#
# Where it comes from, none of it measured by hand:
#   * the plug-in's own layout, read out of the VST3 on 2026-11-10 (probe-results\nolly-layout);
#   * a driven run of 2026-11-11 in REAPER, tools\probe\Probe-NollyViews.py, which showed each
#     section on each amplifier and the link off and on, and saved the whole tree and a picture
#     at every stop (probe-results\nolly-views). The centres below are the tree's, and they
#     equal the layout's to the pixel;
#   * the plug-in's own pictures (tools\probe\Extract-NollyPictures.py, probe-results\nolly-art),
#     from which tools\probe\Find-NollySwitchSpots.py worked out where each switch is read.
#
# How it differs from the Petrucci X in the tree:
#   * the selectors' and the link button's toggle states are true here. In all 19 stops of the
#     run the one selector reading On was the amplifier just clicked, and the link button read
#     On exactly while unlinked. (The add-on only ever clicks; UI Automation's own Invoke and
#     Toggle would flip such a state without the plug-in doing anything.) The pictures cannot
#     stand in for them everywhere: every selector's brightest point is full white, selected or
#     not, and in the unlinked amp row even the mean brightness does not tell.
#   * unlinking does not keep the cabinet that was sounding. Linked, the cabinet follows the
#     amplifier; unlinked, it goes to the cabinet last chosen by itself (the run unlinked on
#     the Lead amplifier and the Rhythm cabinet came up selected).

import re
import time

import controlTypes
import ui
from core import callLater
from logHandler import log

from . import core as engine
from .archetypex import (
    ArchetypeXProfile, AMP_SWITCH_HUSH_S, CAPTION_STATE_KEYS, KNOB_UNITS, TOP_BAR_BACKGROUND_NAME,
    VALUE_BOX_SUFFIX,
    NOTE_VALUE_NAMES, QUICK_HUSH_S, QUICK_RETURN_MS, SECTION_CLICK_GUARD_S, SECTION_KEYS_UP_MS,
    SECTION_KEYS_UP_POLLS, SELECTOR_Y, TUNER_HELP,
)
from .core import CT_BUTTON, CT_SLIDER, CT_TEXT, PROP_BOUNDING_RECT, PROP_NAME, PROP_RANGE_MAX, _prop

# UI Automation's Toggle.ToggleState property: 0 off, 1 on.
PROP_TOGGLE_STATE = 30086

# The five sections in button order, as viewOf names their views.
VIEW_KEYS = ("prefx", "amp", "cab", "eq", "postfx")

# What each knob is counted in, for a knob with no display of its own.
NOLLY_KNOB_UNITS = dict(KNOB_UNITS, **{
    "Left mic level": "decibels",
    "Right mic level": "decibels",
    "Left room level": "decibels",
    "Right room level": "decibels",
    "High pass filter": "hertz",
    "Low pass filter": "hertz",
    "Delay 1 time": "milliseconds",
    "Delay 2 time": "milliseconds",
    "Delay 2 time display": "milliseconds",
    "Delay 2 low cut": "hertz",
    "Delay 2 high cut": "hertz",
    "Delay 2 tempo": "beats per minute",
})

# The EQ's nine bands, left to right, as the plug-in prints them under the sliders on Nolly's
# mod (all four amplifiers in the run of 2026-11-11), worded for speech. These are the names in
# VIEW_SLIDER_LANDMARKS. The captions follow the voicing: on Original they are the layout's own
# texts (EQ_BANDS_ORIGINAL), which Hadi heard on 2026-11-11. A band is named by the caption
# showing under it (NollyProfile._bandNamed), so either set, or another, is said as printed.
EQ_BANDS = ("75 hertz", "150 hertz", "250 hertz", "400 hertz", "800 hertz",
            "1.5 kilohertz", "4.5 kilohertz", "8 kilohertz", "12 kilohertz")
EQ_BANDS_ORIGINAL = ("65 hertz", "125 hertz", "250 hertz", "500 hertz", "1 kilohertz",
                     "2 kilohertz", "4 kilohertz", "8 kilohertz", "16 kilohertz")
for _band in EQ_BANDS + EQ_BANDS_ORIGINAL:
    NOLLY_KNOB_UNITS["Band %s" % _band] = "decibels"
# Which band a landmark name stands for, 0 to 8.
EQ_BAND_INDEX = dict(("Band %s" % band, index) for index, band in enumerate(EQ_BANDS))

# Each view's own controls as (centre y fraction, centre x fraction, name), from the tree dumps
# of 2026-11-11. The names are the ones printed on the pedals, with the pedal's name in front.
VIEW_SLIDER_LANDMARKS = {
    "prefx": (
        (0.4201, 0.0767, "Compression"),
        (0.4201, 0.1880, "Compressor level"),
        (0.4201, 0.3218, "Overdrive 1 drive"),
        (0.4201, 0.4331, "Overdrive 1 level"),
        (0.5058, 0.3774, "Overdrive 1 tone"),
        (0.4201, 0.5688, "Delay 1 mix"),
        (0.4201, 0.6802, "Delay 1 feedback"),
        # With Delay 1 on NOTE a note-value knob stands here instead (see NOTE_KNOB_NAMES).
        (0.5058, 0.5688, "Delay 1 time"),
        (0.5058, 0.6802, "Delay 1 tone"),
        (0.4201, 0.8140, "Overdrive 2 gain"),
        (0.4201, 0.9253, "Overdrive 2 level"),
        (0.5058, 0.8140, "Overdrive 2 bass"),
        (0.5058, 0.9253, "Overdrive 2 treble"),
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
        (0.5390, 0.1860, "High pass filter"),
        (0.5390, 0.8130, "Low pass filter"),
        # The nine bands (see EQ_BANDS), written out so that tools\probe\Summarise-
        # PetrucciLayout.py can hold them against the plug-in's layout like the rest.
        (0.5531, 0.2734, "Band 75 hertz"),
        (0.5531, 0.3301, "Band 150 hertz"),
        (0.5531, 0.3857, "Band 250 hertz"),
        (0.5531, 0.4424, "Band 400 hertz"),
        (0.5531, 0.4990, "Band 800 hertz"),
        (0.5531, 0.5557, "Band 1.5 kilohertz"),
        (0.5531, 0.6113, "Band 4.5 kilohertz"),
        (0.5531, 0.6680, "Band 8 kilohertz"),
        (0.5531, 0.7246, "Band 12 kilohertz"),
    ),
    "postfx": (
        (0.4246, 0.2920, "Delay 2 sync"),
        (0.4699, 0.2319, "Delay 2 mix"),
        (0.4699, 0.4946, "Delay 2 feedback"),
        # The delay's own display. While the delay is free it shows the time and is a slider
        # (the layout's timeNumberEditor, at 290,377); synced, a text with the note stands there.
        (0.4949, 0.3174, "Delay 2 time display"),
        # The tempo beside it: the plug-in's own (371,377 80x20) or the host's (381,377 70x20),
        # whose centres are 5 pixels apart.
        (0.4949, 0.4038, "Delay 2 tempo"),
        (0.5761, 0.2319, "Delay 2 low cut"),
        # With Delay 2 on DAW or TAP a note-value knob stands here instead.
        (0.5761, 0.3188, "Delay 2 time"),
        (0.5761, 0.4058, "Delay 2 mod"),
        (0.5761, 0.4946, "Delay 2 high cut"),
        (0.4201, 0.6636, "Reverb mix"),
        (0.4201, 0.7749, "Reverb decay"),
        (0.5058, 0.6636, "Reverb low cut"),
        (0.5058, 0.7749, "Reverb high cut"),
    ),
}
VIEW_BUTTON_LANDMARKS = {
    # Each pedal's on/off is its stomp, "<pedal> pedal", which says its state from the pedal's
    # lamp. The lamp itself ignores clicks (the layout's activeLed, allowClicks false).
    "prefx": (
        (0.4962, 0.1299, "Compressor attack"),
        (0.5882, 0.1309, "Compressor pedal lamp"),
        (0.7270, 0.1313, "Compressor pedal"),
        (0.4239, 0.3765, "Overdrive 1 bright"),
        (0.5882, 0.3770, "Overdrive 1 pedal lamp"),
        (0.7257, 0.3765, "Overdrive 1 pedal"),
        (0.4648, 0.6255, "Delay 1 sync"),
        (0.5882, 0.6240, "Delay 1 pedal lamp"),
        (0.7257, 0.6235, "Delay 1 pedal"),
        (0.5882, 0.8691, "Overdrive 2 pedal lamp"),
        (0.7257, 0.8696, "Overdrive 2 pedal"),
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
    "eq": (
        # The two captions beside the voicing switch, ORIGINAL and NOLLY'S MOD, are buttons and
        # stops, like Stereo and Mono beside the input mode switch. The switch is the one stop:
        # it says which voicing is on. The captions are passed over, and no landing picks them.
        (0.3728, 0.4531, "EQ voicing caption"),
        (0.3728, 0.5469, "EQ voicing caption"),
        (0.3734, 0.4922, "EQ voicing"),
        (0.6266, 0.1846, "EQ power"),
        (0.6407, 0.8145, "EQ lamp"),
    ),
    "postfx": (
        (0.4265, 0.4302, "Delay 2 ping pong"),
        (0.6912, 0.2300, "Delay 2 pedal"),
        (0.6957, 0.2656, "Delay 2 pedal lamp"),
        # The tempo light is a stop in every sync mode. The Tap tempo stomp itself (the layout's
        # tapTempoSwitch, 475,510 61x61) was not in the tree with the delay on DAW; on the
        # Petrucci X its like is there only while the delay is on tap.
        (0.6957, 0.4570, "Tap tempo light"),
        (0.6912, 0.4937, "Tap tempo"),
        (0.5882, 0.7188, "Reverb pedal lamp"),
        (0.7257, 0.7192, "Reverb pedal"),
    ),
}

# The note-value knob that takes a time knob's place while its delay follows a tempo.
NOTE_KNOB_NAMES = {
    "Delay 1 time": "Delay 1 note",
    "Delay 2 time": "Delay 2 note",
}
# A text box standing on a delay's display: (centre y, centre x, its name while the delay is
# free, its name while it is synced). Delay 1's is above its knobs (the layout's timeTextEditor
# at 611,286 and syncNoteTextEditor at 609,286); Delay 2's is the left half of its display.
DELAY_DISPLAYS = {
    "prefx": ((0.3772, 0.6262, "Delay 1 time readout", "Delay 1 note readout"),),
    "postfx": ((0.4949, 0.3169, "Delay 2 time readout", "Delay 2 note readout"),),
}

# Stops that do nothing: lamps, backgrounds, and the little rockers whose captions are the
# switches. Tab passes over them and a landing never picks them.
DECORATIVE_NAMES = frozenset((
    "Compressor pedal lamp", "Overdrive 1 pedal lamp", "Delay 1 pedal lamp", "Overdrive 2 pedal lamp",
    "Delay 2 pedal lamp", "Tap tempo light", "Reverb pedal lamp", "EQ lamp", "EQ voicing caption",
    "Gate switch", "Doubler switch", "Left room switch", "Right room switch",
    "View background", "Pedal background", "Microphone panel background", "Microphone picture",
))

# The EQ view's captions that the plug-in puts in its own Tab ring: hpfLabel, lpfLabel and
# band1TextLabel to band9TextLabel, the only textLabels its layout marks as taking focus. Each
# says only its caption ("HPF : HPF :", "75 Hz 75 Hz", Hadi, 2026-11-11), and the knob or
# slider it names is a stop of its own, so Tab passes over them. Told by their own names, the
# band captions of both voicings: on Original 0.12.4 passed over 250 Hz and 8 kHz, which both
# voicings print, and stopped on the rest (Hadi's log, 2026-11-11, 18:12).
EQ_CAPTIONS = frozenset(("HPF :", "LPF :", "75 Hz", "150 Hz", "250 Hz", "400 Hz", "800 Hz",
                         "1.5 kHz", "4.5 kHz", "8 kHz", "12 kHz",
                         "65 Hz", "125 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz", "16 kHz"))
# A band caption, "65 Hz" or "1.5 kHz", as (figure, "k" or "").
FREQUENCY_CAPTION = re.compile(r"^(\d+(?:\.\d+)?)\s*(k?)Hz$")

# Tab across the EQ jumps over its two runs of passed-over stops instead of passing them one
# Tab at a time. The plug-in's ring there, from Hadi's log of 2026-11-11: EQ voicing, HPF :, the
# HPF box, the nine band boxes, LPF :, the LPF box, Band 75 hertz and the other sliders, High
# pass filter, Low pass filter, EQ power, the lamp, the nine band captions, the top bar's
# background. Passed one at a time, a step whose focus came later than DECORATIVE_SKIP_S ended
# the run where it stood: Shift+Tab from Band 75 hertz stopped on the LPF box, then on the 4.5
# kilohertz box, then on the HPF box. A box takes focus slowly when Shift+Tab lands on it.
# Each run is told by the height of its row, and each end by its place: (control type, centre y,
# centre x) as fractions of the editor, the landmarks of EQ voicing, the first band and EQ power.
# The stop after the caption run is GATE, found by its name. The top bar's background, which
# comes between them in the ring, takes NVDA's focus when asked but not the plug-in's keyboard
# focus: after a jump to it the next Tab went on from EQ power, to the lamp and the captions
# (Hadi's log, 2026-11-11, 18:12:32). So Tab from EQ power goes to GATE, and Shift+Tab from GATE
# or from the background goes to EQ power.
EQ_BOX_ROW_Y = 0.4463
EQ_CAPTION_ROW_Y = 0.6624
EQ_ROW_TOLERANCE = 0.03
EQ_JUMP_ENDS = {
    "voicing": (CT_BUTTON, 0.3734, 0.4922),
    "firstBand": (CT_SLIDER, 0.5531, 0.2734),
    "power": (CT_BUTTON, 0.6266, 0.1846),
}
EQ_AFTER_CAPTION = "GATE"
# After Enter on EQ voicing, when the band captions are looked for once more: after the click,
# which goes up 230 ms after the key, and the plug-in's redraw.
VOICING_REDRAW_MS = 600

# The modules the bracket keys step through, left to right: (name, axis, low, high). The pedals
# stand at 10 to 268, 261 to 519, 514 to 772 and 765 to 1023 pixels of 1024 in Pre Effects, and
# at 137 to 603 and 611 to 869 in Post Effects.
VIEW_MODULES = {
    "prefx": (("Compressor", "x", 0.0, 0.258), ("Overdrive 1", "x", 0.258, 0.504),
              ("Delay 1", "x", 0.504, 0.750), ("Overdrive 2", "x", 0.750, 1.0)),
    "amp": (("Amplifier", "x", 0.0, 1.0),),
    "cab": (("Left microphone", "x", 0.0, 0.25), ("Amplifier", "x", 0.25, 0.75),
            ("Right microphone", "x", 0.75, 1.0)),
    "eq": (("EQ", "x", 0.0, 1.0),),
    "postfx": (("Delay 2", "x", 0.0, 0.593), ("Reverb", "x", 0.593, 1.0)),
}

# Per amplifier: the knobs left to right as printed on each panel (pictures of 2026-11-11), and
# the small switches. The amp's own OUTPUT knob is "Amp output", so that it cannot be mistaken
# for the Output of the top bar.
AMP_KNOB_TABLES = (
    ("Gain", "Bass", "Middle", "Treble", "Master", "Amp output"),                           # Clean
    ("Gain", "Bass", "Mid", "Treble", "Presence", "Depth", "Master", "Amp output"),         # Crunch
    ("Gain", "Bass", "Mid", "Treble", "Resonance", "Presence", "Master", "Amp output"),     # Rhythm
    ("Gain", "Bass", "Middle", "Treble", "Master", "Amp output"),                           # Lead
)
AMP_SWITCH_TABLES = (
    ("Bright switch",),   # Clean
    ("Bright switch",),   # Crunch
    (),                   # Rhythm
    (),                   # Lead
)

# The pedals' knobs that say where their pointer points: the round knobs whose value is a
# percentage or has no number shown anywhere (the skin's preFXKnob, a strip of 101 pictures like
# the Petrucci's). Left out: the delays' time and note knobs, which have a display.
VIEW_POINTER_KNOBS = {
    "prefx": frozenset((
        "Compression", "Compressor level",
        "Overdrive 1 drive", "Overdrive 1 level", "Overdrive 1 tone",
        "Delay 1 mix", "Delay 1 feedback", "Delay 1 tone",
        "Overdrive 2 gain", "Overdrive 2 level", "Overdrive 2 bass", "Overdrive 2 treble")),
    "postfx": frozenset((
        "Delay 2 mix", "Delay 2 feedback", "Delay 2 mod", "Delay 2 low cut", "Delay 2 high cut",
        "Reverb mix", "Reverb decay", "Reverb low cut", "Reverb high cut")),
}

# The amp power switch's state probe, per live amplifier: each amplifier has its own panel.
POWER_STATE_KEYS = {
    "Clean": "Clean amp power switch",
    "Crunch": "Crunch amp power switch",
    "Rhythm": "Rhythm amp power switch",
    "Lead": "Lead amp power switch",
}
MINI_POWER_STATE_KEYS = {
    "Clean": "Mini Clean amp power switch",
    "Crunch": "Mini Crunch amp power switch",
    "Rhythm": "Mini Rhythm amp power switch",
    "Lead": "Mini Lead amp power switch",
}


# The amp and cab link (the layout's ampCabLinkButton, 24 by 24, left of the selectors).
LINK_NAME = "Amp and cab link"
LINK_POLL_MS = 150
LINK_POLLS = 12
# ---- reading switch positions off the screen ----
#
# No switch of the Nolly X says its state in the tree. Three kinds of reading stand in for it.
#
# 1. Two spots, for the switches the plug-in draws from two pictures (NOLLY_TIP_PROBES). The
#    spots are fractions of the switch's own rectangle, and the first word is said when the
#    first spot is the brighter one. tools\probe\Find-NollySwitchSpots.py found them: it
#    rebuilds each switch on its panel in both states from the plug-in's own pictures and takes
#    the pair of spots with the widest margin over four ways of scaling and a pixel's shift.
#    Which picture is which state is the skin's (normalImage for 0 or off, downImage for 1 or
#    on). Held against the run's pictures of 2026-11-11 the rebuilt switches are within 0.4 of
#    a grey level of the real screen (1.1 and 1.7 on two of the miniatures), and every one of
#    them was read as the state the screen showed. Each switch has been seen on the screen in
#    ONE state only; the other rests on the pictures. The full report is
#    probe-results\nolly-switch-spots.txt, and its margins are quoted below as "worst case".
#
#    A pedal's stomp has no state of its own to look at (its two pictures are a stomp up and a
#    stomp down, and it springs back). It is read from the pedal's lamp, as on the Petrucci:
#    its two spots lie on the lamp, outside the stomp's own rectangle, which is why some of
#    their fractions are negative or over 1.
NOLLY_TIP_PROBES = {
    # The amp's power switch, a red rocker, the same picture on all four panels. Both spots are
    # on the rocker itself. Worst case 38; on the screen (all four amps, on) 144.7 against 86.7.
    "Clean amp power switch": ((0.5572, 0.5001), (0.3572, 0.6287), 0.0858, ("amp on", "amp off")),
    "Crunch amp power switch": ((0.5572, 0.5001), (0.3572, 0.6287), 0.0858, ("amp on", "amp off")),
    "Rhythm amp power switch": ((0.5572, 0.5001), (0.3572, 0.6287), 0.0858, ("amp on", "amp off")),
    "Lead amp power switch": ((0.5572, 0.5001), (0.3572, 0.6287), 0.0858, ("amp on", "amp off")),
    # The Bright toggle of the Clean and Crunch panels, handle up for on, and the EQ's POWER
    # toggle, which is the same picture. Both spots on the toggle itself. Worst case 26.
    "Bright switch": ((0.4401, 0.7001), (0.4201, 0.5001), 0.1001, ("on", "off")),
    "EQ power": ((0.4401, 0.7001), (0.4201, 0.5001), 0.1001, ("on", "off")),
    # The Cab view's miniature Bright switches, 26 pixels on Clean and 28 on Crunch. Worst case
    # 26 and 19; the spots as they would read on the screen are 69 to 71 apart.
    "Mini Clean bright switch": ((0.0386, 0.3463), (0.4232, 0.5001), 0.1155, ("on", "off")),
    "Mini Crunch bright switch": ((0.3930, 0.7144), (0.4287, 0.5001), 0.1072, ("on", "off")),
    # The pedals' small toggles. The compressor's leans left for SMOOTH and right for SNAPPY;
    # Overdrive 1's is up for bright; Delay 1's is up for NOTE and down for MS; Delay 2's ping
    # pong leans right for on. These are the narrowest readings here: worst case 12 to 24, and
    # 27 to 43 apart as the pictures scale at the default size. Under 20 apart nothing is said,
    # which is the safe way for them to fail at another window size.
    "Compressor attack": ((0.2106, 0.3422), (0.6317, 0.3422), 0.1317, ("Snappy", "Smooth")),
    "Overdrive 1 bright": ((0.7318, 0.5855), (0.4147, 0.4879), 0.1221, ("on", "off")),
    "Delay 1 sync": ((0.7074, 0.7318), (0.4147, 0.4879), 0.1221, ("note", "milliseconds")),
    "Delay 2 ping pong": ((0.6001, 0.2001), (0.0858, 0.8001), 0.1430, ("on", "off")),
    # Each stomp, from its pedal's lamp: the first spot on the lamp's middle, the second on the
    # pedal beside it. Worst case 27 to 43. All six lamps were dark in the run.
    "Compressor pedal": ((0.4591, -1.2950), (0.3771, -1.4261), 0.0657, ("on", "off")),
    "Overdrive 1 pedal": ((0.4755, -1.2294), (0.3608, -1.4097), 0.0657, ("on", "off")),
    "Delay 1 pedal": ((0.4919, -1.2294), (0.3608, -1.4097), 0.0657, ("on", "off")),
    "Overdrive 2 pedal": ((0.4755, -1.2458), (0.5739, -1.1802), 0.0657, ("on", "off")),
    "Delay 2 pedal": ((1.0821, 0.5739), (1.1804, 0.6395), 0.0657, ("on", "off")),
    "Reverb pedal": ((0.4755, -1.2294), (0.5739, -1.1802), 0.0657, ("on", "off")),
    # The input mode switch, from the two captions beside it and not from itself: the plug-in
    # prints the chosen one in white and the other in grey (Mono white, with the mean of a
    # 6 by 12 box on its first letter 79 against 44 on Stereo's, in the run). What the switch
    # itself looks like on Stereo has not been seen. The spots are right of the switch.
    "Input mode switch": ((1.3637, 0.6042), (1.3637, 0.0834), 0.25, ("mono", "stereo")),
    # The EQ's voicing switch, 18 by 10. Unlike the other little rockers it is drawn in the
    # same colours in both positions (the skin's eqTypeSwitch gives every background, border
    # and thumb colour the same value normal and selected): a white pill whose black knob
    # stands right for Nolly's mod and left for Original. Read at its middle until 0.12.4, it
    # said "Nolly's mod" whichever way it stood. Each spot is a 6 by 3 box over where the knob
    # can stand, 2 and 10 pixels in and 4 down, wide enough to take in the knob's grey edge:
    # core takes a box of nothing but black for a covered window and reads nothing, and the
    # knob's middle is pure black, which is what 0.12.4's 4 by 2 boxes hit (Hadi's log,
    # 2026-11-11, 18:12: "tip spots None / 231.0" with the knob left, "231.0 / None" right).
    # In the run, on Nolly's mod, the boxes read 231 and about 16.
    "EQ voicing": ((0.1112, 0.4001), (0.5556, 0.4001), 0.3334, ("Nolly's mod", "Original")),
}

# 2. One spot against the brightest point of the control (core.PROBE_OF_PEAK), for the little
#    rockers. The Nolly X draws them differently from the Petrucci X: off, an empty outline
#    with a white knob at the left; on, filled white with a black knob at the right (GATE on
#    and DOUBLER off in the run). So no two spots change places between the states, which is
#    what the Petrucci's reading relies on. (The EQ's voicing switch is not drawn this way; see
#    NOLLY_TIP_PROBES.) The
#    middle of the rocker, between the two places the knob can be, is empty (26) or filled
#    (231), and it is held against half of the brightest point of the control itself - the
#    outline, the filling or the caption's letters, 221 to 255 - so that the reading holds on
#    a dimmed panel: the right-hand ROOM SEND in the run was drawn at 124 where the left one
#    is 221, its microphone being off.
#
#    Offsets and boxes are fractions of the editor: a box 2 wide and 4 high, 9 pixels into a
#    20 by 12 rocker and 4 down. A caption that is itself the switch (GATE, DOUBLER, ROOM SEND)
#    is read at the same place of its rocker, which starts 38, 58 and 72 pixels into it.
_ROCKER_BOX = (0.00196, 0.00512)


def _rocker(x, y, words):
    return (x / 1024.0 + 0.00001, y / 782.0 + 0.00001, 0.5, words, _ROCKER_BOX, engine.PROBE_OF_PEAK)


NOLLY_SWITCH_PROBES = {
    "Gate switch": _rocker(9, 4, ("gate off", "gate on")),
    "Doubler switch": _rocker(9, 4, ("doubler off", "doubler on")),
    "Left room switch": _rocker(9, 4, ("room send off", "room send on")),
    "Right room switch": _rocker(9, 4, ("room send off", "room send on")),
    "Gate": _rocker(38 + 9, 5 + 4, ("off", "on")),
    "Doubler": _rocker(58 + 9, 5 + 4, ("off", "on")),
    "Left room send": _rocker(72 + 9, 5 + 4, ("off", "on")),
    "Right room send": _rocker(72 + 9, 5 + 4, ("off", "on")),
    # A microphone's on/off button. Its background is lit while the microphone is bypassed and
    # dark while it is on, as on the Petrucci X (the style is the plug-in's cabsimBypassSwitch).
    # On, the background reads 55 under a symbol of 245; off, the whole button is one grey, 99
    # on the dimmed panel of the run. So the background is held against the brightest point.
    "Left microphone switch": (0.01367, 0.03325, 0.6, ("on", "off"), (0.00391, 0.00512), engine.PROBE_OF_PEAK),
    "Right microphone switch": (0.01367, 0.03325, 0.6, ("on", "off"), (0.00391, 0.00512), engine.PROBE_OF_PEAK),
    # PHASE draws a dot at the top left corner of its symbol while inverted (the plug-in's
    # selectedPhaseIcon.svg, a circle of radius 2 at 2,2 of a 16 pixel symbol), where the
    # Petrucci X's probe already looks. Both read 27, normal, in the run; inverted has not been
    # seen on this plug-in.
    "Left phase": (0.05176, 0.00639, 0.5, ("normal", "inverted"), (0.00293, 0.00384), engine.PROBE_OF_PEAK),
    "Right phase": (0.05176, 0.00639, 0.5, ("normal", "inverted"), (0.00293, 0.00384), engine.PROBE_OF_PEAK),
    # 3. One spot against a fixed grey level, for the Cab view's miniature power switches. They
    #    are 40 pixels, and no pair of spots on them keeps 20 apart in both states at every
    #    scaling. The lit part of the rocker does: 121 to 131 on, 56 to 60 off (on the screen,
    #    on: 124 to 129 on all four amplifiers).
    "Mini Clean amp power switch": (0.02051, 0.02302, 92, ("amp off", "amp on"), (0.00391, 0.00512)),
    "Mini Crunch amp power switch": (0.02149, 0.02430, 92, ("amp off", "amp on"), (0.00391, 0.00512)),
    "Mini Rhythm amp power switch": (0.02149, 0.02430, 92, ("amp off", "amp on"), (0.00391, 0.00512)),
    "Mini Lead amp power switch": (0.02149, 0.02430, 92, ("amp off", "amp on"), (0.00391, 0.00512)),
    # The tuner window's mute button is the framework's own, as on the Petrucci X.
    "Mute while tuning": ArchetypeXProfile.switchProbes["Mute while tuning"],
}

# A selector picked out by its picture, when the toggle states do not single one out: its mean
# brightness must beat the next one's by this factor. Measured on the run's pictures, selected
# against the brightest of the others: 174 against 96 over a dark view, 217 against 180 over the
# Cab view's cabinet, and 220 against 112 in the unlinked cabinet row.
SELECTOR_MEAN_MARGIN = 1.12


class NollyProfile(ArchetypeXProfile):
    """The Neural DSP Archetype Nolly X, standalone and VST3."""

    id = "nolly"
    displayName = "Archetype Nolly X"

    # The root element's Name is exactly this, and the provider description names the module.
    markers = ("Archetype Nolly X",)

    executableNames = (
        "archetype nolly x",
        "Archetype Nolly X",
        "ARCHETYPE NOLLY X",
    )

    # The five section buttons at the top, left to right. Their HelpText is the section's name
    # as the plug-in spells it.
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

    # The four amplifiers, matching the selectors at the bottom, left to right. Unlinked, the
    # row of cabinet selectors under them goes by the same four names.
    ampModelNames = ("Clean", "Crunch", "Rhythm", "Lead")

    enumValues = {
        "Delay 2 sync": ("free", "DAW sync", "tap sync"),
        "Delay 1 note": NOTE_VALUE_NAMES,
        "Delay 2 note": NOTE_VALUE_NAMES,
    }

    KNOB_UNITS = NOLLY_KNOB_UNITS
    VIEW_SLIDER_LANDMARKS = VIEW_SLIDER_LANDMARKS
    VIEW_BUTTON_LANDMARKS = VIEW_BUTTON_LANDMARKS
    VIEW_MODULES = VIEW_MODULES
    VIEW_POINTER_KNOBS = VIEW_POINTER_KNOBS
    NOTE_KNOB_NAMES = NOTE_KNOB_NAMES
    DELAY_DISPLAYS = DELAY_DISPLAYS
    AMP_KNOB_TABLES = AMP_KNOB_TABLES
    AMP_SWITCH_TABLES = AMP_SWITCH_TABLES
    POWER_STATE_KEYS = POWER_STATE_KEYS
    MINI_POWER_STATE_KEYS = MINI_POWER_STATE_KEYS
    decorativeNames = DECORATIVE_NAMES

    # The Cab view's side panels say ROOM SEND where the Petrucci's say ROOM, and have none of
    # its CLOSE, MID and FAR: taken over, "MID" would put Left in front of the miniature amp
    # row's Mid knob.
    CAPTION_STATE_KEYS = dict(CAPTION_STATE_KEYS, **{"ROOM SEND": "room send"})
    SIDED_CAPTIONS = frozenset(("room send", "phase"))
    CAB_SIDED_NAMES = {"ROOM SEND": "room send", "PHASE": "phase"}

    # The Cab view's miniature amp row is bigger than the Petrucci's: knobs of 34 to 39 pixels
    # with their tops at 342 to 353 of 782, a power switch of 40 and a Bright switch of 26 to 28.
    # The band starts below Post Effects' sync switch and ping pong switch (tops at 313 and 316),
    # and the widths stop short of the EQ's 50 pixel sliders, which stand in the same band.
    CAB_MINI_BAND = (0.42, 0.47)
    CAB_MINI_KNOB_MAX_WIDTH = 0.042
    CAB_MINI_PANEL_MAX_WIDTH = 0.042
    # A miniature switch is at most 40 pixels high (0.051), a full-size one at least 50 (0.064).
    MINI_SWITCH_MAX_HEIGHT = 0.058
    FULL_SIZE_STATE_NAMES = frozenset(("Amp power switch", "Bright switch"))

    # See NOLLY_TIP_PROBES and NOLLY_SWITCH_PROBES above. The Petrucci's readings of the
    # rockers and of the input mode switch are not taken over: the Nolly draws them otherwise.
    switchProbes = NOLLY_SWITCH_PROBES
    tipProbes = NOLLY_TIP_PROBES

    # ---------- telling the views and the amplifiers apart ----------

    def _viewFromSliders(self, sliders, geometry):
        """EQ is the only view with the low pass filter's 20000 hertz, Post Effects the only
        one with Delay 2's high cut (to 5000 hertz) and the reverb's decay (to 8500
        milliseconds), and Pre Effects has Delay 1's feedback, which stops at 0.9, among a
        dozen 65 pixel knobs standing higher than any amp panel's."""
        _left, top, width, height = geometry
        pedalKnobs = 0
        feedback = False
        for element in sliders:
            maximum = _prop(element, PROP_RANGE_MAX)
            try:
                maximum = float(maximum)
            except (TypeError, ValueError):
                maximum = None
            if maximum == 20000.0:
                return "eq"
            if maximum in (5000.0, 8500.0):
                return "postfx"
            if maximum is not None and abs(maximum - 0.9) < 1e-6:
                feedback = True
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4:
                continue
            if 0.055 <= rect[2] / width <= 0.070 and 0.30 <= (rect[1] - top) / height <= 0.55:
                pedalKnobs += 1
        return "prefx" if feedback or pedalKnobs >= 8 else "amp"

    def _ampIndexOf(self, knobs, switches):
        """Clean and Lead have six knobs, Crunch and Rhythm eight, and of each pair only the
        first has a Bright switch."""
        count = len(knobs)
        if count == 6:
            return 0 if switches else 3
        if count == 8:
            return 1 if switches else 2
        return None

    # ---------- the selectors and the link ----------

    def _selectorRows(self, controller):
        """(amplifier selectors, cabinet selectors), each left to right. Linked, the plug-in
        shows four selectors that stand for amplifier and cabinet together, and the second list
        is empty; unlinked, a row of four amplifiers over a row of four cabinets."""
        def build():
            found = ArchetypeXProfile._selectorElements(self, controller)
            if len(found) <= len(self.ampModelNames):
                return found, []
            geometry = controller.clientGeometry()
            slack = geometry[3] * 0.015 if geometry else 10.0
            top = min(rect[1] for _x, rect, _element in found)
            amps = [entry for entry in found if entry[1][1] - top < slack]
            cabs = [entry for entry in found if entry[1][1] - top >= slack]
            return amps, cabs
        return controller._positionalSweep("selectorRows", build)

    def _selectorElements(self, controller):
        return self._selectorRows(controller)[0]

    def cabSelectorElements(self, controller):
        return self._selectorRows(controller)[1]

    def ampCabLinked(self, controller):
        """True while the cabinet follows the amplifier, False while they are chosen apart,
        None when the selectors cannot be found."""
        amps, cabs = self._selectorRows(controller)
        if len(amps) != len(self.ampModelNames):
            return None
        return not cabs

    def linkElement(self, controller):
        """(rect, element) of the amp and cab link button, or None."""
        def build():
            geometry = controller.clientGeometry()
            if not geometry:
                return None
            left, _top, width, _height = geometry
            band = (SELECTOR_Y[0], 0.96)
            for _x, rect, element in self._bandElements(controller, CT_BUTTON, band, unnamedOnly=True):
                if 0.018 <= rect[2] / width <= 0.028 and (rect[0] - left) / width < 0.45:
                    return tuple(rect[:4]), element
            return None
        return controller._positionalSweep("ampCabLink", build)

    @staticmethod
    def _rowIndex(entries, obj):
        """Index of the entry standing where the object stands, or None. Both edges count: an
        unlinked amplifier selector is three pixels right of the cabinet selector under it."""
        try:
            left, top = obj.location.left, obj.location.top
        except Exception:
            return None
        for index, entry in enumerate(entries):
            if abs(entry[1][0] - left) < 3 and abs(entry[1][1] - top) < 3:
                return index
        return None

    def _selectedIn(self, controller, selectors, what):
        """Which of a row of selectors is the selected one, or None. Their toggle states say
        where exactly one of them reads On; failing that the pictures do, where one selector
        is clearly the brightest."""
        states = [_prop(element, PROP_TOGGLE_STATE) for _x, _rect, element in selectors]
        on = [index for index, state in enumerate(states) if state == 1]
        if len(on) == 1:
            engine.STATE_LOG("neuralAccess: %s selectors' toggle states %r -> %r" % (
                what, states, self.ampModelNames[on[0]]))
            return on[0]
        means = [controller.meanGrey(*rect[:4]) for _x, rect, _element in selectors]
        if any(mean is None for mean in means):
            return None
        order = sorted(range(len(means)), key=lambda index: means[index], reverse=True)
        clear = means[order[0]] >= means[order[1]] * SELECTOR_MEAN_MARGIN
        engine.STATE_LOG("neuralAccess: %s selectors' toggle states %r say nothing; mean brightness %s -> %r" % (
            what, states, " / ".join("%.0f" % mean for mean in means),
            self.ampModelNames[order[0]] if clear else None))
        return order[0] if clear else None

    def selectedAmpIndex(self, controller):
        """Which amplifier's selector is the selected one, 0 to 3, or None. Works in every
        view. Unlinked, the amplifier row's pictures are too alike to judge by, so only the
        toggle states are asked there."""
        def build():
            selectors = self.selectorElements(controller)
            if len(selectors) != len(self.ampModelNames):
                return None
            if self.cabSelectorElements(controller):
                states = [_prop(element, PROP_TOGGLE_STATE) for _x, _rect, element in selectors]
                on = [index for index, state in enumerate(states) if state == 1]
                engine.STATE_LOG("neuralAccess: unlinked amp selectors' toggle states %r" % (states,))
                return on[0] if len(on) == 1 else None
            return self._selectedIn(controller, selectors, "amp")
        return controller._positionalSweep("selectedAmp", build)

    def selectedCabIndex(self, controller):
        """Which cabinet is sounding, 0 to 3, or None: the amplifier's own while linked, the
        selected one of the cabinet row while not."""
        def build():
            cabs = self.cabSelectorElements(controller)
            if not cabs:
                return self.liveAmpIndex(controller)
            if len(cabs) != len(self.ampModelNames):
                return None
            return self._selectedIn(controller, cabs, "cab")
        return controller._positionalSweep("selectedCab", build)

    def _isLink(self, obj, controller):
        link = self.linkElement(controller)
        return link is not None and self._sameControl(obj, link[0])

    def positionalLabel(self, obj, controller):
        role = obj.ampNativeRole
        if role in (controlTypes.Role.BUTTON, controlTypes.Role.TOGGLEBUTTON):
            # The cabinet row and the link first: the shared code knows one row of selectors,
            # and would take a cabinet selector for the amplifier above it.
            index = self._rowIndex(self.cabSelectorElements(controller), obj)
            if index is not None and index < len(self.ampModelNames):
                return "%s cabinet" % self.ampModelNames[index]
            if self._isLink(obj, controller):
                return LINK_NAME
        elif role == controlTypes.Role.UNKNOWN:
            name = self._backgroundName(obj, controller)
            if name:
                return name
        return self._bandNamed(super(NollyProfile, self).positionalLabel(obj, controller), controller)

    def _bandNamed(self, name, controller):
        """A band slider's or box's name, with the frequency printed under that band now (see
        EQ_BANDS). Any other name, or a band whose captions cannot be read, is left as it is."""
        base, suffix = name, ""
        if name.endswith(VALUE_BOX_SUFFIX):
            base, suffix = name[:-len(VALUE_BOX_SUFFIX)], VALUE_BOX_SUFFIX
        index = EQ_BAND_INDEX.get(base)
        if index is None:
            return name
        words = self._eqBandWords(controller)
        return "Band %s%s" % (words[index], suffix) if words else name

    def _eqBandWords(self, controller):
        """The nine bands' frequencies, left to right, as the captions under the sliders print
        them now, worded for speech ("65 hertz", "1.5 kilohertz"); None unless nine are found."""
        def build():
            geometry = controller.clientGeometry()
            if not geometry:
                return None
            found = []
            for element in controller.findElements(controlType=CT_TEXT):
                rect = _prop(element, PROP_BOUNDING_RECT)
                if not rect or len(rect) < 4 or rect[2] <= 0:
                    continue
                if abs((rect[1] + rect[3] / 2.0 - geometry[1]) / geometry[3] - EQ_CAPTION_ROW_Y) > 0.02:
                    continue
                match = FREQUENCY_CAPTION.match((_prop(element, PROP_NAME, "") or "").strip())
                if match:
                    found.append((rect[0], "%s %s" % (match.group(1), "kilohertz" if match.group(2) else "hertz")))
            found.sort()
            return tuple(word for _x, word in found) if len(found) == len(EQ_BANDS) else None
        return controller._positionalSweep("eqBandWords", build)

    def _backgroundName(self, obj, controller):
        """A name for the backgrounds that are in the tree as controls of their own: a pedal's
        (258 or 466 wide, 413 high), a microphone panel's (160 by 527) and the two pictures of
        a microphone in front of its speaker (250 by 250). None of them does anything."""
        if self._tunerControlName(obj, controller) is not None \
                or self._midiControlName(obj, controller) is not None:
            return ""
        fractions = self._objFractions(obj, controller)
        if fractions is None:
            return ""
        _xF, yF, wF, hF = fractions
        view = self.viewOf(controller)
        if view in ("prefx", "postfx") and 0.20 <= wF <= 0.50 and 0.48 <= hF <= 0.58:
            return "Pedal background"
        if view == "cab":
            if 0.14 <= wF <= 0.17 and 0.62 <= hF <= 0.72:
                return "Microphone panel background"
            if 0.22 <= wF <= 0.27 and 0.28 <= hF <= 0.36 and yF > 0.6:
                return "Microphone picture"
        return ""

    def _decorate(self, obj, controller, base):
        if base == LINK_NAME and self._isLink(obj, controller):
            linked = self.ampCabLinked(controller)
            return base if linked is None else "%s, %s" % (base, "linked" if linked else "unlinked")
        return super(NollyProfile, self)._decorate(obj, controller, base)

    def passedOver(self, obj):
        """The EQ captions in the Tab ring (see EQ_CAPTIONS) too."""
        if getattr(obj, "ampNativeRole", None) == controlTypes.Role.STATICTEXT:
            element = getattr(obj, "UIAElement", None)
            if element is not None and (_prop(element, PROP_NAME, "") or "").strip() in EQ_CAPTIONS:
                return True
        return super(NollyProfile, self).passedOver(obj)

    def tabPatch(self, obj, controller, backwards):
        if self._eqJump(obj, controller, backwards):
            return True
        return super(NollyProfile, self).tabPatch(obj, controller, backwards)

    def _eqJump(self, obj, controller, backwards):
        """Tab and Shift+Tab over the EQ's two runs of passed-over stops in one move each (see
        EQ_JUMP_ENDS): EQ voicing and the first band are made neighbours, and so are EQ power
        and GATE. From a stop inside a run, or from the top bar's background, the key goes to
        the run's end in its direction. False, and the key goes to the plug-in as before,
        outside the EQ or when an end is not found."""
        if self.viewOf(controller) != "eq":
            return False
        label = getattr(obj, "ampLabel", "") or ""
        element = getattr(obj, "UIAElement", None)
        native = (_prop(element, PROP_NAME, "") or "").strip() if element is not None else ""
        ends = self._eqJumpEnds(controller) or {}
        target = None
        if label == "EQ voicing":
            target = None if backwards else "firstBand"
        elif ends.get("firstBand") is not None and self._sameControl(obj, ends["firstBand"][0]):
            target = "voicing" if backwards else None
        elif label == "EQ power":
            target = None if backwards else "after"
        elif label == TOP_BAR_BACKGROUND_NAME or native == EQ_AFTER_CAPTION:
            target = "power" if backwards else None
        elif self.passedOver(obj):
            fractions = self._objFractions(obj, controller)
            if fractions is None:
                return False
            centre = fractions[1] + fractions[3] / 2.0
            if abs(centre - EQ_BOX_ROW_Y) <= EQ_ROW_TOLERANCE:
                target = "voicing" if backwards else "firstBand"
            elif abs(centre - EQ_CAPTION_ROW_Y) <= EQ_ROW_TOLERANCE:
                target = "power" if backwards else "after"
        if target is None:
            return False
        key = "Shift+Tab" if backwards else "Tab"
        end = ends.get(target)
        if end is None:
            log.info("neuralAccess: EQ jump: %s from %r, no %s found; the key goes to the plug-in"
                     % (key, label or native, target))
            return False
        moved = controller.trySetFocus(end[1])
        log.info("neuralAccess: EQ jump: %s from %r to %s at %r, %s" % (
            key, label or native, target, end[0], "focus set" if moved else "focus could not be set"))
        return moved

    def _eqJumpEnds(self, controller):
        """{"voicing", "firstBand", "power", "after": (rect, element)} for the EQ's jumps, as
        found."""
        def build():
            ends = {}
            for key, (controlType, centreY, centreX) in EQ_JUMP_ENDS.items():
                for element in controller.findElements(controlType=controlType):
                    rect = _prop(element, PROP_BOUNDING_RECT)
                    if not rect or len(rect) < 4 or rect[2] <= 0:
                        continue
                    fractions = self._fractions(controller, rect)
                    if fractions is None:
                        continue
                    xF, yF, wF, hF = fractions
                    if abs(yF + hF / 2.0 - centreY) <= 0.02 and abs(xF + wF / 2.0 - centreX) <= 0.012:
                        ends[key] = (tuple(rect[:4]), element)
                        break
            gate = self._captionElement(controller, EQ_AFTER_CAPTION)
            if gate is not None:
                ends["after"] = (gate[1], gate[0])
            return ends
        return controller._positionalSweep("eqJumpEnds", build)

    def selectedState(self, obj, controller):
        """The cabinet selectors are radio buttons too; the link button is not one."""
        if obj.ampNativeRole in (controlTypes.Role.BUTTON, controlTypes.Role.TOGGLEBUTTON):
            index = self._rowIndex(self.cabSelectorElements(controller), obj)
            if index is not None:
                live = self.selectedCabIndex(controller)
                return None if live is None else live == index
            if self._isLink(obj, controller):
                return None
        return super(NollyProfile, self).selectedState(obj, controller)

    def stateLabel(self, obj):
        """The Cab view's miniature Bright switch is 26 pixels on the Clean amplifier and 28 on
        the Crunch, so its probe is filed per amplifier."""
        label = super(NollyProfile, self).stateLabel(obj)
        if label == "Mini Bright switch":
            controller = obj.ampController
            mini = self.cabMiniPanel(controller) if controller is not None else None
            return "Mini %s bright switch" % mini["name"] if mini else ""
        return label


    def formatValue(self, label, raw, minimum, maximum, unitText=None):
        if label == "Reverb decay" and not unitText:
            # 1000 to 8500 milliseconds, which the plug-in itself counts in seconds (its model
            # shows the setting as "ms2seconds"). The pedal prints no figure.
            return "%.1f seconds" % (raw / 1000.0)
        return super(NollyProfile, self).formatValue(label, raw, minimum, maximum, unitText)

    # ---------- C: the next cabinet ----------

    def switchCabModel(self, controller, direction):
        """C: selects the next cabinet, going round, and says "Rhythm cabinet". Only while the
        amp and cab are unlinked; linked, it says how to unlink them."""
        linked = self.ampCabLinked(controller)
        if linked is None:
            ui.message("Cannot locate the selectors.")
            return True
        if linked:
            ui.message("The cabinet follows the amplifier. Control+A unlinks them.")
            return True
        cabs = self.cabSelectorElements(controller)
        if len(cabs) != len(self.ampModelNames):
            ui.message("Cannot locate the cabinet selectors.")
            return True
        controller._lastTab = None
        clickedAt = time.time()
        lastTarget, lastTime = getattr(controller, "_nollyCabClick", (None, 0.0))
        if lastTarget is not None and clickedAt - lastTime < SECTION_CLICK_GUARD_S:
            # A press straight after another steps on from the cabinet just asked for.
            base = lastTarget
        else:
            base = self.selectedCabIndex(controller)
            if base is None:
                log.info("neuralAccess: cab key: the cabinet selectors do not say which is selected")
                ui.message("Cannot tell which cabinet is selected.")
                return True
        target = (base + direction) % len(self.ampModelNames)
        controller._nollyCabClick = (target, clickedAt)
        targetName = self.ampModelNames[target]
        # A key that changes a setting leaves focus where it is: the click hands it to the
        # selector, so it is sent back and neither change is announced, as for the amp key.
        home = self._quickHome(controller)
        quiet = [self.topBarBackgroundRect(controller), cabs[target][1]] + ([home[1]] if home else [])
        controller.hushFocus([rect for rect in quiet if rect], AMP_SWITCH_HUSH_S)
        controller.clickElement(cabs[target][2])
        if home is not None:
            callLater(QUICK_RETURN_MS, self._returnHome, controller, home[0])
        log.info("neuralAccess: cab key: %s was selected; clicked the %s cabinet selector; focus %s"
                 % (self.ampModelNames[base], targetName, "sent back" if home else "left alone"))
        serial = getattr(controller, "_petrucciSwitchSerial", 0) + 1
        controller._petrucciSwitchSerial = serial

        def poll(remaining):
            if getattr(controller, "_petrucciSwitchSerial", serial) != serial:
                return
            controller.invalidatePositional()
            if self.selectedCabIndex(controller) == target:
                controller.invalidateReadouts()
                controller.invalidateStates()
                prefix = "%s cabinet" % targetName
                focus = engine.focusedElement()
                focusRect = _prop(focus, PROP_BOUNDING_RECT) if focus is not None else None
                stayed = home is not None and focusRect and self._rectMatches(tuple(focusRect[:4]), home[1])
                nowhereBefore = home is None and focus is not None and not controller.isFocusDeadEnd(focus)
                if stayed or nowhereBefore:
                    ui.message(prefix)
                    return
                # The Cab view may be rebuilt for the new cabinet, and what had focus with it.
                stop = self._firstTabStop(controller)
                if stop is None or not self._landOn(controller, stop, prefix):
                    ui.message(prefix)
                return
            if remaining > 0:
                callLater(200, poll, remaining - 1)
            else:
                log.info("neuralAccess: cab key: the %s cabinet never showed as selected" % targetName)
                ui.message("Could not switch cabinet.")

        callLater(500, poll, 8)
        return True

    # ---------- Control+A: the amp and cab link ----------

    def _linkWords(self, controller, linked):
        if linked:
            return "Amp and cab linked"
        cab = self.selectedCabIndex(controller)
        if cab is None:
            return "Amp and cab unlinked"
        return "Amp and cab unlinked. %s cabinet" % self.ampModelNames[cab]

    def _followLink(self, controller, before, home=None):
        """After a click on the link button: says the new state once the selector row shows
        it. The row changes shape with the link, which is what is watched for."""
        serial = getattr(controller, "_nollyLinkSerial", 0) + 1
        controller._nollyLinkSerial = serial

        def poll(remaining):
            if getattr(controller, "_nollyLinkSerial", serial) != serial:
                return
            controller.invalidatePositional()
            now = self.ampCabLinked(controller)
            if now is not None and now != before:
                controller.invalidateStates()
                log.info("neuralAccess: link key: the amp and cab were %s and are now %s"
                         % ("linked" if before else "unlinked", "linked" if now else "unlinked"))
                ui.message(self._linkWords(controller, now))
                return
            if remaining > 0:
                callLater(LINK_POLL_MS, poll, remaining - 1)
            else:
                log.info("neuralAccess: link key: the selector row never changed (linked reads %r)" % (now,))
                ui.message("Could not switch the amp and cab link.")

        callLater(LINK_POLL_MS * 2, poll, LINK_POLLS)

    def ampCabLink(self, controller):
        """Control+A: links or unlinks the amplifier and the cabinet and says which it is now.
        Focus stays where it is."""
        link = self.linkElement(controller)
        before = self.ampCabLinked(controller)
        if link is None or before is None:
            ui.message("Cannot locate the amp and cab link.")
            return True
        rect, element = link
        home = self._quickHome(controller)
        controller._lastTab = None

        def press(remaining):
            # The command's own Control key is still down when it starts, and a click made
            # then is a Control+click. Wait for the keys to come up.
            if engine.modifiersDown() and remaining > 0:
                callLater(SECTION_KEYS_UP_MS, press, remaining - 1)
                return
            quiet = [rect, self.topBarBackgroundRect(controller)] + ([home[1]] if home else [])
            controller.hushFocus([entry for entry in quiet if entry], QUICK_HUSH_S)
            if not controller.clickElement(element):
                ui.message("Could not press the amp and cab link.")
                return
            if home is not None:
                callLater(QUICK_RETURN_MS, self._returnHome, controller, home[0])
            self._followLink(controller, before, home)

        press(SECTION_KEYS_UP_POLLS)
        return True

    def afterClick(self, controller, obj):
        # Enter on EQ voicing: the band captions change with it, so the band names read from
        # them are looked for afresh, now and once the plug-in has redrawn.
        if (getattr(obj, "ampLabel", "") or "") == "EQ voicing":
            controller.forgetPositional("eqBandWords")
            callLater(VOICING_REDRAW_MS, controller.forgetPositional, "eqBandWords")
            return
        # Enter on the link button itself: the same report as Control+A gives.
        if self._isLink(obj, controller):
            before = self.ampCabLinked(controller)
            if before is not None:
                self._followLink(controller, before)
            return
        super(NollyProfile, self).afterClick(controller, obj)


PROFILE = NollyProfile()
