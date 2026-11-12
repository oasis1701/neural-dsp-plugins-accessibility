# neuralAccess - the Archetype Petrucci X profile.
#
# What is the Petrucci X's own: its seven sections, the landmark tables of their views, its four
# amplifiers, and the pictures its switches are read from. Everything it has in common with the
# other X plug-ins is in archetypex.py (ArchetypeXProfile), where these tables are looked up
# under the names they carry here. Until 0.12.0 this file held all of it.
#
# Inspected live inside REAPER on 2026-08-11 (tools\probe\Probe-PetrucciTree.ps1,
# probe-results\petrucci-amp-view.txt, and the manual), with the plug-in's own layout and
# pictures read from 2026-11-08 on (probe-results\petrucci-layout).

from .archetypex import ArchetypeXProfile, NOTE_VALUE_NAMES, TUNER_HELP
from .core import PROP_BOUNDING_RECT, PROP_RANGE_MAX, _prop


# What each knob is counted in, for a knob with no display of its own.
KNOB_UNITS = {
    "Input": "decibels",
    "Gate threshold": "decibels",
    "Output": "decibels",
    "Transpose": "semitones",
    "Doubler spread": "milliseconds",
    "Left mic level": "decibels",
    "Right mic level": "decibels",
    "Left room level": "decibels",
    "Right room level": "decibels",
    "High pass filter": "hertz",
    "Low pass filter": "hertz",
    "Low gain": "decibels",
    "Low mid gain": "decibels",
    "High mid gain": "decibels",
    "High gain": "decibels",
    "Delay time left": "milliseconds",
    "Delay time right": "milliseconds",
    "Delay time left display": "milliseconds",
    "Delay time right display": "milliseconds",
    "Delay low cut": "hertz",
    "Delay high cut": "hertz",
    "Reverb pre-delay": "milliseconds",
    "Tempo": "beats per minute",
    "Delay tempo": "beats per minute",
}

