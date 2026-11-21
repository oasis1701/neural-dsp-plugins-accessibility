# Changelog

## 0.16.2 (2026-11-21)

- First support for the Archetype Cory Wong X. Its controls have the names its panels print, its switches and pedals say their positions, and the number keys, the brackets and Tab work in its six sections. Its three amplifiers, Funk, Clean and Snob, the cabinet selectors and the amp and cab link work as on the Nolly X, with A, C and Control+A.
- The Cory Wong X is drawn light where the other X plug-ins are dark, so the add-on reads its switches in its own way and checks the screen against the Cory Wong's own colours before saying a position.
- On the Cory Wong X, the Clean amplifier's power switch, the small amplifier's power switch in the Cab section and the tuner's mute button say no position. The delay's TIME R knob says "inactive" while the delay is on SINGLE.

## 0.15.3 (2026-11-21)

- First support for the Soldano SLO-100 X. Its controls have the names its panel prints, its switches and pedals say their positions on the amp's default Black look, and the number keys, the brackets and Tab work in its five sections. The amp's knobs say the figure their dial points at, from 0 to 11.
- In the Soldano's Amp section, the controls the chosen channel turns off say "inactive" after their name, and a switch says it after its position. On the OVERDRIVE channel these are Bright, Mode and the PREAMP and MASTER knobs marked NORMAL. On the NORMAL channel they are the PREAMP and MASTER knobs marked OVERDRIVE.
- Before it reads a switch's position off the screen, the add-on now checks that the screen shows the plug-in as expected. If it does not, for example with HDR on or another window over the plug-in, switches say their names without a position. This covers the Nolly X, the Fortin Nameless Suite X and the Soldano SLO-100 X. The Petrucci X is not covered yet. Switch positions are checked at the plug-ins' Medium size and larger. At Small, a few switches may say the wrong position.

## 0.14.2 (2026-11-20)

- First support for the Fortin Nameless Suite X. Its controls have names, its switches say their positions on the amp's Original look, and the number keys, the brackets and Tab work in its five sections.
- Choosing Enable MIDI Learn from a control's menu sometimes said nothing, because the menu closed before the add-on had noted the choice, and the control then did not say that it was waiting. It now says "MIDI learn on" in that case.

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
