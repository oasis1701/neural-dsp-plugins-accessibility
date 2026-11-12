# Neural DSP Plugins Accessibility

This NVDA add-on makes two Neural DSP guitar plug-ins usable with a screen reader, the Archetype Petrucci X and the Archetype Nolly X. It names their controls, says knob values and switch positions, and adds keys for things a mouse user does at a glance.

For the best results, install the VST3 versions of the plug-ins and use them inside REAPER. That is where the add-on is tested. The standalone applications are still being worked on and tested.

This add-on is an independent project. It is not made by, affiliated with or endorsed by Neural DSP. Neural DSP and the other product names in this guide are trademarks of their owners.

## Stepping in and out

In REAPER, open the plug-in's FX window and press **NVDA+Shift+A** to move into the plug-in. Press it again to go back to the REAPER control you came from. With NVDA's laptop keyboard layout the key is **NVDA+Shift+G**. This is the only key that works outside the plug-in.

Tab goes round in a circle inside the plug-in and never leaves it, so NVDA+Shift+A is how you leave. The arrow keys do nothing on buttons and switches, so they cannot drop you out into REAPER's FX window either.

## The signal chain

Your guitar goes through the plug-in's sections from left to right, and the number keys follow the same order. Any section can be switched off whole, and the sound then skips it. The top bar is not a section. It is there in every view and holds Input, the noise gate, Transpose, the presets, the doubler and Output.

The Petrucci X has seven sections.

- **1, Wah Comp.** A wah pedal and a compressor.
- **2, Pre FX.** Overdrive, phaser, chorus and flanger pedals.
- **3, Amp.** Four amplifiers, Piezo, Clean, Rhythm and Lead.
- **4, Cab.** Two microphones, each with its own room. Includes a custom IR loader for both. The Piezo amplifier has no Cab section.
- **5, EQ.** A four-band equaliser with high-pass and low-pass filters. The Piezo amplifier has no EQ section.
- **6, Volume.** A volume pedal.
- **7, Post FX.** Chorus, delay and reverb rack-mounted units.

The Nolly X has five sections.

- **1, Pre Effects.** Compressor, Overdrive 1, Delay 1 and Overdrive 2 pedals.
- **2, Amp.** Four amplifiers, Clean, Crunch, Rhythm and Lead.
- **3, Cab.** Two microphones, each with a room send. Includes a custom IR loader for both.
- **4, EQ.** A nine-band graphic equaliser with two voicings, Original and Nolly's mod, and high-pass and low-pass filters.
- **5, Post Effects.** Delay 2 and reverb pedals.

On the Nolly X the amplifier and the cabinet are linked, so choosing an amplifier brings its own cabinet. Unlink them with Control+A to pair any amplifier with any cabinet.

## Keys

All of these keys work while you are inside the plug-in.

### Moving around

- **Tab** and **Shift+Tab** move to the next and previous control.
- **1** to **7** go to a section, and focus lands on its first control. The Nolly X uses 1 to 5.
- **Left Bracket** and **Right Bracket** move to the previous and next module of the section, such as a pedal, an effects unit, a microphone or the top bar.
- **R** moves to the Transpose knob.
- **P** moves to the preset display and opens the list of presets.

### Knobs and switches

- **Up Arrow** and **Right Arrow** turn the focused knob up, and **Down Arrow** and **Left Arrow** turn it down.
- **Page Up** and **Page Down** turn it in bigger steps, and **Control** with an arrow in the smallest steps.
- **Home** and **End** set it to its minimum and maximum.
- **Enter** presses a button or flips a switch. A switch then says its new position.
- **Enter** on a knob that has a value box takes you into the box. Type a value and press Enter to set it.
- **M** or the **Applications key** opens the focused control's own menu, with Reset parameter and MIDI Learn.

A knob says its value. Knobs with no printed numbers also say where their pointer points, such as "2 o'clock".

### Sections

- **Shift** with a section's number says whether that section is on or off.
- **Control** with a section's number switches that section off or on. You stay where you are.

### Amplifiers and presets

- **A** selects the next amplifier, going round.
- **C** selects the next cabinet, going round, on the Nolly X while the amp and cab are unlinked.
- **Control+A** links or unlinks the amplifier and the cabinet, on the Nolly X.
- **Comma** and **Period** load the previous and next preset and say its name.
- In the list of presets, Up and Down move, Right or Enter opens a folder, Left closes it, and Enter on a preset loads it.

RESET, one of the More preset actions, asks you to press Enter a second time before it acts. DELETE asks with the plug-in's own question, with Cancel chosen first.

### Gate and doubler

- **G** switches the noise gate on or off.
- **D** switches the doubler on or off.

Both say the new state, and focus stays where it was.

### Tools

- **T** opens or closes the tuner. Play a string and NVDA says the note and how far off it is, and "in tune" within 2 cents. The plug-in mutes your guitar while the tuner is open. Tab to "Mute while tuning" to change that.
- **L** starts a level check. Play, then press L again to hear the peak and average level of the input and output, in decibels. A common target is an input peak of about minus 12.
- **Control+M** opens or closes the MIDI mappings window.
- **NVDA+Shift+E** on a microphone selector in the Cab section loads your own impulse response file. A Windows file dialog opens, where you choose the file.

## Good to know

- In a text box, such as a knob's value box or the tuner's reference pitch, the single letter and number keys type. Tab out of the box first, then press the key.
- Comma, Period and the brackets work with any keyboard layout. If your layout types something else on the bracket keys, they are still the two keys to the right of P.
- Every command is listed under "Neural DSP Plugins Accessibility" in NVDA's Input Gestures dialog, where you can change its key.