# The section views' own controls, mapped 2026-08-11 from probe-results\petrucci-views.txt.
# Each entry is (centre y fraction, centre x fraction, name); a control matches when both its
# centre coordinates are within 0.02. The Amp view's controls are handled structurally instead
# (the panel changes with the amplifier), as is the Cab view's miniature amp knob row.
VIEW_SLIDER_LANDMARKS = {
    "wahcomp": (
        (0.3951, 0.6084, "Compression"),
        (0.3951, 0.7100, "Compressor level"),
        (0.4936, 0.6602, "Gain reduction meter"),
        (0.5486, 0.1797, "Wah position"),
        (0.5492, 0.3296, "Wah pedal"),
    ),
    "prefx": (
        (0.3887, 0.5645, "Chorus rate"),
        (0.3887, 0.7910, "Flanger rate"),
        (0.3887, 0.8906, "Flanger depth"),
        (0.3900, 0.1621, "Overdrive tone"),
        (0.4348, 0.3887, "Phaser rate"),
        (0.4808, 0.5645, "Chorus depth"),
        (0.4808, 0.6641, "Chorus level"),
        (0.4808, 0.7910, "Flanger range"),
        (0.4808, 0.8906, "Flanger feedback"),
        (0.4821, 0.1074, "Overdrive drive"),
        (0.4821, 0.2168, "Overdrive level"),
    ),
    "cab": (
        (0.4079, 0.0684, "Left position"),
        (0.4079, 0.1504, "Left distance"),
        (0.4079, 0.8496, "Right position"),
        (0.4079, 0.9316, "Right distance"),
        (0.5550, 0.0684, "Left mic level"),
        # The pan knobs had no name until 0.9.8: the add-on's first automatic capture caught
        # one (capture 13, 2026-11-09). They were not in the tree in the captures of
        # 2026-11-08, so the plug-in shows them only in some setups; which is not known.
        (0.5550, 0.1504, "Left pan"),
        (0.5550, 0.8496, "Right mic level"),
        (0.5550, 0.9316, "Right pan"),
        (0.7673, 0.0684, "Left room level"),
        (0.7673, 0.8496, "Right room level"),
    ),
    "eq": (
        (0.4693, 0.1514, "High pass filter"),
        (0.4693, 0.2900, "Low frequency"),
        (0.4693, 0.4287, "Low mid frequency"),
        (0.4693, 0.5674, "High mid frequency"),
        (0.4693, 0.7061, "High frequency"),
        (0.4693, 0.8447, "Low pass filter"),
        (0.5997, 0.2334, "Low gain"),
        (0.5997, 0.4023, "Low mid gain"),
        (0.5997, 0.5713, "High mid gain"),
        (0.5997, 0.7402, "High gain"),
    ),
    "volume": (
        (0.5128, 0.3320, "Mid-point"),
        (0.5262, 0.4995, "Volume pedal"),
    ),
    "postfx": (
        (0.3491, 0.1689, "Chorus mix"),
        (0.3491, 0.2920, "Chorus rate"),
        (0.3491, 0.3896, "Chorus depth"),
        (0.4693, 0.2734, "Delay sync"),
        (0.5102, 0.5840, "Delay feedback"),
        (0.5115, 0.1680, "Delay mix"),
        (0.5256, 0.2827, "Delay time left display"),
        # Only there while the delay is synced (DAW or tap), between the two note displays.
        (0.5256, 0.3682, "Delay tempo"),
        (0.5256, 0.4702, "Delay time right display"),
        (0.5486, 0.6543, "Delay crystals"),
        (0.5486, 0.7139, "Delay tape"),
        (0.5486, 0.7744, "Delay mod"),
        (0.5959, 0.1680, "Delay low cut"),
        (0.5959, 0.2725, "Delay time left"),
        (0.5959, 0.3770, "Delay cross feed"),
        (0.5959, 0.4814, "Delay time right"),
        (0.5959, 0.5840, "Delay high cut"),
        (0.7673, 0.1680, "Reverb mix"),
        (0.7673, 0.3281, "Reverb pre-delay"),
        (0.7673, 0.4131, "Reverb decay"),
        (0.7673, 0.4980, "Reverb low cut"),
        (0.7673, 0.5840, "Reverb high cut"),
    ),
}
VIEW_BUTTON_LANDMARKS = {
    # 2026-11-08: renamed from the plug-in's own layout (probe-results\petrucci-layout\map.txt).
    # Each effect's on/off is its stomp, named "<effect> pedal" or "<effect> rack unit" with its
    # state; the small "switches" beside the stomps were the effects' lamps, and the "racks" and
    # "surfaces" were dimming layers and on-lights - all marked as ignoring clicks.
    # "Rack unit" and not just "rack" since 0.10.19 (Hadi, 2026-11-10).
    "wahcomp": (
        (0.4923, 0.1943, "Wah switch"),
        (0.5499, 0.3301, "Wah on light"),
        (0.5716, 0.6592, "Compressor pedal lamp"),
        (0.6982, 0.6592, "Compressor pedal"),
    ),
    "prefx": (
        (0.3798, 0.3877, "Phaser mode"),
        (0.3913, 0.6660, "Chorus pedal mode"),
        (0.5588, 0.1621, "Overdrive pedal lamp"),
        (0.5588, 0.3877, "Phaser pedal lamp"),
        (0.5588, 0.6133, "Chorus pedal lamp"),
        (0.5588, 0.8398, "Flanger pedal lamp"),
        (0.6790, 0.6133, "Chorus pedal"),
        (0.6790, 0.8389, "Flanger pedal"),
        (0.6803, 0.1611, "Overdrive pedal"),
        (0.6803, 0.3877, "Phaser pedal"),
    ),
    "cab": (
        (0.2749, 0.0430, "Left previous microphone"),
        (0.2749, 0.0752, "Left next microphone"),
        (0.2749, 0.8242, "Right previous microphone"),
        (0.2749, 0.8564, "Right next microphone"),
        (0.3184, 0.1719, "Left microphone switch"),
        (0.3184, 0.9531, "Right microphone switch"),
        (0.6995, 0.1279, "Left room switch"),
        (0.6995, 0.9092, "Right room switch"),
    ),
    "eq": (
        (0.5575, 0.4971, "EQ dimming layer"),
        (0.5946, 0.1514, "EQ"),
        (0.5946, 0.8447, "EQ lamp"),
    ),
    "volume": (
        (0.4795, 0.5000, "Volume on light"),
        (0.5269, 0.5005, "Volume dimming layer"),
    ),
    "postfx": (
        (0.3382, 0.5132, "Chorus rack unit dimming layer"),
        (0.3485, 0.8667, "Chorus rack unit lamp"),
        (0.3491, 0.2305, "Chorus rack unit mode"),
        (0.3491, 0.8262, "Chorus rack unit"),
        (0.4693, 0.4814, "Delay mode"),
        # The delay's tempo light, a stop in every sync mode. The real Tap Tempo button below is
        # in the tree only while Delay sync is on tap (Hadi's capture 10, 2026-11-09); the two
        # centres are 14 pixels apart, just over the x tolerance.
        (0.5467, 0.8374, "Tap tempo light"),
        (0.5473, 0.8232, "Tap tempo"),
        (0.5486, 0.5132, "Delay rack unit dimming layer"),
        (0.6240, 0.8662, "Delay rack unit lamp"),
        (0.6253, 0.8262, "Delay rack unit"),
        (0.7590, 0.5132, "Reverb rack unit dimming layer"),
        (0.7673, 0.2480, "Shimmer"),
        (0.7692, 0.8667, "Reverb rack unit lamp"),
        (0.7698, 0.8252, "Reverb rack unit"),
    ),
}

