# Changelog

## 0.13.1 (2026-11-12)

The user guide is clearer. The add-on itself is the same as in 0.13.0.

- Escape is described as the other way out of the plug-in. It closes REAPER's FX window.
- The top and bottom bars have their own section, listing what each holds, the tuner included.
- The right-click menu on M or the Applications key is described, with Reset parameter, MIDI Learn and Show MIDI Map.
- How RESET and DELETE ask before they act is under Good to know.

## 0.13.0 (2026-11-12)

The first public release.

- The add-on is now called Neural DSP Plugins Accessibility. Test builds up to 0.12.6 were called neuralAccess. NVDA treats the two as different add-ons, so remove neuralAccess before installing this one.
- Its commands are listed under "Neural DSP Plugins Accessibility" in NVDA's Input Gestures dialog.
- Stepping into and out of a plug-in is now NVDA+Shift+A, or NVDA+Shift+G with NVDA's laptop keyboard layout. It was NVDA+Shift+F, which is one of NVDA's own commands.
- Loading your own impulse response is now NVDA+Shift+E, pressed on a microphone selector. It was NVDA+Shift+I, which is one of NVDA's own commands.
- The add-on no longer has keys for reading out every knob, repeating the focused control, saying the amplifier model, the quick Lead toggle, the standalone's audio settings or the diagnostics report. The number keys 1 to 7 no longer have NVDA+Shift versions, and the plain ones stay.
- The add-on no longer saves pictures of the plug-in, either by itself when it lands on a control with no name or with NVDA+Shift+C. Both were for developing the add-on.
- The arrow keys do nothing on a button or switch inside the plug-in. In REAPER's FX window, Down Arrow on a button used to move focus out of the plug-in to REAPER's Add button.
- Comma and Period (previous and next preset) and the brackets (previous and next module) work with any keyboard layout. The brackets are the two keys to the right of P, whatever the layout types on them.
