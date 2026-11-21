# neuralAccess - the Soldano SLO-100 X profile.
#
# What is the Soldano's own: the landmark tables of its five sections (the Nolly X's five), its one
# amplifier, whose panel has its POWER switch at the right with a lamp beyond it and its CHANNEL,
# BRIGHT and MODE switches at the left, and the words its panel prints. What it has in common with
# the other one-amplifier plug-in, the Fortin Nameless Suite X, is in archetypex.py
# (SingleAmpXProfile), and what every X plug-in has in common in ArchetypeXProfile there.
#
# Where it comes from, none of it measured by hand:
#   * the plug-in's own layout, read out of the VST3 (probe-results\soldano-layout), from which
#     tools\probe\Draft-XProfile.py drafted the centres below;
#   * a driven run of 2026-11-20 in REAPER, tools\probe\Probe-XViews.py --plugin soldano, which
#     showed each section once, on the Black look, and saved the tree and a picture at every stop
#     (probe-results\soldano-views);
#   * the words the panel prints, from its labels drawings (probe-results\soldano-art\svg), and
#     the manual, Soldano SLO-100 X v1.0.0.pdf, pages 10 to 14, where the panel prints none.
#
# How it differs from the Fortin:
#   * the power switch is the panel's right-most button once the lamp beyond it is left out, the
#     STANDBY switch left of it;
#   * BRIGHT and MODE stand one above the other at one left edge, so they are left out of the panel
#     and named by their places;
#   * the amp's knobs run 0 to 1.1, the panel's dials 0 to 11, and say their dial's figure;
#   * on the OVERDRIVE channel the plug-in disables PREAMP and MASTER NORMAL, BRIGHT and MODE, and
#     on NORMAL the two OVERDRIVE knobs. The knobs stay in the tree and keep their names; the
#     switches are drawn dark, levers and all, and still read (notes\soldano.md, "Heard in
#     0.15.0"). Each says "inactive" after its name and position (DISABLED_BY_CHANNEL).

from .archetypex import (
    ArchetypeXProfile, CAB_PANEL_SWITCH_PROBES, KNOB_UNITS, NOTE_VALUE_NAMES, ROOM_SEND_CAB_SIDED_NAMES,
    ROOM_SEND_CAPTION_STATE_KEYS, ROOM_SEND_SIDED_CAPTIONS, SingleAmpXProfile, TOP_BAR_REFERENCES,
    TOP_BAR_SWITCH_PROBES, TOP_BAR_TIP_PROBES, TUNER_HELP,
)
from .core import PROP_RANGE_MAX, _prop

# The five sections in button order, as viewOf names their views.
VIEW_KEYS = ("prefx", "amp", "cab", "eq", "postfx")

# The amp's knobs left to right, in the words the panel prints: NORMAL and OVERDRIVE under
# PREAMP, BASS, MIDDLE, TREBLE, NORMAL and OVERDRIVE under MASTER, PRESENCE and DEPTH. The Cab
# view's miniature has the same.
AMP_KNOBS = ("Preamp normal", "Preamp overdrive", "Bass", "Middle", "Treble",
             "Master normal", "Master overdrive", "Presence", "Depth")
# The panel's buttons but the power switch, left to right, once BRIGHT and MODE are left out: the
# CHANNEL switch (printed OVERDRIVE and NORMAL) and STANDBY (printed ON and STANDBY).
AMP_SWITCHES = ("Channel switch", "Standby switch")
CHANNEL_SWITCH = "Channel switch"
# What each channel disables, by the Channel switch's reading (the manual's page 11, and the run
# on OVERDRIVE, which drew these dark). Each says "inactive" after its name and position.
DISABLED_BY_CHANNEL = {
    "overdrive": frozenset(("Preamp normal", "Master normal", "Bright switch", "Mode switch")),
    "normal": frozenset(("Preamp overdrive", "Master overdrive")),
}
CHANNEL_DISABLES = frozenset().union(*DISABLED_BY_CHANNEL.values())