# The delay changes shape with its sync selector (seen 2026-11-09 on the preset Basic Clean, whose
# delay follows the host; DAW sync is also the plug-in's default). Free: two time knobs, 7 to 6000
# milliseconds, each with a slider display above it. Synced: the same two spots hold note-value
# knobs, 0 to 20, the displays become text boxes printing the note ("1/4"), and a tempo box
# appears between them. probe-results\petrucci-postfx-daw-sync.txt has the synced tree.
NOTE_KNOB_NAMES = {
    "Delay time left": "Delay note left",
    "Delay time right": "Delay note right",
}
# Where the delay's two displays stand in the Post FX view, as (centre y, centre x, the name
# while the delay is free, the name while it is synced). The free and the synced display sit
# within 5 pixels of each other, so the side is all a position can tell.
DELAY_DISPLAYS = {
    "postfx": (
        (0.5256, 0.2822, "Delay time left readout", "Delay note left readout"),
        (0.5256, 0.4727, "Delay time right readout", "Delay note right readout"),
    ),
}
# Range maxima only Post FX has. The delay's high cut (1000 to 16000 hertz) is there in every
# sync mode; its time knobs (6000 milliseconds) only while the delay is free, which is why the
# view went unrecognised with a synced delay until 0.9.2.
POSTFX_RANGE_MAXIMA = (16000.0, 6000.0)

# Stops in the plugin's Tab ring that do nothing: every one is marked allowClicks="false" in the
# plug-in's own layout. Tab passes over them and the view landing never picks them.
DECORATIVE_NAMES = frozenset((
    "Wah on light", "Compressor pedal lamp",
    "Overdrive pedal lamp", "Phaser pedal lamp", "Chorus pedal lamp", "Flanger pedal lamp",
    "EQ dimming layer", "EQ lamp",
    "Volume on light", "Volume dimming layer",
    "Chorus rack unit dimming layer", "Chorus rack unit lamp",
    "Delay rack unit dimming layer", "Delay rack unit lamp",
    "Reverb rack unit dimming layer", "Reverb rack unit lamp",
    # The little rockers beside GATE, DOUBLER, WAH and ROOM. Each caption is a button wired to
    # the same setting as its rocker (plug-in layout: a textButton and a pluginSwitch on one
    # parameter), so the caption is the one stop and says the state (Hadi, 2026-11-08).
    "Gate switch", "Doubler switch", "Wah switch", "Left room switch", "Right room switch",
    # A view's own background, where it is a stop: see VIEW_BACKGROUND_NAME.
    "View background",
))

# The amp power switch's state probe, per live amplifier: each amp has its own panel art, and
# a probe made for one says the wrong thing on another. An amp missing here says no state.
POWER_STATE_KEYS = {
    "Lead": "Lead amp power switch",
    "Clean": "Clean amp power switch",
    "Piezo": "Piezo amp power switch",
    "Rhythm": "Rhythm amp power switch",
}
# The same for the Cab view's miniature amp row. The Piezo has no Cab view.
MINI_POWER_STATE_KEYS = {
    "Lead": "Mini Lead amp power switch",
    "Clean": "Mini Clean amp power switch",
    "Rhythm": "Mini Rhythm amp power switch",
}

# The section views in button order, as viewOf names them.
VIEW_KEYS = ("wahcomp", "prefx", "amp", "cab", "eq", "volume", "postfx")

