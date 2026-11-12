# neuralAccess - what to say about a tuner while a string rings.
#
# Pure decision logic with no NVDA imports, so it can be replayed against recorded probe data
# (tools\dev\Replay-TunerSpeech.py) without a screen reader running.
#
# A tuner display changes many times a second - the Archetype Petrucci X repaints its readout
# about every 60 ms - and speech cannot keep up with that, so this decides which readings are
# worth saying:
#   * a new note is announced in full ("E, 12 cents flat") once it has held for a couple of
#     polls, because the pitch detector flickers between neighbouring notes on the attack;
#   * while the same note rings, the offset is updated at most about once a second, and only when
#     the rounded figure has actually moved, so a steady string goes quiet;
#   * "in tune" is said as soon as the plugin's own verdict has held for a couple of polls, and is
#     not repeated while it holds;
#   * after a moment of silence the next note is announced in full again, so re-plucking a string
#     always says which string it is.
#
# Readings are (note, display, inTune): the note as the plugin prints it ("E", "D#/Eb"), the
# readout text ("+5.0" in cents mode, "659.0 Hz" in hertz mode), and the plugin's own in-tune
# verdict - True, False, or None when it cannot be told. A note of None means nothing is ringing.

import re

# A new note must be seen this many polls running before it is announced.
SETTLE_POLLS = 2
# Seconds between spoken updates while one note rings.
UPDATE_INTERVAL = 0.9
# The full announcement takes longer to say, so the first update waits a little longer.
FIRST_UPDATE_DELAY = 1.4
# Seconds without a note after which the next one is announced in full again.
SILENCE_RESET = 0.7
# Used only when the plugin's verdict is unreadable: measured 2026-10-02, its green arrows
# appear exactly while the readout is within 2.0 cents (132 samples, no exceptions).
IN_TUNE_CENTS = 2.0

_CENTS = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*$")
_HERTZ = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*Hz\s*$", re.IGNORECASE)


def spokenNote(raw):
    """The note as it should be spoken: 'D#/Eb' becomes 'D sharp'.

    The plugin prints both spellings of every black key; one is plenty in speech.
    """
    if not raw:
        return raw
    first = raw.split("/")[0].strip()
    if first.endswith("#"):
        return first[:-1] + " sharp"
    if len(first) == 2 and first.endswith("b"):
        return first[0] + " flat"
    return first


def describe(display, inTune):
    """(key, full, short, tuned) for one readout.

    key changes exactly when the spoken figure would; full is the wording that follows a note
    name, short the wording of an update while that note rings.
    """
    if display:
        match = _CENTS.match(display)
        if match:
            cents = float(match.group(1))
            if inTune is None:
                inTune = abs(cents) <= IN_TUNE_CENTS
            amount = int(round(abs(cents)))
            if inTune or amount == 0:
                return ("in tune", "in tune", "in tune", True)
            direction = "flat" if cents < 0 else "sharp"
            return ((amount, direction), "%d cents %s" % (amount, direction),
                    "%d %s" % (amount, direction), False)
        match = _HERTZ.match(display)
        if match:
            hertz = float(match.group(1))
            text = "%.1f hertz" % hertz
            if inTune:
                return ("in tune", text + ", in tune", "in tune", True)
            return (round(hertz, 1), text, text, False)
        return (display, display, display, bool(inTune))
    return (None, "", "", bool(inTune))


class TunerAnnouncer(object):
    """Fed one reading per poll; answers with the text to speak, or None."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._spokenNote = None
        self._candidate = None
        self._candidateCount = 0
        self._lastHeard = None
        self._nextUpdateAt = 0.0
        self._lastKey = None
        self._inTuneSaid = False
        self._runTuned = None
        self._runLength = 0

    def feed(self, note, display, inTune, now):
        if not note:
            if self._lastHeard is not None and (now - self._lastHeard) >= SILENCE_RESET:
                self._spokenNote = None
                self._candidate = None
                self._candidateCount = 0
            return None
        self._lastHeard = now
        key, full, short, tuned = describe(display, inTune)
        if note != self._spokenNote:
            if note == self._candidate:
                self._candidateCount += 1
            else:
                self._candidate = note
                self._candidateCount = 1
            if self._candidateCount < SETTLE_POLLS:
                return None
            self._spokenNote = note
            self._candidate = None
            self._candidateCount = 0
            self._lastKey = key
            self._inTuneSaid = tuned
            self._runTuned, self._runLength = tuned, 1
            self._nextUpdateAt = now + FIRST_UPDATE_DELAY
            name = spokenNote(note)
            return "%s, %s" % (name, full) if full else name
        # The note that was announced is still ringing.
        self._candidate = None
        self._candidateCount = 0
        if tuned == self._runTuned:
            self._runLength += 1
        else:
            self._runTuned, self._runLength = tuned, 1
        if tuned:
            if not self._inTuneSaid and self._runLength >= SETTLE_POLLS:
                self._inTuneSaid = True
                self._lastKey = key
                self._nextUpdateAt = now + UPDATE_INTERVAL
                return "in tune"
            return None
        # Out of tune: wait for it to hold, for the update interval, and for the figure to move.
        if self._runLength < SETTLE_POLLS or now < self._nextUpdateAt:
            return None
        if key == self._lastKey and not self._inTuneSaid:
            return None
        self._inTuneSaid = False
        self._lastKey = key
        self._nextUpdateAt = now + UPDATE_INTERVAL
        return short