# Where things stand that are left out of the amp panel, (centre y, centre x) as fractions of the
# editor, on the Amp view and then on the Cab view's miniature: the lamp beyond the power switch,
# a nameless button in the tree (the run), and BRIGHT and MODE, which share a left edge.
AMP_LAMPS = ((0.6611, 0.8828), (0.4527, 0.7148))
BRIGHT_SWITCHES = ((0.6330, 0.2100), (0.4367, 0.3364))
MODE_SWITCHES = ((0.6841, 0.2100), (0.4661, 0.3364))

# The EQ's nine bands, as the layout names them ("EQ 65 Hz" to "EQ 16 kHz"), worded for speech.
EQ_BANDS = ("65 hertz", "125 hertz", "250 hertz", "500 hertz", "1 kilohertz",
            "2 kilohertz", "4 kilohertz", "8 kilohertz", "16 kilohertz")

# What each knob is counted in, for a knob with no display of its own.
SOLDANO_KNOB_UNITS = dict(KNOB_UNITS, **{
    "Left mic level": "decibels",
    "Right mic level": "decibels",
    "Left room level": "decibels",
    "Right room level": "decibels",
    "High pass filter": "hertz",
    "Low pass filter": "hertz",
    "Delay time": "milliseconds",
    "Delay time display": "milliseconds",
    "Delay tempo": "beats per minute",
    # 0.1 to 5 hertz and 1 to 20 milliseconds (the layout), with no figure on the pedal.
    "Chorus rate": "hertz",
    "Chorus delay": "milliseconds",
    # 0.5 to 8 seconds (the manual).
    "Reverb decay": "seconds",
})
for _band in EQ_BANDS:
    SOLDANO_KNOB_UNITS["Band %s" % _band] = "decibels"