# The previous and next module keys (the brackets; Hadi, 2026-11-10). Each view's modules in the
# order the keys step through them, which is how they stand on screen - left to right, or top to
# bottom for the Post FX racks: (name, axis, low, high). A control belongs to the module whose
# span holds its centre along that axis, as a client fraction. The boundaries are the middles of
# the gaps between neighbouring modules in probe-results\petrucci-views.txt (2026-08-11); in the
# Pre FX view the pedals' controls end and start at 262 and 358, 441 and 538, 720 and 770 pixels
# of 1024, and the Post FX racks are 202 to 327, 335 to 523 and 531 to 656 pixels of 782.
# The top bar is a module of every view and comes first, so the keys also do something in the
# views that are one module.
VIEW_MODULES = {
    "wahcomp": (("Wah", "x", 0.0, 0.5), ("Compressor", "x", 0.5, 1.0)),
    "prefx": (("Overdrive", "x", 0.0, 0.303), ("Phaser", "x", 0.303, 0.478),
              ("Chorus", "x", 0.478, 0.728), ("Flanger", "x", 0.728, 1.0)),
    "amp": (("Amplifier", "x", 0.0, 1.0),),
    "cab": (("Left microphone", "x", 0.0, 0.25), ("Amplifier", "x", 0.25, 0.75),
            ("Right microphone", "x", 0.75, 1.0)),
    "eq": (("EQ", "x", 0.0, 1.0),),
    "volume": (("Volume", "x", 0.0, 1.0),),
    "postfx": (("Chorus", "y", 0.0, 0.423), ("Delay", "y", 0.423, 0.674), ("Reverb", "y", 0.674, 1.0)),
}

# Value boxes Tab does not pass over (see VALUE_BOX_SUFFIX in archetypex.py).
# Not passed over: the tempo's box only comes into being when Tab lands on it (0.9.3), so Enter
# on the Delay tempo knob may find no box to go into, and Tab is then the one way to type a tempo.
VALUE_BOX_KEPT = frozenset(("Delay tempo readout",))

# Per amplifier: the knobs left to right, and the small switch buttons left to right, as printed
# on each panel (manual pages 12 and 13). The Lead panel was verified against the live tree; the
# other three follow the manual's order and are confirmed by Verify-PetrucciVst3.ps1 when it
# walks each amp. The amp's own OUTPUT knob is named "Amp output" so it cannot be mistaken for
# the global Output in the top bar.
AMP_KNOB_TABLES = (
    ("Body", "Bass", "Middle", "Treble", "Presence", "Amp output"),                      # Piezo
    ("Gain", "Bass", "Middle", "Treble", "Presence", "Master", "Amp output"),            # Clean
    ("Gain", "Tight", "Bass", "Middle", "Treble", "Presence", "Master", "Amp output"),   # Rhythm
    ("Gain", "Bass", "Middle", "Treble", "Presence", "Master", "Amp output"),            # Lead
)

# The pedals' and racks' knobs that say where their pointer points, by view, under the names
# VIEW_SLIDER_LANDMARKS gives them. They are the round knobs (rotaryFilmStripKnob with one of
# the strips above, in the plug-in's layout) whose value is a percentage and which have no
# number shown beside them: 2, 11 and 13 of them, and the three of POINTER_KNOB_SKEW. Left out
# on purpose:
#   - Wah pedal and Volume pedal, treadles of 51 pictures, and the Gain reduction meter;
#   - Wah position and Mid-point, knobs the plug-in draws by code, each with a number box;
#   - Delay sync, a three-position switch, and the delay's time and note knobs, which have a
#     number shown beside them.
VIEW_POINTER_KNOBS = {
    "wahcomp": frozenset(("Compression", "Compressor level")),
    "prefx": frozenset((
        "Overdrive tone", "Overdrive drive", "Overdrive level", "Phaser rate",
        "Chorus rate", "Chorus depth", "Chorus level",
        "Flanger rate", "Flanger depth", "Flanger range", "Flanger feedback")),
    "postfx": frozenset((
        "Chorus mix", "Chorus rate", "Chorus depth",
        "Delay mix", "Delay feedback", "Delay cross feed", "Delay crystals", "Delay tape", "Delay mod",
        "Delay low cut", "Delay high cut",
        "Reverb mix", "Reverb pre-delay", "Reverb decay", "Reverb low cut", "Reverb high cut")),
}

# Knobs of VIEW_POINTER_KNOBS counted in hertz or milliseconds, whose pointer does not move
# evenly with the value: it is at ((value - min) / (max - min)) ** skew of its travel. The
# figure is the skew the plug-in's model definitions give the setting (delayLowCut,
# delayHighCut, reverbPreDelay). Capture 10 agrees: tools\probe\Match-CaptureKnobs.py reads
# pictures 27, 89 and 8 off it for 111.259 hertz, 13161.1 hertz and 4.46464 milliseconds, a
# method good to one picture, and this gives 27.6, 88.2 and 8.8 where an even scale would give
# 12, 81 and 2.
POINTER_KNOB_SKEW = {"Delay low cut": 0.6, "Delay high cut": 0.6, "Reverb pre-delay": 0.6}
AMP_SWITCH_TABLES = (
    ("Air switch",),                      # Piezo
    ("Bright switch",),                   # Clean
    ("Bite switch", "Mid boost switch"),  # Rhythm
    ("Soar switch",),                     # Lead
)


