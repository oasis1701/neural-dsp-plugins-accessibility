# neuralAccess - what the Archetype X plug-ins share.
#
# Neural DSP's X generation (Archetype Petrucci X, Archetype Nolly X) is built on one framework:
# the same top bar with its two meters, the same preset row, section buttons, amp selectors and
# bottom bar, the same tuner and MIDI mappings windows, and the same habits in the accessibility
# tree. ArchetypeXProfile holds everything that follows from that framework. A plug-in's own
# profile (petrucci.py, nolly.py) subclasses it, fills in the tables listed at the top of the
# class - its sections, landmarks, amplifiers and switch probes - and overrides the few methods
# where the plug-ins really differ (_viewFromSliders, _ampIndexOf).
#
# All of it was worked out on the Petrucci X and lived in petrucci.py until 0.12.0. That is why
# the comments here speak of that plug-in, and why the state kept on a controller is still named
# _petrucci...: the offline check, tools\dev\Check-PetrucciNames.py, reads some of those names.
#
# The facts this is built on, verified against the running Petrucci X on 2026-08-11 and seen
# again in the Nolly X's tree on 2026-11-11:
#
#   * Mixed naming. Some controls carry a real Name (GATE, DOUBLER, SAVE AS..., TUNER, MIDI, the
#     preset display with the loaded preset's name), the seven section buttons carry their label
#     in HelpText with an empty Name, and every slider is completely anonymous - no Name, no
#     HelpText. The anonymous ones get positional names from the layout tables below.
#   * UIA Invoke and a plain Enter are BOTH ignored by every button; only a real cursor click
#     works. Verified 2026-08-11: Invoke on the amp selectors changed nothing, Enter on a focused
#     section button changed nothing, a genuine click switched the view at once. So every press
#     this profile makes goes through controller.clickElement.
#   * The Toggle pattern's state is a LATCH, not the selection: it flips permanently once a
#     button has been activated and all four amp selectors read On after one sweep through them.
#     Nothing may be announced from it (dropPressedState), and the live amp is detected from the
#     STRUCTURE of the amp panel instead - each amplifier has a different knob count, and the
#     two seven-knob amps differ in where their switch button sits.
#   * Sliders report real ranges through RangeValue and accept SetValue (verified: INPUT moved
#     0 to +1 dB and back, with the readout following live).
#   * The five top-bar readouts are Edit controls whose text lives only in the Text pattern
#     ('0.0 dB', '-93.1 dB', '0 st', '7.00 ms'), matched to their knobs by x overlap.
#
# Coordinates are client fractions of the editor (1024 x 782 at default size), so they survive
# the plugin's three fixed sizes and its continuous drag resizing.

import os
import re
import time

import api
import controlTypes
import ui
from core import callLater
from keyboardHandler import KeyboardInputGesture
from logHandler import log

from . import core as engine
from . import popups
from . import tuning
from .core import (
    CT_BUTTON, CT_COMBOBOX, CT_CUSTOM, CT_EDIT, CT_SLIDER, CT_TEXT,
    PROP_BOUNDING_RECT, PROP_CONTROL_TYPE, PROP_HELP_TEXT, PROP_IS_ENABLED,
    PROP_IS_KEYBOARD_FOCUSABLE, PROP_NAME,
    PROP_RANGE_MAX, PROP_RANGE_MIN, PROP_RANGE_VALUE,
    STATE_CACHE_TTL, TREESCOPE_DESCENDANTS,
    _prop, textPatternText,
)

# The bands of the client area, as (low, high) fractions of its height.
TOP_KNOB_Y = (0.10, 0.20)        # the five global knobs, y fraction 0.136
READOUT_Y = (0.19, 0.25)         # their display texts, y fraction 0.212
HEADER_Y = (0.09, 0.125)         # captions, small switches, preset arrows, y fraction 0.102
AMP_BAND_Y = (0.60, 0.70)        # the amp panel's knobs and switches, y fraction 0.643
SELECTOR_Y = (0.85, 0.93)        # the four amp model buttons, y fraction 0.885
UTILITY_Y = (0.94, 1.01)         # the utility bar, y fraction 0.964

# The five global knobs, left to right.
TOP_KNOB_NAMES = ("Input", "Gate threshold", "Transpose", "Doubler spread", "Output")
KNOB_UNITS = {
    "Input": "decibels",
    "Gate threshold": "decibels",
    "Output": "decibels",
    "Transpose": "semitones",
    "Doubler spread": "milliseconds",
    "Tempo": "beats per minute",
}

# A delay that follows a tempo has a note-value knob standing where its time knob does, with
# 21 positions, 0 to 20 (see NOTE_KNOB_NAMES in ArchetypeXProfile).
NOTE_KNOB_MAX = 20.0
# Note values in the plug-in's own order (model definition, 0 = 1/64T ... 20 = 1/1D), worded for
# speech: a synthesiser makes "1/8D" into "one slash eight D".
NOTE_VALUE_NAMES = (
    "sixty-fourth note triplet", "sixty-fourth note", "thirty-second note triplet",
    "dotted sixty-fourth note", "thirty-second note", "sixteenth note triplet",
    "dotted thirty-second note", "sixteenth note", "eighth note triplet",
    "dotted sixteenth note", "eighth note", "quarter note triplet",
    "dotted eighth note", "quarter note", "half note triplet",
    "dotted quarter note", "half note", "whole note triplet",
    "dotted half note", "whole note", "dotted whole note",
)

# In the EQ view the view's background is itself a stop, the first of the ring: an unnamed
# Custom control at the editor's corner, as wide as the editor and 750 of its 782 pixels high
# (Hadi's log, 2026-11-10: "focus '', UNKNOWN ... at (330, 241, 1024, 750)" between High pass
# filter and Resize window; no other view's log has it). NVDA called it "unknown". Worse, at
# 96 per cent of the editor's height it counted as the editor with nothing focused
# (AmpObject.ampIsDeadEnd), so Tab or Shift+Tab pressed on it put focus back on the last
# control instead of moving on, and he went round between it and Resize window. Named, and
# listed among the stops Tab passes over, it is left the way a lamp is: the key goes on to
# the plug-in. The editor's own root is the full height and is not matched.
VIEW_BACKGROUND_NAME = "View background"
VIEW_BACKGROUND_HEIGHT = (0.93, 0.985)

# The top bar's background container, a stop in the plug-in's ring between a view's last
# control and GATE. Named so that a landing on it any other way (the plug-in drops focus there
# while it rebuilds a panel) says something, and passed over by Tab and Shift+Tab in every view
# since 0.12.6 (Hadi, 2026-11-11: "skip it everywhere in both plugins"). Until then only the
# Nolly's EQ went round it, as a side effect of its jumps (0.12.5).
TOP_BAR_BACKGROUND_NAME = "decorative background"

# Captions that are switches, by the plugin's own name for them -> the key their state probe is
# filed under. ROOM and PHASE exist once per Cab side and get Left or Right in front.
CAPTION_STATE_KEYS = {
    "GATE": "Gate", "DOUBLER": "Doubler", "WAH": "Wah", "ROOM": "room", "PHASE": "phase",
}
SIDED_CAPTIONS = frozenset(("room", "phase"))

# Where focus lands after a view or amp switch: the view's first stop in the plugin's own Tab
# order. JUCE builds its Tab order and its accessibility tree with one traversal - siblings sorted
# by top edge to the pixel, then left edge, children straight after their parent - and the view's
# content comes first in the tree, ahead of the top bar (checked against the captured native ring
# in probe-results\petrucci-tab-ring.txt). So the first operable control in document order that
# sits between the top bar and the amp selectors is where Tab starts in that view. Landing on a
# control picked by eye put Hadi mid-ring: Pre FX starts on the chorus pedal, one pixel higher
# than the overdrive.
LANDING_TYPES = (CT_SLIDER, CT_BUTTON, CT_COMBOBOX, CT_EDIT)
VIEW_CONTENT_Y = (0.243, 0.85)   # below the 190 pixel top bar, above the amp selectors

# The top bar is a module of every view and comes first for the bracket keys (see
# VIEW_MODULES in ArchetypeXProfile), so the keys also do something in a view of one module.
TOP_BAR_MODULE = "Top bar"

# G and D: which -> (the caption's own Name, how the switch is spoken of). The caption is the
# switch (see CAPTION_STATE_KEYS), so it is what gets clicked. Focus stays where it was (Hadi,
# 2026-11-10): the click hands keyboard focus to the caption, so it is sent back once the
# button is up again (core.clickElement: down at 150 ms, up at 230), both focus changes are
# kept quiet for QUICK_HUSH_S, and the place to go back to is remembered for QUICK_HOME_S so
# that a second press, made while focus is still on the caption, returns to the same place.
QUICK_SWITCHES = {"gate": ("GATE", "Gate"), "doubler": ("DOUBLER", "Doubler")}
QUICK_RETURN_MS = 320
QUICK_HUSH_S = 1.2
QUICK_HOME_S = 1.5

# The list of presets is watched from the click that opens it until it closes: how often, how
# many looks it is given to appear, and when to stop watching one that is left open.
PRESET_LIST_POLL_MS = 120
PRESET_LIST_APPEAR_POLLS = 25
PRESET_LIST_MAX_S = 600.0

# DELETE, in the preset row while a user preset is loaded, asks before it deletes. The question
# is the plug-in's own (presetDeleteDialogView.xml among the layouts inside the VST3, read
# 2026-11-10; never yet seen on screen): a 344 by 155 panel in the middle of the editor, over a
# layer that dims everything else and closes the question when clicked. In the panel, at these
# offsets in its own pixels: the question at 16 down, "This action is permanent." at 74, and at
# 107 down the buttons Cancel (174 across, 60 wide) and "Yes, delete" (242 across, 86 wide).
# The panel is found from the "Yes, delete" button, whose width gives the scale.
#
# Seen on 0.10.4 (Hadi's log, probe-results\nvda-log-2026-11-10-0.10.4-delete-tab.txt): the
# question comes up about 0.6 s after Enter on DELETE with exactly these names and places, and
# Cancel takes focus and a click. "Yes, delete" does NOT take keyboard focus, whatever the
# layout says: focus asked onto it lands on the first stop of the plug-in's ring (Chorus rate
# on Pre FX), which is where JUCE sends focus that a component will not take, and the
# plug-in's own Tab goes from Cancel to that same stop. So focus stays on Cancel, Tab and
# Shift+Tab choose between the two buttons by name without moving it, and Enter clicks the
# chosen one. The choice goes back to Cancel on any focus change and any other key, so that
# Enter never does anything other than what NVDA would say focus is on - except straight
# after a Tab that has just said "Yes, delete".
DELETE_BUTTON_NAME = "DELETE"
DELETE_QUESTION_YES = "Yes, delete"
DELETE_QUESTION_CANCEL = "Cancel"
DELETE_QUESTION_PANEL = (344.0, 155.0)
DELETE_QUESTION_YES_AT = (242.0, 107.0, 86.0)
DELETE_QUESTION_MARGIN = 24.0
# Both lines of text are 312 wide. The view behind the panel is still in the tree, dimmed, and
# its captions lie inside the panel's rectangle too ("TAP", "SINGLE / DUAL" on Post FX): the
# width is what tells the question's own lines from those.
DELETE_QUESTION_TEXT_WIDTH = 312.0
# How often the question is looked for, how many looks it is given to come up after the click
# on DELETE and to go away after an answer, and how many more a deleted preset is given to
# disappear from the preset button and from disk.
DELETE_QUESTION_POLL_MS = 120
DELETE_QUESTION_APPEAR_POLLS = 20
DELETE_QUESTION_CLOSE_POLLS = 20
DELETE_QUESTION_SETTLE_POLLS = 6
# The amplifier whose delete question is up, for noteGesture, which is told the key and nothing
# about where it was pressed.
_deleteQuestionController = None

# More preset actions swaps the preset row's DELETE, SAVE and SAVE AS... for IMPORT, RESET and
# LOCATE FILE, and swaps them back when pressed again (the layouts' moreActionsNormalView and
# moreActionsSelectedView; the button itself is a different one in each, at the same place).
# IMPORT is the first of the three, and whether it is in the tree says which row is showing.
# After a press the row is looked at this often, this many times, for the swap to happen.
MORE_ACTIONS_FIRST = "IMPORT"
MORE_ACTIONS_POLL_MS = 120
MORE_ACTIONS_POLLS = 12

# The EQ view's two filters are off at one end of their travel, where the display beside the
# knob prints OFF: the high pass at its minimum (20 of 20 to 500 hertz), the low pass at its
# maximum (20000 of 1000 to 20000). What is said for a knob is that display's text, and for
# these two it was behind the knob: stepping up from OFF, Hadi heard "off, off, off, off, 39"
# while the knob went 24.8, 29.6, 34.4, 39.2, and stepping back down he heard every value
# (2026-11-10). Whether the plug-in is slow to change the display on leaving OFF or the add-on
# was holding an old display (the list of displays is kept for POSITIONAL_CACHE_TTL) is not
# known. So for these knobs the display is believed only while it agrees with the knob (see
# _filterReadoutAgrees), a display that disagrees is looked for afresh, at most this often, and
# failing that the knob's own figure is said. The first few disagreements are logged.
FILTER_OFF_END = {"High pass filter": "min", "Low pass filter": "max"}
FILTER_RESWEEP_GAP_S = 0.3
FILTER_LOG_MAX = 12

# The value boxes: the display beside a knob is a text box and a stop in the plug-in's ring,
# named "<knob> readout" here. Each says what its knob says, and Hadi asked for them out of the
# Tab order (2026-11-10: "they show the same things that our controls show and add to the tab
# order clutter"). So Tab and Shift+Tab pass over them (passedOver). They are also the only
# place an exact value can be typed, which a mouse user does by clicking the display, and that
# is kept: Enter on a knob puts focus in its box, and Enter in the box - the key that makes the
# plug-in take what was typed - is followed, this long afterwards, by focus going back to the
# knob, which then says the value. A box gone into is remembered for at most this long.
VALUE_BOX_SUFFIX = " readout"
VALUE_BOX_RETURN_MS = 300
VALUE_BOX_MAX_S = 300.0

# Which amplifier is live, in any view. The four selectors at the bottom are in every view, but
# their toggle state is a latch and not the selection, so until 0.10.13 the live amplifier was
# only ever told from the amp panel's shape, and outside the Amp view the amp keys said "Amp
# model unknown. Switch to the amp view first" (Hadi, 2026-11-10, who had it from tutorials
# that the selectors work at any time; they do). The plug-in draws each selector from three
# pictures: ...AmpSelectorSelected.svg is white at full strength, ...NotSelected.svg the same
# drawing at opacity 0.5, ...Hover.svg at 0.7, for all four amplifiers. So the selector whose
# brightest point is the brightest is the live one. Measured on captures 1, 8, 10, 13 and 16:
# 255 against 167 to 200 for the others, and 127 against 78 behind the Save As panel's dimming.
# The answer is taken only when the brightest beats the next by this factor (a selector under
# the mouse pointer comes to about 225) and is at least this bright (a covered window is black).
AMP_SELECTOR_MARGIN = 1.08
AMP_SELECTOR_MIN = 60.0
# When the amplifier changes the plug-in rebuilds what had focus (the amp panel; the EQ view
# too) and drops focus on the top bar's background until the add-on has put it somewhere. NVDA
# began to say "decorative background" each time (Hadi, 2026-11-10; his log has that stop 0.25
# to 0.33 s after the click and the landing 0.3 s later). That stop, and in other views the
# selector and the control focus goes back to, are kept quiet for this long after the key.
AMP_SWITCH_HUSH_S = 1.5

# The two captions beside the input mode switch are buttons of their own, on the same setting
# as the switch (the layout's stereoButton and monoButton: radio values 1 and 0 of
# selectedMode), and stops in the ring. The switch is the one stop Hadi wants: it says "mono"
# or "stereo" and Enter flips it (2026-11-10: "two more controls in the tab order that we
# probably should remove"). Tab passes over a button with one of these names in this band of
# the editor's height, where the switch is (the captions' tops are at 0.147 and 0.179).
INPUT_MODE_CAPTIONS = frozenset(("Stereo", "Mono"))
INPUT_MODE_CAPTION_Y = (0.12, 0.20)

# How long the plug-in's own stop on MIDI is kept quiet while the tuner window closes.
TUNER_CLOSE_HUSH_S = 1.5
# R: which -> the top bar knob of that name.
QUICK_JUMPS = {"transpose": "Transpose"}

# Double-clicking a section button bypasses that whole section (found while probing, and the
# reason every probe script single-clicks). Plain number keys make a quick double press easy, so
# a second click on the same section button inside this window is never sent.
SECTION_CLICK_GUARD_S = 1.0

# A whole section on or off: Shift+number says which it is and Control+number switches it
# (Hadi, 2026-11-11). The seven views are seven sections of the signal chain and the plug-in can
# take any of them out (its settings wahCompParameters:sectionActive and so on, "Active Wah Comp
# Section" to a host).
#
# Nothing in the tree says whether a section is on: every section button's value reads "Off" in
# every dump on file, sections on or off. The button's picture does. Hadi's capture 15
# (2026-11-10) has Wah Comp, Volume and Post FX switched off. An icon is white at full strength
# while its section is on, 255 at its brightest point on every background in captures 1, 10 and
# 11, and at about a third of that while it is off: brightest point 114 to 119 on a background of
# 52, which is 0.31 to 0.33 of the way from the background to white. The button of the view that
# is showing has a white dot under its icon whatever its section is (capture 15: Post FX's icon
# 119, its dot 255).
#
# So the icon is measured against the whitest thing in the whole row, dots included. That holds
# behind the Save As panel and the MIDI mappings window, which halve everything (icons and dot
# both 127 in captures 16 and 34), and under the mouse pointer, where the plug-in lays a wash of
# white over the button. The measure is (the icon's brightest point - its mean) / (the row's
# brightest point - that mean): 1.0 on and about 0.3 off in the captures, and 1.00 and 0.29 on
# the plug-in itself in Hadi's log of 0.11.14. An icon in between gives no answer. The icon is
# looked for in this part of its button, as fractions of the button's width and height (the icon
# lies between 12 and 41 of the 54 pixels down, the dot between 46 and 50), and a row whose
# brightest point is under SECTION_ROW_MIN is a window that is covered or not drawn.
#
# Reading a box off the screen costs time for every pixel in it, and 0.11.14 read all seven
# buttons at every look: 21 boxes, about a quarter of a second (his log: five looks took 1.2 s
# more than their timers). The row's whitest point is now looked for on the section's own
# button first and then on the others only until one holds full white, SECTION_WHITE or more,
# which the first one looked at does unless everything is dimmed.
SECTION_ICON_BOX = (4 / 54.0, 6 / 54.0, 46 / 54.0, 36 / 54.0)
SECTION_ROW_MIN = 60.0
SECTION_WHITE = 250.0
SECTION_MIN_RANGE = 20.0
SECTION_ON_AT = 0.6
SECTION_OFF_AT = 0.45
# Switching one is the double click a mouse user makes on the section's button. The first of
# those two clicks also shows that section's view (the layout: selectSection on mouseDown), so
# when it has shown another view the add-on clicks back to the view he was in and puts focus
# back where it was, since a key that flips a switch must not move focus (Hadi, 2026-11-10).
#
# 0.11.14 tried UI Automation's Toggle pattern on the button first, which nobody had tried
# before (in August only Invoke and Enter were). His log of that build,
# probe-results\nvda-log-2026-11-11-0.11.14-sections.txt, says what it does: the button's own
# value goes from 'Off' to 'On', the plug-in puts keyboard focus on the button 20 ms later
# ("focus 'Amp section', BUTTON", which he heard as "Amp section, button"), and the section
# stays as it was. The add-on waited two seconds on it before the double click and then took
# the button for the place to send focus back to. So the pattern is not used, here or in core.
#
# After the double click the button is looked at once the pointer is back where it rested
# (core puts it back 330 ms after the call), then this often, this many times. The first look
# that shows the change is believed: in his log the plug-in had redrawn the button by the first
# look every time, and no focus change can cut the answer short, because they are kept quiet.
SECTION_DOUBLE_FIRST_MS = 400
SECTION_DOUBLE_POLL_MS = 120
SECTION_DOUBLE_POLLS = 10
# The way back to the view he was in. In his log that view was showing again 285 ms after the
# click back.
SECTION_RETURN_FIRST_MS = 250
SECTION_RETURN_POLL_MS = 100
SECTION_RETURN_POLLS = 20
# Every focus change in the amplifier is kept quiet from the double click until focus is back,
# and at most this long.
SECTION_TRIP_HUSH_S = 6.0
# One switch at a time: while one is being made, and at most this long, another Control+number
# is left out. A second one starting half way through another view would take that view for
# the one to come back to.
SECTION_BUSY_S = 8.0
# The command's own keys are still down when it starts, and a click made then is a Control+click.
# The double click waits for them to come up, looking this often, at most this many times.
SECTION_KEYS_UP_MS = 50
SECTION_KEYS_UP_POLLS = 30

# The two level meters, at the ends of the top bar: input beside the Input knob, output beside
# the Output knob. Each is in the tree as a background with one bar in it (mono, 7 wide with a
# bar of 5) or two (stereo, 11 wide with two bars of 4), 110 high with bars of 104. They carry no
# name, no value and no pattern, so the level exists only as the drawn bar. For a sighted player
# they are the plug-in's only sign of clipping.
#
# From the plug-in's own files (probe-results\petrucci-layout\raw): the values behind them run
# from -60 to 0 decibels (110-modelDefinition, inputMeterMono and so on), each has a clip flag
# beside it, the clip light is a box four pixels high above the bar in the skin's "errors"
# colour, FFFF2727, and a mouse press on a meter resets its lights (100-layout-topBarView). The
# bar has a mark at 0.775 of its height, which is -13.5 decibels if the scale is even. That
# agrees with what users on Neural DSP's forum report, that the plug-ins are built around -13
# and that input peaks near -12 are what to aim at. No official page saying so was found.
#
# No capture on file has a meter showing anything (he was not playing when they were taken), so
# what a lit bar looks like has not been seen. An empty bar is the same wash as the left edge of
# its background: never more than 12 apart in any colour in captures 1, 10, 13 and 34. So a row
# of a bar counts as lit when the bar's middle is further than METER_LIT_DIFFERENCE from that
# edge in some colour, whatever the colour, and the level is the run of lit rows standing on the
# bottom of the bar. A clip light is red in every one of its rows: red at least METER_RED_MIN,
# green and blue at most METER_RED_OTHERS of the red, which FFFF2727 is at full and at half
# brightness and no wash is. A bar lit to its top is clipping too.
METER_FLOOR_DB = -60.0
METER_LIT_DIFFERENCE = 40
METER_RED_MIN = 90
METER_RED_OTHERS = 0.4
# The meters are watched only while a level check is on. L starts one and L ends it, and it has
# no time limit. Hadi, 2026-11-11: "let's disable the monitor outside of level check. and have
# it watching when level check is on. and let's not have a timer for level check." 0.11.16 and
# 0.11.17 also watched the clip lights whenever the plug-in had focus, and ended a check by
# themselves after two minutes; he asked what the watching would cost the keyboard before he
# had tried either, and chose this when he had the answer.
#
# What a look costs is the read of the screen, and that costs the same whatever its size: 10 ms
# on his machine for one pixel and for the whole editor alike (timed 2026-11-11 outside NVDA
# with the calls NVDA's screenBitmap makes; asking the pixels afterwards is a fraction of a
# millisecond). NVDA does nothing else meanwhile, so a key pressed during a look waits for it.
# A look therefore reads ONE box, the strip of the top bar from one meter to the other. His
# log of 0.11.16, which read two boxes a look, has five looks in 0.8 s where the timer is 100
# ms, so inside NVDA a look took more like 40 ms than the 20 its reads would be. The watch
# writes its own count and timings to the log every METER_TIMING_LOOKS looks and at the end of
# a check.
#
# During a check the watch looks this often. It asks the tree for the meters only when the
# editor's window has moved or the tree has been declared changed, never on a timer: every
# question put to the plug-in is a chance of a stall. It stops while another window is in
# front and starts again with the next focus in the amplifier, the check still on. Meters that
# were not found are looked for again after METER_RETRY_S.
METER_CHECK_POLL_MS = 100
METER_TIMING_LOOKS = 240
METER_RETRY_S = 3.0
# A clip light that comes on during a check is said at once, "Input clipping", and for the same
# meter not again within this many seconds.
METER_CLIP_REPEAT_S = 3.0
# A look counts as signal when the level is above METER_SIGNAL_DB. The answer has each meter's
# highest level and, from this many looks with signal on, its average level over those looks:
# one pick scrape sets the peak, and where the meter was on average is what says how hard the
# amplifier is driven (he asked whether the peak alone is enough, having never had a meter).
# 0.11.16 said the median and called it "usually", and he found the word confusing before he
# had tried it; "peak" and "average" are what a meter's two readings are called.
METER_SIGNAL_DB = -50.0
METER_AVERAGE_MIN = 3
METER_NAMES = (("input", "Input"), ("output", "Output"))
METER_NAMES = (("input", "Input"), ("output", "Output"))

# The view name rides on the landing control's own announcement - a separate message would be
# cut off by the focus change - and only for this long after the switch.
LANDING_PREFIX_S = 2.0

# The Cab view's miniature amp knob row (24 pixel knobs mirroring the amp panel).
CAB_MINI_BAND = (0.40, 0.47)

# Names the Cab view uses on both of its sides; they are told apart by which half they sit in.
CAB_SIDED_NAMES = {"CLOSE": "close", "MID": "mid", "FAR": "far", "ROOM": "room", "PHASE": "phase"}

# How far the pointer of a knob turns, in degrees, with 12 o'clock at the middle. Each knob is
# drawn from a strip of 101 pictures, one for each percent: PetrucciAmp<Amp>Knob.png for the amp
# panels, PetrucciCab<Amp>Knob.png for the Cab view's miniature row, PetrucciPreFXKnob.png for
# the pedals, PetrucciPostFXBigKnob.png and PetrucciPostFXSmallKnob.png for the racks. Looked at
# on 2026-11-10 with tools\probe\Show-KnobTravel.py: on every one of them the pointer is at half
# past 7 in picture 0, straight up in picture 50 and at half past 4 in picture 100. Measured on
# the Piezo strip the travel is 267.7 degrees. The amp panel pictures print no scale or marks
# round the knobs.
POINTER_KNOB_SWEEP = 270.0