# Each view's own controls as (centre y fraction, centre x fraction, name), from the layout map
# (probe-results\soldano-layout\draft-tables.py), held against the run's trees. A pedal's
# controls have the pedal's name in front, in the words each pedal prints.
VIEW_SLIDER_LANDMARKS = {
    "prefx": (
        (0.4233, 0.0771, "Compressor comp"),
        (0.4233, 0.1885, "Compressor level"),
        (0.4233, 0.3232, "Overdrive 1 drive"),
        (0.5038, 0.3789, "Overdrive 1 tone"),
        (0.4233, 0.4336, "Overdrive 1 level"),
        (0.4220, 0.5674, "Overdrive 2 drive"),
        (0.4220, 0.6787, "Overdrive 2 level"),
        (0.5038, 0.6240, "Overdrive 2 tone"),
        (0.4220, 0.8125, "Chorus rate"),
        (0.4220, 0.9238, "Chorus depth"),
        (0.5051, 0.8125, "Chorus delay"),
        (0.5051, 0.9238, "Chorus mix"),
    ),
    # The amp's knobs are named from the panel (AMP_KNOBS).
    "amp": (),
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
        (0.5396, 0.1914, "High pass filter"),
        (0.5396, 0.8096, "Low pass filter"),
        (0.5396, 0.2686, "Band 65 hertz"),
        (0.5396, 0.3262, "Band 125 hertz"),
        (0.5396, 0.3828, "Band 250 hertz"),
        (0.5396, 0.4404, "Band 500 hertz"),
        (0.5396, 0.4980, "Band 1 kilohertz"),
        (0.5396, 0.5547, "Band 2 kilohertz"),
        (0.5396, 0.6123, "Band 4 kilohertz"),
        (0.5396, 0.6699, "Band 8 kilohertz"),
        (0.5396, 0.7266, "Band 16 kilohertz"),
    ),
    "postfx": (
        (0.4405, 0.2310, "Delay sync"),
        (0.4821, 0.1611, "Delay mix"),
        (0.4821, 0.4434, "Delay feedback"),
        # The delay's display. While the delay is free it shows the time and is a slider (the
        # layout's delayTimeMsEditor, read-only); synced, a text with the note stands there
        # (DELAY_DISPLAYS).
        (0.5147, 0.2485, "Delay time display"),
        # The tempo beside it: the host's while on DAW (globalTempoEditor, as in the run) or the
        # tapped one while on TAP (delayTempoEditor), at one place.
        (0.5147, 0.3447, "Delay tempo"),
        # While the delay is synced a note-value knob stands here instead (NOTE_KNOB_NAMES).
        (0.5703, 0.2295, "Delay time"),
        (0.5716, 0.3721, "Delay tone"),
        (0.4425, 0.7080, "Reverb mix"),
        (0.4425, 0.8223, "Reverb decay"),
        (0.5269, 0.7637, "Reverb tone"),
    ),
}
VIEW_BUTTON_LANDMARKS = {
    # Each pedal's on/off is its stomp, "<pedal> pedal", which springs back; its lamp ignores
    # clicks. The compressor's ATTACK switch (slow or fast) and the second overdrive's peak switch.
    "prefx": (
        (0.5115, 0.1338, "Compressor attack"),
        (0.7104, 0.1743, "Compressor pedal lamp"),
        (0.7104, 0.1323, "Compressor pedal"),
        (0.7091, 0.4214, "Overdrive 1 pedal lamp"),
        (0.7104, 0.3794, "Overdrive 1 pedal"),
        (0.4386, 0.6230, "Overdrive 2 peak"),
        (0.7091, 0.6655, "Overdrive 2 pedal lamp"),
        (0.7091, 0.6226, "Overdrive 2 pedal"),
        (0.7091, 0.9106, "Chorus pedal lamp"),
        (0.7091, 0.8667, "Chorus pedal"),
    ),
    # The Soldano logo, which changes the amp's look, the lamp beyond the power switch, and the
    # BRIGHT and MODE switches, left out of the panel (see SoldanoProfile.PANEL_LEFT_OUT).
    "amp": (
        (0.4783, 0.5029, "Amp skin"),
        (0.6611, 0.8828, "Amp power lamp"),
        (0.6330, 0.2100, "Bright switch"),
        (0.6841, 0.2100, "Mode switch"),
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
        (0.3453, 0.5000, "Amp skin"),
        (0.4527, 0.7148, "Amp power lamp"),
        (0.4367, 0.3364, "Bright switch"),
        (0.4661, 0.3364, "Mode switch"),
    ),
    "eq": (
        (0.6324, 0.8550, "EQ power"),
        (0.6304, 0.8096, "EQ power lamp"),
    ),
    "postfx": (
        (0.4405, 0.3687, "Delay ping pong"),
        (0.7155, 0.1567, "Delay pedal"),
        (0.7168, 0.2026, "Delay pedal lamp"),
        (0.7168, 0.4038, "Tap tempo light"),
        # The Tap tempo stomp, in the tree only with the delay on TAP (the Fortin's, heard).
        (0.7155, 0.4468, "Tap tempo"),
        (0.7321, 0.8062, "Reverb pedal lamp"),
        (0.7321, 0.7632, "Reverb pedal"),
    ),
}

# The note-value knob that takes the time knob's place while the delay follows a tempo.
NOTE_KNOB_NAMES = {"Delay time": "Delay note"}
# The text box standing on the delay's display: (centre y, centre x, its name while free, its
# name while synced). Synced, it is the layout's delayTimeNoteEditor, a text with no name that
# takes focus, at 224,389 61x27 (the run, "1/4").
DELAY_DISPLAYS = {
    "postfx": ((0.5147, 0.2485, "Delay time readout", "Delay note readout"),),
}

# Stops that do nothing: lamps, backgrounds, the little rockers whose captions are the switches,
# the logo, and the delay's time display while it is free (a read-only number display of the time
# the knob under it sets, which Hadi heard on the Fortin as a second slider of the same time).
DECORATIVE_NAMES = frozenset((
    "Compressor pedal lamp", "Overdrive 1 pedal lamp", "Overdrive 2 pedal lamp", "Chorus pedal lamp",
    "Delay pedal lamp", "Tap tempo light", "Reverb pedal lamp",
    "Gate switch", "Doubler switch", "Left room switch", "Right room switch",
    "View background", "Pedal background", "Microphone panel background", "Microphone picture",
    "Amp power lamp", "Amp skin", "EQ power lamp",
    "Delay time display",
))