class PetrucciProfile(ArchetypeXProfile):
    """The Neural DSP Archetype Petrucci X, standalone and VST3."""

    id = "petrucci"
    displayName = "Archetype Petrucci X"

    # The root element's Name is exactly this, and the provider description names the module.
    markers = ("Archetype Petrucci X",)

    executableNames = (
        "archetype petrucci x",
        "Archetype Petrucci X",
        "ARCHETYPE PETRUCCI X",
    )

    # The seven section buttons at the top, left to right. Their HelpText is the bare section
    # name. Until 0.11.13 the word after it was "view", as on the Mesa; Hadi asked for "section"
    # here (2026-11-11: "can we switch the wording from view to section, when I switch to them
    # with the number keys? right now it says: amp view, cab view, etc"), on the day the keys
    # that switch a section off and on came in.
    sectionNames = ("Wah Comp", "Pre FX", "Amp", "Cab", "EQ", "Volume", "Post FX")

    # The standalone's audio settings open from the named SETTINGS tab in the utility bar.
    audioSettingsButtonName = "SETTINGS"

    friendlyNames = {
        "Wah Comp": "Wah Comp section",
        "Pre FX": "Pre FX section",
        "Amp": "Amp section",
        "Cab": "Cab section",
        "EQ": "EQ section",
        "Volume": "Volume section",
        "Post FX": "Post FX section",
        TUNER_HELP: "Tuner",
    }

    # The four amplifier models, matching the selector buttons at the bottom, left to right.
    ampModelNames = ("Piezo", "Clean", "Rhythm", "Lead")

    # The delay's sync selector is a three position slider, and its note-value knobs have 21.
    enumValues = {
        "Delay sync": ("free", "DAW sync", "tap sync"),
        "Delay note left": NOTE_VALUE_NAMES,
        "Delay note right": NOTE_VALUE_NAMES,
    }

    # ---- reading switch positions off the screen ----
    #
    # None of these switches exposes any state to the tree. Calibrated 2026-08-11 by
    # tools\probe\Probe-PetrucciSwitchGrid.ps1 with the cursor parked away from every capture
    # (hover highlighting once contaminated the readings by 77 grey levels) and the polarity
    # assigned by looking at the saved state screenshots in probe-results\swgrid-*.png.
    #
    # Keys are the POSITIONAL names this profile gives the switches (they carry no HelpText), so
    # a probe is only consulted while its amp panel is actually on screen. Boxes are 6x6 pixels
    # at the default window size, offsets in client fractions from each control's own rectangle.
    # Below the threshold speaks the first word, at or above it the second.
    #
    # Verified polarities: the GATE and DOUBLER rockers light up with the nub to the right when
    # active (both read "on" in the session state); the INPUT MODE nub points at the brighter of
    # the Mono / Stereo captions (Mono active read 50.7 against Stereo 27.9). The amp panels'
    # bat toggles (power, Soar, Air, Bright, Bite, Mid boost) had their on position settled from
    # the plug-in's own pictures, which are named Off and On; see the entries below.
    switchProbeSize = (0.00586, 0.00767)
    switchProbes = {
        "Input mode switch": (0.00781, 0.01023, 135, ("mono", "stereo")),
        # Soar's polarity settled 2026-11-08 without an ear test: the plug-in's pictures of the
        # switch are named Off and On, and On has the lamp dot beside the toggle lit. Hadi's
        # captures 8 and 9 show this probe reading 156 with the dot dark and 98 with it lit, so
        # below the threshold (handle down) is on.
        "Soar switch": (0.01953, 0.01535, 132, ("on", "off")),
        # (The amp power switch is read per amplifier, in tipProbes below.)
        # These four said "up" or "down" until 0.9.4, for want of knowing which position is on.
        # Settled 2026-11-09 from the plug-in's own pictures, named SwitchOff and SwitchOn per
        # amp: the real screen crops of 2026-08-11 (probe-results\swgrid-*.png) match one
        # picture each to within 3 grey levels, and at these spots the On picture reads 108
        # (Bright), 109 (Air) and 57 (Bite, Mid boost) against 17, 30 and 20 for Off. Air's
        # setting is not on/off: the plug-in calls its two values Normal and Ultra.
        "Air switch": (0.00391, 0.00512, 69, ("Normal", "Ultra")),
        "Bright switch": (0.01172, 0.01023, 62, ("off", "on")),
        "Bite switch": (0.01172, 0.02558, 38, ("off", "on")),
        "Mid boost switch": (0.01172, 0.02558, 38, ("off", "on")),
        # The tuner window's mute button is a red square while muted: 104 against 30 for the
        # unmuted dark grey, measured 4 pixels in from its corner (tuner2-mute-*.png). Hadi
        # confirmed by ear that red is muted - the plugin silences itself while tuning.
        "Mute while tuning": (0.00391, 0.00512, 67, ("not muted", "muted")),
        # Each effect's on/off stomp, read from its own lamp (2026-11-08). The box sits on the
        # lamp's centre, offset from the stomp's corner; positions from the plug-in's layout.
        # Post FX racks: the middle of three dots, 76 and 79 dark against 153 lit
        # (probe-results\petrucci-layout, screenshots of 2026-11-08).
        "Chorus rack unit": (0.06348, 0.02941, 115, ("off", "on")),
        "Delay rack unit": (0.05859, 0.02302, 115, ("off", "on")),
        "Reverb rack unit": (0.06055, 0.02430, 115, ("off", "on")),
        # Pedals and the compressor share one lamp picture: centre 58.6 dark on screen, which is
        # exactly the plug-in's "off" picture, and 250 in its "on" picture.
        "Overdrive pedal": (0.03320, -0.07928, 150, ("off", "on")),
        "Phaser pedal": (0.03223, -0.07928, 150, ("off", "on")),
        "Chorus pedal": (0.03223, -0.07801, 150, ("off", "on")),
        "Flanger pedal": (0.03320, -0.07801, 150, ("off", "on")),
        "Compressor pedal": (0.03320, -0.08312, 150, ("off", "on")),
        # From Hadi's before-and-after captures, 2026-11-08 (%TEMP%\neuralAccess-captures 1-6).
        # The microphone switch's background: 32 off, 138 on, sampled at the bottom centre, which
        # is inside the button on both sides whichever corners are rounded. That light means on
        # comes from the plug-in's skin: the switched-on background colour is U97, off U25.
        #
        # WORDS SWAPPED in 0.9.8: dark is ON. The first reading of the skin had light as on, and
        # nobody had checked by ear. Against it: the plug-in's own style for this button is
        # called "cabsimBypassSwitch", so its lit state is the bypass; the preset Basic Clean
        # stores both microphones active and both read 32 on 2026-11-09; and both read 32 in the
        # first capture of 2026-11-08 on another preset - nobody plays with both microphones
        # off. Still to be confirmed by Hadi's ear.
        "Left microphone switch": (0.01367, 0.03325, 85, ("on", "off"), (0.00391, 0.00512)),
        "Right microphone switch": (0.01367, 0.03325, 85, ("on", "off"), (0.00391, 0.00512)),
        # PHASE lights a dot beside its symbol when inverted: 21 against 226. Same spot on both
        # sides (the right one read 226 in the same captures, and looks identical).
        "Left phase": (0.05176, 0.00639, 120, ("normal", "inverted"), (0.00293, 0.00384)),
        "Right phase": (0.05176, 0.00639, 120, ("normal", "inverted"), (0.00293, 0.00384)),
        # The Cab view's miniature Soar: its lamp dot, 157 dark against 224 lit.
        "Mini Soar switch": (0.01660, 0.01407, 190, ("off", "on"), (0.00195, 0.00256)),
        # The Rhythm amp's miniatures (0.9.10), from the plug-in's pictures ONLY: no capture of
        # the Cab view on the Rhythm amp exists. Its art is dark on dark, so comparing two spots
        # gives too little; these read one 3x3 spot each. Power, on the lamp dot: 94 lit, 23
        # dark in the model (66 to 96 and 20 to 27 over a pixel's shift). Bite and Mid boost, at
        # the handle's tip: 84 on, 36 off at the default size, but only 53 against 36 in the
        # worst case, so these two are the least certain readings in the add-on. Check the
        # first values that show up in a log against these numbers.
        "Mini Rhythm amp power switch": (0.01661, 0.01407, 58, ("amp off", "amp on"), (0.00293, 0.00384)),
        "Mini Bite switch": (0.00587, 0.00129, 60, ("off", "on"), (0.00293, 0.00384)),
        "Mini Mid boost switch": (0.00587, 0.00129, 60, ("off", "on"), (0.00293, 0.00384)),
    }

    # The mode switches and the EQ's on/off, read from where the handle's bright tip is
    # (2026-11-08). Each pair of spots is where the plug-in's two pictures of that switch differ
    # most, restricted to pixels solid in both pictures - the first attempt let the panel's
    # VIBE caption show through and misread the phaser. Checked on the screenshots: chorus rack
    # 141 against 8, shimmer 175 against 23, delay 21 against 184, chorus pedal 124 against 69,
    # phaser 129 against 53, all the right way. The EQ pair is from its pictures only, with
    # off = handle down by the naming order of its two pictures; not yet seen on screen.
    decorativeNames = DECORATIVE_NAMES
    tipProbes = {
        "Chorus rack unit mode": ((0.4565, 0.2174), (0.4565, 0.6522), 0.0870, ("Vintage", "Spatial")),
        "Shimmer": ((0.4792, 0.6458), (0.4792, 0.2292), 0.0833, ("off", "on")),
        "Delay mode": ((0.2045, 0.4545), (0.6591, 0.4545), 0.0909, ("Single", "Dual")),
        "Chorus pedal mode": ((0.4500, 0.3000), (0.4333, 0.6500), 0.0667, ("Normal", "Tri")),
        "Phaser mode": ((0.3167, 0.4333), (0.6500, 0.4167), 0.0667, ("Phase", "Vibe")),
        "EQ": ((0.4259, 0.5556), (0.5000, 0.3704), 0.0741, ("off", "on")),
        # The little pill rockers (GATE, DOUBLER, WAH, ROOM), 20x12 with a white nub that sits
        # right when on. Read by comparing the pill's two ends since 0.9.3, because the pill is
        # see-through: its empty end read 16 on the Lead amp's dark background but 92 on the
        # Clean amp's sky, over the old fixed threshold of 90, and a gate that was on said "off"
        # (Hadi's capture 10, 2026-11-09). The nub reads 204 to 225 either way. Checked on
        # captures 1 to 6, 8, 9 and 10: gate and doubler on 12 against 205, gate on over sky 89
        # against 220, doubler off over sky 225 against 111, rooms off 209 against 36. The wah
        # is the same pill and has not been seen on screen with this probe.
        "Gate switch": ((0.20, 0.3334), (0.50, 0.3334), 0.30, ("gate off", "gate on")),
        "Doubler switch": ((0.20, 0.3334), (0.50, 0.3334), 0.30, ("doubler off", "doubler on")),
        "Wah switch": ((0.20, 0.3334), (0.50, 0.3334), 0.30, ("wah off", "wah on")),
        "Left room switch": ((0.20, 0.3334), (0.50, 0.3334), 0.30, ("room off", "room on")),
        "Right room switch": ((0.20, 0.3334), (0.50, 0.3334), 0.30, ("room off", "room on")),
        # Captions that are switches (see CAPTION_STATE_KEYS) sample the same two ends of their
        # rocker, measured from the caption's own rectangle: the rocker starts 38 pixels into
        # GATE (64 wide), 58 into DOUBLER (83), 34 into WAH (60) and 40 into ROOM (62).
        "Gate": ((0.65625, 0.4091), (0.75, 0.4091), 0.09375, ("off", "on")),
        "Doubler": ((0.74699, 0.4091), (0.81928, 0.4091), 0.07229, ("off", "on")),
        "Wah": ((0.63334, 0.4091), (0.73334, 0.4091), 0.1, ("off", "on")),
        "Left room": ((0.70968, 0.4091), (0.80646, 0.4091), 0.09677, ("off", "on")),
        "Right room": ((0.70968, 0.4091), (0.80646, 0.4091), 0.09677, ("off", "on")),
        # The amp power switch, one probe per amplifier because each has its own panel art (see
        # POWER_STATE_KEYS). Until 0.9.4 one fixed threshold measured on the Lead's light panel
        # served all four, and on the other three, whose panels are dark, it could only say
        # "amp off" (Hadi, 2026-11-09, on Clean). These spots were computed with nothing on
        # screen, from the plug-in's own pictures of each panel and switch
        # (tools\probe\Find-SwitchSpotsFromArt.py): the first spot is brighter while the amp is
        # on, the second while it is off, by at least 34 grey levels in the worst case over
        # four ways of scaling the pictures and a pixel of misalignment either way. The model
        # was checked against real screen pixels on the Lead amp only: it gives 212.3 / 154.4
        # on and 145.2 / 214.2 off, the screen 211.9 / 153.9 and 144.8 / 214.1. Clean agrees
        # with the two readings in Hadi's log; Piezo and Rhythm have never been seen on screen.
        "Lead amp power switch": ((0.1401, 0.7401), (0.1401, 0.1201), 0.12, ("amp on", "amp off")),
        "Clean amp power switch": ((0.1201, 0.1001), (0.1001, 0.7401), 0.12, ("amp on", "amp off")),
        "Piezo amp power switch": ((0.0751, 0.1001), (0.1001, 0.6501), 0.15, ("amp on", "amp off")),
        "Rhythm amp power switch": ((0.8201, 0.4401), (0.0801, 0.7601), 0.12, ("amp on", "amp off")),
        # The Cab view's miniature amp row on the Clean and Lead amps (0.9.10), found the same
        # way with a 3 pixel box. Checked on real captures in the states they show: Clean power
        # on 163.9 / 19.4 (model 164.4 / 19.7) and Bright off 28.9 / 111.5 (model 16.8 / 112.1)
        # in capture 13; Lead power on 209.4 / 165.6 (model 209.7 / 166.1) in captures 5 and 6.
        # The other states are from the model. Lead's power has the thinnest margin, 21 to 25
        # in the worst case: under 20 it says nothing, which is the safe way to fail.
        "Mini Clean amp power switch": ((0.0801, 0.1201), (0.1201, 0.7201), 0.1201, ("amp on", "amp off")),
        "Mini Lead amp power switch": ((0.1201, 0.7601), (0.1201, 0.0801), 0.1201, ("amp on", "amp off")),
        "Mini Bright switch": ((0.2918, 0.1668), (0.2918, 0.6668), 0.1251, ("on", "off")),
    }

    # Switch names that also appear on the Cab view's miniature amp row. The probes above are
    # calibrated for the full-size panel controls; a miniature carrying the same name must stay
    # stateless rather than sample the wrong pixels.
    FULL_SIZE_STATE_NAMES = frozenset((
        "Soar switch", "Amp power switch", "Air switch", "Bright switch",
        "Bite switch", "Mid boost switch",
    ))

    # The tables above, where the shared code looks for them.
    KNOB_UNITS = KNOB_UNITS
    VIEW_SLIDER_LANDMARKS = VIEW_SLIDER_LANDMARKS
    VIEW_BUTTON_LANDMARKS = VIEW_BUTTON_LANDMARKS
    VIEW_KEYS = VIEW_KEYS
    VIEW_MODULES = VIEW_MODULES
    VIEW_POINTER_KNOBS = VIEW_POINTER_KNOBS
    POINTER_KNOB_SKEW = POINTER_KNOB_SKEW
    NOTE_KNOB_NAMES = NOTE_KNOB_NAMES
    DELAY_DISPLAYS = DELAY_DISPLAYS
    VALUE_BOX_KEPT = VALUE_BOX_KEPT
    AMP_KNOB_TABLES = AMP_KNOB_TABLES
    AMP_SWITCH_TABLES = AMP_SWITCH_TABLES
    POWER_STATE_KEYS = POWER_STATE_KEYS
    MINI_POWER_STATE_KEYS = MINI_POWER_STATE_KEYS

    # Only the Piezo amp lacks sections, and only two: with it live the plug-in drops the Cab
    # and EQ buttons (a piezo pickup has no cabinet).
    MISSING_SECTION_MESSAGE = "No %s section on the Piezo amplifier."

    def _ampIndexOf(self, knobs, switches):
        """Piezo has six knobs, Rhythm has eight, and the two seven-knob amps are told apart by
        where the switch button sits - Lead's SOAR between the third and fourth knobs, Clean's
        BRIGHT between the first and second."""
        count = len(knobs)
        if count == 6:
            return 0
        if count == 8:
            return 2
        if count == 7:
            for x, _rect, _element in switches:
                if knobs[2][0] < x < knobs[3][0]:
                    return 3
            return 1
        return None

    def _viewFromSliders(self, sliders, geometry):
        """Post FX is the only view with the delay's 16000 hertz high cut (see
        POSTFX_RANGE_MAXIMA), EQ the only one with a 20 to 500 hertz knob, the two pedal views
        have a giant pedal slider told apart by where it stands, and Pre FX is a wall of 80
        pixel pedal knobs."""
        left, top, width, height = geometry
        bigPedalCentre = None
        knob80 = 0
        for element in sliders:
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4:
                continue
            wF = rect[2] / width
            hF = rect[3] / height
            if wF > 0.25 and hF > 0.55:
                bigPedalCentre = (rect[0] + rect[2] / 2.0 - left) / width
                continue
            maximum = _prop(element, PROP_RANGE_MAX)
            if maximum is not None:
                try:
                    maximum = float(maximum)
                except Exception:
                    maximum = None
            if maximum in POSTFX_RANGE_MAXIMA:
                return "postfx"
            if maximum == 500.0:
                return "eq"
            if 0.074 <= wF <= 0.082 and (rect[1] - top) / height > 0.30:
                knob80 += 1
        if bigPedalCentre is not None:
            return "wahcomp" if bigPedalCentre < 0.4 else "volume"
        return "prefx" if knob80 >= 8 else "amp"


PROFILE = PetrucciProfile()
