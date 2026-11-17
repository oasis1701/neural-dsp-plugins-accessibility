# Changelog

## 0.13.10 (2026-11-16)

- Enter on a microphone's previous or next arrow in the Cab section now says the microphone it chose. Focus stays on the arrow, so you no longer need to Tab to the list to hear it. Press it several times quickly and only the last microphone is said.
- Quick Tab and Shift+Tab could go the wrong way, most often from a microphone list to that microphone's switch. Inside a section and along the top and bottom bars they now always go where they should.
- In the Petrucci X's Cab section, Tab now reaches each microphone's room distance buttons, Close, Mid and Far, which the plug-in leaves out of its own Tab order. Each says whether it is the chosen distance, and Enter on one chooses it.
- In the Petrucci X's Post FX section, with the delay's sync on free, Tab passes over the two time readouts above the delay's time knobs. They only show the times, which the knobs say too.

## 0.13.5 (2026-11-15)

Previous preset and Next preset are now in the Tab order, so M or the Applications key can open their right-click menu and assign them to a MIDI control. The plug-ins give neither arrow a Tab stop of its own.

- Tab from the preset display goes to Previous preset, then Next preset, then More preset actions. Shift+Tab goes back the same way.
- Enter on an arrow loads the previous or next preset and says its name, as Comma and Period do.

## 0.13.4 (2026-11-15)

The on/off switch of each pedal, effects unit, microphone, amplifier and EQ now comes first when you Tab through it. The plug-ins put most of these switches after the knobs.

- Tab reaches a module's switch before its knobs, and Shift+Tab from the first knob goes back to the switch.
- The brackets land on a module's switch, and the number keys land on the first switch of the section.
- In the Petrucci X's Pre FX section, Tab goes through the pedals from left to right, as the brackets do. It used to start on the Chorus pedal.
- In the Cab section, Tab and the brackets go to the left microphone, then the right microphone, then the amplifier. Tab used to start on the amplifier, and the brackets went left, amplifier, right.
- A microphone's Room switch stays where it was.
- The Volume section has no switch of its own and is unchanged.
- The number keys no longer say "decorative background" before the section's first control. It was heard most in the Cab and EQ sections.

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