# The EQ's two captions in the plug-in's Tab ring, as text stops with names (the run).
EQ_CAPTIONS = frozenset(("HPF :", "LPF :"))

# The modules the bracket keys step through, left to right but for the Cab section: (name, axis,
# low, high). The pedals stand at 9 to 266, 261 to 518, 510 to 764 and 762 to 1015 pixels of 1024
# in Pre Effects, and at 82 to 533 and 655 to 908 in Post Effects; the Cab's miniature amp at 312
# to 750, between the microphone panels at 32 to 192 and 832 to 992.
VIEW_MODULES = {
    "prefx": (("Compressor", "x", 0.0, 0.257), ("Overdrive 1", "x", 0.257, 0.502),
              ("Overdrive 2", "x", 0.502, 0.745), ("Chorus", "x", 0.745, 1.0)),
    "amp": (("Amplifier", "x", 0.0, 1.0),),
    # Left microphone, right microphone, then the amp, as on the Nolly X (Hadi, 2026-11-15).
    "cab": (("Left microphone", "x", 0.0, 0.25), ("Right microphone", "x", 0.75, 1.0),
            ("Amplifier", "x", 0.25, 0.75)),
    "eq": (("EQ", "x", 0.0, 1.0),),
    "postfx": (("Delay", "x", 0.0, 0.58), ("Reverb", "x", 0.58, 1.0)),
}
# Each module's on/off switch, first in its Tab order (see RING_TYPES in archetypex.py).
MODULE_SWITCHES = frozenset((
    "Compressor pedal", "Overdrive 1 pedal", "Overdrive 2 pedal", "Chorus pedal",
    "Amp power switch",
    "Left microphone switch", "Right microphone switch",
    "EQ power",
    "Delay pedal", "Reverb pedal",
))
# Tab goes through these views' modules in the bracket keys' order rather than the plug-in's,
# which in Pre Effects goes overdrive 2, chorus, compressor, overdrive 1 (the run).
TAB_IN_MODULE_ORDER = frozenset(("prefx", "cab", "postfx"))
# And through the amp left to right as the panel reads, where the plug-in goes by top edge
# (BRIGHT, STANDBY and POWER, the knobs, then CHANNEL and MODE).
TAB_LEFT_TO_RIGHT_MODULES = frozenset(("Amplifier",))

# The pedals' knobs that say where their pointer points: those with no figure shown anywhere.
# Left out: the delay's time and note knobs, which have the display.
VIEW_POINTER_KNOBS = {
    "prefx": frozenset(("Compressor comp", "Compressor level", "Overdrive 1 drive", "Overdrive 1 tone",
                        "Overdrive 1 level", "Overdrive 2 drive", "Overdrive 2 tone", "Overdrive 2 level",
                        "Chorus rate", "Chorus depth", "Chorus delay", "Chorus mix")),
    "postfx": frozenset(("Delay mix", "Delay feedback", "Delay tone", "Reverb mix", "Reverb decay", "Reverb tone")),
}

# The amp's knobs run 0 to 1.1 in the tree and the panel's dials 0 to 11: each says its dial's
# figure, 0.5 as "5.0".
AMP_DIAL_RANGE_MAX = 1.1


def isDialRange(maximum):
    """True for the amp knobs' top. The plug-in gives 1.1 as a 32-bit float, 1.100000023841858,
    which is not 1.1: compared exactly, the knobs said "0.69" for 6.9 (Hadi's log of 0.15.2)."""
    return abs(maximum - AMP_DIAL_RANGE_MAX) < 1e-4