# The tuner, mapped 2026-10-02 in REAPER by tools\probe\Probe-PetrucciTuner.ps1 and
# Probe-PetrucciTuner2.ps1 (probe-results\petrucci-tuner*.txt). The TUNER button in the utility
# bar carries this HelpText always; its Name "TUNER" disappears while the Live Tuner is on, so
# the HelpText is what finds it. A plain click opens the tuner window, a panel drawn inside the
# editor whose title is a Text named "Tuner" and which takes focus itself; Ctrl+click toggles
# the Live Tuner, which shows only the note letter in the utility bar.
#
# While a note rings the window exposes it all as Text: the note in large type, the readout
# ("+5.0" in cents, "659.0 Hz" in hertz) centred near the top, and two small chevrons either
# side of the readout - the left one alone means flat, the right one alone sharp, both together
# are the plugin's green in-tune verdict (within 2.0 cents across 132 samples). All of it
# vanishes when nothing rings. Positions below are fractions of the tuner window itself.
TUNER_HELP = "Open Tuner Window (CTRL + Click to toggle Live Tuner)"
TUNER_TITLE = "Tuner"
TUNER_NOTE_MIN_HEIGHT = 0.12      # the note is 55 of 362 pixels; its neighbours 31, the title 21
TUNER_READOUT_X = (0.40, 0.60)    # the readout is centred; the -50 and +50 scale ends are not
TUNER_READOUT_MAX_Y = 0.45
TUNER_CHEVRON_Y = (0.15, 0.35)
TUNER_HEADER_MAX_Y = 0.15         # mute and close sit in the title bar
TUNER_CLOSE_MIN_X = 0.90          # close is the right-hand of the two (0.936 against 0.867)
TUNER_FOOTER_MIN_Y = 0.75         # Cents, Hz, the Live Tuner switch and the reference pitch
# The selected mode's caption is drawn in full white, the other in grey: peaks 255 against 149.
TUNER_MODE_MIN_GAP = 40

# The MIDI mappings window, which the MIDI button of the bottom bar opens. Seen for the first
# time in Hadi's capture 34 (2026-11-11, no mappings yet); the rest is from the plug-in's own
# layouts (midiMappingsView.xml, midiMappingsCellContainerView.xml and
# midiMappingsNewMappingView.xml, saved as 125, 123 and 124 in probe-results\petrucci-layout\raw).
#
# It is a panel 848 by 502 in the middle of the 1024 by 782 editor, over a mask that covers the
# whole editor. Like the tuner window it has no subtree: its parts follow its frame in document
# order as siblings of everything else. They are a title bar 53 high with an unnamed options
# button on the left, the text "MIDI Mappings" and an unnamed close button on the right; six
# column headings; and a list twice the panel's width (1696) with one row, 36 high, per mapping
# and a last row holding the button "New MIDI Mapping".
#
# The plug-in's own ring has two stops in the window, the list and the row, both without a name
# ("I get two unknown controls", Hadi), and neither button of the title bar, so nothing in the
# ring closes the window. A row with a mapping in it has not been seen. By the layout it holds
# an on/off button, six combo boxes under the headings (the last shares its place with a text
# box) and a delete button.
MIDI_BUTTON_NAME = "MIDI"
MIDI_TITLE = "MIDI Mappings"
MIDI_NEW_NAME = "New MIDI Mapping"
MIDI_WINDOW_NAME = "MIDI mappings"
MIDI_OPTIONS_NAME = "MIDI mapping options"
MIDI_CLOSE_NAME = "Close MIDI mappings"
MIDI_FRAME_WIDTH = (0.70, 0.95)   # of the editor's width: 848 of 1024 is 0.83
MIDI_FRAME_HEIGHT = (0.50, 0.80)  # of the editor's height: 502 of 782 is 0.64
MIDI_HEADER_MAX_Y = 0.11          # of the panel's height: the title bar is 53 of 502
MIDI_WIDE = 1.2                   # the list and its rows are twice as wide as the panel
MIDI_LIST_MIN_HEIGHT = 0.40       # of the panel's height: the list is 412 of 502
MIDI_ROW_MAX_HEIGHT = 0.12        # a row is 36 of 502
MIDI_EDGE_BUTTON = 0.08           # of the panel's width: the on/off button is 8 in, delete 808
MIDI_HEADING_SLACK = 12           # a row's control starts 5 pixels right of its heading
MIDI_OPERABLE = (CT_BUTTON, CT_COMBOBOX, CT_EDIT, CT_SLIDER)
MIDI_POLL_MS = 150
MIDI_POLLS = 14
MIDI_SETTLE_MS = 300
MIDI_CHANGE_HUSH_S = 1.2

# A control's own menu, the one a right click opens (see ArchetypeXProfile.contextMenu). Its first
# line says what the menu is for.
CONTEXT_MENU_HEADINGS = ("Parameter:", "Preset:", "Action:")
CONTEXT_MENU_APPEAR_POLLS = 12    # at PRESET_LIST_POLL_MS each, about a second and a half

# MIDI learn. While the plug-in waits for a MIDI message it lays a veil over the control that is
# to learn, and that is all it does: nothing changes in the tree. Measured on Gain of the Rhythm
# amp from Hadi's log of 2026-11-11, the control's rectangle read off the screen: mean grey 32.4
# and brightest 237.0 without it, 57.7 and 206.5 with it, 32.4 and 237.0 again once learn was
# switched off. That is a layer of about 27 percent over the picture, which pulls dark and
# bright together: the brightest minus the mean falls to 0.73 of what it was, whatever the
# control looks like there. On Gain of the Lead amp, whose panel is bright, the same day: 190.7
# and 230.0 without it, 186.0 and 219.0 with it, a far smaller step and not the same layer. So
# no one factor is relied on. A look is the pair (mean, brightest), two looks are compared by
# adding up how far each number moved (55.8 on the Rhythm amp, 15.8 on the Lead, 0.04 between
# two readings with nothing changed), and MIDI_LEARN_MOVED is the least that counts.
MIDI_LEARN_ON_ITEM = "Enable MIDI Learn"
MIDI_LEARN_OFF_ITEM = "Disable MIDI Learn"
MIDI_LEARN_MOVED = 4.0
MIDI_LEARN_POLL_MS = 700
MIDI_LEARN_WATCH_S = 600.0


class ArchetypeXProfile(engine.AmpProfile):
    """What every Archetype X plug-in has, standalone and VST3. A plug-in's own profile
    subclasses this and fills in the tables below."""

    # The standalone's audio settings open from the named SETTINGS tab in the utility bar.
    audioSettingsButtonName = "SETTINGS"

    friendlyNames = {TUNER_HELP: "Tuner"}

    # ---- what a plug-in's own profile fills in ----
    #
    # sectionNames (see core.AmpProfile) holds the section buttons' HelpText, left to right.
    # VIEW_KEYS holds the names viewOf gives their views, in the same order.
    VIEW_KEYS = ()
    # Said when a key asks for a section whose button the plug-in is not showing.
    MISSING_SECTION_MESSAGE = "No %s section on this amplifier."
    # The amplifier models, matching the selector buttons at the bottom, left to right.
    ampModelNames = ()
    # Per amplifier, in that order: its knobs left to right as printed on the panel, and its
    # small switches left to right (the power switch is found by itself).
    AMP_KNOB_TABLES = ()
    AMP_SWITCH_TABLES = ()
    # The key the amp power switch's state probe is filed under, per live amplifier, since
    # each amplifier has its own panel art: for the amp panel, and for the Cab view's miniature.
    POWER_STATE_KEYS = {}
    MINI_POWER_STATE_KEYS = {}
    # Switch names that also appear on the Cab view's miniature amp row. A miniature never
    # borrows the full-size probe: it looks for one under "Mini <name>".
    FULL_SIZE_STATE_NAMES = frozenset()
    # The Cab view's miniature amp row: its band of the editor's height, how wide one of its
    # knobs and any of its controls may be (fractions of the editor's width), and the height
    # under which a switch carrying a full-size name is the miniature.
    CAB_MINI_BAND = CAB_MINI_BAND
    CAB_MINI_KNOB_MAX_WIDTH = 0.03
    CAB_MINI_PANEL_MAX_WIDTH = 0.035
    MINI_SWITCH_MAX_HEIGHT = 0.033
    # Each view's own controls: {view: ((centre y, centre x, name), ...)}, centres as fractions
    # of the editor. A control matches when its centre is within 0.02 in y and 0.012 in x. The
    # Amp view's controls are handled structurally instead (the panel changes with the
    # amplifier), as is the Cab view's miniature amp knob row.
    VIEW_SLIDER_LANDMARKS = {}
    VIEW_BUTTON_LANDMARKS = {}
    # The modules the bracket keys step through: {view: ((name, axis, low, high), ...)}.
    VIEW_MODULES = {}
    # The knobs that say where their pointer points, {view: names}, and those among them whose
    # pointer does not move evenly with the value, {name: skew}.
    VIEW_POINTER_KNOBS = {}
    POINTER_KNOB_SKEW = {}
    # {knob name: unit}, for a knob with no display of its own.
    KNOB_UNITS = KNOB_UNITS
    # {time knob's name: the name of the note-value knob that takes its place while synced}.
    NOTE_KNOB_NAMES = {}
    # A delay's displays: {view: ((centre y, centre x, name while free, name while synced), ...)}.
    DELAY_DISPLAYS = {}
    # Value boxes Tab does not pass over (see VALUE_BOX_SUFFIX).
    VALUE_BOX_KEPT = frozenset()
    CAPTION_STATE_KEYS = CAPTION_STATE_KEYS
    SIDED_CAPTIONS = SIDED_CAPTIONS
    CAB_SIDED_NAMES = CAB_SIDED_NAMES

    # Switch readings are each plug-in's own, the top bar's too: the Petrucci X and the Nolly X
    # draw the little rockers beside GATE and DOUBLER and the input mode switch differently
    # (see the tables in petrucci.py and nolly.py). Only the tuner window's mute button, a red
    # square while muted, is known to be the same; it was measured on the Petrucci X.
    switchProbeSize = (0.00586, 0.00767)
    switchProbes = {
        "Mute while tuning": (0.00391, 0.00512, 67, ("not muted", "muted")),
    }
    tipProbes = {}
    decorativeNames = frozenset(("Gate switch", "Doubler switch", "View background"))

    def stateLabel(self, obj):
        helpText = obj.ampHelpText
        if helpText:
            if helpText in self.sectionNames:
                # The section buttons have no state to read. The EQ view's button shares its
                # label with the EQ's on/off switch and borrowed that switch's probe, so it said
                # "EQ view, on" from pixels that mean nothing (Hadi's capture 10, 2026-11-09).
                return ""
            return self.stripPrefix(helpText)[0]
        controller = obj.ampController
        # A printed caption that is itself the switch (GATE, WAH, ROOM...) carries the state; the
        # little rocker beside it is passed over. Keyed by the plugin's own name for it.
        caption = self.CAPTION_STATE_KEYS.get(_prop(obj.UIAElement, PROP_NAME, "") or "")
        if caption:
            if caption not in self.SIDED_CAPTIONS:
                return caption
            fractions = self._objFractions(obj, controller) if controller else None
            if fractions is None:
                return ""
            return "%s %s" % ("Left" if fractions[0] + fractions[2] / 2.0 < 0.5 else "Right", caption)
        label = obj.ampLabel or ""
        if label in self.FULL_SIZE_STATE_NAMES:
            # The Cab view's miniature amp row is 24 to 25 pixels tall; the smallest full-size
            # panel switch (Piezo's Air, 28 pixels) must keep its state. The cutoff sits
            # between them - 0.045 once swallowed Air and it announced as a bare button.
            # A miniature never borrows the full-size calibration: it has its own, under
            # "Mini ...", and stays silent where there is none.
            fractions = self._objFractions(obj, controller) if controller else None
            if fractions is None:
                return ""
            if fractions[3] < self.MINI_SWITCH_MAX_HEIGHT:
                if label == "Amp power switch":
                    mini = self.cabMiniPanel(controller) if controller else None
                    return self.MINI_POWER_STATE_KEYS.get(mini["name"] if mini else None, "")
                return "Mini " + label
        if label == "Amp power switch":
            panel = self.ampPanel(controller) if controller else None
            return self.POWER_STATE_KEYS.get(panel["name"] if panel else None, "")
        return label

    # ---------- geometry helpers ----------

    def _fractions(self, controller, rect):
        """(xF, yF, wF, hF) of a raw UIA rectangle within the editor's client area, or None."""
        geometry = controller.clientGeometry()
        if not geometry or not rect or len(rect) < 4:
            return None
        left, top, width, height = geometry
        return ((rect[0] - left) / width, (rect[1] - top) / height,
                rect[2] / width, rect[3] / height)

    def _objFractions(self, obj, controller):
        try:
            rect = obj.location
            if not rect:
                return None
            return self._fractions(controller, (rect.left, rect.top, rect.width, rect.height))
        except Exception:
            return None

    def _bandElements(self, controller, controlType, band, unnamedOnly=False):
        """Elements of one control type inside a y band, as (x, rect, element), sorted by x."""
        geometry = controller.clientGeometry()
        if not geometry:
            return []
        _left, top, _width, height = geometry
        out = []
        for element in controller.findElements(controlType=controlType):
            if unnamedOnly and (_prop(element, PROP_NAME, "") or _prop(element, PROP_HELP_TEXT, "")):
                continue
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4 or rect[2] <= 0:
                continue
            yF = (rect[1] - top) / height
            if band[0] <= yF <= band[1]:
                out.append((rect[0], tuple(rect[:4]), element))
        out.sort(key=lambda item: item[0])
        return out

    @staticmethod
    def _xMatch(entries, obj):
        """Index of the entry whose left edge matches the object's, or None."""
        try:
            targetLeft = obj.location.left
        except Exception:
            return None
        for index, entry in enumerate(entries):
            if abs(entry[0] - targetLeft) < 3:
                return index
        return None

    # ---------- cached sweeps ----------

    def sectionElements(self, controller):
        """The seven section buttons, ordered left to right."""
        return controller._positionalSweep("sections", lambda: self._sectionElements(controller))

    def _sectionElements(self, controller):
        wanted = set(self.sectionNames)
        ordered = []
        for element in controller.findElements(controlType=CT_BUTTON):
            helpText = _prop(element, PROP_HELP_TEXT, "")
            if helpText not in wanted:
                continue
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4 or rect[2] <= 0:
                continue
            ordered.append((rect[0], helpText, element))
        ordered.sort(key=lambda item: item[0])
        return ordered

    def topKnobElements(self, controller):
        return controller._positionalSweep(
            "topKnobs", lambda: [entry for entry in self._bandElements(controller, CT_SLIDER, TOP_KNOB_Y)
                                 if entry[1][2] < 100])

    def readoutElements(self, controller):
        """Every readout Edit anywhere in the editor, with its rectangle."""
        return controller._positionalSweep(
            "readouts", lambda: self._bandElements(controller, CT_EDIT, (0.0, 1.0)))

    def topReadoutElements(self, controller):
        """The top bar's five readouts, left to right. Most views bring text boxes of their own
        (the Cab view has eight, a synced delay two), so the top bar's are picked out by their
        band before being counted: counted among all of them, Input's readout in the Cab view
        was called Doubler spread and the other four had no name (found 2026-11-09)."""
        return controller._positionalSweep(
            "topReadouts", lambda: self._bandElements(controller, CT_EDIT, READOUT_Y))

    def _readoutForRect(self, controller, rect):
        """(rectangle, element) of the display belonging to a knob: an Edit overlapping it in
        x, sitting inside it or just below it. None when the knob has none."""
        if not rect or len(rect) < 4:
            return None
        centre = rect[0] + rect[2] / 2.0
        top = rect[1]
        bottom = rect[1] + rect[3]
        for _x, readoutRect, element in self.readoutElements(controller):
            if not ((readoutRect[0] - 6) <= centre <= (readoutRect[0] + readoutRect[2] + 6)):
                continue
            if (top - 24) <= readoutRect[1] <= (bottom + 34):
                return readoutRect, element
        return None

    def _readoutTextForRect(self, controller, rect):
        """The display text belonging to a knob, in speakable units."""
        found = self._readoutForRect(controller, rect)
        return self._speakableUnits(textPatternText(found[1])) if found else None

    def selectorElements(self, controller):
        return controller._positionalSweep(
            "selectors", lambda: self._selectorElements(controller))

    def _selectorElements(self, controller):
        geometry = controller.clientGeometry()
        if not geometry:
            return []
        _left, _top, width, _height = geometry
        out = []
        for x, rect, element in self._bandElements(controller, CT_BUTTON, SELECTOR_Y, unnamedOnly=True):
            wF = rect[2] / width
            if 0.030 <= wF <= 0.048:
                out.append((x, rect, element))
        return out

    def ampPanel(self, controller):
        """The live amp panel: which amplifier it is and where its controls sit.

        The amp selectors' toggle latches cannot be trusted, so the amplifier is identified from
        the panel itself, by how many knobs it has and where its small switches sit. Each
        plug-in says how in _ampIndexOf.
        """
        return controller._positionalSweep("ampPanel", lambda: self._panelIn(controller, AMP_BAND_Y, 0.10))

    def topBarBackgroundRect(self, controller):
        """The rectangle of the top bar's background, the stop positionalLabel calls
        "decorative background", or None. The plug-in drops focus there when it has rebuilt
        whatever had it."""
        def build():
            for element in controller.findElements(controlType=CT_CUSTOM):
                rect = _prop(element, PROP_BOUNDING_RECT)
                if not rect or len(rect) < 4:
                    continue
                fractions = self._fractions(controller, rect)
                if fractions is None:
                    continue
                _xF, yF, wF, hF = fractions
                if yF < 0.05 and wF > 0.9 and 0.15 <= hF <= 0.30:
                    return tuple(rect[:4])
            return None
        return controller._positionalSweep("topBarBackground", build)

    def selectedAmpIndex(self, controller):
        """Which amplifier's selector is drawn as the selected one, 0 to 3, or None when the
        pictures do not say (see AMP_SELECTOR_MARGIN). Works in every view."""
        def build():
            selectors = self.selectorElements(controller)
            if len(selectors) != len(self.ampModelNames):
                return None
            peaks = [controller.peakGrey(*rect[:4]) for _x, rect, _element in selectors]
            if any(peak is None for peak in peaks):
                return None
            order = sorted(range(len(peaks)), key=lambda index: peaks[index], reverse=True)
            best, runnerUp = peaks[order[0]], peaks[order[1]]
            clear = best >= AMP_SELECTOR_MIN and best >= runnerUp * AMP_SELECTOR_MARGIN
            engine.STATE_LOG("neuralAccess: amp selectors' brightest points %s -> %r" % (
                " / ".join("%.0f" % peak for peak in peaks),
                self.ampModelNames[order[0]] if clear else None))
            return order[0] if clear else None
        return controller._positionalSweep("selectedAmp", build)

    def liveAmpIndex(self, controller):
        """Which amplifier is live, 0 to 3, or None. From the amp panel's shape where there is
        one (the Amp view), and from the selectors' pictures everywhere else."""
        panel = self.ampPanel(controller)
        if panel:
            return panel["index"]
        return self.selectedAmpIndex(controller)

    def cabMiniPanel(self, controller):
        """The Cab view's miniature mirror of the amp knob row: same amps, 24 pixel knobs."""
        return controller._positionalSweep("cabMini", lambda: self._panelIn(
            controller, self.CAB_MINI_BAND, self.CAB_MINI_PANEL_MAX_WIDTH))

    def _panelIn(self, controller, band, maxWidthFraction):
        geometry = controller.clientGeometry()
        if not geometry:
            return None
        _left, _top, width, _height = geometry
        # The open tuner window's reference pitch slider and Live Tuner switch fall inside the
        # amp panel's band; counted as amp controls they would turn the Clean amp into Rhythm.
        tunerRects = [child[2] for child in (self._tunerChildren(controller) or ())]
        knobs = [entry for entry in self._bandElements(controller, CT_SLIDER, band)
                 if entry[1][2] / width <= maxWidthFraction
                 and not any(self._rectMatches(entry[1], rect) for rect in tunerRects)]
        buttons = [entry for entry in self._bandElements(controller, CT_BUTTON, band, unnamedOnly=True)
                   if entry[1][2] / width <= maxWidthFraction
                   and not any(self._rectMatches(entry[1], rect) for rect in tunerRects)]
        if not knobs or not buttons:
            return None
        power = buttons[-1] if buttons[-1][0] > knobs[-1][0] else None
        switches = buttons[:-1] if power is not None else list(buttons)
        index = self._ampIndexOf(knobs, switches)
        if index is None:
            return None
        return {"index": index, "name": self.ampModelNames[index],
                "knobs": knobs, "switches": switches, "power": power}

    def _ampIndexOf(self, knobs, switches):
        """Which amplifier a panel with these knobs and small switches belongs to, as an index
        into ampModelNames, or None. The selectors' toggle latches cannot be trusted, so each
        plug-in tells its amplifiers apart by the shape of their panels. Both lists hold
        (x, rectangle, element), left to right; the power switch is not among the switches."""
        return None

    # ---------- knowing which section view is open ----------

    def viewOf(self, controller):
        """Which section's content is on screen, one of VIEW_KEYS, detected from structure and
        never from the lying section button toggles. Cab is the only view with combo boxes; each
        plug-in tells its other views apart by their sliders in _viewFromSliders."""
        return controller._positionalSweep("viewid", lambda: self._viewOfLogged(controller))

    def _viewOfLogged(self, controller):
        """_viewOf, keeping the last answer while the tree cannot be read, and with a line in
        the log whenever the answer changes.

        While one of the plug-in's pop-up text boxes is open (Tab from Delay tempo opens one),
        a search of the editor finds no elements at all, for as long as the box stays open.
        Found 2026-11-09 by a driven probe, the add-on's own log and its automatic capture 11,
        all three: 119 elements with Delay tempo focused, none a quarter second and three
        seconds after the Tab. Before 0.9.6 nothing found was read as the Amp view, so the text
        box and the next stops reached within the two second cache had no names."""
        view = self._viewOf(controller)
        last = getattr(controller, "_petrucciLastView", None)
        if view is None:
            if not getattr(controller, "_petrucciTreeEmpty", False):
                controller._petrucciTreeEmpty = True
                engine.STATE_LOG("neuralAccess: the editor's tree is empty (a text box is open?); "
                                 "keeping the view as %r" % last)
            return last or "amp"
        controller._petrucciTreeEmpty = False
        if view in self.DELAY_DISPLAYS:
            # Noted while the tree can be read, for the names of the delay's text boxes: the
            # first time one of them asks may be while the tree is empty. Not more than every
            # two seconds: a view switch works the view out afresh seven times a second.
            noted = getattr(controller, "_petrucciSyncNoted", None)
            if not isinstance(noted, dict):
                noted = controller._petrucciSyncNoted = {}
            if time.time() - noted.get(view, 0.0) > 2.0:
                noted[view] = time.time()
                self._delaySyncedNow(controller, view)
        if view != last:
            try:
                sliders = controller.findElements(controlType=CT_SLIDER)
                maxima = sorted(set(str(_prop(element, PROP_RANGE_MAX)) for element in sliders))
                focus = api.getFocusObject()
                engine.STATE_LOG(
                    "neuralAccess: view read as %r, was %r (%d sliders, range maxima %s, "
                    "%d combo boxes, geometry %r, focus role %s)" % (
                        view, getattr(controller, "_petrucciLastView", None), len(sliders),
                        ", ".join(maxima), len(controller.findElements(controlType=CT_COMBOBOX)),
                        controller.clientGeometry(), getattr(focus.role, "name", focus.role)))
            except Exception:
                log.info("neuralAccess: view change log failed", exc_info=True)
            controller._petrucciLastView = view
        return view

    def _viewOf(self, controller):
        # Exactly two combo boxes means the Cab view's microphones. Three or more means the
        # standalone's audio settings overlay is open on top of whatever view - the settings
        # machinery owns the tree then, so no view claims it.
        comboCount = len(controller.findElements(controlType=CT_COMBOBOX))
        if comboCount >= 3:
            # A mapping in the MIDI mappings window has four lists of its own, and they are no
            # part of any view. With one mapping the Cab view was read as "settings" (Hadi's
            # log, 2026-11-11: "view read as 'settings', was 'cab' (... 6 combo boxes ...)").
            midi = self.midiState(controller, fresh=True)
            if midi is not None:
                comboCount -= sum(1 for child in midi["children"] if child[0] == CT_COMBOBOX)
        if comboCount == 2:
            return "cab"
        if comboCount >= 3:
            return "settings"
        geometry = controller.clientGeometry()
        if not geometry:
            return "amp"
        sliders = controller.findElements(controlType=CT_SLIDER)
        if not sliders:
            # Every view has the top bar's five knobs, so no slider at all is not a view: the
            # tree cannot be read just now. None tells the caller to keep what it knew.
            return None
        return self._viewFromSliders(sliders, geometry)

    def _viewFromSliders(self, sliders, geometry):
        """Which view these sliders make up, once the Cab view and the audio settings are
        ruled out. Each plug-in has its own tells; the Amp view is whatever is left."""
        return "amp"

    def _landmarkName(self, obj, controller, tables):
        table = tables.get(self.viewOf(controller))
        if not table:
            return ""
        fractions = self._objFractions(obj, controller)
        if fractions is None:
            return ""
        xF, yF, wF, hF = fractions
        cx = xF + wF / 2.0
        cy = yF + hF / 2.0
        # The x tolerance is deliberately tight: the WAH and ROOM captions sit 0.014 left of
        # their rockers, and a caption that borrows the rocker's landmark also borrows its
        # pixel probe - sampled over caption text, which can lie about the state.
        for ly, lx, name in table:
            if abs(cy - ly) <= 0.02 and abs(cx - lx) <= 0.012:
                return name
        return ""

    def _syncedName(self, name, element):
        """A delay time knob's name, corrected when the knob standing there is the note-value
        knob the plug-in swaps in while the delay is synced. Other names pass through."""
        noteName = self.NOTE_KNOB_NAMES.get(name)
        if noteName:
            try:
                if float(_prop(element, PROP_RANGE_MAX)) == NOTE_KNOB_MAX:
                    return noteName
            except (TypeError, ValueError):
                pass
        return name

    def _delaySynced(self, controller, view):
        """True while that view's delay has note-value knobs standing where its time knobs do
        (the delay follows the host's tempo or a tapped one)."""
        return controller._positionalSweep(
            "delaySynced:%s" % view, lambda: self._delaySyncedNow(controller, view))

    def _delaySyncedNow(self, controller, view):
        # The last answer stands while the tree cannot be read (see _viewOfLogged): the note
        # displays are text boxes, and it is while a text box is open that the tree is empty.
        known = getattr(controller, "_petrucciDelaySynced", None)
        if not isinstance(known, dict):
            known = controller._petrucciDelaySynced = {}
        answer = self._hasNoteKnob(controller, view)
        if answer is None:
            return known.get(view, False)
        known[view] = answer
        return answer

    def _hasNoteKnob(self, controller, view):
        """True or False, or None when the editor's tree has no sliders to judge by."""
        geometry = controller.clientGeometry()
        if not geometry:
            return None
        left, top, width, height = geometry
        sliders = controller.findElements(controlType=CT_SLIDER)
        if not sliders:
            return None
        for element in sliders:
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4:
                continue
            cx = (rect[0] + rect[2] / 2.0 - left) / width
            cy = (rect[1] + rect[3] / 2.0 - top) / height
            for ly, lx, name in self.VIEW_SLIDER_LANDMARKS.get(view, ()):
                if name in self.NOTE_KNOB_NAMES and abs(cy - ly) <= 0.02 and abs(cx - lx) <= 0.012:
                    if self._syncedName(name, element) != name:
                        return True
        return False

    def _delayDisplayName(self, controller, view, cx, cy):
        """The name of a text box standing on one of a delay's displays in that view, or ""."""
        for ly, lx, freeName, syncedName in self.DELAY_DISPLAYS.get(view, ()):
            if abs(cy - ly) <= 0.02 and abs(cx - lx) <= 0.012:
                return syncedName if self._delaySynced(controller, view) else freeName
        return ""

    # ---------- naming ----------

    def _ampKnobName(self, obj, controller, fractions):
        """The name of a knob of the amp panel, or of the Cab view's miniature copy of that
        panel; None for any other slider."""
        _xF, yF, wF, _hF = fractions
        if AMP_BAND_Y[0] <= yF <= AMP_BAND_Y[1]:
            panel = self.ampPanel(controller)
            if panel:
                index = self._xMatch(panel["knobs"], obj)
                table = self.AMP_KNOB_TABLES[panel["index"]]
                if index is not None and index < len(table):
                    return table[index]
        if self.CAB_MINI_BAND[0] <= yF <= self.CAB_MINI_BAND[1] and wF < self.CAB_MINI_KNOB_MAX_WIDTH:
            mini = self.cabMiniPanel(controller)
            if mini:
                index = self._xMatch(mini["knobs"], obj)
                table = self.AMP_KNOB_TABLES[mini["index"]]
                if index is not None and index < len(table):
                    return table[index]
        return None

    def dialPosition(self, obj, raw, minimum, maximum):
        """The amp panel's knobs say where their pointer points, and so do the Cab view's
        miniature row, which is the same knobs drawn small, and the pedals' and racks' knobs
        listed in VIEW_POINTER_KNOBS (see POINTER_KNOB_SWEEP). No other knob does: one with a
        number beside it shows that number, and that is what a tutorial quotes for it."""
        controller = obj.ampController
        if controller is None or maximum <= minimum:
            return ""
        # The open tuner's reference pitch slider lies in the amp panel's band.
        if self._tunerControlName(obj, controller) is not None:
            return ""
        fractions = self._objFractions(obj, controller)
        if fractions is None:
            return ""
        skew = None
        if self._ampKnobName(obj, controller, fractions) is None:
            name = self._landmarkName(obj, controller, self.VIEW_SLIDER_LANDMARKS)
            if name not in self.VIEW_POINTER_KNOBS.get(self.viewOf(controller), ()):
                return ""
            skew = self.POINTER_KNOB_SKEW.get(name)
        travel = min(1.0, max(0.0, (raw - minimum) / (maximum - minimum)))
        if skew:
            travel = travel ** skew
        # Worked out from the whole percent of the travel, which for most of these knobs is the
        # percent that is spoken, so that one figure always goes with the same position.
        return engine.clockPosition(int(round(travel * 100.0)) / 100.0, POINTER_KNOB_SWEEP)

    def positionalLabel(self, obj, controller):
        # The tuner window is drawn over whatever view is open, and that view's controls stay in
        # the tree underneath it - so its own controls are settled first, by identity, before
        # any landmark could lend them a pedal's name.
        tunerName = self._tunerControlName(obj, controller)
        if tunerName is not None:
            return tunerName
        # The MIDI mappings window is drawn over the view in the same way.
        midiName = self._midiControlName(obj, controller)
        if midiName is not None:
            return midiName
        fractions = self._objFractions(obj, controller)
        if fractions is None:
            return ""
        xF, yF, wF, hF = fractions
        role = obj.ampNativeRole
        if role == controlTypes.Role.SLIDER:
            if TOP_KNOB_Y[0] <= yF <= TOP_KNOB_Y[1] and wF < 0.09:
                index = self._xMatch(self.topKnobElements(controller), obj)
                if index is not None and index < len(TOP_KNOB_NAMES):
                    return TOP_KNOB_NAMES[index]
            ampKnob = self._ampKnobName(obj, controller, fractions)
            if ampKnob is not None:
                return ampKnob
            if yF >= UTILITY_Y[0]:
                # The standalone's global tempo display doubles as a slider.
                return "Tempo"
            return self._syncedName(
                self._landmarkName(obj, controller, self.VIEW_SLIDER_LANDMARKS), obj.UIAElement)
        if role in (controlTypes.Role.BUTTON, controlTypes.Role.TOGGLEBUTTON):
            if AMP_BAND_Y[0] <= yF <= AMP_BAND_Y[1]:
                panel = self.ampPanel(controller)
                if panel:
                    if panel["power"] is not None and abs(panel["power"][0] - obj.location.left) < 3:
                        return "Amp power switch"
                    index = self._xMatch(panel["switches"], obj)
                    table = self.AMP_SWITCH_TABLES[panel["index"]]
                    if index is not None and index < len(table):
                        return table[index]
            if self.CAB_MINI_BAND[0] <= yF <= self.CAB_MINI_BAND[1] \
                    and wF < self.CAB_MINI_PANEL_MAX_WIDTH:
                mini = self.cabMiniPanel(controller)
                if mini:
                    if mini["power"] is not None and abs(mini["power"][0] - obj.location.left) < 3:
                        return "Amp power switch"
                    index = self._xMatch(mini["switches"], obj)
                    table = self.AMP_SWITCH_TABLES[mini["index"]]
                    if index is not None and index < len(table):
                        return table[index]
            if SELECTOR_Y[0] <= yF <= SELECTOR_Y[1] and 0.030 <= wF <= 0.048:
                index = self._xMatch(self.selectorElements(controller), obj)
                if index is not None and index < len(self.ampModelNames):
                    return "%s amplifier" % self.ampModelNames[index]
                return "amplifier selector"
            if HEADER_Y[0] <= yF <= HEADER_Y[1]:
                if hF <= 0.020:
                    # The two tiny rocker switches beside the GATE and DOUBLER captions.
                    return "Gate switch" if xF < 0.5 else "Doubler switch"
                if 0.40 <= xF <= 0.50 and wF <= 0.030:
                    arrows = controller._positionalSweep(
                        "presetArrows", lambda: self._presetArrows(controller))
                    index = self._xMatch(arrows, obj)
                    if index == 0:
                        return "Previous preset"
                    if index == 1:
                        return "Next preset"
                    return "preset arrow"
                if xF > 0.65 and wF <= 0.020:
                    return "More preset actions"
            if 0.125 <= yF <= 0.185 and wF <= 0.030 and 0.045 <= hF <= 0.085:
                return "Input mode switch"
            if 0.145 <= yF <= 0.185 and wF <= 0.020:
                # The small chevron on the right edge of the preset display.
                return "Open preset browser"
            if yF >= UTILITY_Y[0] and wF <= 0.030:
                # In the standalone the metronome's play button sits left of SETTINGS; the
                # resize button is at the far right in both flavours.
                if xF < 0.85:
                    return "Metronome play"
                return "Resize window"
            return self._landmarkName(obj, controller, self.VIEW_BUTTON_LANDMARKS)
        if role == controlTypes.Role.EDITABLETEXT:
            if READOUT_Y[0] <= yF <= READOUT_Y[1]:
                index = self._xMatch(self.topReadoutElements(controller), obj)
                if index is not None and index < len(TOP_KNOB_NAMES):
                    return "%s readout" % TOP_KNOB_NAMES[index]
            # A view readout sits inside or just under its knob; name it after the knob.
            view = self.viewOf(controller)
            table = self.VIEW_SLIDER_LANDMARKS.get(view)
            if table:
                cx = xF + wF / 2.0
                cy = yF + hF / 2.0
                # A delay's displays sit ABOVE their knobs and right under the sync selector,
                # which the loose match below would name them after.
                name = self._delayDisplayName(controller, view, cx, cy)
                if name:
                    return name
                for ly, lx, name in table:
                    if abs(cx - lx) <= 0.05 and abs(cy - ly) <= 0.12:
                        return "%s readout" % name
            return ""
        if role == controlTypes.Role.STATICTEXT:
            # On the Nolly X a synced delay's note display is a text element, not a text box,
            # and still a stop in the plug-in's Tab ring (Hadi heard only "text", 2026-11-11).
            # The captions are text elements too, each named by its own caption: Delay 2's FREE
            # sits about two pixels outside its display's landmark, so a named one is left be.
            if _prop(obj.UIAElement, PROP_NAME, "") or "":
                return ""
            return self._delayDisplayName(
                controller, self.viewOf(controller), xF + wF / 2.0, yF + hF / 2.0)
        if role == controlTypes.Role.UNKNOWN:
            # The level meters flanking the top bar: tall, hair thin, and genuinely in this
            # generation's Tab ring.
            if yF < 0.25 and wF < 0.02 and hF > 0.10:
                return "Input level meter" if xF < 0.5 else "Output level meter"
            # The top bar's background container holds the ring's one junk stop (see
            # TOP_BAR_BACKGROUND_NAME).
            if yF < 0.05 and wF > 0.9 and 0.15 <= hF <= 0.30:
                return TOP_BAR_BACKGROUND_NAME
            if xF < 0.01 and yF < 0.01 and wF > 0.9 \
                    and VIEW_BACKGROUND_HEIGHT[0] <= hF <= VIEW_BACKGROUND_HEIGHT[1]:
                return VIEW_BACKGROUND_NAME
        return ""

    def _presetArrows(self, controller):
        geometry = controller.clientGeometry()
        if not geometry:
            return []
        _left, _top, width, _height = geometry
        out = []
        for x, rect, element in self._bandElements(controller, CT_BUTTON, HEADER_Y, unnamedOnly=True):
            xF = (rect[0] - geometry[0]) / width
            hF = rect[3] / geometry[3]
            if 0.40 <= xF <= 0.50 and hF > 0.020:
                out.append((x, rect, element))
        return out

    def decorateName(self, obj, base):
        """Context for names the tree provides bare.

        The preset display's name IS the loaded preset's name (an asterisk in front is the
        plugin's mark for unsaved changes). The Cab view repeats CLOSE, MID, FAR, ROOM and PHASE
        on both of its sides, and names its microphone combo boxes only by the chosen mic.
        """
        controller = obj.ampController
        if controller is None:
            return base
        decorated = self._decorate(obj, controller, base) if base else base
        # A control that MIDI learn is waiting on says so every time, not only when learn was
        # switched on. Hadi, 2026-11-11: "when I tabbed forward and back to it, now it says,
        # Gain slider 83 percent ... and midi learn is still on i think".
        learning = getattr(controller, "_petrucciLearn", None)
        if learning and decorated and learning.get("rect") \
                and self._isLandingTarget(obj, learning["rect"], learning["type"]):
            decorated = "%s, MIDI learn on" % decorated
        # Straight after a view switch the control focus landed on also says which view it is in.
        # Checked before giving up on an empty name: the Volume view's first stop has none, and
        # returning early there lost "Volume view" (Hadi, 2026-11-08).
        landing = getattr(controller, "_petrucciLanding", None)
        if landing:
            rect, controlType, prefix, expiry = landing
            if time.time() > expiry:
                controller._petrucciLanding = None
            elif self._isLandingTarget(obj, rect, controlType):
                return "%s, %s" % (prefix, decorated) if decorated else prefix
        return decorated

    def _decorate(self, obj, controller, base):
        tunerName = self._decorateTunerName(obj, controller, base)
        if tunerName is not None:
            return tunerName
        midiName = self._decorateMidiName(obj, controller, base)
        if midiName is not None:
            return midiName
        fractions = self._objFractions(obj, controller)
        if fractions is None:
            return base
        xF, yF, wF, hF = fractions
        if 0.125 <= yF <= 0.185 and wF > 0.20:
            return self.spokenPreset(controller, base)
        side = "Left" if (xF + wF / 2.0) < 0.5 else "Right"
        if obj.ampNativeRole == controlTypes.Role.COMBOBOX:
            # Only the Cab view's two microphone combos get the side prefix - the standalone's
            # audio settings combos are combo boxes too, and calling the device selector a
            # microphone once confused a whole settings panel.
            if self.viewOf(controller) == "cab" and 0.25 <= yF <= 0.35 and wF < 0.15:
                return "%s microphone, %s" % (side, base)
            return base
        if self.viewOf(controller) == "cab":
            sided = self.CAB_SIDED_NAMES.get(base.strip().upper())
            if sided:
                return "%s %s" % (side, sided)
        return base

    def roleOverride(self, obj):
        # Every button's toggle state is a meaningless latch, so nothing here may present as a
        # toggle button - NVDA would speak "pressed" from it.
        role = obj.ampNativeRole
        if role == controlTypes.Role.TOGGLEBUTTON:
            return controlTypes.Role.BUTTON
        # The tuner window's own container is where focus lands when it opens. A grouping says
        # what it is; left alone it would be announced as "unknown".
        if role == controlTypes.Role.UNKNOWN:
            controller = obj.ampController
            if controller is not None and self._isTunerPanelObject(obj, controller):
                return controlTypes.Role.GROUPING
            # So is the MIDI mappings window's list, which takes focus as that window opens.
            if controller is not None and self._isMidiList(obj, controller):
                return controlTypes.Role.GROUPING
        return None

    def dropPressedState(self, obj):
        return True

    def suppressValue(self, obj):
        return obj.ampNativeRole in (controlTypes.Role.BUTTON, controlTypes.Role.TOGGLEBUTTON)

    def selectedState(self, obj, controller):
        """The amp model selectors present as radio buttons, selected from panel structure, and
        so do the tuner's Cents and Hz buttons, selected from which caption is drawn in white."""
        role = obj.ampNativeRole
        if role not in (controlTypes.Role.BUTTON, controlTypes.Role.TOGGLEBUTTON):
            return None
        native = _prop(obj.UIAElement, PROP_NAME, "") or ""
        if native in ("Cents", "Hz"):
            if self._tunerChild(obj, controller) is None:
                return None
            mode = self.tunerMode(controller)
            return None if mode is None else (mode == native)
        fractions = self._objFractions(obj, controller)
        if fractions is None:
            return None
        _xF, yF, wF, _hF = fractions
        if not (SELECTOR_Y[0] <= yF <= SELECTOR_Y[1] and 0.030 <= wF <= 0.048):
            return None
        index = self._xMatch(self.selectorElements(controller), obj)
        if index is None:
            return None
        live = self.liveAmpIndex(controller)
        if live is None:
            return None
        return live == index

    # RESET cannot be undone and the plugin fires it with no confirmation of its own (seen
    # 2026-08-11: one click and the test knob was back at its default). It is reachable exactly
    # like everything else; Enter warns, and Enter again carries it out.
    #
    # DELETE was here too until 0.10.4, on the belief that it fired the same way. It does not:
    # the plug-in asks "Are you sure you want to delete the preset ...?" itself (see
    # DELETE_QUESTION_YES). The add-on's warning was a second question in front of that one,
    # and after it "preset deleted" was said with the plug-in's question still unanswered.
    confirmActions = {
        "RESET": ("returns every parameter in the plugin to its default", "parameters reset"),
    }

    def needsClick(self, obj):
        """Every button in this generation ignores Enter and Invoke alike, so Enter is turned
        into a real cursor click for all of them. RESET goes through the confirmation path in
        core first, which does its own clicking."""
        return obj.ampNativeRole in (controlTypes.Role.BUTTON, controlTypes.Role.TOGGLEBUTTON)

    # ---------- values ----------

    def readoutText(self, controller, obj):
        label = obj.ampLabel
        if label == "Reference pitch":
            # Its text box shares its rectangle and prints the figure with no unit; the range
            # value is exact, so formatValue says it with one.
            return None
        try:
            rect = obj.location
            raw = (rect.left, rect.top, rect.width, rect.height)
        except Exception:
            return None
        text = self._readoutTextForRect(controller, raw)
        if label not in FILTER_OFF_END:
            return text
        rangeInfo = getattr(obj, "ampRange", None)
        if not rangeInfo:
            return text
        value, minimum, maximum = rangeInfo[:3]
        if self._filterReadoutAgrees(label, value, minimum, maximum, text):
            return text
        # The display says something the knob does not. It may be an old display: look afresh,
        # though not on every one of the several times NVDA asks for a control's value.
        fresh = text
        now = time.time()
        if now - getattr(controller, "_petrucciFilterResweep", 0.0) >= FILTER_RESWEEP_GAP_S:
            controller._petrucciFilterResweep = now
            controller.forgetPositional("readouts")
            fresh = self._readoutTextForRect(controller, raw)
        agrees = self._filterReadoutAgrees(label, value, minimum, maximum, fresh)
        logged = getattr(self, "_filterDisagreementsLogged", 0)
        if logged < FILTER_LOG_MAX:
            self._filterDisagreementsLogged = logged + 1
            log.info("neuralAccess: value: %s knob is at %.1f, its display says %r, looked for afresh %r; %s"
                     % (label, value, text, fresh, "the fresh one is said" if agrees else "the knob's figure is said"))
        return fresh if agrees else None

    @staticmethod
    def _filterIsOff(label, raw, minimum, maximum):
        end = minimum if FILTER_OFF_END[label] == "min" else maximum
        return abs(raw - end) <= (maximum - minimum) * 0.001

    def _filterReadoutAgrees(self, label, raw, minimum, maximum, text):
        """True when a filter knob's display says what the knob's value is: OFF at the off end
        and nowhere else, and otherwise a figure within one unit of its last digit of the
        value ("39 Hz" for 39.2, "19.2 kHz" for 19240). A wording with no figure in it has not
        been seen and is left to the plug-in."""
        words = (text or "").strip()
        if not words:
            return False
        off = self._filterIsOff(label, raw, minimum, maximum)
        if words.upper() == "OFF":
            return off
        if off:
            return False
        match = re.search(r"\d+(?:[.,]\d+)?", words)
        if not match:
            return True
        figure = match.group(0).replace(",", ".")
        decimals = len(figure.split(".")[1]) if "." in figure else 0
        scale = 1000.0 if re.search(r"\d\s*k", words, re.IGNORECASE) else 1.0
        return abs(float(figure) * scale - raw) <= (10.0 ** -decimals) * scale + 0.01

    def _filterValue(self, label, raw, minimum, maximum, unitText):
        if self._filterReadoutAgrees(label, raw, minimum, maximum, unitText):
            return unitText
        if self._filterIsOff(label, raw, minimum, maximum):
            # In capitals, as the display prints it, for the same reason as "hertz" above.
            return "OFF"
        return "%d hertz" % int(round(raw))

    @staticmethod
    def _speakableUnits(text):
        if not text:
            return None
        # Hertz in words as well, so that a filter knob's own figure ("25 hertz", see
        # _filterValue) and its display's are the same text: the plug-in's report of a change
        # is kept quiet only when it is exactly what the arrow key has just said.
        return (text.replace(" dB", " decibels")
                    .replace(" st", " semitones")
                    .replace(" ms", " milliseconds")
                    .replace(" kHz", " kilohertz")
                    .replace(" Hz", " hertz"))

    def formatValue(self, label, raw, minimum, maximum, unitText=None):
        # A named position is said in its own words whatever display text stands nearby: with
        # the delay synced, the left note display sits under the sync selector and the readout
        # pairing would have it say "1/4" for "DAW sync".
        enum = self.enumValues.get(label)
        if enum:
            index = int(round(raw))
            if 0 <= index < len(enum):
                return enum[index]
            return str(index)
        if label in ("Left pan", "Right pan"):
            # The plug-in prints "C" for the middle. Its wording off centre has not been seen,
            # so anything else is passed on as the plug-in prints it.
            if (unitText or "").strip() == "C" or (not unitText and round(raw) == 0):
                return "centre"
            return unitText or "%d" % int(round(raw))
        if label in FILTER_OFF_END:
            return self._filterValue(label, raw, minimum, maximum, unitText)
        if unitText:
            return unitText
        if label == "Reference pitch":
            # 420 to 460 hertz in steps of 0.4, so the decimal matters.
            return "%.1f hertz" % raw
        unit = self.KNOB_UNITS.get(label)
        if unit == "semitones":
            return "%d semitones" % int(round(raw))
        if unit == "hertz" or unit == "milliseconds":
            return "%d %s" % (int(round(raw)), unit)
        if unit:
            return "%.1f %s" % (raw, unit)
        return super(ArchetypeXProfile, self).formatValue(label, raw, minimum, maximum, unitText)

    def announceAllParts(self, controller):
        parts = []
        tops = self.topKnobElements(controller)
        for position, (x, rect, element) in enumerate(tops):
            if position >= len(TOP_KNOB_NAMES):
                break
            name = TOP_KNOB_NAMES[position]
            text = self._readoutTextForRect(controller, rect)
            if text is None:
                raw = _prop(element, PROP_RANGE_VALUE)
                if raw is not None:
                    text = self.formatValue(name, float(raw), 0.0, 1.0)
            if text:
                parts.append("%s %s" % (name, text))
        # The current section's own knobs, from its landmark table.
        view = self.viewOf(controller)
        table = self.VIEW_SLIDER_LANDMARKS.get(view)
        if table:
            geometry = controller.clientGeometry()
            if geometry:
                left, top, width, height = geometry
                for element in controller.findElements(controlType=CT_SLIDER):
                    rect = _prop(element, PROP_BOUNDING_RECT)
                    if not rect or len(rect) < 4:
                        continue
                    cx = (rect[0] + rect[2] / 2.0 - left) / width
                    cy = (rect[1] + rect[3] / 2.0 - top) / height
                    name = None
                    for ly, lx, candidate in table:
                        if abs(cy - ly) <= 0.02 and abs(cx - lx) <= 0.012:
                            name = candidate
                            break
                    if not name or name.endswith("display"):
                        continue
                    name = self._syncedName(name, element)
                    raw = _prop(element, PROP_RANGE_VALUE)
                    if raw is None:
                        continue
                    minimum = float(_prop(element, PROP_RANGE_MIN, 0.0))
                    maximum = float(_prop(element, PROP_RANGE_MAX, 1.0))
                    text = self._readoutTextForRect(controller, rect)
                    parts.append("%s %s" % (
                        name, self.formatValue(name, float(raw), minimum, maximum, text)))
        panel = self.ampPanel(controller)
        if panel:
            parts.append("%s amplifier" % panel["name"])
            table = self.AMP_KNOB_TABLES[panel["index"]]
            for position, (x, rect, element) in enumerate(panel["knobs"]):
                if position >= len(table):
                    break
                raw = _prop(element, PROP_RANGE_VALUE)
                if raw is None:
                    continue
                parts.append("%s %d percent" % (table[position], int(round(float(raw) * 100))))
        return parts

    # ---------- actions (every one of them a real click) ----------

    def entryElement(self, controller, hwnd):
        """Entering always lands on the leftmost section button, a familiar place."""
        sections = self.sectionElements(controller)
        if sections:
            return sections[0][2]
        return None

    def activeAmpModel(self, controller):
        index = self.liveAmpIndex(controller)
        return self.ampModelNames[index] if index is not None else None

    def sectionElement(self, controller, index):
        """The section button for view number index, found by its own label, or None when the
        plug-in is not showing that button.

        Never by counting: with the Piezo amp live the plug-in drops the Cab and EQ buttons (a
        piezo pickup has no cabinet) and moves the other five together. Counting then made key
        4 press Volume and key 5 press Post FX, each followed by "view did not open" and focus
        left wherever the plug-in dropped it (Hadi, 2026-11-09)."""
        if not 0 <= index < len(self.sectionNames):
            return None
        wanted = self.sectionNames[index]
        for _x, helpText, element in self.sectionElements(controller):
            if helpText == wanted:
                return element
        return None

    def switchSection(self, controller, index):
        sections = self.sectionElements(controller)
        if not sections:
            ui.message("Cannot locate the amplifier window.")
            return
        if index >= len(self.sectionNames):
            ui.message("Section not available.")
            return
        element = self.sectionElement(controller, index)
        if element is None:
            ui.message(self.MISSING_SECTION_MESSAGE % self.sectionNames[index])
            return
        # Focus is about to move on purpose: a Tab pressed a moment ago must not skip anything
        # the switch hands focus to.
        controller._lastTab = None
        controller.invalidatePositional()
        now = time.time()
        lastIndex, lastTime = getattr(controller, "_petrucciSectionClick", (None, 0.0))
        repeated = lastIndex == index and now - lastTime < SECTION_CLICK_GUARD_S
        # No click at all when the view is already showing or was clicked a moment ago: a second
        # click inside the double-click time would bypass the whole section.
        if not repeated and self.viewOf(controller) != self.VIEW_KEYS[index]:
            controller._petrucciSectionClick = (index, now)
            controller.clickElement(element)
            controller.invalidatePositional()
            controller.invalidateReadouts()
            controller.invalidateStates()
        # A newer key press supersedes this one: its landing poll stops quietly instead of later
        # reporting that a view the user already moved on from "did not open".
        serial = getattr(controller, "_petrucciSwitchSerial", 0) + 1
        controller._petrucciSwitchSerial = serial
        callLater(250, self._landAfterSwitch, controller, index, element, 14, serial)

    def _firstTabStop(self, controller):
        """The showing view's first stop in the plugin's Tab order, or None. See LANDING_TYPES."""
        geometry = controller.clientGeometry()
        items = self._sweep(controller)
        if not geometry or not items:
            return None
        _left, top, _width, height = geometry
        view = self.viewOf(controller)
        for controlType, _name, rect, element in items:
            if controlType not in LANDING_TYPES or rect[2] <= 0 or rect[3] <= 0:
                continue
            centreY = (rect[1] + rect[3] / 2.0 - top) / height
            if not (VIEW_CONTENT_Y[0] <= centreY < VIEW_CONTENT_Y[1]):
                continue
            if controlType == CT_BUTTON and self._landmarkAt(controller, view, rect) in self.decorativeNames:
                continue
            return element
        return None

    def _landmarkAt(self, controller, view, rect):
        """The button landmark name at a raw rectangle in the given view, or ""."""
        fractions = self._fractions(controller, rect)
        if fractions is None:
            return ""
        xF, yF, wF, hF = fractions
        cx = xF + wF / 2.0
        cy = yF + hF / 2.0
        for ly, lx, name in self.VIEW_BUTTON_LANDMARKS.get(view, ()):
            if abs(cy - ly) <= 0.02 and abs(cx - lx) <= 0.012:
                return name
        return ""

    def _landOn(self, controller, element, prefix):
        """Puts focus on element, its announcement led by prefix. True when that was done."""
        rect = _prop(element, PROP_BOUNDING_RECT)
        if not rect or len(rect) < 4:
            return False
        rect = tuple(rect[:4])
        controlType = _prop(element, PROP_CONTROL_TYPE)
        if self._isLandingTarget(api.getFocusObject(), rect, controlType):
            # Already standing on it: SetFocus would raise no event and say nothing.
            log.info("neuralAccess: landing target already has focus (%r, type %r)" % (rect, controlType))
            ui.message(prefix)
            return True
        controller._petrucciLanding = (rect, controlType, prefix, time.time() + LANDING_PREFIX_S)
        controller._lastTab = None
        if controller.trySetFocus(element):
            # The plugin sometimes hands its focus to a container a moment after a switch, which
            # announces as a bare "unknown". Take it back once.
            callLater(600, self._holdLanding, controller, element)
            return True
        controller._petrucciLanding = None
        return False

    def _landAfterSwitch(self, controller, index, sectionElement, remaining, serial):
        with engine.Timed("a landing check for the %s view" % self.sectionNames[index]):
            self._landAfterSwitchStep(controller, index, sectionElement, remaining, serial)

    def _landAfterSwitchStep(self, controller, index, sectionElement, remaining, serial):
        """Puts focus on the new view's first control once the view has really changed.

        The view is recognised from its structure, so this waits for the plugin to rebuild the
        tree. If it never does, focus goes to the section button, which says the view's name.
        """
        if getattr(controller, "_petrucciSwitchSerial", serial) != serial:
            return
        controller.invalidatePositional()
        prefix = "%s section" % self.sectionNames[index]
        view = self.VIEW_KEYS[index]
        # "amp" is also viewOf's answer for a half-built tree, so the Amp view must show its panel.
        if self.viewOf(controller) == view and (view != "amp" or self.ampPanel(controller)):
            target = self._firstTabStop(controller)
            if target is not None and self._landOn(controller, target, prefix):
                return
        if remaining > 0:
            callLater(150, self._landAfterSwitch, controller, index, sectionElement, remaining - 1,
                      serial)
            return
        if self.viewOf(controller) != self.VIEW_KEYS[index]:
            # The click did not take (a covered window, say). Focus is still on a control that
            # exists, so leave it there and say so.
            log.info("neuralAccess: the %s view never appeared after its button was clicked"
                     % self.VIEW_KEYS[index])
            ui.message("%s section did not open" % self.sectionNames[index])
            return
        log.info("neuralAccess: no landing control found for the %s view" % self.VIEW_KEYS[index])
        if not controller.trySetFocus(sectionElement):
            ui.message(prefix)

    def _holdLanding(self, controller, target):
        if controller.isFocusDeadEnd(engine.focusedElement()):
            controller._lastTab = None
            controller.trySetFocus(target)

    # ---------- a whole section on or off (Shift+number, Control+number) ----------

    def _sectionLook(self, controller, index):
        """How strongly the icon of the section of that number is drawn: 1.0 at full strength,
        about 0.3 for a section that is off. None when the row of buttons cannot be seen or
        has no such button. See SECTION_ICON_BOX for the measure and where it comes from."""
        if not 0 <= index < len(self.sectionNames):
            return None
        wanted = self.sectionNames[index]
        own = None
        others = []
        for _x, name, element in self.sectionElements(controller):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4 or rect[2] <= 0 or rect[3] <= 0:
                continue
            if name == wanted:
                own = tuple(rect[:4])
            else:
                others.append(tuple(rect[:4]))
        if own is None:
            return None
        white = 0.0
        for rect in [own] + others:
            peak = controller.peakGrey(*rect)
            if peak is not None and peak > white:
                white = peak
            if white >= SECTION_WHITE:
                break
        if white < SECTION_ROW_MIN:
            return None
        left, top, width, height = own
        xF, yF, wF, hF = SECTION_ICON_BOX
        box = (left + width * xF, top + height * yF, width * wF, height * hF)
        peak = controller.peakGrey(*box)
        mean = controller.meanGrey(*box)
        if peak is None or mean is None or white - mean < SECTION_MIN_RANGE:
            return None
        return (peak - mean) / (white - mean)

    @staticmethod
    def _sectionIsOn(look):
        if look is None:
            return None
        if look >= SECTION_ON_AT:
            return True
        if look <= SECTION_OFF_AT:
            return False
        return None

    def sectionActive(self, controller, index):
        """True when the section of that number is switched on, False when it is off, None when
        its button's picture does not say or the plug-in is showing no such button."""
        return self._sectionIsOn(self._sectionLook(controller, index))

    @staticmethod
    def _lookText(look):
        return "not to be seen" if look is None else "%.2f" % look

    @staticmethod
    def _sectionWords(name, active):
        if active is None:
            return "Cannot tell whether the %s section is on." % name
        return "%s section, %s" % (name, "on" if active else "off")

    def _sectionButton(self, controller, index):
        """The button of the section of that number, or None after saying why there is none."""
        if not 0 <= index < len(self.sectionNames):
            ui.message("Section not available.")
            return None
        if not self.sectionElements(controller):
            ui.message("Cannot locate the amplifier window.")
            return None
        element = self.sectionElement(controller, index)
        if element is None:
            ui.message(self.MISSING_SECTION_MESSAGE % self.sectionNames[index])
        return element

    def sectionState(self, controller, index):
        """Shift+number: "Pre FX section, on". Nothing is clicked and focus does not move."""
        if self._sectionButton(controller, index) is None:
            return True
        name = self.sectionNames[index]
        look = self._sectionLook(controller, index)
        active = self._sectionIsOn(look)
        log.info("neuralAccess: section key: %s reads %r (its icon %s)" % (name, active, self._lookText(look)))
        ui.message(self._sectionWords(name, active))
        return True

    def sectionToggle(self, controller, index):
        """Control+number: switches the section off or on and says "Pre FX section, off". Focus
        and the view stay where they are. See SECTION_DOUBLE_FIRST_MS for how."""
        if time.time() < getattr(controller, "_petrucciSectionBusy", 0.0):
            # One at a time; see SECTION_BUSY_S.
            log.info("neuralAccess: section key: still at work on the press before; this one is left out")
            return True
        if self.tunerPanel(controller) is not None:
            ui.message("Close the tuner first.")
            return True
        if self.midiState(controller) is not None:
            # Its mask takes every click meant for the top bar.
            ui.message("Close the MIDI mappings window first.")
            return True
        if self._sectionButton(controller, index) is None:
            return True
        name = self.sectionNames[index]
        look = self._sectionLook(controller, index)
        before = self._sectionIsOn(look)
        if before is None:
            log.info("neuralAccess: section key: %s cannot be read, so it is left alone (its icon %s)"
                     % (name, self._lookText(look)))
            ui.message(self._sectionWords(name, None))
            return True
        serial = getattr(controller, "_petrucciSectionSerial", 0) + 1
        controller._petrucciSectionSerial = serial
        controller._petrucciSectionBusy = time.time() + SECTION_BUSY_S
        trip = {"index": index, "name": name, "before": before, "serial": serial}
        log.info("neuralAccess: section key: %s was %s (its icon %s)"
                 % (name, "on" if before else "off", self._lookText(look)))
        self._sectionStep(controller, trip, self._sectionDoubleClick, controller, trip)
        return True

    def _sectionStep(self, controller, trip, step, *args):
        """One step of a section switch. A newer press stops it without a word. A step that
        fails ends the switch out loud: nothing may be left kept quiet, and he is owed an
        answer to the key."""
        if getattr(controller, "_petrucciSectionSerial", trip["serial"]) != trip["serial"]:
            return
        try:
            step(*args)
        except Exception:
            log.info("neuralAccess: section key: a step failed", exc_info=True)
            self._sectionFinish(controller, trip)
            controller.hushFocus([], 0.0)
            ui.message("Could not switch the %s section." % trip["name"])

    @staticmethod
    def _sectionFinish(controller, trip):
        controller._petrucciSectionBusy = 0.0

    def _viewShowing(self, controller, view):
        """True when this view is the one on screen. "amp" is also viewOf's answer for a tree
        that is half built, so the Amp view must show its panel as well."""
        return self.viewOf(controller) == view and (view != "amp" or bool(self.ampPanel(controller)))

    def _sectionDoubleClick(self, controller, trip):
        """The double click a mouse user makes, and then the way back."""
        index, name, before = trip["index"], trip["name"], trip["before"]
        trip["homeView"] = self.viewOf(controller)
        trip["switchSerial"] = getattr(controller, "_petrucciSwitchSerial", 0)
        trip["home"] = None
        focus = engine.focusedElement()
        if focus is not None and not controller.isFocusDeadEnd(focus):
            rect = _prop(focus, PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4:
                trip["home"] = (tuple(rect[:4]), _prop(focus, PROP_CONTROL_TYPE))

        def look(remaining):
            controller.invalidatePositional()
            now = self.sectionActive(controller, index)
            changed = now is not None and now != before
            if changed or remaining <= 0:
                self._sectionReturn(controller, trip, now if changed else None)
                return
            callLater(SECTION_DOUBLE_POLL_MS, self._sectionStep, controller, trip, look, remaining - 1)

        def press(remaining):
            if engine.modifiersDown() and remaining > 0:
                callLater(SECTION_KEYS_UP_MS, self._sectionStep, controller, trip, press, remaining - 1)
                return
            controller.invalidatePositional()
            element = self.sectionElement(controller, index)
            controller._lastTab = None
            controller.hushFocus([], SECTION_TRIP_HUSH_S, everything=True)
            # The number key of this section must not add a click of its own to these two.
            controller._petrucciSectionClick = (index, time.time())
            sent = element is not None and controller.doubleClickElement(element)
            log.info("neuralAccess: section key: double click on %s %s; the %r view was showing, focus was at %r"
                     % (name, "sent" if sent else "could not be sent", trip["homeView"],
                        trip["home"][0] if trip["home"] else None))
            if not sent:
                self._sectionReturn(controller, trip, None)
                return
            callLater(SECTION_DOUBLE_FIRST_MS, self._sectionStep, controller, trip, look,
                      SECTION_DOUBLE_POLLS)

        press(SECTION_KEYS_UP_POLLS)

    def _sectionReturn(self, controller, trip, now):
        """After the double click: back to the view he was in, if the click showed another."""
        name = trip["name"]
        message = self._sectionWords(name, now) if now is not None else "Could not switch the %s section." % name
        log.info("neuralAccess: section key: after the double click %s reads %s"
                 % (name, "as before" if now is None else ("on" if now else "off")))
        controller.invalidatePositional()
        controller.invalidateReadouts()
        controller.invalidateStates()
        homeView = trip["homeView"]
        # A view key or the amp key pressed in the meantime has taken him somewhere on purpose.
        trip["moved"] = getattr(controller, "_petrucciSwitchSerial", 0) != trip["switchSerial"]
        if not trip["moved"] and homeView in self.VIEW_KEYS and not self._viewShowing(controller, homeView):
            homeIndex = self.VIEW_KEYS.index(homeView)
            button = self.sectionElement(controller, homeIndex)
            if button is not None:
                controller._petrucciSectionClick = (homeIndex, time.time())
                controller.clickElement(button)
                controller.invalidatePositional()
                log.info("neuralAccess: section key: the %r view is showing; clicked back to %r"
                         % (self.viewOf(controller), homeView))
                callLater(SECTION_RETURN_FIRST_MS, self._sectionStep, controller, trip,
                          self._sectionSettle, controller, trip, message, SECTION_RETURN_POLLS)
                return
        self._sectionSettle(controller, trip, message, 0)

    def _controlAt(self, controller, place):
        """The control of this type at this rectangle in the tree as it is now, or None. A view
        that has been away and come back is made of new elements at the old places."""
        rect, controlType = place
        for itemType, _name, itemRect, element in self._sweep(controller) or ():
            if itemType == controlType and itemRect and len(itemRect) >= 4 \
                    and self._rectMatches(tuple(itemRect[:4]), rect):
                return element
        return None

    def _sectionSettle(self, controller, trip, message, remaining):
        """Once the view he was in is showing again: focus back where it was, then the word."""
        controller.invalidatePositional()
        homeView, home, moved = trip["homeView"], trip["home"], trip["moved"]
        moved = moved or getattr(controller, "_petrucciSwitchSerial", 0) != trip["switchSerial"]
        back = moved or homeView not in self.VIEW_KEYS or self._viewShowing(controller, homeView)
        if not back and remaining > 0:
            callLater(SECTION_RETURN_POLL_MS, self._sectionStep, controller, trip,
                      self._sectionSettle, controller, trip, message, remaining - 1)
            return
        self._sectionFinish(controller, trip)
        focus = engine.focusedElement()
        focusRect = _prop(focus, PROP_BOUNDING_RECT) if focus is not None else None
        there = bool(home and focusRect and len(focusRect) >= 4
                     and self._rectMatches(tuple(focusRect[:4]), home[0]))
        target = self._controlAt(controller, home) if home and back and not moved and not there else None
        log.info("neuralAccess: section key: the %r view is showing (%r wanted); focus %s"
                 % (self.viewOf(controller), homeView,
                    "was taken elsewhere by another key" if moved else "is where it was" if there
                    else "goes back to %r" % (home[0],) if target is not None
                    else "had nowhere to go back to" if home is None else "found nothing at %r" % (home[0],)))
        if home and target is None and not there and not moved:
            # The control he was on is gone. The view's first stop, with the word in front.
            stop = self._firstTabStop(controller)
            controller.hushFocus([], 0.0)
            if stop is None or not self._landOn(controller, stop, message):
                ui.message(message)
            return
        # From here on only the stops this switch itself may still cause are kept quiet: the
        # control focus goes back to, the buttons that were clicked, and the top bar's
        # background, where the plug-in drops focus after rebuilding what had it.
        quiet = [home[0] if home else None, self.topBarBackgroundRect(controller)]
        quiet += [_prop(element, PROP_BOUNDING_RECT) for _x, _name, element in self.sectionElements(controller)]
        controller.hushFocus([rect for rect in quiet if rect], QUICK_HUSH_S)
        if target is not None:
            controller._lastTab = None
            controller.trySetFocus(target)
        ui.message(message)

    def switchAmpModel(self, controller, direction):
        selectors = self.selectorElements(controller)
        if len(selectors) != len(self.ampModelNames):
            ui.message("Cannot locate the amplifier selectors.")
            return
        controller._lastTab = None
        clickedAt = time.time()
        lastTarget, lastTime = getattr(controller, "_petrucciAmpClick", (None, 0.0))
        if lastTarget is not None and clickedAt - lastTime < SECTION_CLICK_GUARD_S:
            # A press straight after another steps on from the amp just asked for. The panel may
            # not show it yet, and reading it would click the same selector twice.
            base = lastTarget
        else:
            base = self.liveAmpIndex(controller)
            if base is None:
                log.info("neuralAccess: amp key: neither the amp panel nor the selectors' pictures say which amplifier is live")
                ui.message("Cannot tell which amplifier is live.")
                return
        target = (base + direction) % len(self.ampModelNames)
        controller._petrucciAmpClick = (target, clickedAt)
        targetName = self.ampModelNames[target]
        # In the Amp view the control that has focus goes with the old amplifier's panel, and
        # focus is landed on the new one. Anywhere else it is a key that changes a setting and
        # focus stays put: the click hands it to the selector, so it is sent back and neither
        # change is announced, as for the gate and doubler keys.
        inAmpView = bool(self.ampPanel(controller))
        home = None if inAmpView else self._quickHome(controller)
        quiet = [self.topBarBackgroundRect(controller)]
        if not inAmpView:
            quiet += [selectors[target][1]] + ([home[1]] if home else [])
        controller.hushFocus([rect for rect in quiet if rect], AMP_SWITCH_HUSH_S)
        controller.clickElement(selectors[target][2])
        if home is not None:
            callLater(QUICK_RETURN_MS, self._returnHome, controller, home[0])
        log.info("neuralAccess: amp key: %s was live; clicked the %s selector; %s"
                 % (self.ampModelNames[base], targetName,
                    "Amp view" if inAmpView else "focus %s" % ("sent back" if home else "left alone")))
        serial = getattr(controller, "_petrucciSwitchSerial", 0) + 1
        controller._petrucciSwitchSerial = serial

        def poll(remaining):
            if getattr(controller, "_petrucciSwitchSerial", serial) != serial:
                return
            controller.invalidatePositional()
            if self.liveAmpIndex(controller) == target:
                controller.invalidateReadouts()
                controller.invalidateStates()
                prefix = "%s amplifier" % targetName
                focus = engine.focusedElement()
                focusRect = _prop(focus, PROP_BOUNDING_RECT) if focus is not None else None
                stayed = home is not None and focusRect and self._rectMatches(tuple(focusRect[:4]), home[1])
                if stayed:
                    ui.message(prefix)
                    return
                # In the Amp view the knob that had focus went with the old panel, and the
                # plugin drops focus on the next stop in its ring - the top bar's background.
                # Elsewhere the view can be rebuilt for the new amplifier too (and with Piezo
                # the Cab and EQ views do not exist). Land on the first stop of what shows.
                stop = self._firstTabStop(controller)
                if stop is None or not self._landOn(controller, stop, prefix):
                    ui.message(prefix)
                return
            if remaining > 0:
                callLater(200, poll, remaining - 1)
            else:
                log.info("neuralAccess: amp key: the %s amplifier never showed as live" % targetName)
                ui.message("Could not switch amplifier.")

        callLater(500, poll, 8)

    def moreActionsElement(self, controller):
        """The More preset actions button: import, reset, locate file."""
        def build():
            for x, rect, element in self._bandElements(controller, CT_BUTTON, HEADER_Y, unnamedOnly=True):
                fractions = self._fractions(controller, rect)
                if fractions is None:
                    continue
                xF, _yF, wF, _hF = fractions
                if xF > 0.65 and wF <= 0.020:
                    return (rect, element)
            return None
        return controller._positionalSweep("moreActions", build)

    def _doublerCaption(self, controller):
        def build():
            for element in controller.findElements(controlType=CT_BUTTON, name="DOUBLER"):
                rect = _prop(element, PROP_BOUNDING_RECT)
                if rect and len(rect) >= 4:
                    return (tuple(rect[:4]), element)
            return None
        return controller._positionalSweep("doublerCaption", build)

    @staticmethod
    def _isLandingTarget(obj, rect, controlType):
        """True when obj is the landing element itself: whole rectangle and control type.

        The corner alone is not enough. The Volume view's "on" light is a full-view button whose
        rectangle starts at the editor's corner, exactly like the view container the plugin
        hands focus to after a switch - matched by corner, the landing thought it was already
        there and never moved (Hadi, 2026-11-08).
        """
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

    @staticmethod
    def _sameControl(obj, rect):
        if not rect:
            return False
        try:
            return abs(obj.location.left - rect[0]) < 3 and abs(obj.location.top - rect[1]) < 3
        except Exception:
            return False

    def tabPatch(self, obj, controller, backwards):
        """Splices the controls the plugin leaves out of its own Tab ring back into it.

        Three patches, each anchored on a pair of stops measured to be neighbours in the native
        ring: More preset actions, TUNER, and the tuner window's close and mode buttons. In
        front of them, the delete question keeps Tab between its own two buttons while it is up.
        """
        if self._deleteQuestionPatch(obj, controller, backwards):
            return True
        if self._midiWindowPatch(obj, controller, backwards):
            return True
        if self._moreActionsPatch(obj, controller, backwards):
            return True
        if self._topBarRunPatch(obj, controller, backwards):
            return True
        for chain in (self._tunerButtonChain(controller), self._tunerWindowChain(controller)):
            if chain and self._chainStep(obj, controller, backwards, chain):
                return True
        return False

    def _chainStep(self, obj, controller, backwards, chain):
        """Moves along a chain of (rect, element, controlType) whose two ends are neighbours in
        the native ring. The ends pass the key on when it points out of the chain."""
        objType = _prop(obj.UIAElement, PROP_CONTROL_TYPE)
        for index, (rect, _element, controlType) in enumerate(chain):
            # The reference pitch slider and its text box share one rectangle; the type is
            # what tells them apart.
            if controlType != objType or not self._sameControl(obj, rect):
                continue
            if backwards:
                if index == 0:
                    return False
                target = chain[index - 1]
            else:
                if index == len(chain) - 1:
                    return False
                target = chain[index + 1]
            return controller.trySetFocus(target[1])
        return False

    def inputModeSwitchElement(self, controller):
        """(rectangle, element) of the Input mode switch, by the place positionalLabel names it
        from, or None."""
        def build():
            for _x, rect, element in self._bandElements(controller, CT_BUTTON, TOP_KNOB_Y, unnamedOnly=True):
                fractions = self._fractions(controller, rect)
                if fractions is None:
                    continue
                _xF, yF, wF, hF = fractions
                if 0.125 <= yF <= 0.185 and wF <= 0.030 and 0.045 <= hF <= 0.085:
                    return (rect, element)
            return None
        return controller._positionalSweep("inputModeSwitch", build)

    def _tunerButtonChain(self, controller):
        """Input mode switch, TUNER, MIDI.

        In the plug-in's own ring seven stops lie between the switch and MIDI, in this order
        (Hadi's log, 2026-11-10): Stereo, Mono, and the readouts of Input, Gate threshold,
        Transpose, Doubler spread and Output. All seven are passed over since 0.10.11, and
        TUNER, which takes focus when asked but has no stop of its own, goes after them. Until
        0.10.12 the chain began at the Output readout and the seven were left one key at a
        time, which gives out after DECORATIVE_SKIP_MAX; now it begins at the switch, and
        _topBarRunPatch takes anything standing on one of the seven to an end of the chain.
        Without the switch (not found) it is the older chain, from the Output readout.
        Verified 2026-10-02 in REAPER: Shift+Tab from MIDI lands on the Output readout and Tab
        from there returns to MIDI. The standalone's ring is presumed the same and has not
        been checked."""
        def build():
            geometry = controller.clientGeometry()
            if not geometry:
                return None
            _left, top, _width, height = geometry
            readouts = [entry for entry in self.readoutElements(controller)
                        if READOUT_Y[0] <= (entry[1][1] - top) / height <= READOUT_Y[1]]
            tuner = self.tunerButton(controller)
            midi = controller.findElements(controlType=CT_BUTTON, name="MIDI")
            if not readouts or tuner is None or not midi:
                return None
            tunerRect = _prop(tuner, PROP_BOUNDING_RECT)
            midiRect = _prop(midi[0], PROP_BOUNDING_RECT)
            if not tunerRect or not midiRect:
                return None
            switch = self.inputModeSwitchElement(controller)
            if switch is not None:
                first = (tuple(switch[0][:4]), switch[1], CT_BUTTON)
            else:
                _x, outputRect, output = readouts[-1]
                first = (outputRect, output, CT_EDIT)
            return [first,
                    (tuple(tunerRect[:4]), tuner, CT_BUTTON),
                    (tuple(midiRect[:4]), midi[0], CT_BUTTON)]
        return controller._positionalSweep("tunerChain", build)

    def _topBarRunPatch(self, obj, controller, backwards):
        """From any of the top bar's seven passed-over stops (see _tunerButtonChain): Tab to
        the Tuner button, Shift+Tab to the Input mode switch, in one move. This is where Tab
        or Shift+Tab pressed in a top bar value box goes, and where a key that has landed on
        one of the seven is taken on from (AmpController.skipDecorative asks here first)."""
        role = getattr(obj, "ampNativeRole", None)
        if role == controlTypes.Role.EDITABLETEXT:
            label = getattr(obj, "ampLabel", "") or ""
            if not label.endswith(VALUE_BOX_SUFFIX) or label[:-len(VALUE_BOX_SUFFIX)] not in TOP_KNOB_NAMES:
                return False
        elif role != controlTypes.Role.BUTTON or not self._isInputModeCaption(obj):
            return False
        chain = self._tunerButtonChain(controller)
        if not chain or chain[0][2] != CT_BUTTON:
            return False
        return controller.trySetFocus((chain[0] if backwards else chain[1])[1])

    def _tunerWindowChain(self, controller):
        """Mute, close, Cents, Hz, reference pitch. The plugin's ring runs from mute straight to
        the reference pitch slider, leaving out close and both mode buttons, which all take
        focus when asked (verified 2026-10-02)."""
        parts = self._tunerParts(controller)
        if parts is None:
            return None
        names = ("mute", "close", "Cents", "Hz", "reference")
        if any(parts.get(name) is None for name in names):
            return None
        return [(parts[name][2], parts[name][3], parts[name][0]) for name in names]

    def _moreActionsPatch(self, obj, controller, backwards):
        """Splices the More preset actions button into the Tab ring.

        The plugin gives it no Tab stop of its own, so it is inserted between the preset
        display and the DOUBLER caption - deliberately not next to SAVE AS, where the SAVE and
        DELETE buttons materialise for user presets and a patch would skip them.
        """
        more = self.moreActionsElement(controller)
        if more is None:
            return False
        moreRect, moreElement = more
        display = self.presetDisplayElement(controller)
        displayRect = _prop(display, PROP_BOUNDING_RECT) if display is not None else None
        doubler = self._doublerCaption(controller)
        if self._sameControl(obj, moreRect):
            if backwards:
                if display is not None:
                    return controller.trySetFocus(display)
            elif doubler is not None:
                return controller.trySetFocus(doubler[1])
            return False
        if not backwards and displayRect and self._sameControl(obj, tuple(displayRect[:4])):
            return controller.trySetFocus(moreElement)
        if backwards and doubler is not None and self._sameControl(obj, doubler[0]):
            return controller.trySetFocus(moreElement)
        return False

    def presetDisplayElement(self, controller):
        geometry = controller.clientGeometry()
        if not geometry:
            return None
        _left, _top, width, height = geometry
        for element in controller.findElements(controlType=CT_BUTTON):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4:
                continue
            fractions = self._fractions(controller, rect)
            if fractions is None:
                continue
            _xF, yF, wF, _hF = fractions
            if 0.125 <= yF <= 0.185 and wF > 0.20:
                return element
        return None

    def presetName(self, controller):
        element = self.presetDisplayElement(controller)
        if element is None:
            return None
        return _prop(element, PROP_NAME, "") or None

    # The headings of this amplifier's menus (capture 15: "PRESETS" over the list of presets;
    # capture 14: "INTERNAL MICS" over a Cab microphone's list, which also holds CUSTOM IR and
    # LOAD, so "Microphones" and not the heading's own words).
    menuNames = {"PRESETS": "Presets", "INTERNAL MICS": "Microphones"}

    # The folder under "Neural DSP" in ProgramData that holds this amplifier's preset files. It
    # is named after the plug-in ("Archetype Petrucci X", "Archetype Nolly X"), which is each
    # profile's displayName; a profile whose folder is named otherwise sets this.
    presetFolderName = None
    PRESET_INDEX_TTL_S = 30.0

    def presetRoot(self):
        return os.path.join(os.environ.get("ProgramData") or "C:" + os.sep + "ProgramData",
                            "Neural DSP", self.presetFolderName or self.displayName)

    def _presetFolders(self, fresh=False):
        """{preset name in lower case: [folder, ...]} for every preset file on disk.

        The plug-in shows a preset's name and never its folder, but each preset is a file named
        after it (Default.xml, John Petrucci, Artists with a folder per artist, Neural DSP,
        User). The folder is the one the file is in, so an artist's own name and never
        "Artists"; a file directly in the root has none. 187 files on 2026-11-10, read in a few
        milliseconds and kept for PRESET_INDEX_TTL_S.
        """
        root = self.presetRoot()
        now = time.time()
        cached = getattr(self, "_presetIndex", None)
        if not fresh and cached is not None and cached[0] == root \
                and now - cached[1] < self.PRESET_INDEX_TTL_S:
            return cached[2]
        index = {}
        try:
            rootKey = os.path.normcase(os.path.abspath(root))
            for folder, _folders, files in os.walk(root):
                inRoot = os.path.normcase(os.path.abspath(folder)) == rootKey
                label = "" if inRoot else os.path.basename(folder)
                for fileName in files:
                    base, extension = os.path.splitext(fileName)
                    if extension.lower() == ".xml":
                        index.setdefault(base.strip().lower(), []).append(label)
        except Exception:
            log.info("neuralAccess: could not read the preset folders under %r" % root, exc_info=True)
        for folders in index.values():
            folders.sort(key=lambda label: label.lower())
        self._presetIndex = (root, now, index)
        return index

    def _presetFolderOf(self, controller, name, stepped):
        """The folder to say in front of a preset's name, or "" when there is none to say."""
        key = name.strip().lower()
        index = self._presetFolders()
        if key not in index:
            # Saved a moment ago, perhaps. Look again, but once per name and not on every one
            # of the several times NVDA asks for a control's name.
            missed = getattr(self, "_presetMiss", None)
            if missed is None or missed[0] != key or time.time() - missed[1] > 2.0:
                self._presetMiss = (key, time.time())
                index = self._presetFolders(fresh=True)
        folders = []
        for label in index.get(key, ()):
            if label not in folders:
                folders.append(label)
        if not folders or "" in folders:
            if folders == [""]:
                controller._petrucciPresetFolder = ""
            return ""
        if len(folders) == 1:
            controller._petrucciPresetFolder = folders[0]
            return folders[0]
        # The same name in several folders ("Space Lead" is in the Andy Sneap folder and in
        # the Tim Henson one). The previous and next preset keys move to a neighbour, so after
        # one of them the folder of the preset before settles it. Reached any other way it
        # does not, and both are named: saying one of them could be wrong.
        previous = getattr(controller, "_petrucciPresetFolder", None)
        if stepped and previous in folders:
            return previous
        return " or ".join(folders)

    def spokenPreset(self, controller, rawName, stepped=False):
        """How a preset is spoken: "Preset John Petrucci, As I Am", with "modified" at the end
        when the plug-in marks it changed (an asterisk in front of the name)."""
        if not rawName:
            return None
        modified = rawName.startswith("*")
        name = rawName[1:].strip() if modified else rawName.strip()
        folder = self._presetFolderOf(controller, name, stepped)
        text = "Preset %s, %s" % (folder, name) if folder else "Preset %s" % name
        return text + ", modified" if modified else text

    def presetStep(self, controller, direction):
        arrows = controller._positionalSweep(
            "presetArrows", lambda: self._presetArrows(controller))
        if len(arrows) < 2:
            return False
        before = self.presetName(controller)
        controller.clickElement(arrows[0 if direction < 0 else 1][2])

        def poll(remaining):
            now = self.presetName(controller)
            if now and now != before:
                ui.message(self.spokenPreset(controller, now, stepped=True))
                return
            if remaining > 0:
                callLater(200, poll, remaining - 1)
            elif now:
                # The name never moved - a single preset, or the end of a non-wrapping list.
                ui.message(self.spokenPreset(controller, now, stepped=True))

        callLater(500, poll, 8)
        return True

    # ---------- the level meters: the L key and the clipping warning ----------

    @staticmethod
    def _editorRect(controller):
        """Where the editor's window stands on screen, asked of Windows and not of the plug-in."""
        try:
            return popups.windowRect(controller.hwnd)
        except Exception:
            return None

    def _meters(self, controller):
        """{"input": (background, [bar, ...]), "output": ...}, each a (left, top, width, height)
        on screen, for the meters that are in the tree. See METER_FLOOR_DB.

        Kept until the editor's window moves or the positional lookups are thrown away, which
        every view switch and every click that rebuilds something does. The input meter changes
        between one bar and two with the input mode switch."""
        window = self._editorRect(controller)
        cached = controller._positionalCache.get("meterRects")
        # Meters that were not found are looked for again after a while: the tree is empty for
        # as long as one of the plug-in's pop-up text boxes is open.
        if cached is not None and cached[0] == window                 and (cached[2] or time.time() - cached[1] < METER_RETRY_S):
            return cached[2]
        found = {"input": [], "output": []}
        # One sweep of the tree, which is one question to the plug-in, and not one per element.
        for controlType, _name, rect, _element in self._sweep(controller) or ():
            if controlType != CT_CUSTOM:
                continue
            fractions = self._fractions(controller, rect)
            if fractions is None:
                continue
            xF, yF, wF, hF = fractions
            if yF < 0.25 and 0 < wF < 0.02 and hF > 0.10:
                found["input" if xF < 0.5 else "output"].append(tuple(int(round(value)) for value in rect[:4]))
        meters = {}
        for key, rects in found.items():
            if len(rects) < 2:
                continue
            background = max(rects, key=lambda rect: rect[2] * rect[3])
            bars = sorted(rect for rect in rects if rect != background
                          and rect[0] >= background[0] and rect[0] + rect[2] <= background[0] + background[2])
            if bars:
                meters[key] = (background, bars)
        controller._positionalCache["meterRects"] = (window, time.time(), meters)
        if meters != getattr(controller, "_petrucciMetersLogged", None):
            controller._petrucciMetersLogged = meters
            log.info("neuralAccess: meters: found %r" % (meters,))
        return meters

    @staticmethod
    def _isClipRed(colour):
        red, green, blue = colour
        return red >= METER_RED_MIN and green <= red * METER_RED_OTHERS and blue <= red * METER_RED_OTHERS

    def _barReading(self, box, corner, background, bar):
        """(lit rows standing on the bottom, rows in all, clip light on, the colour at the top of
        the lit run and the colour beside it) for one bar. box is what was read of the screen
        and corner where its top left stands."""
        edgeColumn = background[0] - corner[0]
        column = bar[0] - corner[0] + bar[2] // 2
        top = bar[1] - corner[1]
        height = bar[3]
        lit = 0
        colours = None
        for row in range(top + height - 1, top - 1, -1):
            here, edge = box.at(column, row), box.at(edgeColumn, row)
            if max(abs(here[index] - edge[index]) for index in range(3)) <= METER_LIT_DIFFERENCE:
                break
            lit += 1
            colours = (here, edge)
        lightRows = range(background[1] - corner[1] + 1, top)
        light = len(lightRows) > 0 and all(self._isClipRed(box.at(column, row)) for row in lightRows)
        return lit, height, light, colours

    def meterLevels(self, controller, detail=None):
        """{"input": (level, clipped), "output": (level, clipped)} for the meters in the tree.
        The level is in decibels on the plug-in's scale, -60.0 for an empty bar, and None when
        the meter cannot be seen. With two bars the level is the higher. detail, a dictionary,
        is given what was read of each bar, for the log."""
        levels = {}
        meters = self._meters(controller)
        if not meters:
            return levels
        # One read of the screen for both meters; see METER_CHECK_POLL_MS.
        backgrounds = [background for background, _bars in meters.values()]
        corner = (min(rect[0] for rect in backgrounds), min(rect[1] for rect in backgrounds))
        box = controller.screenBox(corner[0], corner[1],
                                   max(rect[0] + rect[2] for rect in backgrounds) - corner[0],
                                   max(rect[1] + rect[3] for rect in backgrounds) - corner[1])
        for key, (background, bars) in meters.items():
            edgeColumn = background[0] - corner[0]
            rows = [background[1] - corner[1] + offset for offset in (1, background[3] // 2, background[3] - 2)]
            if box is None or not any(box.at(edgeColumn, row) != (0, 0, 0) for row in rows):
                # Nothing there to read, or the all black of a window that is not drawn.
                levels[key] = (None, False)
                continue
            level = METER_FLOOR_DB
            clipped = False
            for bar in bars:
                lit, height, light, colours = self._barReading(box, corner, background, bar)
                level = max(level, METER_FLOOR_DB - METER_FLOOR_DB * lit / float(height))
                clipped = clipped or light or lit >= height
                if detail is not None:
                    detail.setdefault(key, []).append((lit, height, light, colours))
            levels[key] = (level, clipped)
        return levels

    def _meterState(self, controller):
        state = getattr(controller, "_petrucciMeterWatch", None)
        if state is None:
            state = controller._petrucciMeterWatch = {
                "running": False, "serial": 0, "check": None, "clipOn": {}, "clipSaid": {}, "clipSince": {},
                "timing": [0, 0.0, 0.0]}
        return state

    def _watchMeters(self, controller):
        """Starts the watch on the meters, if a level check is on and it is not running."""
        state = self._meterState(controller)
        if state["check"] is None or state["running"]:
            return
        state["running"] = True
        state["serial"] += 1
        callLater(METER_CHECK_POLL_MS, self._meterPoll, controller, state["serial"])

    def _meterPoll(self, controller, serial):
        state = self._meterState(controller)
        if state["serial"] != serial:
            return
        started = time.time()
        try:
            again = self._meterLook(controller, state)
        except Exception:
            log.info("neuralAccess: meters: a look failed; the watch stops until focus next arrives", exc_info=True)
            again = False
        took = time.time() - started
        timing = state["timing"]
        timing[0] += 1
        timing[1] += took
        timing[2] = max(timing[2], took)
        if timing[0] >= METER_TIMING_LOOKS:
            self._logMeterTiming(state)
        if not again:
            state["running"] = False
            return
        callLater(METER_CHECK_POLL_MS, self._meterPoll, controller, serial)

    @staticmethod
    def _logMeterTiming(state):
        """How long the looks since the last such line took, which is how long NVDA was held."""
        looks, total, longest = state["timing"]
        if looks:
            log.info("neuralAccess: meters: %d looks, %.1f ms each on average, %.1f ms the longest"
                     % (looks, total * 1000.0 / looks, longest * 1000.0))
        state["timing"] = [0, 0.0, 0.0]

    def _meterLook(self, controller, state):
        """One look. False when the watch should stop: the level check is over, or the editor
        is not what is on screen."""
        check = state["check"]
        now = time.time()
        if check is None:
            return False
        if not controller.editorIsForeground() or not self._editorShowing(controller):
            return False
        if self._menuWindows(controller):
            # A menu of the plug-in's may lie over a meter; what is read there is the menu.
            return True
        detail = {}
        levels = self.meterLevels(controller, detail)
        said = []
        for key, spoken in METER_NAMES:
            level, clipped = levels.get(key, (None, False))
            if level is None:
                continue
            was = state["clipOn"].get(key, False)
            state["clipOn"][key] = clipped
            if clipped and not was:
                state["clipSince"][key] = now
                bars = detail.get(key) or []
                light = any(bar[2] for bar in bars)
                full = any(bar[0] >= bar[1] for bar in bars)
                # His first clipping (0.11.18) was the bar at its top with no red light seen,
                # and the log called it the light all the same.
                log.info("neuralAccess: meters: the %s meter is clipping (level %.1f): %s"
                         % (key, level, "the red light is on and the bar is at its top" if light and full
                            else "the red light is on" if light else "the bar is lit to its top, no red light"))
                if now - state["clipSaid"].get(key, 0.0) >= METER_CLIP_REPEAT_S:
                    state["clipSaid"][key] = now
                    said.append("%s clipping" % spoken)
            elif was and not clipped:
                log.info("neuralAccess: meters: the %s meter stopped clipping after %.1f s"
                         % (key, now - state["clipSince"].get(key, now)))
            check["looks"][key] = check["looks"].get(key, 0) + 1
            if clipped:
                check["clipped"][key] = True
            if check["peak"].get(key) is None or level > check["peak"][key]:
                check["peak"][key] = level
                check["detail"][key] = detail.get(key)
            if level > METER_SIGNAL_DB:
                check["samples"].setdefault(key, []).append(level)
        if said:
            ui.message(". ".join(said))
        return True

    @staticmethod
    def _decibelWords(level):
        whole = int(round(level))
        return "0" if whole >= 0 else "minus %d" % -whole

    def _levelWords(self, check):
        """What is said as a level check ends: that it is off, then what it found. The first
        words are Hadi's (2026-11-11: "when I turn it off, it needs to say level check off.
        too"); until 0.11.18 the answer came by itself."""
        if not check["looks"]:
            return "Level check off. Nothing was read."
        parts = ["Level check off"]
        for key, spoken in METER_NAMES:
            peak = check["peak"].get(key)
            if peak is None:
                continue
            if peak <= METER_SIGNAL_DB:
                parts.append("%s, no signal" % spoken)
                continue
            words = "%s peak %s" % (spoken, self._decibelWords(peak))
            samples = check["samples"].get(key, [])
            if len(samples) >= METER_AVERAGE_MIN:
                words += ", average %s" % self._decibelWords(sum(samples) / len(samples))
            if check["clipped"].get(key):
                words += ", clipped"
            parts.append(words)
        return ". ".join(parts) + "."

    def _endLevelCheck(self, controller):
        """Ends the level check and the watch with it, and says what the check found."""
        state = self._meterState(controller)
        check, state["check"] = state["check"], None
        if check is None:
            return
        # The look that is waiting on its timer finds another serial and does nothing.
        state["serial"] += 1
        state["running"] = False
        words = self._levelWords(check)
        self._logMeterTiming(state)
        log.info("neuralAccess: level check: %.1f s; looks %r; peaks %r; looks with signal %r; clipped %r; "
                 "each bar at its meter's peak as (lit rows, rows, clip light, (its colour, the colour beside it)): %r; said %r"
                 % (time.time() - check["started"], check["looks"], check["peak"],
                    dict((key, len(samples)) for key, samples in check["samples"].items()),
                    check["clipped"], check["detail"], words))
        ui.message(words)

    def levelCheck(self, controller):
        """L: starts a level check, or ends the one that is running and says what it found:
        "Level check off. Input peak minus 9, average minus 15. Output peak minus 6, average
        minus 11." """
        state = self._meterState(controller)
        if state["check"] is not None:
            self._endLevelCheck(controller)
            return True
        controller._positionalCache.pop("meterRects", None)
        if not self._meters(controller):
            ui.message("Cannot find the level meters.")
            return True
        state["check"] = {"started": time.time(), "looks": {}, "peak": {}, "samples": {}, "clipped": {}, "detail": {}}
        # A light that was on before the check began counts as coming on within it.
        state["clipOn"] = {}
        ui.message("Level check on")
        self._watchMeters(controller)
        return True

    # ---------- the single keys: G, D, R, P and the brackets ----------

    def _arriveOn(self, controller, element, spoken):
        """Puts focus on element, whose own announcement then says everything. When focus is
        already there SetFocus raises no event and nothing would be said, so spoken is."""
        rect = _prop(element, PROP_BOUNDING_RECT)
        controlType = _prop(element, PROP_CONTROL_TYPE)
        if rect and len(rect) >= 4 \
                and self._isLandingTarget(api.getFocusObject(), tuple(rect[:4]), controlType):
            ui.message(spoken)
            return
        # Focus is moving on purpose: a Tab pressed a moment ago must not skip what it lands on.
        controller._lastTab = None
        if not controller.trySetFocus(element):
            ui.message(spoken)

    def _captionElement(self, controller, caption):
        """(element, rect) of the caption button with this Name, or None."""
        for candidate in controller.findElements(controlType=CT_BUTTON, name=caption):
            rect = _prop(candidate, PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4 and rect[2] > 0:
                return (candidate, tuple(rect[:4]))
        return None

    def _quickHome(self, controller):
        """(element, rect) of the control focus is sent back to after a G or D click, or None
        when there is nowhere to send it.

        That is the control that has focus as the key is pressed. A second press may come while
        focus still sits on the caption the first click put it on; the place remembered from the
        first press is used then. With focus on a caption and nothing remembered, the user is
        standing on the switch itself and focus stays there.
        """
        now = time.time()
        focus = engine.focusedElement()
        rect = _prop(focus, PROP_BOUNDING_RECT) if focus is not None else None
        rect = tuple(rect[:4]) if rect and len(rect) >= 4 else None
        remembered = getattr(controller, "_petrucciQuickHome", None)
        if remembered is not None and now > remembered[2]:
            remembered = controller._petrucciQuickHome = None
        captions = [found[1] for found in (self._captionElement(controller, entry[0])
                                           for entry in QUICK_SWITCHES.values()) if found]
        if rect is not None and any(self._rectMatches(rect, caption) for caption in captions):
            if remembered is None:
                return None
            controller._petrucciQuickHome = (remembered[0], remembered[1], now + QUICK_HOME_S)
            return remembered[:2]
        if rect is None or controller.isFocusDeadEnd(focus):
            return None
        controller._petrucciQuickHome = (focus, rect, now + QUICK_HOME_S)
        return (focus, rect)

    def _returnHome(self, controller, element):
        controller._lastTab = None
        controller.trySetFocus(element)

    def quickToggle(self, controller, which):
        """G and D: flips the switch where it stands and says its new state, "Gate, off".

        Focus does not move as far as the user can tell. The click does hand it to the caption,
        so it is sent straight back and neither change is announced (see QUICK_SWITCHES). The
        state is said once it can be read off the screen, with the timing every switch uses.
        """
        entry = QUICK_SWITCHES.get(which)
        if entry is None:
            return False
        caption, spoken = entry
        found = self._captionElement(controller, caption)
        if found is None:
            return False
        element, rect = found
        label = self.CAPTION_STATE_KEYS[caption]
        home = self._quickHome(controller)
        controller.invalidateStates()
        before = controller.switchPosition(label, rect)
        return self._pressAndSay(controller, "%s key" % which, element, rect, label, rect, spoken, before, home)

    def _pressAndSay(self, controller, what, element, rect, label, stateRect, spoken, before, home):
        """Clicks element (at rect), sends focus back to home, (element, rect) or None, and
        says spoken with the switch's new state, read under label at stateRect, once two looks
        agree that it has changed from before. Neither focus change is announced. The G and D
        keys go this way."""
        controller._lastTab = None
        controller.hushFocus([rect] + ([home[1]] if home else []), QUICK_HUSH_S)
        if not controller.clickElement(element):
            ui.message("Could not press %s." % spoken)
            return True
        if home is not None:
            callLater(QUICK_RETURN_MS, self._returnHome, controller, home[0])
        # A newer press of either key takes over the reporting, so a quick double press says
        # where the switch ended up once instead of twice.
        serial = getattr(controller, "_petrucciQuickSerial", 0) + 1
        controller._petrucciQuickSerial = serial

        def poll(remaining, pending):
            if getattr(controller, "_petrucciQuickSerial", serial) != serial:
                return
            controller.invalidateStates()
            now = controller.switchPosition(label, stateRect)
            changed = now is not None and now != before
            # A change is believed once two readings in a row agree, like any switch; and when
            # none ever shows, what the switch reads is said all the same.
            if (changed and pending == now) or remaining <= 0:
                log.info("neuralAccess: %s: read %r before the click and %r after; focus %s"
                         % (what, before, now, "sent back" if home else "left alone"))
                ui.message("%s, %s" % (spoken, now) if now else spoken)
                return
            callLater(engine.STATE_SETTLE_MS, poll, remaining - 1, now if changed else None)

        callLater(engine.STATE_SETTLE_FIRST_MS, poll, engine.STATE_SETTLE_POLLS, None)
        return True

    def jumpTo(self, controller, which):
        """R: focus on the named top bar knob, and nothing else."""
        name = QUICK_JUMPS.get(which)
        if name is None:
            return False
        knobs = self.topKnobElements(controller)
        index = TOP_KNOB_NAMES.index(name)
        if index >= len(knobs):
            return False
        self._arriveOn(controller, knobs[index][2], name)
        return True

    def openPresetList(self, controller):
        """P: focus on the preset button, then the click it needs. The click opens the plug-in's
        list of presets, which takes focus itself (Hadi, 2026-11-10). Focus goes to the button
        first so that he is on it, and can press Enter, if the click does not take."""
        element = self.presetDisplayElement(controller)
        if element is None:
            return False
        controller._lastTab = None
        controller.trySetFocus(element)
        pressed = controller.clickElement(element)
        log.info("neuralAccess: preset key: preset button %r, click %s"
                 % (_prop(element, PROP_NAME, ""), "sent" if pressed else "could not be sent"))
        if not pressed:
            ui.message("Could not press the preset button.")
        else:
            self._followPresetList(controller)
        return True

    def _isPresetButton(self, obj, controller):
        """True for the preset display (told by where it is and how wide, as its name is) and
        for the small "Open preset browser" button on it. Both open the list of presets."""
        fractions = self._objFractions(obj, controller)
        if fractions is not None and 0.125 <= fractions[1] <= 0.185 and fractions[2] > 0.20:
            return True
        return (obj.ampLabel or "") == "Open preset browser"

    def _menuWindows(self, controller):
        """The amplifier's open menus: top level windows of its process titled "menu"."""
        editorRoot = engine.rootWindow(controller.hwnd)
        return [hwnd for hwnd in popups.popupWindows(controller.processID, editorRoot)
                if engine.windowTitle(hwnd) == "menu"]

    def _followPresetList(self, controller):
        """After a click on the preset button: waits for the list of presets to open and then
        to close, and puts focus back on the preset button.

        The list is a menu, a top level window of its own (capture 15: two windows titled
        "menu", the folders and an open folder's presets). When it closes, by Enter on a preset
        or by Escape, Windows hands focus to the host's FX window and not to the plug-in, so
        Hadi was left outside the amplifier (2026-11-10). Back on the preset button he hears
        which preset is loaded now.
        """
        serial = getattr(controller, "_petrucciListSerial", 0) + 1
        controller._petrucciListSerial = serial
        started = time.time()

        def poll(opened, remaining):
            if getattr(controller, "_petrucciListSerial", serial) != serial:
                return
            isOpen = bool(self._menuWindows(controller))
            if isOpen and not opened:
                opened = True
                try:
                    focus = api.getFocusObject()
                    log.info("neuralAccess: preset list: open; NVDA's focus is %r, %s" % (
                        focus.name, getattr(focus.role, "name", focus.role)))
                except Exception:
                    log.info("neuralAccess: preset list: open")
            if not opened:
                if remaining > 0:
                    callLater(PRESET_LIST_POLL_MS, poll, False, remaining - 1)
                else:
                    log.info("neuralAccess: preset list: no menu window appeared")
                return
            if isOpen:
                if time.time() - started < PRESET_LIST_MAX_S:
                    callLater(PRESET_LIST_POLL_MS, poll, True, 0)
                return
            # A moment for the plug-in and the host to settle where focus goes.
            callLater(150, self._returnFromPresetList, controller, serial)

        callLater(PRESET_LIST_POLL_MS, poll, False, PRESET_LIST_APPEAR_POLLS)

    def _returnFromPresetList(self, controller, serial):
        if getattr(controller, "_petrucciListSerial", serial) != serial:
            return
        controller.invalidatePositional()
        display = self.presetDisplayElement(controller)
        name = self.presetName(controller)
        focus = engine.focusedElement()
        inside = focus is not None and controller.elementIsInside(focus) \
            and not controller.isFocusDeadEnd(focus)
        foreground = controller.editorIsForeground()
        log.info("neuralAccess: preset list: closed; preset %r, focus %s the amplifier, its window %s in front"
                 % (name, "inside" if inside else "outside", "is" if foreground else "is not"))
        if not foreground or display is None:
            # The user has gone to another window; nothing is taken from there.
            return
        if inside:
            # Focus came back by itself, so nothing announces the preset. Say it.
            spoken = self.spokenPreset(controller, name)
            if spoken:
                ui.message(spoken)
            return
        controller._lastTab = None
        controller.trySetFocus(display)

    def _moduleAt(self, controller, view, rect):
        """The module a rectangle's centre lies in: the top bar, one of the view's own, or None
        below the views (the amp selectors and the utility bar)."""
        fractions = self._fractions(controller, rect)
        if fractions is None:
            return None
        xF, yF, wF, hF = fractions
        cx = xF + wF / 2.0
        cy = yF + hF / 2.0
        if cy < VIEW_CONTENT_Y[0]:
            return TOP_BAR_MODULE
        if cy >= VIEW_CONTENT_Y[1]:
            return None
        for name, axis, low, high in self.VIEW_MODULES.get(view, ()):
            if low <= (cx if axis == "x" else cy) < high:
                return name
        return None

    def moduleStops(self, controller):
        """[(module name, element)] for the view that is showing, in the order the bracket keys
        step through them: the top bar, then the view's own modules.

        The element is the module's first stop in the plug-in's Tab order, found as a view
        landing is (see LANDING_TYPES): the first operable control in document order, lamps and
        dimming layers passed over. In the top bar the row of section buttons is passed over
        too - they have the number keys - which makes GATE its first stop, as it is for Tab.
        Empty when the view cannot be told or is not a view (the audio settings).
        """
        view = self.viewOf(controller)
        geometry = controller.clientGeometry()
        items = self._sweep(controller)
        if view not in self.VIEW_MODULES or not geometry or not items:
            return []
        _left, top, _width, height = geometry
        first = {}
        for controlType, _name, rect, element in items:
            if controlType not in LANDING_TYPES or rect[2] <= 0 or rect[3] <= 0:
                continue
            module = self._moduleAt(controller, view, rect)
            if module is None or module in first:
                continue
            if module == TOP_BAR_MODULE:
                if (rect[1] - top) / height < HEADER_Y[0]:
                    continue
            elif controlType == CT_BUTTON and self._landmarkAt(controller, view, rect) in self.decorativeNames:
                continue
            first[module] = element
        order = (TOP_BAR_MODULE,) + tuple(entry[0] for entry in self.VIEW_MODULES[view])
        return [(name, first[name]) for name in order if name in first]

    def stepModule(self, controller, direction):
        """The bracket keys: focus on the previous or next module's first stop, round and round,
        the module's name said in front of the control's own announcement."""
        if self.tunerPanel(controller) is not None:
            # The tuner window is drawn over the view, whose controls stay in the tree under it.
            ui.message("Close the tuner first.")
            return True
        if self.midiState(controller) is not None:
            # So is the MIDI mappings window, and its mask keeps clicks from the view.
            ui.message("Close the MIDI mappings window first.")
            return True
        stops = self.moduleStops(controller)
        if not stops:
            ui.message("No modules to move between here.")
            return True
        names = [name for name, _element in stops]
        focus = engine.focusedElement()
        rect = _prop(focus, PROP_BOUNDING_RECT) if focus is not None else None
        current = None
        if rect and len(rect) >= 4:
            current = self._moduleAt(controller, self.viewOf(controller), tuple(rect[:4]))
        if current in names:
            index = (names.index(current) + direction) % len(names)
        else:
            # Below the views, or nowhere: that counts as past the last module.
            index = 0 if direction > 0 else len(names) - 1
        name, element = stops[index]
        log.info("neuralAccess: module key: from %r to %r" % (current, name))
        if not self._landOn(controller, element, name):
            ui.message(name)
        return True

    # ---------- the tuner ----------

    def tunerButton(self, controller):
        """The utility bar's TUNER button, found by HelpText because its Name vanishes while the
        Live Tuner is on."""
        for element in controller.findElements(controlType=CT_BUTTON, helpText=TUNER_HELP):
            return element
        for element in controller.findElements(controlType=CT_BUTTON, name="TUNER"):
            return element
        return None

    def liveTunerOn(self, controller, button=None):
        """True while the Live Tuner shows in the utility bar, None when it cannot be told.

        Structural: the TUNER button gives up its Name and widens to hold the note while the
        Live Tuner is on. The toggle pattern is a latch like everywhere else in this plugin.
        """
        if button is None:
            button = self.tunerButton(controller)
        if button is None:
            return None
        return not (_prop(button, PROP_NAME, "") or "")

    def liveTunerNote(self, controller, button):
        """The note the Live Tuner shows inside the TUNER button, or None while nothing rings."""
        rect = _prop(button, PROP_BOUNDING_RECT)
        if not rect or len(rect) < 4:
            return None
        for element in controller.findElements(controlType=CT_TEXT):
            textRect = _prop(element, PROP_BOUNDING_RECT)
            if not textRect or len(textRect) < 4:
                continue
            if rect[0] - 2 <= textRect[0] and textRect[0] + textRect[2] <= rect[0] + rect[2] + 2 \
                    and rect[1] - 2 <= textRect[1] <= rect[1] + rect[3]:
                return _prop(element, PROP_NAME, "") or None
        return None

    def _sweep(self, controller, condition=None):
        """Every element of the editor as (controlType, name, rect, element), in document order
        and in one cross-process call, or None when the editor cannot be read."""
        client = engine._uiaClient()
        root = controller._mainElement()
        if client is None or root is None:
            return None
        try:
            request = client.CreateCacheRequest()
            for propertyId in (PROP_CONTROL_TYPE, PROP_NAME, PROP_BOUNDING_RECT):
                request.AddProperty(propertyId)
        except Exception:
            log.debugWarning("neuralAccess: could not build the tuner cache request", exc_info=True)
            return None
        try:
            # Nothing may be filtered out for not being a "control" element.
            request.TreeFilter = client.RawViewCondition
        except Exception:
            log.debugWarning("neuralAccess: could not widen the tuner cache request", exc_info=True)
        try:
            found = root.FindAllBuildCache(
                TREESCOPE_DESCENDANTS, condition or client.CreateTrueCondition(), request)
        except Exception:
            log.debugWarning("neuralAccess: tuner sweep failed", exc_info=True)
            return None
        out = []
        for index in range(found.Length if found else 0):
            try:
                element = found.GetElement(index)
                controlType = element.GetCachedPropertyValue(PROP_CONTROL_TYPE)
                name = element.GetCachedPropertyValue(PROP_NAME) or ""
                rect = element.GetCachedPropertyValue(PROP_BOUNDING_RECT)
            except Exception:
                continue
            if not rect or len(rect) < 4:
                continue
            out.append((controlType, name, tuple(rect[:4]), element))
        return out

    @staticmethod
    def _inside(rect, outer, tolerance=2):
        return (outer[0] - tolerance <= rect[0] and rect[0] + rect[2] <= outer[0] + outer[2] + tolerance
                and outer[1] - tolerance <= rect[1] and rect[1] + rect[3] <= outer[1] + outer[3] + tolerance)

    def _tunerIn(self, controller, items):
        """The tuner window within one sweep, as {"rect", "element", "children"}, or None.

        JUCE gives the window no subtree of its own: its title, buttons and readouts are all
        siblings of everything else in the editor (verified 2026-10-02 - the title's parent is the
        editor's root, and the frame has no descendants at all). They do follow the frame in
        document order, because the window is the editor's last child and the view beneath it
        comes first. So the window's elements are the ones after the frame that lie inside it;
        the amp knobs under it lie inside it too, but come before it.
        """
        geometry = controller.clientGeometry()
        if not geometry or not items:
            return None
        _left, _top, width, height = geometry
        title = None
        for item in items:
            if item[0] == CT_TEXT and item[1] == TUNER_TITLE:
                title = item[2]
                break
        if title is None:
            return None
        for index, (controlType, _name, rect, element) in enumerate(items):
            if controlType == CT_CUSTOM and 0.50 <= rect[2] / width <= 0.70                     and 0.35 <= rect[3] / height <= 0.55                     and rect[0] <= title[0] <= rect[0] + rect[2] and rect[1] <= title[1] <= rect[1] + rect[3]:
                children = [item for item in items[index + 1:] if self._inside(item[2], rect)]
                return {"rect": rect, "element": element, "children": children}
        return None

    def tunerState(self, controller, fresh=False):
        """The open tuner window as {"rect", "element", "children"}, briefly cached, or None."""
        if fresh:
            controller._positionalCache.pop("tuner", None)
        def build():
            # The title search is filtered on the provider's side and cheap; the full sweep is
            # only paid for while the window is actually open.
            if not controller.findElements(controlType=CT_TEXT, name=TUNER_TITLE):
                return None
            return self._tunerIn(controller, self._sweep(controller))
        state = controller._positionalSweep("tuner", build)
        # While a click of ours is opening or closing the window, an answer that still shows
        # the old state may be the cache talking, so it is looked at again. The tuner key looks
        # first and clicks second, and that look ("closed") used to be served for its two
        # seconds: the window's frame takes focus a quarter of a second after the click and was
        # named from it, which is no name and no role. Hadi heard "unknown" (2026-11-10).
        pending = getattr(controller, "_petrucciTunerPending", None)
        if pending is not None:
            expectOpen, deadline = pending
            if time.time() > deadline:
                controller._petrucciTunerPending = None
            elif (state is not None) != expectOpen:
                self._forgetTuner(controller)
                state = controller._positionalSweep("tuner", build)
        return state

    def tunerPanel(self, controller):
        """(rect, element) of the open tuner window, or None when it is closed."""
        state = self.tunerState(controller)
        return (state["rect"], state["element"]) if state else None

    def _forgetTuner(self, controller):
        for key in ("tuner", "tunerChain", "ampPanel"):
            controller._positionalCache.pop(key, None)

    def _tunerChildren(self, controller, fresh=False):
        """The tuner window's own elements, briefly cached; None when it is closed."""
        state = self.tunerState(controller, fresh=fresh)
        return state["children"] if state else None

    def _tunerParts(self, controller):
        """The tuner window's operable controls by role, each a (type, name, rect, element)."""
        panel = self.tunerPanel(controller)
        children = self._tunerChildren(controller)
        if panel is None or not children:
            return None
        px, py, pw, ph = panel[0]
        parts = {}
        for child in children:
            controlType, name, rect, _element = child
            rx = (rect[0] - px) / pw
            ry = (rect[1] - py) / ph
            if controlType == CT_BUTTON:
                if name in ("Cents", "Hz"):
                    parts[name] = child
                elif name == "Live Tuner":
                    parts["liveLabel"] = child
                elif not name and ry < TUNER_HEADER_MAX_Y:
                    parts["close" if rx >= TUNER_CLOSE_MIN_X else "mute"] = child
                elif not name and ry >= TUNER_FOOTER_MIN_Y:
                    parts["live"] = child
            elif controlType == CT_SLIDER:
                parts["reference"] = child
            elif controlType == CT_EDIT:
                parts["entry"] = child
        return parts

    @staticmethod
    def _rectMatches(a, b, tolerance=2):
        return all(abs(a[i] - b[i]) <= tolerance for i in range(4))

    def _isTunerPanelObject(self, obj, controller):
        panel = self.tunerPanel(controller)
        if panel is None:
            return False
        try:
            loc = obj.location
            return self._rectMatches((loc.left, loc.top, loc.width, loc.height), panel[0])
        except Exception:
            return False

    def _tunerChild(self, obj, controller):
        """The tuner window's own element this object is, or None.

        The view underneath stays in the tree beneath the window, so lying inside its outline
        proves nothing - an amp knob does too. Only the window's own descendants count.
        """
        panel = self.tunerPanel(controller)
        if panel is None:
            return None
        try:
            loc = obj.location
            rect = (loc.left, loc.top, loc.width, loc.height)
        except Exception:
            return None
        px, py, pw, ph = panel[0]
        if not (px - 2 <= rect[0] and rect[0] + rect[2] <= px + pw + 2
                and py - 2 <= rect[1] and rect[1] + rect[3] <= py + ph + 2):
            return None
        controlType = _prop(obj.UIAElement, PROP_CONTROL_TYPE)
        # The reference pitch's text box only exists while it has focus, so a miss on a text box
        # gets one fresh look before giving up.
        for fresh in ((False, True) if controlType == CT_EDIT else (False,)):
            for child in self._tunerChildren(controller, fresh=fresh) or ():
                if child[0] == controlType and self._rectMatches(child[2], rect):
                    return child
        return None

    def _tunerControlName(self, obj, controller):
        """A name for one of the tuner window's anonymous controls; "" for one of its elements
        with nothing to say; None when the object is not part of the tuner window at all."""
        if self._isTunerPanelObject(obj, controller):
            return "Tuner"
        child = self._tunerChild(obj, controller)
        if child is None:
            return None
        parts = self._tunerParts(controller) or {}
        names = {"mute": "Mute while tuning", "close": "Close tuner", "live": "Live tuner switch",
                 "reference": "Reference pitch", "entry": "Reference pitch entry"}
        for key, name in names.items():
            part = parts.get(key)
            if part is not None and part[0] == child[0] and self._rectMatches(part[2], child[2]):
                return name
        return ""

    def _decorateTunerName(self, obj, controller, base):
        """The tuner's controls with their state, or None for anything else."""
        element = obj.UIAElement
        if obj.ampHelpText == TUNER_HELP:
            parts = ["Tuner"]
            if self.tunerPanel(controller) is not None:
                parts.append("window open")
            if self.liveTunerOn(controller, element):
                parts.append("live tuner on")
                note = self.liveTunerNote(controller, element)
                if note:
                    parts.append(tuning.spokenNote(note))
            return ", ".join(parts)
        if self._isTunerPanelObject(obj, controller):
            # Say why the guitar has gone quiet: the plugin mutes itself while tuning.
            mute = (self._tunerParts(controller) or {}).get("mute")
            if mute is not None and controller.switchPosition("Mute while tuning", mute[2]) == "muted":
                return "Tuner, sound muted while tuning"
            return "Tuner"
        if base in ("Hz", "Live Tuner", "Live tuner switch"):
            if self._tunerChild(obj, controller) is None:
                return None
            if base == "Hz":
                return "Hertz"
            live = self.liveTunerOn(controller)
            if live is None:
                return base
            return "%s, %s" % (base, "on" if live else "off")
        return None

    def tunerMode(self, controller):
        """"Cents" or "Hz", whichever the tuner window shows, or None when it cannot be read.

        The selected mode's caption is drawn in full white and the other in grey, so the
        brighter peak wins; no fixed threshold, so the window's backdrop does not matter.
        """
        now = time.time()
        cached = controller._stateCache.get("tunerMode")
        if cached is not None and (now - cached[0]) < STATE_CACHE_TTL:
            return cached[1]
        parts = self._tunerParts(controller) or {}
        peaks = {}
        for name in ("Cents", "Hz"):
            part = parts.get(name)
            if part is None:
                peaks = None
                break
            x, y, w, h = part[2]
            peak = controller.peakBrightness(x + 2, y + 2, w - 4, h - 4)
            if peak is None:
                peaks = None
                break
            peaks[name] = peak
        mode = None
        if peaks:
            high = max(peaks, key=peaks.get)
            low = min(peaks, key=peaks.get)
            if peaks[high] - peaks[low] >= TUNER_MODE_MIN_GAP:
                mode = high
        controller._stateCache["tunerMode"] = (now, mode)
        log.debug("neuralAccess: tuner mode peaks %r -> %r" % (peaks, mode))
        return mode

    def tunerReading(self, controller):
        # A fresh sweep every poll, of only the two kinds of element the display is made of.
        client = engine._uiaClient()
        if client is None:
            return None
        try:
            condition = client.CreateOrCondition(
                client.CreatePropertyCondition(PROP_CONTROL_TYPE, CT_TEXT),
                client.CreatePropertyCondition(PROP_CONTROL_TYPE, CT_CUSTOM))
        except Exception:
            return None
        state = self._tunerIn(controller, self._sweep(controller, condition))
        if state is None:
            self._forgetTuner(controller)
            return None
        px, py, pw, ph = state["rect"]
        children = state["children"]
        note = display = None
        left = right = False
        for controlType, name, (x, y, w, h), _element in children:
            rx = (x + w / 2.0 - px) / pw
            ry = (y - py) / ph
            if controlType == CT_TEXT:
                if h >= TUNER_NOTE_MIN_HEIGHT * ph:
                    note = name or None
                elif TUNER_READOUT_X[0] <= rx <= TUNER_READOUT_X[1] and ry < TUNER_READOUT_MAX_Y \
                        and name != TUNER_TITLE:
                    display = name or None
            elif controlType == CT_CUSTOM and w < 0.03 * pw and h < 0.08 * ph \
                    and TUNER_CHEVRON_Y[0] <= ry <= TUNER_CHEVRON_Y[1]:
                if rx < 0.5:
                    left = True
                else:
                    right = True
        if left and right:
            inTune = True
        elif left or right:
            inTune = False
        else:
            inTune = None
        return (note, display, inTune)

    # ---------- the MIDI mappings window (see MIDI_TITLE) ----------

    @staticmethod
    def _cornerInside(rect, outer, tolerance=2):
        return (outer[0] - tolerance <= rect[0] <= outer[0] + outer[2] + tolerance
                and outer[1] - tolerance <= rect[1] <= outer[1] + outer[3] + tolerance)

    def _midiIn(self, controller, items):
        """The MIDI mappings window within one sweep, as {"rect", "element", "children"}, or
        None.

        Found the way the tuner window is (see _tunerIn): the frame is the panel-sized container
        that holds the title, and the window's own elements are the ones after it in document
        order. The list is twice as wide as the frame, so a child is told by where its corner
        is and not by lying inside. The knobs of the view underneath have their corner inside
        the frame too, but come before it.
        """
        geometry = controller.clientGeometry()
        if not geometry or not items:
            return None
        _left, _top, width, height = geometry
        title = None
        for item in items:
            if item[0] == CT_TEXT and item[1] == MIDI_TITLE:
                title = item[2]
                break
        if title is None:
            return None
        for index, (controlType, _name, rect, element) in enumerate(items):
            if controlType == CT_CUSTOM \
                    and MIDI_FRAME_WIDTH[0] <= rect[2] / width <= MIDI_FRAME_WIDTH[1] \
                    and MIDI_FRAME_HEIGHT[0] <= rect[3] / height <= MIDI_FRAME_HEIGHT[1] \
                    and self._cornerInside(title, rect):
                children = [item for item in items[index + 1:] if self._cornerInside(item[2], rect)]
                return {"rect": rect, "element": element, "children": children}
        return None

    def midiState(self, controller, fresh=False):
        """The open MIDI mappings window as {"rect", "element", "children"}, briefly cached, or
        None while it is closed."""
        if fresh:
            self._forgetMidi(controller)

        def build():
            # The title search is filtered on the provider's side and cheap; the full sweep is
            # only paid for while the window is open.
            if not controller.findElements(controlType=CT_TEXT, name=MIDI_TITLE):
                return None
            return self._midiIn(controller, self._sweep(controller))
        state = controller._positionalSweep("midi", build)
        # As for the tuner window (see tunerState): while a click of ours is opening or closing
        # the window, an answer that still shows the old state is looked at again, or the list
        # would take focus and be named from "closed", which is no name at all.
        pending = getattr(controller, "_petrucciMidiPending", None)
        if pending is not None:
            expectOpen, deadline = pending
            if time.time() > deadline:
                controller._petrucciMidiPending = None
            elif (state is not None) != expectOpen:
                self._forgetMidi(controller)
                state = controller._positionalSweep("midi", build)
        return state

    def _forgetMidi(self, controller):
        controller._positionalCache.pop("midi", None)

    def _midiParts(self, controller):
        """The open window taken apart, or None while it is closed.

        "options", "close", "new" and "list" are children (type, name, rect, element) or None.
        "headings" are the column headings as (x, y, words), left to right. "rows" are the rows'
        rectangles, top to bottom. "controls" is every operable control of a mapping's row as
        (the mapping's number from 1, child), in document order, which is the order Tab goes in.
        "mappings" is how many mappings there are.
        """
        state = self.midiState(controller)
        if state is None:
            return None
        px, py, pw, ph = state["rect"]
        parts = {"rect": state["rect"], "options": None, "close": None, "new": None, "list": None,
                 "headings": [], "rows": [], "controls": [], "mappings": 0}
        loose = []
        for child in state["children"]:
            controlType, name, rect, _element = child
            if controlType == CT_TEXT:
                if name and name != MIDI_TITLE:
                    parts["headings"].append((rect[0], rect[1], name))
            elif controlType == CT_CUSTOM:
                if rect[2] <= pw * MIDI_WIDE:
                    continue
                if rect[3] >= ph * MIDI_LIST_MIN_HEIGHT:
                    if parts["list"] is None:
                        parts["list"] = child
                elif rect[3] <= ph * MIDI_ROW_MAX_HEIGHT \
                        and not any(self._rectMatches(rect, row) for row in parts["rows"]):
                    parts["rows"].append(rect)
            elif controlType in MIDI_OPERABLE:
                if controlType == CT_BUTTON and name == MIDI_NEW_NAME:
                    parts["new"] = child
                elif controlType == CT_BUTTON and not name and (rect[1] - py) / ph < MIDI_HEADER_MAX_Y:
                    parts["close" if (rect[0] - px) / pw >= 0.5 else "options"] = child
                else:
                    loose.append(child)
        parts["rows"].sort(key=lambda row: row[1])
        # Only the texts above the list are headings; a row may have texts of its own.
        listTop = parts["list"][2][1] if parts["list"] is not None else None
        parts["headings"] = sorted(heading for heading in parts["headings"]
                                   if listTop is None or heading[1] < listTop)
        # A mapping is one line of controls. The lines are counted from the controls themselves,
        # so that the numbering does not depend on what the rows' containers turn out to be.
        lines = []
        for child in loose:
            centre = child[2][1] + child[2][3] / 2.0
            if not any(abs(centre - line) <= 10 for line in lines):
                lines.append(centre)
        lines.sort()
        parts["lines"] = lines
        parts["mappings"] = len(lines)
        for child in loose:
            parts["controls"].append((self._midiLine(parts, child[2]), child))
        # A mapping that is switched off has no lists: the plug-in takes them out of the tree
        # and leaves the on/off button and the delete button (Hadi's log, 2026-11-11: 33
        # elements with the mapping on, 29 after Enter on its switch, 33 after the next). So a
        # mapping is on when its line holds anything that is not a button.
        parts["live"] = set(number for number, child in parts["controls"] if child[0] != CT_BUTTON)
        return parts

    @staticmethod
    def _midiLine(parts, rect):
        """Which mapping, from 1, a rectangle is on the line of; None for none."""
        centre = rect[1] + rect[3] / 2.0
        for index, line in enumerate(parts.get("lines") or ()):
            if abs(centre - line) <= 10:
                return index + 1
        return None

    def _midiChild(self, obj, controller):
        """The MIDI mappings window's own element this object is, or None. Only the window's
        own elements count: the view underneath stays in the tree beneath it."""
        state = self.midiState(controller)
        if state is None:
            return None
        try:
            loc = obj.location
            rect = (loc.left, loc.top, loc.width, loc.height)
        except Exception:
            return None
        controlType = _prop(obj.UIAElement, PROP_CONTROL_TYPE)
        for child in state["children"]:
            if child[0] == controlType and self._rectMatches(child[2], rect):
                return child
        return None

    @staticmethod
    def _midiListName(parts):
        count = parts["mappings"]
        if not count:
            return "%s, no mappings" % MIDI_WINDOW_NAME
        return "%s, %d mapping%s" % (MIDI_WINDOW_NAME, count, "" if count == 1 else "s")

    @staticmethod
    def _midiHeading(parts, rect):
        """The column heading a row's control stands under, "" when it stands under none. Two
        columns are both headed Note/CC/PC, and are told apart as 1 and 2."""
        best = None
        for index, (x, _y, _words) in enumerate(parts["headings"]):
            if x <= rect[0] + MIDI_HEADING_SLACK:
                best = index
        if best is None:
            return ""
        words = parts["headings"][best][2]
        same = [index for index, heading in enumerate(parts["headings"]) if heading[2] == words]
        if len(same) > 1:
            return "%s %d" % (words, same.index(best) + 1)
        return words

    @staticmethod
    def _midiEdgeButton(parts, child):
        """"switch" for a mapping's on/off button at the start of its row, "delete" for the
        delete button at its end, None for anything else."""
        controlType, _name, rect, _element = child
        if controlType != CT_BUTTON:
            return None
        px, _py, pw, _ph = parts["rect"]
        across = (rect[0] - px) / pw
        if across < MIDI_EDGE_BUTTON:
            return "switch"
        if across > 1.0 - 2 * MIDI_EDGE_BUTTON:
            return "delete"
        return None

    def _midiRowControlName(self, parts, number, child):
        """What a control of a mapping's row is called, without its value: "Mapping 2, Type".
        The on/off button is the mapping itself with its state, "Mapping 2, off", as a rack
        unit's switch is "Delay rack unit, off"."""
        mapping = "Mapping %d" % number if number else "Mapping"
        edge = self._midiEdgeButton(parts, child)
        if edge == "switch":
            return "%s, %s" % (mapping, "on" if number in parts["live"] else "off")
        if edge == "delete":
            return "Delete %s" % mapping.lower()
        heading = self._midiHeading(parts, child[2])
        return "%s, %s" % (mapping, heading) if heading else mapping

    def _midiPartIs(self, parts, key, child):
        part = parts.get(key)
        return part is not None and part[0] == child[0] and self._rectMatches(part[2], child[2])

    def _midiControlName(self, obj, controller):
        """A name for one of the MIDI mappings window's parts; "" for one with nothing to say;
        None when the object is not part of that window."""
        child = self._midiChild(obj, controller)
        if child is None:
            return None
        parts = self._midiParts(controller)
        if parts is None:
            return None
        if self._midiPartIs(parts, "options", child):
            return MIDI_OPTIONS_NAME
        if self._midiPartIs(parts, "close", child):
            return MIDI_CLOSE_NAME
        if child[0] == CT_CUSTOM:
            if self._midiPartIs(parts, "list", child):
                return self._midiListName(parts)
            if any(self._rectMatches(child[2], row) for row in parts["rows"]):
                number = self._midiLine(parts, child[2])
                return "Mapping %d row" % number if number else "New mapping row"
            return ""
        for number, control in parts["controls"]:
            if control[0] == child[0] and self._rectMatches(control[2], child[2]):
                return self._midiRowControlName(parts, number, control)
        return ""

    def _isMidiList(self, obj, controller):
        child = self._midiChild(obj, controller)
        if child is None or child[0] != CT_CUSTOM:
            return False
        parts = self._midiParts(controller)
        return parts is not None and self._midiPartIs(parts, "list", child)

    def _decorateMidiName(self, obj, controller, base):
        """The MIDI button with "window open" while it is, and a mapping's control that has a
        name of its own (a list says what is chosen in it) with its mapping and its column in
        front: "Mapping 2, Type, CC Absolute". None for anything else."""
        native = (_prop(obj.UIAElement, PROP_NAME, "") or "").strip()
        child = self._midiChild(obj, controller)
        if child is None:
            if native == MIDI_BUTTON_NAME and self.midiState(controller) is not None:
                return "%s, window open" % base
            return None
        parts = self._midiParts(controller)
        if parts is None:
            return None
        for number, control in parts["controls"]:
            if control[0] == child[0] and self._rectMatches(control[2], child[2]):
                full = self._midiRowControlName(parts, number, control)
                return "%s, %s" % (full, native) if native else full
        return None

    def _midiRing(self, parts):
        """The window's stops in order: the list, each mapping's controls, New MIDI Mapping,
        the options button, the close button."""
        ring = []
        if parts["list"] is not None:
            ring.append(parts["list"])
        ring.extend(control for _number, control in parts["controls"])
        for key in ("new", "options", "close"):
            if parts[key] is not None:
                ring.append(parts[key])
        return ring

    def _midiWindowPatch(self, obj, controller, backwards):
        """With the MIDI mappings window open, Tab and Shift+Tab go round its own parts and
        nowhere else.

        The plug-in's ring has the list and a row in it and then goes on into the view
        underneath, which is dimmed behind the window's mask. It has neither the close button
        nor New MIDI Mapping. Without the close button nothing is kept in: the way out must be
        one of the stops.
        """
        parts = self._midiParts(controller)
        if parts is None or parts["close"] is None:
            return False
        ring = self._midiRing(parts)
        if len(ring) < 2:
            return False
        try:
            loc = obj.location
            rect = (loc.left, loc.top, loc.width, loc.height)
        except Exception:
            rect = None
        objType = _prop(obj.UIAElement, PROP_CONTROL_TYPE)
        index = None
        if rect is not None:
            for position, child in enumerate(ring):
                if child[0] == objType and self._rectMatches(child[2], rect):
                    index = position
                    break
        if index is None and parts["list"] is not None and objType == CT_CUSTOM \
                and self._midiChild(obj, controller) is not None:
            # One of the rows, which the plug-in's own ring stops on: it counts as the list.
            index = 0
        if index is None:
            target = ring[-1] if backwards else ring[0]
        else:
            target = ring[(index + (-1 if backwards else 1)) % len(ring)]
        # Focus is moving on purpose: a Tab pressed a moment ago must not pass over the stop.
        controller._lastTab = None
        return controller.trySetFocus(target[3])

    def _midiButton(self, controller):
        for element in controller.findElements(controlType=CT_BUTTON, name=MIDI_BUTTON_NAME):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4 and rect[2] > 0 and rect[3] > 0:
                return element
        return None

    def _midiDescribe(self, controller):
        """The open window's elements in one line for the log, placed from the panel's corner."""
        state = self.midiState(controller)
        if state is None:
            return "nothing, it is closed"
        px, py = state["rect"][0], state["rect"][1]
        kinds = {CT_BUTTON: "Button", CT_COMBOBOX: "ComboBox", CT_CUSTOM: "Custom", CT_EDIT: "Edit",
                 CT_SLIDER: "Slider", CT_TEXT: "Text"}
        return "%d elements: %s" % (len(state["children"]), "; ".join(
            "%s %r at (%d, %d) %dx%d" % (kinds.get(controlType, controlType), name,
                                         rect[0] - px, rect[1] - py, rect[2], rect[3])
            for controlType, name, rect, _element in state["children"]))

    def midiMappings(self, controller):
        """Control+M opens the MIDI mappings window, or closes it with its own close button.
        It was M alone in 0.11.4 to 0.11.7; Hadi gave M to the control's menu (2026-11-11)."""
        self._forgetMidi(controller)
        parts = self._midiParts(controller)
        wasOpen = parts is not None
        element = parts["close"][3] if wasOpen and parts["close"] is not None else self._midiButton(controller)
        if element is None:
            return False
        pressed = controller.clickElement(element)
        log.info("neuralAccess: midi key: the window was %s; click %s"
                 % ("open" if wasOpen else "closed", "sent" if pressed else "could not be sent"))
        if not pressed:
            ui.message("Could not press the MIDI button.")
        else:
            self._followMidiWindow(controller, wasOpen)
        return True

    # ---------- a control's own menu ----------
    #
    # A right click on a knob or switch opens a menu for it. Not seen on screen when this was
    # written (0.11.8). The plug-in file has its words in one run: "Parameter: ", "Reset
    # parameter", "Disable MIDI Learn", "Enable MIDI Learn", "Show MIDI Map", "Action: ",
    # "Remove", with "Preset: " just before. The layouts give every view and both bars a
    # showRightClickMenu action on mousePopupMenu, and the controllers wrap 209 widgets in a
    # midiLearnControl. MIDI learn binds the next MIDI message that arrives to the control.
    #
    # Hadi chose the key (2026-11-11): "bind m to the right click menu. so m for menu, and then
    # assign ctrl m for the midi window toggle". He does not want the Applications key, which
    # small keyboards are losing.

    def menuName(self, heading):
        """A control's own menu starts with a line saying what it is for, "Parameter: " and the
        control's name. Its window is called by that line; the other menus by their table."""
        words = (heading or "").strip()
        if words.startswith(CONTEXT_MENU_HEADINGS):
            return words
        return super(ArchetypeXProfile, self).menuName(heading)

    def contextMenu(self, controller):
        """The M key: a right click on the control that has focus, which opens its menu."""
        if self.midiState(controller) is not None:
            # The window's mask takes every click meant for the view.
            ui.message("No menu here. Control+M closes the MIDI mappings window.")
            return True
        if self.tunerPanel(controller) is not None:
            ui.message("Close the tuner first.")
            return True
        focus = engine.focusedElement()
        if focus is None or not controller.elementIsInside(focus) or controller.isFocusDeadEnd(focus):
            ui.message("No control has focus.")
            return True
        try:
            standingOn = api.getFocusObject().name
        except Exception:
            standingOn = None
        before = self._treeSnapshot(controller)
        look = self._controlLook(controller, focus)
        pressed = controller.clickElement(focus, right=True)
        log.info("neuralAccess: menu key: on %r at %r; right click %s" % (
            standingOn, _prop(focus, PROP_BOUNDING_RECT), "sent" if pressed else "could not be sent"))
        if not pressed:
            ui.message("Could not open the menu.")
        else:
            self._followContextMenu(controller, focus, before, look, standingOn)
        return True

    @staticmethod
    def _controlLook(controller, element):
        """(mean grey, brightest grey) of a control's rectangle on screen, for the log.

        Switching MIDI learn on changes nothing in the tree (Hadi's log, 2026-11-11: 72
        elements before and after), so whatever shows that learn is waiting is only drawn.
        These two numbers before and after a choice in the menu are there to find it."""
        rect = _prop(element, PROP_BOUNDING_RECT)
        if not rect or len(rect) < 4:
            return None
        try:
            return (controller.meanGrey(rect[0], rect[1], rect[2], rect[3]),
                    controller.peakGrey(rect[0], rect[1], rect[2], rect[3]))
        except Exception:
            return None

    def _treeSnapshot(self, controller):
        """Every element of the editor as (type, name, rectangle), to see afterwards what a
        choice in a menu added or took away."""
        return set((controlType, name, rect) for controlType, name, rect, _element
                   in self._sweep(controller) or ())

    def _menuItemsText(self, controller):
        """What the amplifier's open menus hold, in one line for the log."""
        found = []
        try:
            client = engine._uiaClient()
            for hwnd in self._menuWindows(controller):
                root = client.ElementFromHandle(hwnd)
                items = root.FindAll(TREESCOPE_DESCENDANTS, client.CreateTrueCondition())
                for index in range(items.Length):
                    element = items.GetElement(index)
                    found.append("%s %r" % (_prop(element, PROP_CONTROL_TYPE), _prop(element, PROP_NAME, "")))
        except Exception:
            log.debugWarning("neuralAccess: could not list a menu's items", exc_info=True)
        return "; ".join(found) or "nothing that could be read"

    def _learnChange(self, before, after, lastItem):
        """"on" or "off" when a choice in a control's menu has switched MIDI learn, else None.

        Two things must agree: the item that had focus as the menu closed, and the control
        looking different afterwards (see MIDI_LEARN_MOVED). The item alone does not say whether
        Enter or Escape closed the menu, and the picture alone changes for other reasons, a
        switch that Reset parameter has flipped for one. Which way the picture changed is not
        asked: the veil is not the same on every panel.
        """
        moved = self._lookDistance(before, after)
        if moved is None or moved < MIDI_LEARN_MOVED:
            return None
        item = lastItem.strip() if isinstance(lastItem, str) else ""
        if item == MIDI_LEARN_ON_ITEM:
            return "on"
        if item == MIDI_LEARN_OFF_ITEM:
            return "off"
        return None

    @staticmethod
    def _lookDistance(one, other):
        """How far apart two looks of a control are: the change in mean grey plus the change
        in brightest grey. None when either could not be read."""
        if not one or not other or None in tuple(one[:2]) or None in tuple(other[:2]):
            return None
        return abs(one[0] - other[0]) + abs(one[1] - other[1])

    @staticmethod
    def _editorShowing(controller):
        """False while the editor's own window is hidden. REAPER's FX chain window shows one
        effect at a time, so with another effect chosen there the window in front is still the
        editor's, and what is on screen where the control was is some other effect."""
        try:
            return bool(popups._user32.IsWindowVisible(controller.hwnd))
        except Exception:
            return True

    def _watchLearn(self, controller):
        """While MIDI learn waits on a control: notices the veil over it going away without the
        menu having been used, and says "MIDI learned".

        That is what a sighted user sees when a MIDI message has arrived and been learned. Seen
        once, 2026-11-11, with a test effect in REAPER sending a sweep of control changes: the
        veil over Gain went five seconds after learn was switched on, Gain took the last value
        sent, and the MIDI mappings window held a new mapping for Lead Amp Gain on CC #20.
        Until 0.11.13 the words were "MIDI learn off", the same as after Disable MIDI Learn;
        Hadi chose "MIDI learned". If the plug-in ever ends learn for another reason, the same
        words are said.

        Nothing is looked at while another window is in front or while a menu, the tuner or the
        MIDI mappings window may cover the control, and the watch ends without a word when the
        control is gone (another view) or after ten minutes.
        """
        serial = getattr(controller, "_petrucciLearnSerial", 0) + 1
        controller._petrucciLearnSerial = serial

        def poll():
            state = getattr(controller, "_petrucciLearn", None)
            if getattr(controller, "_petrucciLearnSerial", serial) != serial or not state:
                return
            if time.time() - state["since"] > MIDI_LEARN_WATCH_S \
                    or not controller._stillUsable(state["element"]):
                log.info("neuralAccess: midi learn: no longer watching %r" % (state["name"],))
                controller._petrucciLearn = None
                return
            covered = not controller.editorIsForeground() or not self._editorShowing(controller) \
                or bool(self._menuWindows(controller)) \
                or self.tunerPanel(controller) is not None or self.midiState(controller) is not None
            look = None if covered else self._controlLook(controller, state["element"])
            toClear = self._lookDistance(look, state["clear"])
            toVeiled = self._lookDistance(look, state["veiled"])
            if toClear is None or toVeiled is None or toClear >= toVeiled:
                state["seen"] = 0
                callLater(MIDI_LEARN_POLL_MS, poll)
                return
            # Nearer to how it looked without the veil than with it. Seen twice running
            # before it is believed.
            state["seen"] = state.get("seen", 0) + 1
            if state["seen"] < 2:
                callLater(MIDI_LEARN_POLL_MS, poll)
                return
            controller._petrucciLearn = None
            log.info("neuralAccess: midi learn: the veil over %r went by itself (it looks %r; it was %r "
                     "veiled, %r clear)" % (state["name"], look, state["veiled"], state["clear"]))
            ui.message("MIDI learned")

        callLater(MIDI_LEARN_POLL_MS, poll)

    def _followContextMenu(self, controller, element, before, look=None, name=None):
        """After the right click: says so if no menu comes, and once the menu has closed puts
        focus back on the control, which then says what it is and what it reads now.

        When one of this plug-in's menus closes, the host takes focus (see _followPresetList).
        What the menu held, which item had focus last and what changed in the editor all go to
        the log: nothing here knows yet how the plug-in shows that MIDI learn is waiting.

        Show MIDI Map opens the MIDI mappings window, and the plug-in puts focus on its list.
        The list is wider than the editor, so it does not count as inside it, and 0.11.8
        pulled focus back to the knob under the window's mask (his log, 10:55:38). With that
        window open focus belongs in it.
        """
        serial = getattr(controller, "_petrucciListSerial", 0) + 1
        controller._petrucciListSerial = serial
        started = time.time()
        last = {"item": None}

        def back():
            if getattr(controller, "_petrucciListSerial", serial) != serial:
                return
            controller.invalidatePositional()
            controller.invalidateStates()
            controller.invalidateReadouts()
            focus = engine.focusedElement()
            inside = focus is not None and controller.elementIsInside(focus) \
                and not controller.isFocusDeadEnd(focus)
            foreground = controller.editorIsForeground()
            after = self._treeSnapshot(controller)
            log.info("neuralAccess: menu key: menu closed; the last item in focus was %r; focus %s the "
                     "amplifier, its window %s in front; the editor has %d elements, had %d; new: %r; gone: %r"
                     % (last["item"], "inside" if inside else "outside", "is" if foreground else "is not",
                        len(after), len(before), sorted(after - before, key=repr)[:12],
                        sorted(before - after, key=repr)[:12]))
            nowLook = self._controlLook(controller, element) if controller._stillUsable(element) else None
            learn = self._learnChange(look, nowLook, last["item"])
            log.info("neuralAccess: menu key: the control's mean and brightest grey were %r, are %r; MIDI learn %s"
                     % (look, nowLook, learn or "as it was"))
            if learn == "on":
                rect = _prop(element, PROP_BOUNDING_RECT)
                controller._petrucciLearn = {
                    "element": element, "name": name, "since": time.time(),
                    "rect": tuple(rect[:4]) if rect and len(rect) >= 4 else None,
                    "type": _prop(element, PROP_CONTROL_TYPE), "clear": look, "veiled": nowLook}
                self._watchLearn(controller)
            elif learn == "off":
                controller._petrucciLearn = None
            if not foreground:
                if learn:
                    ui.message("MIDI learn %s" % learn)
                return
            self._forgetMidi(controller)
            if self.midiState(controller) is not None:
                self._landInMidi(controller, getattr(controller, "_petrucciMidiSerial", 0))
                return
            if learn == "off":
                # In front of the control's own name as focus comes back to it, so that the
                # announcement of focus does not cut the words off.
                if not controller._stillUsable(element) or not self._landOn(controller, element, "MIDI learn off"):
                    ui.message("MIDI learn off")
                return
            if inside:
                # Focus came back by itself, so nothing will name the control again.
                if learn == "on":
                    ui.message("MIDI learn on")
                return
            # With learn on, the control says so itself for as long as it waits (decorateName).
            controller._lastTab = None
            if controller._stillUsable(element):
                controller.trySetFocus(element)

        def poll(opened, remaining):
            if getattr(controller, "_petrucciListSerial", serial) != serial:
                return
            isOpen = bool(self._menuWindows(controller))
            if isOpen and not opened:
                opened = True
                log.info("neuralAccess: menu key: menu open; it holds %s" % self._menuItemsText(controller))
            if not opened:
                if remaining > 0:
                    callLater(PRESET_LIST_POLL_MS, poll, False, remaining - 1)
                else:
                    log.info("neuralAccess: menu key: no menu appeared")
                    ui.message("No menu opened.")
                return
            if isOpen:
                try:
                    last["item"] = api.getFocusObject().name
                except Exception:
                    pass
                if time.time() - started < PRESET_LIST_MAX_S:
                    callLater(PRESET_LIST_POLL_MS, poll, True, 0)
                return
            # A moment for the plug-in and the host to settle where focus goes.
            callLater(150, back)

        callLater(PRESET_LIST_POLL_MS, poll, False, CONTEXT_MENU_APPEAR_POLLS)

    def _followMidiWindow(self, controller, wasOpen):
        """After a click that should open or close the MIDI mappings window: waits for that,
        then puts focus on the window's list, or back on the MIDI button."""
        controller._petrucciMidiPending = (not wasOpen, time.time() + 3.0)
        serial = getattr(controller, "_petrucciMidiSerial", 0) + 1
        controller._petrucciMidiSerial = serial

        def poll(remaining):
            if getattr(controller, "_petrucciMidiSerial", serial) != serial:
                return
            self._forgetMidi(controller)
            isOpen = self.midiState(controller) is not None
            if isOpen != wasOpen:
                controller._petrucciMidiPending = None
                controller.invalidatePositional()
                if isOpen:
                    log.info("neuralAccess: midi: window open; it holds %s" % self._midiDescribe(controller))
                    callLater(MIDI_SETTLE_MS, self._landInMidi, controller, serial)
                else:
                    log.info("neuralAccess: midi: window closed")
                    callLater(150, self._recoverAfterMidi, controller, serial)
                return
            if remaining > 0:
                callLater(MIDI_POLL_MS, poll, remaining - 1)
                return
            controller._petrucciMidiPending = None
            log.info("neuralAccess: midi: the window did not %s" % ("close" if wasOpen else "open"))
            ui.message("The MIDI mappings window did not %s." % ("close" if wasOpen else "open"))

        callLater(400, poll, MIDI_POLLS)

    def _landInMidi(self, controller, serial):
        """Once the window is open: focus on its list, unless focus is on one of the window's
        stops already. The plug-in puts focus on the list itself as the window opens (Hadi's
        log, 2026-11-11), and the list is then announced from there."""
        if getattr(controller, "_petrucciMidiSerial", serial) != serial:
            return
        parts = self._midiParts(controller)
        if parts is None:
            return
        ring = self._midiRing(parts)
        if not ring or not controller.editorIsForeground():
            ui.message("%s open" % MIDI_WINDOW_NAME)
            return
        focus = engine.focusedElement()
        rect = _prop(focus, PROP_BOUNDING_RECT) if focus is not None else None
        if rect and len(rect) >= 4 and any(self._rectMatches(tuple(rect[:4]), child[2]) for child in ring):
            return
        controller._lastTab = None
        if not controller.trySetFocus(ring[0][3]):
            ui.message("%s open" % MIDI_WINDOW_NAME)

    def _recoverAfterMidi(self, controller, serial):
        """Once the window has closed: focus on the MIDI button, which says "MIDI mappings
        closed" in front of its own name. With another window in front, the words alone."""
        if getattr(controller, "_petrucciMidiSerial", serial) != serial:
            return
        button = self._midiButton(controller)
        if button is None or not controller.editorIsForeground() \
                or not self._landOn(controller, button, "%s closed" % MIDI_WINDOW_NAME):
            ui.message("%s closed" % MIDI_WINDOW_NAME)

    def _followMidiChange(self, controller, what, hushList=False, switchOf=None):
        """After a click inside the window: when a mapping has come or gone, says so by where
        focus is put, the new mapping's first control or New MIDI Mapping. What the window
        holds afterwards goes to the log, because a mapping's row had not been seen when this
        was written.

        hushList is for New MIDI Mapping and a mapping's delete button. The plug-in rebuilds
        the list then and drops focus on it, a moment before this has seen the change, so the
        list was announced with the count from before: "MIDI mappings, no mappings" as the
        first mapping appeared (Hadi's log, 2026-11-11). Focus is about to be moved on, so
        that stop is kept quiet.

        switchOf is the mapping's number after Enter on its on/off button. Its lists come or
        go with its state, which is how the state is known (see _midiParts), and the new state
        is said: focus stays on the button, so nothing else would say it.
        """
        serial = getattr(controller, "_petrucciMidiSerial", 0) + 1
        controller._petrucciMidiSerial = serial
        parts = self._midiParts(controller)
        before = (parts["mappings"], len(parts["controls"])) if parts is not None else None
        if hushList and parts is not None and parts["list"] is not None:
            controller.hushFocus([parts["list"][2]], MIDI_CHANGE_HUSH_S)

        def poll(remaining):
            if getattr(controller, "_petrucciMidiSerial", serial) != serial:
                return
            self._forgetMidi(controller)
            now = self._midiParts(controller)
            if now is None:
                return
            after = (now["mappings"], len(now["controls"]))
            if after == before:
                if remaining > 0:
                    callLater(MIDI_POLL_MS, poll, remaining - 1)
                else:
                    log.info("neuralAccess: midi: nothing came or went after %s" % what)
                return
            controller.invalidatePositional()
            # The words first, and the log after them. Until 0.11.7 the window was read twice
            # more between seeing the change and saying it, and each reading can stall for
            # half a second inside REAPER. In Hadi's log of 0.11.6 a mapping came on and went
            # off again a second later, twice running, which is what a second Enter does when
            # the first seems to have done nothing.
            if before is not None and controller.editorIsForeground():
                target = None
                if after[0] > before[0]:
                    added = [control for number, control in now["controls"] if number == after[0]]
                    target = added[0] if added else now["new"]
                elif after[0] < before[0]:
                    ui.message("Mapping deleted.")
                    target = now["new"] or now["list"]
                elif switchOf is not None:
                    ui.message("Mapping %d, %s" % (switchOf, "on" if switchOf in now["live"] else "off"))
                if target is not None:
                    controller._lastTab = None
                    controller.trySetFocus(target[3])
            log.info("neuralAccess: midi: after %s the window holds %s" % (what, self._midiDescribe(controller)))

        callLater(MIDI_POLL_MS, poll, MIDI_POLLS)

    def _followMidiMenu(self, controller, element, what):
        """After Enter on one of a mapping's lists, or a click on the options button: once the
        menu that opened has closed, focus is put back on the control it was opened from if the
        host has taken it, as it does when the preset list closes (see _followPresetList)."""
        serial = getattr(controller, "_petrucciListSerial", 0) + 1
        controller._petrucciListSerial = serial
        started = time.time()

        def back():
            if getattr(controller, "_petrucciListSerial", serial) != serial:
                return
            self._forgetMidi(controller)
            controller.invalidatePositional()
            focus = engine.focusedElement()
            inside = focus is not None and controller.elementIsInside(focus) \
                and not controller.isFocusDeadEnd(focus)
            foreground = controller.editorIsForeground()
            log.info("neuralAccess: midi: %s: menu closed; focus %s the amplifier, its window %s in front; "
                     "the window holds %s" % (what, "inside" if inside else "outside",
                                              "is" if foreground else "is not", self._midiDescribe(controller)))
            if not foreground or inside:
                return
            controller._lastTab = None
            if controller._stillUsable(element) and controller.trySetFocus(element):
                return
            parts = self._midiParts(controller)
            if parts is not None and parts["list"] is not None:
                controller.trySetFocus(parts["list"][3])

        def poll(opened, remaining):
            if getattr(controller, "_petrucciListSerial", serial) != serial:
                return
            isOpen = bool(self._menuWindows(controller))
            if isOpen and not opened:
                opened = True
                log.info("neuralAccess: midi: %s: menu open" % what)
            if not opened:
                if remaining > 0:
                    callLater(PRESET_LIST_POLL_MS, poll, False, remaining - 1)
                else:
                    log.info("neuralAccess: midi: %s: no menu window appeared" % what)
                return
            if isOpen:
                if time.time() - started < PRESET_LIST_MAX_S:
                    callLater(PRESET_LIST_POLL_MS, poll, True, 0)
                return
            # A moment for the plug-in and the host to settle where focus goes.
            callLater(150, back)

        callLater(PRESET_LIST_POLL_MS, poll, False, PRESET_LIST_APPEAR_POLLS)

    def _midiAfterClick(self, controller, obj, native):
        """True when the click was on the MIDI button or inside the MIDI mappings window, and
        is being followed."""
        child = self._midiChild(obj, controller)
        if child is None:
            if native != MIDI_BUTTON_NAME:
                return False
            self._forgetMidi(controller)
            self._followMidiWindow(controller, self.midiState(controller) is not None)
            return True
        parts = self._midiParts(controller)
        if parts is None:
            return False
        if self._midiPartIs(parts, "close", child):
            self._followMidiWindow(controller, True)
        elif self._midiPartIs(parts, "options", child):
            self._followMidiMenu(controller, child[3], "options")
        else:
            # New MIDI Mapping and a delete button change how many mappings there are.
            changes = self._midiPartIs(parts, "new", child)
            switchOf = None
            for number, control in parts["controls"]:
                if control[0] == child[0] and self._rectMatches(control[2], child[2]):
                    edge = self._midiEdgeButton(parts, control)
                    changes = edge == "delete"
                    switchOf = number if edge == "switch" else None
                    break
            self._followMidiChange(controller, "a click on %s" % (native or obj.ampLabel or "a button"),
                                   changes, switchOf)
        return True

    def onFocus(self, controller, obj):
        # With the delete question up, "Yes, delete" is chosen without focus moving. Focus
        # arriving anywhere means something else has happened since.
        self._deleteChoiceBackToCancel(controller, "focus moved")
        # Whichever way the tuner window was opened, landing in the amp with it open starts the
        # narration.
        if self.tunerPanel(controller) is not None:
            controller.watchTuner()
        # A level check that is on goes on watching the meters. The watch stops by itself while
        # another window is in front, and this starts it again. With no check on it does nothing.
        self._watchMeters(controller)

    def diagnose(self, controller, obj):
        """Walks the tuner detection step by step, recording where it stops and what it costs.
        The first line is the spoken summary, empty unless the tuner window is open."""
        lines = []
        summary = ""
        try:
            lines.append("client geometry %r" % (controller.clientGeometry(),))
            started = time.time()
            items = self._sweep(controller)
            lines.append("full sweep: %s in %.0f ms" % (
                "failed" if items is None else "%d elements" % len(items), (time.time() - started) * 1000))
            self._forgetTuner(controller)
            state = self.tunerState(controller)
            lines.append("tuner window %r" % (state["rect"] if state else None,))
            if state:
                summary = "Tuner window detected, %d controls." % len(state["children"])
                for child in state["children"][:40]:
                    lines.append("  %r %r %r" % (child[0], child[1], child[2]))
                lines.append("parts %r" % (sorted((self._tunerParts(controller) or {}).keys()),))
                started = time.time()
                reading = self.tunerReading(controller)
                lines.append("reading %r in %.0f ms" % (reading, (time.time() - started) * 1000))
                lines.append("mode %r" % (self.tunerMode(controller),))
            lines.append("focus object role %r name %r location %r" % (
                getattr(obj, "role", None), getattr(obj, "name", None), getattr(obj, "location", None)))
            lines.append("focus is tuner window %r, tuner child %r" % (
                self._isTunerPanelObject(obj, controller), self._tunerChild(obj, controller) is not None))
            lines.append("watching %r, editor foreground %r" % (
                controller._tunerWatching, controller.editorIsForeground()))
        except Exception:
            log.info("neuralAccess: tuner diagnosis failed", exc_info=True)
            lines.append("diagnosis raised; see the traceback above")
        return [summary] + lines

    # ---------- DELETE and the plug-in's own question ----------

    def deleteDialog(self, controller):
        """The plug-in's "delete this preset?" question while it is on screen, else None:
        {"yes": (rect, element), "cancel": (rect, element) or None, "text": what it says}.

        Found by its "Yes, delete" button, a name nothing else in the plug-in has. The panel is
        worked out from that button. Cancel is the button of that name inside the panel - the
        Save As panel has a Cancel of its own - and the text is the lines inside it that are as
        wide as the question's are (see DELETE_QUESTION_TEXT_WIDTH).
        """
        yes = None
        for element in controller.findElements(controlType=CT_BUTTON, name=DELETE_QUESTION_YES):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4 and rect[2] > 0 and rect[3] > 0:
                yes = (tuple(rect[:4]), element)
                break
        if yes is None:
            return None
        acrossAt, downAt, yesWidth = DELETE_QUESTION_YES_AT
        scale = yes[0][2] / yesWidth
        margin = DELETE_QUESTION_MARGIN * scale
        panelLeft = yes[0][0] - acrossAt * scale - margin
        panelTop = yes[0][1] - downAt * scale - margin
        panelRight = panelLeft + DELETE_QUESTION_PANEL[0] * scale + 2 * margin
        panelBottom = panelTop + DELETE_QUESTION_PANEL[1] * scale + 2 * margin

        def inPanel(rect):
            x = rect[0] + rect[2] / 2.0
            y = rect[1] + rect[3] / 2.0
            return panelLeft <= x <= panelRight and panelTop <= y <= panelBottom

        cancel = None
        for element in controller.findElements(controlType=CT_BUTTON, name=DELETE_QUESTION_CANCEL):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4 and rect[2] > 0 and inPanel(rect):
                cancel = (tuple(rect[:4]), element)
                break
        lines = []
        for element in controller.findElements(controlType=CT_TEXT):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if not rect or len(rect) < 4 or not inPanel(rect) \
                    or abs(rect[2] - DELETE_QUESTION_TEXT_WIDTH * scale) > 0.15 * DELETE_QUESTION_TEXT_WIDTH * scale:
                continue
            words = " ".join((_prop(element, PROP_NAME, "") or "").split())
            if words:
                lines.append((rect[1], rect[0], words))
        lines.sort()
        return {"yes": yes, "cancel": cancel, "text": " ".join(line[2] for line in lines)}

    @staticmethod
    def _presetFileKey(rawName):
        """A preset as its file is named: without the asterisk of a changed preset, lower case."""
        return (rawName or "").lstrip("*").strip().lower()

    def _presetFileCount(self, rawName):
        return len(self._presetFolders(fresh=True).get(self._presetFileKey(rawName), ()))

    def _followDeleteDialog(self, controller):
        """After a click on DELETE: waits for the plug-in's question, reads it out and puts
        focus on its Cancel button.

        Nothing puts focus in the panel by itself (unlike Save As, whose text box takes it), and
        the panel's two lines are text, which is never announced unasked. Cancel is where focus
        lands so that a second Enter, pressed out of habit, deletes nothing: "Yes, delete" is
        one Tab away.
        """
        global _deleteQuestionController
        serial = getattr(controller, "_petrucciDeleteSerial", 0) + 1
        controller._petrucciDeleteSerial = serial
        before = self.presetName(controller)

        def poll(remaining):
            global _deleteQuestionController
            if getattr(controller, "_petrucciDeleteSerial", serial) != serial:
                return
            dialog = self.deleteDialog(controller)
            if dialog is None:
                if remaining > 0:
                    callLater(DELETE_QUESTION_POLL_MS, poll, remaining - 1)
                    return
                now = self.presetName(controller)
                log.info("neuralAccess: delete: no question came up after the click; preset %r, was %r"
                         % (now, before))
                ui.message("Preset deleted." if now != before else "DELETE did not respond.")
                return
            controller._petrucciDeleteQuestion = {
                "preset": before, "files": self._presetFileCount(before), "choice": "cancel"}
            _deleteQuestionController = controller
            text = dialog["text"] or "Delete the preset %s? This action is permanent." % (
                (before or "").lstrip("*").strip() or "that is loaded")
            target = dialog["cancel"] or dialog["yes"]
            log.info("neuralAccess: delete: the plug-in asks %r; Cancel at %r, Yes at %r; preset %r, %d file(s)"
                     % (dialog["text"], dialog["cancel"][0] if dialog["cancel"] else None, dialog["yes"][0],
                        before, controller._petrucciDeleteQuestion["files"]))
            # Why "Yes, delete" will not take focus is not known; what it says of itself is kept.
            log.info("neuralAccess: delete: Yes says enabled %r, focusable %r; Cancel says enabled %r, focusable %r"
                     % (_prop(dialog["yes"][1], PROP_IS_ENABLED), _prop(dialog["yes"][1], PROP_IS_KEYBOARD_FOCUSABLE),
                        _prop(dialog["cancel"][1], PROP_IS_ENABLED) if dialog["cancel"] else None,
                        _prop(dialog["cancel"][1], PROP_IS_KEYBOARD_FOCUSABLE) if dialog["cancel"] else None))
            ui.message(text)
            # Focus is moving on purpose: a Tab pressed a moment ago must not skip what it lands on.
            controller._lastTab = None
            if not controller.trySetFocus(target[1]):
                ui.message("Could not reach the question's buttons.")

        callLater(DELETE_QUESTION_POLL_MS, poll, DELETE_QUESTION_APPEAR_POLLS)

    def _followDeleteAnswer(self, controller, confirmed):
        """After a click on Cancel or "Yes, delete": waits for the question to close, says what
        became of the preset and puts focus somewhere useful - the button either answer was
        given from is gone by then.

        "Preset deleted." is said only when the preset button shows another preset or the file
        has gone from disk. 0.10.3 said it on the strength of having clicked, and it was not true.
        """
        serial = getattr(controller, "_petrucciDeleteSerial", 0) + 1
        controller._petrucciDeleteSerial = serial
        state = getattr(controller, "_petrucciDeleteQuestion", None) or {}
        before = state.get("preset")

        def deleteButton():
            found = controller.findElements(controlType=CT_BUTTON, name=DELETE_BUTTON_NAME)
            return found[0] if found else None

        def poll(remaining, settle):
            global _deleteQuestionController
            if getattr(controller, "_petrucciDeleteSerial", serial) != serial:
                return
            if self.deleteDialog(controller) is not None:
                if remaining > 0:
                    callLater(DELETE_QUESTION_POLL_MS, poll, remaining - 1, settle)
                    return
                log.info("neuralAccess: delete: the question is still up after %s"
                         % ("Yes, delete" if confirmed else "Cancel"))
                ui.message("The question is still open.")
                return
            controller._petrucciDeleteQuestion = None
            if _deleteQuestionController is controller:
                _deleteQuestionController = None
            controller.invalidatePositional()
            now = self.presetName(controller)
            display = self.presetDisplayElement(controller)
            if not confirmed:
                log.info("neuralAccess: delete: cancelled; preset %r" % (now,))
                ui.message("Cancelled.")
                target = deleteButton() or display
            else:
                files = self._presetFileCount(before)
                deleted = now != before or files < state.get("files", 0)
                if not deleted and settle > 0:
                    # The file and the preset button can trail the panel by a moment.
                    callLater(DELETE_QUESTION_POLL_MS, poll, 0, settle - 1)
                    return
                log.info("neuralAccess: delete: answered yes; preset %r, was %r; %d file(s), were %d; %s"
                         % (now, before, files, state.get("files", 0), "deleted" if deleted else "NOT deleted"))
                ui.message("Preset deleted." if deleted else "The preset was not deleted.")
                target = display if deleted else (deleteButton() or display)
            if target is not None and controller.editorIsForeground():
                controller._lastTab = None
                controller.trySetFocus(target)

        callLater(DELETE_QUESTION_POLL_MS, poll, DELETE_QUESTION_CLOSE_POLLS, DELETE_QUESTION_SETTLE_POLLS)

    def deleteChoice(self, controller):
        """Which of the delete question's buttons Enter would press, "cancel" or "yes"; None
        when no question is up."""
        state = getattr(controller, "_petrucciDeleteQuestion", None)
        return state.get("choice", "cancel") if state else None

    def _deleteQuestionUp(self, controller):
        """(state, the question as deleteDialog gives it), or (None, None) when it is not up."""
        state = getattr(controller, "_petrucciDeleteQuestion", None)
        if not state:
            return None, None
        dialog = self.deleteDialog(controller)
        if dialog is None:
            # Closed some other way: a click on the dimmed editor does that.
            controller._petrucciDeleteQuestion = None
            return None, None
        return state, dialog

    def _deleteQuestionPatch(self, obj, controller, backwards):
        """While the delete question is up, Tab and Shift+Tab choose between its two buttons
        and go nowhere else: everything behind the panel is dimmed and a click there closes it.

        Focus stays on Cancel throughout, because "Yes, delete" will not take it (see
        DELETE_BUTTON_NAME). The choice is spoken the way NVDA speaks a button taking focus.
        """
        state, dialog = self._deleteQuestionUp(controller)
        if state is None or dialog["cancel"] is None:
            return False
        cancel = dialog["cancel"]
        if not self._sameControl(obj, cancel[0]):
            state["choice"] = "cancel"
            return controller.trySetFocus(cancel[1])
        if state.get("choice") == "yes":
            state["choice"] = "cancel"
            ui.message("Cancel, button")
            return True
        state["choice"] = "yes"
        enabled = _prop(dialog["yes"][1], PROP_IS_ENABLED)
        ui.message("Yes, delete, button" + (", unavailable" if enabled is not None and not enabled else ""))
        return True

    def passedOver(self, obj):
        """The lamps and dimming layers, the top bar's background, and the value boxes (see
        VALUE_BOX_SUFFIX). A text box with no such name - Save As's, the tuner's reference
        pitch - is a stop like any other."""
        label = getattr(obj, "ampLabel", "") or ""
        if label in self.decorativeNames or label == TOP_BAR_BACKGROUND_NAME:
            return True
        role = getattr(obj, "ampNativeRole", None)
        if role == controlTypes.Role.EDITABLETEXT:
            return label.endswith(VALUE_BOX_SUFFIX) and label not in self.VALUE_BOX_KEPT
        if role == controlTypes.Role.STATICTEXT:
            # A note display that cannot be typed into (see positionalLabel): its knob says
            # the same note, so it goes out of the Tab order with the other readouts.
            return label.endswith(VALUE_BOX_SUFFIX)
        if role == controlTypes.Role.BUTTON:
            return self._isInputModeCaption(obj)
        return False

    def _isInputModeCaption(self, obj):
        """True for the Stereo and Mono captions beside the input mode switch (see
        INPUT_MODE_CAPTIONS)."""
        element = getattr(obj, "UIAElement", None)
        controller = getattr(obj, "ampController", None)
        if element is None or controller is None:
            return False
        if (_prop(element, PROP_NAME, "") or "").strip() not in INPUT_MODE_CAPTIONS:
            return False
        fractions = self._objFractions(obj, controller)
        return fractions is not None and INPUT_MODE_CAPTION_Y[0] <= fractions[1] <= INPUT_MODE_CAPTION_Y[1]

    def _valueBoxEnter(self, obj, controller):
        """Enter on a knob that has a value box, and Enter in a box gone into that way."""
        role = getattr(obj, "ampNativeRole", None)
        try:
            location = obj.location
            rect = (location.left, location.top, location.width, location.height)
        except Exception:
            return False
        if role == controlTypes.Role.SLIDER:
            found = self._readoutForRect(controller, rect)
            if found is None:
                return False
            boxRect, box = found
            # The knob is kept as an element: while one of these boxes is open a search of the
            # editor can come back empty (see the tempo box), so it could not be found again.
            controller._petrucciValueBox = (tuple(boxRect[:4]), obj.UIAElement, time.time())
            log.info("neuralAccess: value box: Enter on the knob at %r; focus to its box at %r" % (rect, tuple(boxRect[:4])))
            # Focus is moving on purpose: a Tab pressed a moment ago must not pass over the box.
            controller._lastTab = None
            if not controller.trySetFocus(box):
                controller._petrucciValueBox = None
                return False
            return True
        entered = getattr(controller, "_petrucciValueBox", None)
        if role != controlTypes.Role.EDITABLETEXT or not entered:
            return False
        boxRect, knob, when = entered
        controller._petrucciValueBox = None
        if time.time() - when > VALUE_BOX_MAX_S or not self._sameControl(obj, boxRect):
            return False

        def back():
            log.info("neuralAccess: value box: Enter in the box at %r; focus back to its knob" % (boxRect,))
            controller.invalidateReadouts()
            controller.invalidatePositional()
            if controller.editorIsForeground():
                controller._lastTab = None
                controller.trySetFocus(knob)

        callLater(VALUE_BOX_RETURN_MS, back)
        # The key itself still has to reach the plug-in: it is what takes the typed value.
        return False

    def enterPatch(self, obj, controller):
        """Enter on Cancel with "Yes, delete" chosen clicks "Yes, delete"; Enter on a knob goes
        into its value box (see _valueBoxEnter). Everything else is left alone, Enter on Cancel
        with Cancel chosen included: that is an ordinary click."""
        if self.deleteChoice(controller) != "yes":
            # Enter opens a list of the MIDI mappings window by itself. It is only watched, so
            # that focus can be brought back when the list's menu has closed.
            if getattr(obj, "ampNativeRole", None) == controlTypes.Role.COMBOBOX:
                child = self._midiChild(obj, controller)
                if child is not None:
                    self._followMidiMenu(controller, child[3], "a mapping's list")
                    return False
            return self._valueBoxEnter(obj, controller)
        state, dialog = self._deleteQuestionUp(controller)
        if state is None:
            return False
        state["choice"] = "cancel"
        if dialog["cancel"] is None or not self._sameControl(obj, dialog["cancel"][0]):
            return False
        log.info("neuralAccess: delete: Enter with Yes, delete chosen; clicking it at %r" % (dialog["yes"][0],))
        if not controller.clickElement(dialog["yes"][1]):
            ui.message("Could not press Yes, delete.")
            return True
        self._followDeleteAnswer(controller, True)
        return True

    def _deleteChoiceBackToCancel(self, controller, why):
        state = getattr(controller, "_petrucciDeleteQuestion", None)
        if state and state.get("choice") == "yes":
            state["choice"] = "cancel"
            log.info("neuralAccess: delete: the choice is Cancel again, %s" % why)

    def noteGesture(self, gesture):
        controller = _deleteQuestionController
        if controller is None or self.deleteChoice(controller) != "yes":
            return
        if getattr(gesture, "isModifier", False) or engine.gestureIsKey(gesture, "tab", "shift+tab", "enter"):
            return
        self._deleteChoiceBackToCancel(controller, "another key was pressed")

    def _moreActionsFirst(self, controller):
        """IMPORT, the first of the three buttons More preset actions opens; None while the
        row shows DELETE, SAVE and SAVE AS... instead."""
        for element in controller.findElements(controlType=CT_BUTTON, name=MORE_ACTIONS_FIRST):
            rect = _prop(element, PROP_BOUNDING_RECT)
            if rect and len(rect) >= 4 and rect[2] > 0 and rect[3] > 0:
                return element
        return None

    def _followMoreActions(self, controller):
        """After a click on More preset actions: once the three buttons are there, puts focus
        on the first, which then says its own name.

        The press itself says nothing and leaves focus on a button that has just been swapped
        for its twin, so until 0.10.6 the only sign that anything had opened was what Tab
        found next (Hadi, 2026-11-10). Pressed with the three open, it closes them; focus is
        then left alone.
        """
        serial = getattr(controller, "_petrucciMoreSerial", 0) + 1
        controller._petrucciMoreSerial = serial
        wasOpen = self._moreActionsFirst(controller) is not None

        def poll(remaining):
            if getattr(controller, "_petrucciMoreSerial", serial) != serial:
                return
            first = self._moreActionsFirst(controller)
            if (first is not None) == wasOpen:
                if remaining > 0:
                    callLater(MORE_ACTIONS_POLL_MS, poll, remaining - 1)
                else:
                    log.info("neuralAccess: more preset actions: the row did not change; it is %s"
                             % ("open" if wasOpen else "closed"))
                return
            # The row's buttons are different ones now; nothing remembered about it holds.
            controller.invalidatePositional()
            if first is None:
                log.info("neuralAccess: more preset actions: closed")
                return
            log.info("neuralAccess: more preset actions: open; focus to %s" % MORE_ACTIONS_FIRST)
            if controller.editorIsForeground():
                # Focus is moving on purpose: a Tab pressed a moment ago must not skip it.
                controller._lastTab = None
                controller.trySetFocus(first)

        callLater(MORE_ACTIONS_POLL_MS, poll, MORE_ACTIONS_POLLS)

    def afterClick(self, controller, obj):
        if self._isPresetButton(obj, controller):
            # Enter on the preset button opens the list, as the P key does.
            self._followPresetList(controller)
            return
        native = (_prop(obj.UIAElement, PROP_NAME, "") or "").strip()
        if native == DELETE_BUTTON_NAME:
            self._followDeleteDialog(controller)
            return
        if self._midiAfterClick(controller, obj, native):
            return
        if not native:
            more = self.moreActionsElement(controller)
            if more is not None and self._sameControl(obj, more[0]):
                self._followMoreActions(controller)
                return
        if native in (DELETE_QUESTION_YES, DELETE_QUESTION_CANCEL) \
                and getattr(controller, "_petrucciDeleteQuestion", None):
            # The click goes out a moment from now, so the question is still up to be measured.
            dialog = self.deleteDialog(controller)
            if dialog is not None and any(part is not None and self._sameControl(obj, part[0])
                                          for part in (dialog["yes"], dialog["cancel"])):
                self._followDeleteAnswer(controller, native == DELETE_QUESTION_YES)
                return
        if obj.ampHelpText == TUNER_HELP:
            self._forgetTuner(controller)
            self._followTunerWindow(controller, self.tunerPanel(controller) is not None)
            return
        child = self._tunerChild(obj, controller)
        if child is None:
            return
        parts = self._tunerParts(controller) or {}

        def isPart(key):
            part = parts.get(key)
            return part is not None and self._rectMatches(part[2], child[2])
        if isPart("close"):
            self._followTunerWindow(controller, True)
        elif isPart("live") or isPart("liveLabel"):
            self._followLiveTuner(controller, self.liveTunerOn(controller))
        elif isPart("Cents") or isPart("Hz"):
            self._followTunerMode(controller, child[1])

    def tuner(self, controller):
        """The T key opens or closes the tuner window."""
        button = self.tunerButton(controller)
        if button is None:
            return "Tuner not available."
        self._forgetTuner(controller)
        wasOpen = self.tunerPanel(controller) is not None
        if not controller.clickElement(button):
            return "Could not press the tuner."
        self._followTunerWindow(controller, wasOpen)
        return ""

    def _focusInTuner(self, controller):
        panel = self.tunerPanel(controller)
        focus = engine.focusedElement()
        rect = _prop(focus, PROP_BOUNDING_RECT) if focus is not None else None
        if panel is None or not rect or len(rect) < 4:
            return False
        px, py, pw, ph = panel[0]
        return px - 2 <= rect[0] and rect[0] + rect[2] <= px + pw + 2 \
            and py - 2 <= rect[1] and rect[1] + rect[3] <= py + ph + 2

    def _followTunerWindow(self, controller, wasOpen):
        """Confirms the tuner window opened or closed, and starts or settles the narration."""
        # Until then, what is remembered about the window is about to be wrong; see tunerState.
        controller._petrucciTunerPending = (not wasOpen, time.time() + engine.POSITIONAL_CACHE_TTL)
        if wasOpen:
            # When the window closes the plug-in drops focus on MIDI, the next stop in its ring
            # (the Tuner button is not in it). Focus is about to be put on the Tuner button, so
            # that stop is not worth hearing.
            midi = self._captionElement(controller, "MIDI")
            if midi is not None:
                controller.hushFocus([midi[1]], TUNER_CLOSE_HUSH_S)

        def poll(remaining):
            self._forgetTuner(controller)
            isOpen = self.tunerPanel(controller) is not None
            if isOpen != wasOpen:
                controller._petrucciTunerPending = None
                controller.invalidatePositional()
                if isOpen:
                    controller.watchTuner()
                    # The window takes focus by itself and is announced from there; only speak
                    # when it did not.
                    if not self._focusInTuner(controller):
                        ui.message("Tuner open")
                else:
                    callLater(150, self._recoverAfterTuner, controller)
                return
            if remaining > 0:
                callLater(150, poll, remaining - 1)
            else:
                ui.message("The tuner did not respond.")

        callLater(400, poll, 10)

    def _recoverAfterTuner(self, controller):
        """Once the window has closed: focus on the Tuner button, which says "Tuner closed" in
        front of its own name.

        Left alone, the plug-in drops focus on MIDI. Hadi, 2026-11-10: "landing back on the
        tuner button itself would make a bit more sense". With another window in front by now,
        focus is not touched and the words are only said.
        """
        button = self.tunerButton(controller)
        if button is None or not controller.editorIsForeground() \
                or not self._landOn(controller, button, "Tuner closed"):
            ui.message("Tuner closed")

    def _followLiveTuner(self, controller, before):
        def poll(remaining):
            now = self.liveTunerOn(controller)
            if now is not None and now != before:
                controller.invalidatePositional()
                ui.message("live tuner on" if now else "live tuner off")
                return
            if remaining > 0:
                callLater(150, poll, remaining - 1)

        callLater(400, poll, 10)

    def _followTunerMode(self, controller, clicked):
        # The first look waits for the cursor to be put back: hovering brightens captions.
        def poll(remaining):
            controller.invalidateStates()
            mode = self.tunerMode(controller)
            if mode == clicked or remaining <= 0:
                if mode:
                    ui.message("cents" if mode == "Cents" else "hertz")
                return
            callLater(150, poll, remaining - 1)

        callLater(600, poll, 8)

    def leadToggle(self, controller):
        """On this amp, NVDA+shift+L jumps straight to the Lead amplifier."""
        selectors = self.selectorElements(controller)
        if len(selectors) != len(self.ampModelNames):
            return "Amplifier selectors not available."
        if self.liveAmpIndex(controller) == 3:
            return "Lead amplifier already selected."
        controller.clickElement(selectors[3][2])
        controller.invalidatePositional()
        return "Lead amplifier"

    # ---------- custom impulse responses ----------
    #
    # Each Cab side's microphone combo box opens a list (Enter does it) whose last row is a
    # "CUSTOM IR" label and a LOAD button (layout irLoaderItemView; captured 2026-11-08, capture
    # 7). The arrows only walk the microphones, LOAD is no menu item, and like every button
    # here it answers only a real click. Its action opens a menu and then a file browser.

    def loadImpulseResponse(self, controller, focus, processID):
        controller._petrucciLoadProcess = processID
        editorRoot = engine.rootWindow(controller.hwnd)
        found = popups.findInPopups(processID, "LOAD", CT_BUTTON, editorRoot)
        if found is not None:
            # The list is open already. Press LOAD once this command's own keys are up.
            def press(remaining):
                if engine.modifiersDown() and remaining > 0:
                    callLater(50, press, remaining - 1)
                    return
                message = self._pressLoad(controller, found)
                if message:
                    ui.message(message)

            press(30)
            return None
        isSelector = (isinstance(focus, engine.AmpObject)
                      and focus.ampNativeRole == controlTypes.Role.COMBOBOX
                      and self.viewOf(controller) == "cab")
        if not isSelector:
            return "Go to the left or right microphone selector in the Cab view first."
        selector = focus.UIAElement

        def poll(remaining):
            opened = popups.findInPopups(processID, "LOAD", CT_BUTTON, editorRoot)
            if opened is not None:
                message = self._pressLoad(controller, opened)
                if message:
                    ui.message(message)
                return
            if remaining > 0:
                callLater(100, poll, remaining - 1)
            else:
                log.info("neuralAccess: load IR: no LOAD button appeared; popups of the process: %r"
                         % ([engine.windowTitle(hwnd) for hwnd in popups.popupWindows(processID, editorRoot)],))
                ui.message("The microphone list did not open.")

        def openList(remaining):
            # This command's own keys are still down when it starts. Enter sent now would reach
            # the plug-in as shift+Enter, which it ignores - the list never opened and the
            # command said so every time (Hadi, 2026-11-09). So wait for the keys to come up.
            if engine.modifiersDown() and remaining > 0:
                callLater(50, openList, remaining - 1)
                return
            if engine.modifiersDown():
                # Still held after a second and a half: a click opens the list whatever is held.
                log.info("neuralAccess: load IR: keys still held, opening the list with a click")
                controller.clickElement(selector)
            else:
                log.info("neuralAccess: load IR: keys released, opening the list with Enter")
                KeyboardInputGesture.fromName("enter").send()
            callLater(150, poll, 15)

        openList(30)
        return None

    def _pressLoad(self, controller, found):
        window, element = found
        if not controller.clickElement(element, window=window):
            log.info("neuralAccess: load IR: the click on LOAD in popup %r was refused" % (window,))
            return "Could not press LOAD."
        log.info("neuralAccess: pressed LOAD in popup %r" % (window,))
        # What LOAD opens had never been seen when this was written. Note every window the
        # process has a moment later, so the log says what came up.
        processID = getattr(controller, "_petrucciLoadProcess", None)

        def note():
            try:
                for hwnd in popups.topLevelWindows(processID):
                    log.info("neuralAccess: load IR: window %r class %r title %r at %r" % (
                        hwnd, engine._className(hwnd), engine.windowTitle(hwnd), popups.windowRect(hwnd)))
            except Exception:
                log.info("neuralAccess: load IR: could not list the windows", exc_info=True)

        if processID:
            callLater(1200, note)
        return "Load custom IR"