# ---- reading switch positions off the screen, on the Black look ----
#
# No switch of the Soldano says its state in the tree. The top bar's and the Cab view's side
# panels' are drawn as the Nolly X and the Fortin draw them and are read the same way
# (TOP_BAR_SWITCH_PROBES, TOP_BAR_TIP_PROBES and CAB_PANEL_SWITCH_PROBES in archetypex.py). The rest
# are pictures, two per switch, read at two spots each: the first word is said when the first spot
# is the brighter by 20 grey levels or more, the second when the second is, and nothing otherwise.
# The spots are fractions of the switch's own rectangle. tools\probe\Find-XSwitchSpots.py found
# them (probe-results\soldano-switch-spots.txt), rebuilding each switch on its panel with the words
# the panel prints, and the run of 2026-11-20 showed each switch in one state. Which picture is
# which state is the skin's (normalImage for off, downImage for on). Notes in notes\soldano.md.
#
# The power and standby switches hold a worst case of 34.0 over four ways of scaling and a pixel's
# shift, EQ power 47.2. The amp's three small toggles (chrome on the silver faceplate), the
# compressor's attack, the second overdrive's peak and the delay's ping pong do not, but on a
# screen that lines up with the plug-in's pictures, as Hadi's does (box averaging, no shift, the
# run within 0.4 to 1.0 of the rebuild), their spots stand 40 to 68 apart, and in none of the 72
# variants do they lean the wrong way by 20, so a screen that does not line up makes them silent,
# never wrong. On the OVERDRIVE channel the plug-in draws BRIGHT and MODE dimmed, and they read
# with a threshold of their own (below). The Cab view's miniature switches (17 and 27 pixels)
# have no reading.
#
# Purple and Snake change only the panel picture behind the amp's switches; every spot lies where
# the switch's own picture covers it, and the check holds each reading on their pictures.
SOLDANO_TIP_PROBES = dict(TOP_BAR_TIP_PROBES, **{
    "Soldano amp power switch": ((0.4584, 0.3751), (0.4793, 0.5001), 0.1043, ("amp on", "amp off")),
    "Standby switch": ((0.4584, 0.3751), (0.4793, 0.5001), 0.1043, ("amp on", "amp off")),
    # Up is OVERDRIVE, BRIGHT and CRUNCH, as the panel prints them above each toggle.
    "Channel switch": ((0.4334, 0.3668), (0.4334, 0.5668), 0.1668, ("overdrive", "normal")),
    # On the OVERDRIVE channel the plug-in draws BRIGHT and MODE with their own pixels darkened to
    # 0.42, levers and all (fitted within 1.7 grey levels on the run's picture). Hadi heard them
    # silent in 0.15.0 (2026-11-21), where 5-pixel spots stood only 12 apart dimmed. These
    # 3-pixel spots stand 66.6 apart full, 20.5 dimmed on the run's picture (lever up) and about
    # 28 dimmed by the model (lever down), and lean the wrong way by 8.4 at most in any of the
    # 72 variants, full or dimmed, so they speak at 12 apart (the fifth entry, core._tipPosition).
    "Bright switch": ((0.4334, 0.4001), (0.4668, 0.5668), 0.1001, ("on", "off"), 12),
    "Mode switch": ((0.4334, 0.4001), (0.4668, 0.5668), 0.1001, ("crunch", "clean"), 12),
    "EQ power": ((0.5112, 0.1557), (0.4668, 0.7557), 0.1112, ("on", "off")),
    # Leaning right for FAST and for on; the spots are on the levers' tips.
    "Compressor attack": ((0.3612, 0.0557), (0.1668, 0.0279), 0.1390, ("fast", "slow")),
    "Overdrive 2 peak": ((0.3334, 0.0557), (0.1390, 0.0279), 0.1390, ("on", "off")),
    "Delay ping pong": ((0.3549, 0.0324), (0.1614, 0.0324), 0.1614, ("on", "off")),
})
# Each stomp, from its pedal's lamp, which glows blue when the pedal is on: the stomps spring back,
# so their own pictures say nothing. One box of 5 pixels on the lamp's glow, carried into the
# stomp's rectangle (so the fractions pass 1), read for how blue it is for how bright it is
# (core.AmpController._colourPosition), which no darkening of the section changes. The off and on
# lines are a third and two thirds of the worst-case gap above the unlit lamp's highest share over
# four ways of scaling and a pixel's shift: gaps of 0.198 (compressor), 0.125 (overdrive 1), 0.137
# (overdrive 2), 0.120 (chorus, on an orange pedal), 0.169 (delay) and 0.155 (reverb). On the run,
# every lamp unlit, each read 0.05 to 0.12 under its off line.
SOLDANO_COLOUR_PROBES = {
    "Compressor pedal": ((0.9156, 0.4931), 0.0705, 0.077, 0.011, ("on", "off")),
    "Overdrive 1 pedal": ((1.0283, 0.5353), 0.0705, 0.386, 0.345, ("on", "off")),
    "Overdrive 2 pedal": ((1.0424, 0.5494), 0.0705, 0.382, 0.337, ("on", "off")),
    "Chorus pedal": ((1.0846, 0.6057), 0.0705, -0.509, -0.548, ("on", "off")),
    "Delay pedal": ((1.0424, 0.5353), 0.0705, 0.309, 0.252, ("on", "off")),
    "Reverb pedal": ((1.1550, 0.4508), 0.0705, 0.386, 0.335, ("on", "off")),
}

POWER_STATE_KEYS = {"Soldano": "Soldano amp power switch"}
# Filed so that the miniature never borrows the full-size reading.
MINI_POWER_STATE_KEYS = {"Soldano": "Mini Soldano amp power switch"}

SOLDANO_SWITCH_PROBES = dict(TOP_BAR_SWITCH_PROBES, **CAB_PANEL_SWITCH_PROBES)
# The tuner window's mute button is the framework's own, as on the Petrucci X.
SOLDANO_SWITCH_PROBES["Mute while tuning"] = ArchetypeXProfile.switchProbes["Mute while tuning"]


class SoldanoProfile(SingleAmpXProfile):
    """The Neural DSP Soldano SLO-100 X, standalone and VST3."""

    id = "soldano"
    displayName = "Soldano SLO-100 X"

    # The editor's UI Automation name in the run of 2026-11-20.
    markers = ("Soldano SLO-100 X",)

    executableNames = (
        "soldano slo-100 x",
        "Soldano SLO-100 X",
        "SOLDANO SLO-100 X",
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
    ampModelNames = ("Soldano",)

    enumValues = {
        "Delay sync": ("free", "DAW sync", "tap sync"),
        "Delay note": NOTE_VALUE_NAMES,
    }

    KNOB_UNITS = SOLDANO_KNOB_UNITS
    VIEW_SLIDER_LANDMARKS = VIEW_SLIDER_LANDMARKS
    VIEW_BUTTON_LANDMARKS = VIEW_BUTTON_LANDMARKS
    VIEW_MODULES = VIEW_MODULES
    MODULE_SWITCHES = MODULE_SWITCHES
    TAB_IN_MODULE_ORDER = TAB_IN_MODULE_ORDER
    TAB_LEFT_TO_RIGHT_MODULES = TAB_LEFT_TO_RIGHT_MODULES
    VIEW_POINTER_KNOBS = VIEW_POINTER_KNOBS
    NOTE_KNOB_NAMES = NOTE_KNOB_NAMES
    DELAY_DISPLAYS = DELAY_DISPLAYS
    AMP_KNOB_TABLES = (AMP_KNOBS,)
    AMP_SWITCH_TABLES = (AMP_SWITCHES,)
    decorativeNames = DECORATIVE_NAMES

    # The power switch is the right-most button of the panel once the lamp and BRIGHT and MODE
    # are left out; the EQ's captions in the Tab ring are passed over (see SingleAmpXProfile).
    PANEL_LEFT_OUT = AMP_LAMPS + BRIGHT_SWITCHES + MODE_SWITCHES
    POWER_SWITCH_AT_LEFT = False
    EQ_CAPTIONS = EQ_CAPTIONS

    # The Cab view's side panels are the Nolly's: ROOM SEND and PHASE on each side.
    CAPTION_STATE_KEYS = ROOM_SEND_CAPTION_STATE_KEYS
    SIDED_CAPTIONS = ROOM_SEND_SIDED_CAPTIONS
    CAB_SIDED_NAMES = ROOM_SEND_CAB_SIDED_NAMES

    # See SOLDANO_TIP_PROBES and SOLDANO_COLOUR_PROBES above. The Cab view's miniature has the
    # amp's switches under the same names and is read under "Mini <name>", where nothing is filed:
    # its switches are 17 and 27 pixels high (0.022 and 0.035 of the editor), the Amp view's 30
    # and 48 (0.038 and 0.061).
    POWER_STATE_KEYS = POWER_STATE_KEYS
    MINI_POWER_STATE_KEYS = MINI_POWER_STATE_KEYS
    FULL_SIZE_STATE_NAMES = frozenset(("Amp power switch", "Standby switch", "Channel switch", "Bright switch",
                                       "Mode switch"))
    MINI_SWITCH_MAX_HEIGHT = 0.0365
    switchProbes = SOLDANO_SWITCH_PROBES
    tipProbes = SOLDANO_TIP_PROBES
    colourProbes = SOLDANO_COLOUR_PROBES
    # The self-check's boxes, which the Fortin shares (archetypex.TOP_BAR_REFERENCES).
    screenReferences = TOP_BAR_REFERENCES

    # ---------- telling the views apart ----------

    def _viewFromSliders(self, sliders, geometry):
        """Each section has a slider maximum no other has (the layout's settings): the low pass
        filter's 20000 hertz in the EQ; the reverb's decay (8 seconds) or the free delay's time
        (1500 milliseconds) in Post Effects; the amp's knobs' 1.1 in the Amp view (the Cab's
        miniature has them too, but the Cab is told by its combo boxes first); and the chorus's
        rate (5 hertz) in Pre Effects. 20 is no tell: the top bar's doubler spread goes to 20."""
        amp = prefx = postfx = False
        for element in sliders:
            try:
                maximum = float(_prop(element, PROP_RANGE_MAX))
            except (TypeError, ValueError):
                continue
            if maximum == 20000.0:
                return "eq"
            if maximum in (8.0, 1500.0):
                postfx = True
            elif isDialRange(maximum):
                amp = True
            elif maximum == 5.0:
                prefx = True
        if postfx:
            return "postfx"
        if prefx:
            return "prefx"
        return "amp"

    # ---------- what the channel disables ----------

    def inactiveWord(self, obj):
        """"inactive" for a control the channel disables (DISABLED_BY_CHANNEL), on the Amp view,
        by the Channel switch's own reading. Nothing when that cannot be read, and nothing on the
        Cab view's miniature, whose channel switch has no reading: a channel remembered from the
        Amp view could be stale after a preset or MIDI changed it (Hadi asked, 2026-11-21)."""
        label = obj.ampLabel or ""
        if label not in CHANNEL_DISABLES:
            return ""
        controller = obj.ampController
        panel = self.ampPanel(controller) if controller is not None else None
        index = AMP_SWITCHES.index(CHANNEL_SWITCH)
        if panel is None or len(panel["switches"]) <= index:
            return ""
        channel = controller.switchPosition(CHANNEL_SWITCH, panel["switches"][index][1])
        return "inactive" if label in DISABLED_BY_CHANNEL.get(channel, ()) else ""

    # ---------- what the amp's knobs say ----------

    def formatValue(self, label, raw, minimum, maximum, unitText=None):
        """The amp's knobs and the miniature's say the figure their dial points at, 0 to 11, as the
        panel numbers it, the tree's 0 to 1.1 times ten; the chorus's two small ranges keep their
        decimals."""
        if label in AMP_KNOBS and isDialRange(maximum) and minimum == 0.0:
            return "%.1f" % (raw * 10.0)
        # The chorus's rate runs 0.1 to 5 hertz and its delay 1 to 20 milliseconds, where the whole
        # numbers the other hertz and milliseconds are said in would lose most of the knob.
        if label == "Chorus rate" and not unitText:
            return "%.2f hertz" % raw
        if label == "Chorus delay" and not unitText:
            return "%.1f milliseconds" % raw
        return super(SoldanoProfile, self).formatValue(label, raw, minimum, maximum, unitText)


PROFILE = SoldanoProfile()
