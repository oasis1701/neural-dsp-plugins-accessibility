# Neural DSP Plugins Accessibility

This NVDA add-on makes Neural DSP amplifiers usable without sight, both as standalone
applications and as **VST3 plug-ins** loaded into a host such as REAPER. It currently covers
three amplifiers:

- the **Mesa Boogie Mark IIC+ Suite**
- the **Archetype Petrucci X**
- the **Archetype Nolly X**, new in version 0.12.0

The same keys work in all three. Everything in "The commands" and "Getting keyboard focus in and
out" applies to every amplifier; each amp then has a section of its own for what makes it
special. The two Archetypes are built alike, so what the Petrucci X's section says about the
tuner, the MIDI mappings window, a control's own menu, typing an exact value, the level meters
and the presets holds for the Nolly X as well.

This add-on is an independent project. It is not made by, affiliated with or endorsed by Neural
DSP. Neural DSP and the other product names in this guide are trademarks of their owners.

## The commands

All of these work while a control inside an amplifier has focus. That scoping is deliberate: in a
host, none of the amplifier's keys are claimed while you are anywhere else, so your DAW and any
other accessibility add-ons keep every key they had. **NVDA+Shift+A** is the one exception and
works from anywhere, because it is how you step in. With NVDA's laptop keyboard layout the same
command is **NVDA+Shift+G**, because the laptop layout uses NVDA+Shift+A for say all with review.

- **Tab** and **Shift+Tab** — move between controls
- **Arrow keys** — adjust the focused knob; **Page Up/Down** larger steps; **Control+arrows**
  finest; **Home/End** minimum and maximum
- **Enter** — press the focused button or flip the focused switch. Buttons that ignore Enter
  (a few on the Mesa, every one of them on the Petrucci X) are clicked for you with a real
  mouse click, so they all behave the same from the keyboard
- **1** through **7** on the number row — show a section of the amplifier (the Petrucci X
  has seven, the Nolly X five, and the Mesa has five, which it calls views). A number past the
  last section says "Section not available". Focus then moves to that section's first control in Tab order, which says the
  section's name along with its own, for example "Pre FX section, Chorus rate" on the
  Petrucci X and "Amp view, Bright pull switch, pushed" on the Mesa. While a text box has
  focus, such as a knob's value box or the tuner's reference pitch, the number keys type
  into the box. Leave the box first
- **Shift+1** through **7** — say whether that section is switched on, on the Petrucci X and the
  Nolly X, for example "Pre FX section, on". Nothing is clicked and focus does not move. In a
  text box these keys type their character
- **Control+1** through **7** — switch that section off or on, on the Petrucci X and the Nolly X.
  NVDA says the
  new state, for example "Pre FX section, off", and you stay in the view and on the control you
  were on; see "Switching a whole section off or on" below
- **Enter** on a knob that has a value box (Petrucci X and Nolly X) — go into the box to type an exact
  value; see "Typing an exact value" below
- **A** — the next amplifier model. On the Petrucci X that is Piezo, Clean, Rhythm, Lead and
  round to Piezo again, on the Nolly X Clean, Crunch, Rhythm, Lead and round to Clean, and on
  the Mesa the Mark II C+ and the Mark II C++. It works in every
  view. In the Amp view focus lands on the new amp's first control, which says the amp's name
  first, for example "Lead amplifier, Gain". In any other view NVDA says "Lead amplifier" and
  focus stays where it was
- **C** — the next cabinet, on the Nolly X, going round like A. It does something only while the
  amplifier and cabinet are unlinked. While they are linked NVDA says "The cabinet follows the
  amplifier. Control+A unlinks them"; see "The amp and cab link" in the Nolly X's section
- **Control+A** — link or unlink the amplifier and the cabinet, on the Nolly X. NVDA says "Amp and
  cab unlinked. Rhythm cabinet" or "Amp and cab linked", and focus stays where it was. In a text
  box Control+A selects the text, as it does everywhere
- **T** — open or close the tuner. On the Petrucci X and the Nolly X the note you play and how
  far off it is are spoken while the string rings; see "The tuner" below
- **M** or the **Applications key** — open the menu of the control you are on, the one a mouse
  user gets with a right click, on the Petrucci X and the Nolly X. It holds Reset parameter and MIDI learn; see "A control's own
  menu" below
- **Control+M** — open or close the MIDI mappings window, on the Petrucci X and the Nolly X; see "The MIDI
  mappings window" below
- **L** — start a level check, on the Petrucci X and the Nolly X. Press L again to end it and hear what the
  input and output meters showed while you played, for example "Level check off. Input peak
  minus 9, average minus 15. Output peak minus 6, average minus 11"; see "The level meters"
  below
- **Comma** and **Period** — previous and next preset. On the Petrucci X and the Nolly X the
  preset you landed on is announced with its folder, for example "Preset John Petrucci, As I Am"
- **P** — move to the preset button and press it, which opens the list of presets
- **G** — switch the noise gate on or off from wherever you are. NVDA says "Gate, off" or
  "Gate, on" and focus stays where it was. The Mesa has a Gate knob and no gate switch, so
  there G moves to that knob
- **D** — switch the doubler on or off from wherever you are. NVDA says "Doubler, on" or
  "Doubler, off" and focus stays where it was
- **R** — move to the Transpose knob and stay there
- **Left bracket** and **Right bracket** — previous and next module of the view you are in;
  see "Moving between modules" below for the Petrucci X, and the Nolly X's and the Mesa's own
  sections for theirs
- **NVDA+Shift+A** — step keyboard focus into the amplifier, or back out to the host. With NVDA's
  laptop keyboard layout it is **NVDA+Shift+G**
- **NVDA+Shift+E** — load your own impulse response file, on a microphone selector in the
  Cab view of the Petrucci X or the Nolly X (see the Cab view below)

The single keys - A, C, T, L, M, comma, period, P, G, D, R and the brackets - need no NVDA key.
**In a text box they type**, like any key: a knob's value box, the delay's tempo box and the
tuner's reference pitch are text boxes. Leave the box, then press the key. The
brackets, comma and period work with the Persian keyboard layout active as well as the English
one. Every single key works on all three amplifiers except L and M, which the Mesa answers with
"Not available on this amplifier", and C and Control+A, which only the Nolly X has.

Every command appears under "Neural DSP Plugins Accessibility" in NVDA's Input Gestures dialog, so you can reassign
any of them.

## Getting keyboard focus in and out

Every Neural DSP amplifier takes keyboard focus without handing it to any control inside itself,
and its own Tab handling has nothing to move on from until something inside is focused.

In a **standalone**, the add-on puts focus on a real control whenever the window comes forward -
the first time you arrive it lands on the first view button, after that it returns to the control
you were last using. If focus is ever stranded, Tab steps in, and **NVDA+Shift+A** does the same
on demand.

In a **plug-in window**, press **NVDA+Shift+A** to step in, and **press it again to step back
out** to the host control you came from. This matters: the amplifier's Tab ring is cyclic and has
no way out of its own, so without the deliberate way back you would be stuck inside it. The
add-on never grabs focus by itself in a host - your DAW's own controls are somewhere you
legitimately want to be.

More than one instance is fine. Each amplifier window is tracked separately.

## The Archetype Petrucci X

The plugin has seven sections, each with a view of its own. Left to right they are **Wah Comp,
Pre FX, Amp, Cab, EQ, Volume, Post FX** (1 to 7 on the number row). After a switch, focus lands on the view's first
stop in the plugin's own Tab order, which says the section's name first, as in "Wah Comp
section, Wah pedal", and Tab carries on through the view from there. Until version 0.11.13 the
word was "view", as in "Wah Comp view". The plugin orders its
stops by height to the pixel before left to right, which is why Pre FX starts on the chorus
pedal rather than the overdrive. Pressing the key of the view you are already in moves focus
back to that first stop without clicking anything. Switching amplifiers with A while in the
Amp view lands on the new amp panel's first stop the same way. **With the Piezo amplifier selected the plugin has
no Cab and no EQ view** (a piezo pickup has no cabinet), so keys 4 and 5 say "No Cab section on the
Piezo amplifier" and do nothing; the other five keys work as usual. A double click on a section button switches that whole section off in this plugin, so
the add-on never clicks the same section button twice within a second, however fast the key is
pressed. The global controls above them are always present: Input, the Gate switch
and its threshold knob, Transpose, the Input mode switch (plug-in only), the preset controls, the
Doubler switch and its spread knob, and Output. Knob values are spoken with their real units -
decibels, semitones, milliseconds, hertz - taken live from the plugin's own displays.

- **Switching a whole section off or on.** Each of the seven is a section of the signal chain,
  and the plugin can take any of them out whole. **Shift+1** to **7** says which state a
  section is in, "Wah Comp section, on" or "Post FX section, off". **Control+1** to **7**
  switches it and says the new state in the same words. Neither key moves you. You stay in the
  view you were in, with focus on the control you were on. The state is read from the
  section's button at the top of the window, whose icon the plugin draws faintly while the
  section is off, so it can be read from any view, and with the MIDI mappings window open too.
  With the tuner or the MIDI mappings window open, Control+number asks you to close the window
  first. With the Piezo amplifier, 4 and 5 say "No Cab section on the Piezo amplifier" and the
  same for EQ. A mouse user switches a section with a double click on its button, and the first
  of those two clicks also shows that section's view. The add-on makes that double click for
  you. If it showed another view, the add-on clicks back to the view you were in and puts
  focus back, and nothing is said on the way. Let go of Control after the number, because the
  double click waits for the key to come up. Press Control+number once and wait for the
  answer, because a second press made before the answer is left out. If the section cannot be
  switched you hear "Could not switch the Wah Comp section". Version 0.11.14 took three
  seconds to answer and said the section's button first, as in "Amp section, button". Version
  0.11.15 leaves out the step that caused both. It answers in about 0.6 seconds from the
  section's own view and just under a second from another view.
- **The level meters.** The plugin has two meters, one beside the Input knob and one beside
  the Output knob. Each is a thin bar that rises with the signal, on a scale from minus 60
  decibels at the bottom to 0 at the top, with a red clip light above it that comes on when
  the signal reaches 0. The plugin gives a screen reader no number for them, so the add-on
  reads the bars off the screen. Press **L** and NVDA says "Level check on". Play for as long
  as you like, then press L again. NVDA says "Level check off" and then each meter's highest
  level and its average level in decibels, for example "Level check off. Input peak minus 9,
  average minus 15. Output peak minus 6, average minus 11". The numbers count down from the
  ceiling, so minus 9 means 9 decibels of room
  before clipping. The peak is the single loudest moment, which one pick scrape can set. The
  average is where the meter stood on average while sound was coming through, with the
  silences left out, and it says how hard the amplifier is being driven. A meter that never
  moved is reported as "Input, no signal", which tells you
  whether your guitar is reaching the plugin, and a meter whose clip light came on has
  "clipped" after its numbers. Nothing is said while you play except "Input clipping" or
  "Output clipping", when a clip light comes on, at most once in three seconds for each
  meter. A check has no time limit and runs until you press L again. The meters are read off
  the screen, so a check counts only what happens while the plugin's window is in front. As
  something to aim at, the plugin marks each meter at about minus 13.5 decibels, and users on
  Neural DSP's forum report input peaks around minus 12 as the level the plugins are built
  for. To match two presets in loudness, run a check on each and compare the output's average.
  The meters are watched only while a level check is on. During one the add-on reads a strip
  of the screen ten times a second, and each read holds NVDA for a few hundredths of a
  second, so end the check with L when you have your answer. With no check on, nothing is
  read and nothing is said about clipping. The numbers were checked with a steady test tone
  whose peak was at minus 20 decibels, which the level check read as "Input peak minus 20,
  average minus 20". "Clipping" is said when a bar reaches the very top of its scale, which
  was tried by turning an audio interface's input up until it clipped. The plugin's own red
  clip light has not been seen lit yet, and it does not stay on afterwards.
- **The loaded preset is announced with its folder.** The preset display reads "Preset",
  the folder and the name - "Preset John Petrucci, As I Am", "Preset Cory Wong, Church Tone" -
  with "modified" added when there are unsaved changes, and comma and period announce the
  preset you landed on the same way. The folder is the one the preset's file is in, so an
  artist's own name and never "Artists"; the Default preset has no folder. Two names exist in
  two folders each (Heavy Rhythm and Space Lead). Reached with comma or period they take the
  folder of the preset you came from; reached any other way both folders are said, "Preset
  Andy Sneap or Tim Henson (Polyphia), Space Lead", because the plugin shows only the name.
  Beside the display sit SAVE AS... and - for user presets - SAVE and DELETE.
- **The list of presets.** P moves to the preset display and presses it, from anywhere in the
  plugin; Enter on the display does the same. The plugin opens its own menu and NVDA says
  "Presets, menu" (the plugin calls the menu's window "Archetype Petrucci X, window"; the
  add-on renames it, and the Cab view's microphone lists say "Microphones, menu" the same
  way). The menu shows the folders
  first, and each folder opens to the right with its presets. Up and Down move, Right or
  Enter opens a folder, Left closes it, Enter on a preset loads it. When the menu closes,
  focus is put back on the preset display, which says the preset that is now loaded. Without
  that, Windows hands focus to the host's own window and you are outside the plugin.
- **The mouse pointer and menus.** The plugin treats a pointer that happens to lie over a
  menu as the mouse hovering there: the menu opened with that row already chosen and the
  first arrow key opened its folder. The add-on clicks with the real pointer and used to put
  it back where it rested afterwards. It no longer puts it back onto a menu its own click has
  just opened; in that case the pointer stays on the control that was clicked.
- **Moving between modules.** The right bracket moves to the next module of the view you are
  in and the left bracket to the previous one, round and round. Focus lands on the module's
  first control in Tab order, which says the module's name first, for example "Delay, Delay
  sync". The modules are: Wah and Compressor in Wah Comp; Overdrive, Phaser, Chorus and
  Flanger in Pre FX; Left microphone, Amplifier (the miniature amp row) and Right microphone
  in Cab; Chorus, Delay and Reverb in Post FX. Amp, EQ and Volume are one module each. The
  top bar counts as a module in every view and lands on GATE, so in a one-module view the
  brackets move between the view and the top bar. From the bottom of the window (the
  amplifier selectors, Tuner, MIDI) the right bracket goes to the top bar and the left one to
  the view's last module. While the tuner window is open the brackets say "Close the tuner
  first".
- **Gate and doubler from anywhere.** G and D click the switch and say its new state, "Gate,
  off", about three quarters of a second later, once the new position can be read off the
  screen. Focus stays on the control you were on. The plugin does move it to the switch for a
  moment when the switch is clicked; the add-on sends it straight back and says nothing about
  either move.
- **More preset actions.** Tab once past the preset display and you reach "More preset
  actions". The plugin gives this button no Tab stop of its own, so the add-on inserts one;
  Shift+Tab from the Doubler caption reaches it from the other side. Press Enter and the row
  changes into **IMPORT**, **RESET** and **LOCATE FILE**, and focus goes to IMPORT, the first
  of them; Tab walks on through the other two, then the preset display, then the More button
  again. Press Enter on the More button again to close the row and bring SAVE AS... back -
  Escape does not close it.
- **RESET asks before it acts.** RESET cannot be undone and the plugin asks nothing of its
  own, so the first Enter only tells you what the button would do - "RESET returns every
  parameter in the plugin to its default. Press Enter again to confirm." - and Enter on it
  again carries it out, then says "parameters reset". You have ten seconds for the second
  Enter, so there is time to hear the warning to the end. Tab away, press any other key, or
  let the ten seconds pass, and it is cancelled. Control, to silence the warning, does not
  cancel it.
- **DELETE asks with the plugin's own question.** DELETE is in the preset row while one of
  your own presets is loaded. Press Enter on it and the plugin opens its question, which the
  add-on reads out - "Are you sure you want to delete the preset 'My Sound'? This action is
  permanent." - and focus goes to **Cancel**. Tab says "Yes, delete, button", Tab again says
  "Cancel, button", and Enter presses the one you heard last. After Yes, delete you hear
  "Preset deleted." and land on the preset display, which says the preset that is loaded now.
  After Cancel you hear "Cancelled." and are back on DELETE. The plugin does not let keyboard
  focus rest on its Yes, delete button, so focus itself stays on Cancel the whole time and the
  add-on keeps track of your choice. Press any key other than Tab or Enter and the choice is
  Cancel again, so Enter never deletes unless "Yes, delete" was the last thing you heard.
- **Four amplifier models**: Piezo, Clean, Rhythm and Lead, as four radio buttons at the bottom
  of the window that announce which is live. They are there in every view, and A steps through
  them from any view; the amp panel's knobs rename themselves to match - each model has its
  own set.
- **Knobs say where their pointer points.** The amp panels, the pedals and the rack units print no
  numbers round their knobs, so a sighted player reads the pointer like the hand of a clock,
  and tutorials say "gain at 2 o'clock". Landing on such a knob you hear its value and then
  that position, for example "Gain, slider, 72 percent, 2 o'clock". While you turn it you hear
  the percent, and the position again only when the pointer reaches the next half hour, as in
  "75 percent, half past 2". The pointer travels from half past 7 at 0 percent, through 12
  o'clock at 50, to half past 4 at 100, so one hour is about 11 percent: 9 o'clock is 17
  percent, 10 is 28, 11 is 39, 1 is 61, 2 is 72 and 3 is 83. The position is the nearest half
  hour. The knobs that say it are the amp knobs, their miniature copy in the Cab view, every
  knob of the compressor and of the overdrive, phaser, chorus and flanger pedals, and on the
  rack units the chorus's three knobs, every knob of the delay except its two time knobs, and
  every knob of the reverb. A knob with a number shown beside it says that number and no
  position. The delay's low cut and high cut and the reverb's pre-delay are said in hertz and
  milliseconds with the position after, as in "Delay low cut, slider, 111 hertz, 10 o'clock".
  On those three the pointer does not move evenly with the number: it covers the low values
  quickly and the high ones slowly, so the delay's low cut is at 12 o'clock at about 266
  hertz of its 20 to 800.
- **Switch positions are announced**: the Input mode switch says mono or stereo, and the
  amp's power switch says amp on or amp off on all four amplifiers. Enter on the Input mode
  switch flips it. The words Stereo and Mono printed beside it are buttons for the same
  setting and stops in the plugin's Tab order; Tab passes over them.
- **GATE, DOUBLER, WAH and ROOM are switches themselves.** Each printed caption is a button
  that does exactly what the little rocker beside it does, so the caption is the one stop and
  says the state - "GATE, on", "Left room, off" - and Tab passes over the rocker.
- **The amp panels' small bat toggles** say their setting: Soar, Bright, Bite and Mid boost
  say on or off, and Air says Normal or Ultra, which is what the plugin itself calls its two
  positions. Which position is which comes from the plugin's own pictures of each switch.
- **Every effect has one on/off switch that says its state**, read from the effect's own lamp.
  In Wah Comp and Pre FX they are pedals - "Compressor pedal", "Overdrive pedal", "Phaser
  pedal", "Chorus pedal", "Flanger pedal" - and in Post FX they are rack units - "Chorus rack
  unit", "Delay rack unit", "Reverb rack unit" - so the two choruses cannot be mixed up. You
  hear the name and then the state, for example "Chorus rack unit, off". The EQ view's on/off
  switch is just "EQ".
- **The mode switches say their setting**: Chorus pedal mode (Normal or Tri), Phaser mode
  (Phase or Vibe), Chorus rack unit mode (Vintage or Spatial), Delay mode (Single or Dual) and
  Shimmer (on or off). Pressing Enter on any of these switches says the new setting.
- **Lamps and dimming layers are skipped.** The plugin puts the effects' lamps, the shading it
  draws over a switched-off section and a few on-lights into its Tab order, though none of
  them does anything. Tab and Shift+Tab pass straight over them, and switching views never
  lands on one.
- **Every button needs a real click**, and the add-on does the clicking whenever you press
  Enter. This is the plugin's own behaviour: it ignores both Enter and the standard
  accessibility action on every button it has.
- The **Cab view** has two microphone slots. Each side announces as Left or Right: the
  microphone combo box, previous and next microphone, the microphone switch (on or off),
  position, distance, mic level and pan knobs, the room module with its switch, level and CLOSE,
  MID and FAR distances, and phase (normal or inverted). A miniature copy of the amp knob row
  also lives in this view and is named like the real one, and its switches say their setting
  too: amp on or off, and Soar, Bright, Bite or Mid boost on or off.
- **Your own impulse responses**: on either microphone selector, press **NVDA+Shift+E** and
  let go of the keys. The add-on opens the microphone list and presses its LOAD button, which
  the plugin offers only to the mouse. A standard Windows file dialog titled "Select IR" opens,
  and you pick the file there as in any other program. Enter on the selector opens the list
  yourself; the arrow keys there walk the six built-in microphones only. NVDA+Shift+E works on the
  selector and not inside the open list, so close the list first. On any other control it says
  "Go to the left or right microphone selector in the Cab view first."
- The **EQ view** is a four band semi-parametric equaliser per amplifier: frequency and gain
  knobs per band with gains in decibels, plus high-pass and low-pass filters in hertz.
- The **Post FX view** holds the chorus, delay and reverb rack units, including the delay's sync
  selector (free, DAW sync, tap sync), single or dual mode, and the reverb's shimmer.
- **The delay changes with its sync selector.** Set to free, it has "Delay time left" and
  "Delay time right" in milliseconds. Set to DAW sync or tap sync, the same two knobs choose a
  note value instead and are called "Delay note left" and "Delay note right", spoken as
  "quarter note", "dotted eighth note", "eighth note triplet" and so on, and a "Delay tempo"
  control in beats per minute appears. Most of the presets that ship with the plug-in have the
  delay synced.
- **Tap tempo** is a stop only while Delay sync is on tap sync, because the plugin offers the
  button only then. Enter presses it once per tap. The stop after it, "Tap tempo light", is
  the delay's blinking tempo light and is there in every sync setting.
- In the **standalone**, the utility bar adds TAP, a Tempo slider in beats per minute, the
  metronome and its play button, and SETTINGS, which Enter opens. The audio
  device, sample rate, buffer size and channel lists live there, along with the MIDI input
  device list. The stereo/mono Input mode switch exists only in the plug-in, where a stereo
  input is possible.

### The tuner

The Petrucci X has a chromatic tuner, and it talks. Open it with **T**, or Tab to
**Tuner** (straight after the Input mode switch) and press Enter. Focus lands on the tuner window,
announced as "Tuner, sound muted while tuning" - the plugin silences your guitar while the
tuner is open, so that is why it goes quiet.

- **Play a string** and NVDA says the note and how far off it is: "E, 12 cents flat". While the
  note rings you hear short updates about once a second as you turn the peg - "8 flat",
  "3 flat" - and **"in tune"** the moment the plugin's own in-tune lights come on, which is
  within 2 cents. A steady string goes quiet rather than repeating itself. Let the string stop
  and pluck again, and the note is announced in full again.
- Nothing is spoken while you are in another window, so leaving the tuner open does not follow
  you around.
- **Tab inside the window** reaches: **Mute while tuning** (says muted or not muted - turn it
  off to hear your guitar while you tune), **Close tuner**, **Cents** and **Hertz** (radio
  buttons; in Hertz mode you hear the frequency instead, such as "E, 329.6 hertz"), **Reference
  pitch** (420 to 460 hertz, adjusted with the arrows; 440 is standard), its text box, and the
  **Live tuner switch** with its label. The plugin leaves Close, Cents and Hertz out of its own
  Tab order; the add-on puts them back.
- **Close it** with Enter on Close tuner, or T again (not while you are in the reference
  pitch's text box, where T types). Focus goes to the Tuner button and NVDA says "Tuner
  closed, Tuner". The plugin itself would leave you on MIDI.
- **The Live Tuner** is the plugin's small always-on tuner in the bottom bar. It shows only the
  note, not how far off it is, so the tuner window is the one to tune with. When it is on, the
  Tuner button says so and includes the note that is ringing, for example "Tuner, live tuner
  on, E".

### The MIDI mappings window

The MIDI button in the bottom bar opens a window where a MIDI controller's knobs, switches and
program changes are tied to the plugin's controls and presets. Open it with **Control+M**, or
Tab to MIDI and press Enter. Focus lands on the list, which says how many mappings there are, for
example "MIDI mappings, no mappings".

- Tab and Shift+Tab go round the window's own parts and stay inside it. The order is the list,
  each mapping's controls, New MIDI Mapping, MIDI mapping options, Close MIDI mappings. The
  view behind the window is dimmed and takes no clicks while the window is open.
- **Enter on New MIDI Mapping** adds a mapping and moves focus to its first control.
- A mapping is one row. Its controls are named with the mapping's number and the column they
  stand under, for example "Mapping 1, Type, CC Absolute". The columns are Type,
  Parameter/Preset, Channel, two called Note/CC/PC, and Value. Enter on a list opens it, and
  when you have chosen, focus comes back to the list and it says the new choice.
- A row starts with the mapping's own switch, which says "Mapping 1, on" or "Mapping 1, off",
  and ends with "Delete mapping 1". Enter on the switch changes it and says the new state.
  **A mapping that is off has no lists.** The plugin takes them away until the mapping is
  switched on again, so Tab goes from its switch straight to its delete button.
- Enter on a delete button removes the mapping at once. The plugin does not ask first.
- To close the window press **Control+M** again, or Enter on Close MIDI mappings. Focus goes back to
  the MIDI button and NVDA says "MIDI mappings closed, MIDI". While the window is open the
  bracket keys ask you to close it first.

The names of a mapping's controls have been heard for one kind of mapping, CC Absolute, which
has a single Note/CC/PC list and no Value. Other kinds show a second Note/CC/PC list or a Value
box. Those two are named from the plugin's layout files and have not been seen on screen.

### A control's own menu

Every knob and switch has a small menu that a mouse user opens with a right click. Press **M**
or the **Applications key** on the control to open it. NVDA reads the menu as the plugin presents it. Use the arrow keys
and Enter, or Escape to leave without choosing. When the menu closes, focus goes back to the
control you were on, which says its name and its value again.

The menu holds these items.

- A first line naming the control, for example "Parameter: Rhythm Amp Gain". NVDA says it
  as the menu's name when the menu opens.
- Reset parameter, which puts that one control back to its default. Back on the control you
  hear the new value.
- Enable MIDI Learn. After it the plugin waits for the next message from a MIDI controller
  and ties that knob, switch or pedal to the control, without a visit to the MIDI mappings
  window. While it waits, the item reads Disable MIDI Learn, and choosing that stops the
  waiting. Press M on the control again to find out which of the two it is.
- Show MIDI Map, which opens the MIDI mappings window and leaves you on its list.

When you choose Enable MIDI Learn, the control says so after its name for as long as the
plugin waits: "Gain, MIDI learn on". You hear it as focus comes back, and again whenever you
Tab to that control. When you choose Disable MIDI Learn, NVDA says "MIDI learn off" in front
of the name once. Both are read from what the plugin draws, which is a veil over the control
while it waits.

When a message arrives from the controller, the plugin learns it and takes the veil away, and
NVDA says "MIDI learned". The control then follows the controller, and the new mapping is in
the MIDI mappings window. This was tried with control messages sent by a test effect inside
REAPER, not with a hardware controller. The control is not watched while another window is in
front, while a menu, the tuner or the MIDI mappings window is open, or after you leave the
view. Going to another effect in REAPER's FX window and back also ends the watch, and after
that the menu item is the only sign of whether learn is still waiting.

If the control has no menu, NVDA says "No menu opened." In a text box M types, as every
single key does.

### Typing an exact value

Many knobs on the Petrucci X have a small display beside them showing the value: the five in
the top bar, the two filters in the EQ view, the microphone knobs in the Cab view and others.
Each display is a text box, and the plugin puts every one of them in its Tab order. They say
the same thing as their knob, so Tab and Shift+Tab pass over them.

To type a value instead of stepping to it, press **Enter on the knob**. Focus goes into its
box - "Input readout, edit, selected 0.0 dB" - with the old value selected, so what you type
replaces it. Press **Enter** again and the plugin takes the value; focus returns to the knob,
which says the value it now has. Tab leaves the box without going back to the knob. A knob
with no display, such as a percentage knob on a pedal, does nothing new on Enter.

The delay's tempo box is the exception: it only exists once Tab has landed on it, so Tab
still stops there.

### What Tab reaches, and what only the commands reach

The plugin's own Tab ring is 32 stops and leaves several things out entirely. Tab covers the
global bar - the gate and doubler captions and their switches, SAVE AS..., the preset display,
the five knobs, the input mode switch - then MIDI, the developed-by strip, the resize button,
and the whole of the live amp's panel. The knobs' value boxes are in the plugin's ring too and
Tab passes over them, as it does over the top bar's background, which the plugin puts between a
view's last control and GATE. The add-on adds stops of its own: More preset actions, the Tuner button
between the Input mode switch and MIDI, and inside the tuner window the Close, Cents and Hertz
buttons. The top bar's order is therefore: the five knobs, the Input mode switch, Tuner, MIDI.

**Not in the Tab ring at all**, so the commands are the only keyboard route: the seven section
buttons (1 to 7), the four amplifier selectors (A),
the previous and next preset arrows (comma and period), and the two level meters (L starts
and ends a level check).

Known limitations on the Petrucci X:

- Inside the plugin's list of presets the add-on adds nothing: NVDA reads the menu as the
  plugin presents it, and the single keys do not act there.
- The delay's Tap Tempo button can only be reached with Delay sync on tap sync. Tapping a
  tempo with Enter has not been tried by ear yet.
- The switches inside a section that is off have not been checked. The plugin draws shading
  over such a section, and a switch read through the shading may say the wrong state.
- Landing in a section with its number key does not say whether the section is off. Shift
  and the same number does.
- With the MIDI mappings window open, the single keys still act on the view behind it, which
  takes no clicks then. Close the window first, with Control+M.
- The channel list ticks in the standalone's audio settings use the Mesa calibration and have
  not been separately verified on this plugin.

## The Archetype Nolly X

The plugin has five sections, each with a view of its own. Left to right they are **Pre
Effects, Amp, Cab, EQ, Post Effects** (1 to 5 on the number row; 6 and 7 say "Section not
available"). After a switch, focus lands on the view's first stop in the plugin's own Tab
order, which says the section's name first, as in "Pre Effects section, Compression". The top
bar is the Petrucci X's: Input, the Gate switch and its threshold knob, Transpose, the Input
mode switch (plug-in only), the preset controls, the Doubler switch and its spread knob, and
Output, with a level meter at each end.

Support for this plugin is new in 0.12.0. It was built from the plugin's own layout and
pictures and from one run through every section on every amplifier, and it has passed an
offline check of 569 points, but nobody had used it by ear when this was written. See "What
has not been tried yet" at the end of this section.

Everything the Petrucci X's section says under these headings works the same way here: the
level meters and the L key, switching a whole section off or on with Shift and Control and a
number, the preset display and the list of presets, the tuner, the MIDI mappings window, a
control's own menu, and typing an exact value.

- **The four amplifiers.** Clean, Crunch, Rhythm and Lead, chosen with **A**. Clean has Gain,
  Bass, Middle, Treble, Master and Amp output, and a Bright switch. Crunch has Gain, Bass, Mid,
  Treble, Presence, Depth, Master and Amp output, and a Bright switch. Rhythm has Gain, Bass,
  Mid, Treble, Resonance, Presence, Master and Amp output. Lead has Gain, Bass, Middle, Treble,
  Master and Amp output. The amp's own output knob is called Amp output so that it cannot be
  mistaken for Output in the top bar. Each knob says its value in percent and where its
  pointer points, as on the Petrucci X. The Crunch and Rhythm panels print a scale from 0 to
  10 round their knobs, and a tenth of the percentage is the number on that scale, so 70
  percent is 7. The red power switch at the right of each panel says "amp on" or "amp off",
  and the Bright switch "on" or "off".
- **The amp and cab link.** At the bottom of the window the plugin has four selectors, one for
  each amplifier with its own cabinet, and a small link button to their left. While the link is
  on, choosing an amplifier brings its cabinet with it. **Control+A** switches the link off, and
  the plugin then shows a row of four amplifiers over a row of four cabinets, so that any
  amplifier can play through any cabinet. **A** goes round the amplifiers as before and **C**
  goes round the cabinets, each saying what it chose, "Lead amplifier" or "Crunch cabinet", and
  leaving focus where it was. Control+A again links them, and NVDA says "Amp and cab linked".
  One thing to know. Unlinking does not keep the cabinet you were hearing. The plugin goes to
  the cabinet that was last chosen by itself, which is why Control+A says it, as in "Amp and
  cab unlinked. Rhythm cabinet". On the Petrucci X the selectors are not in the Tab order, and
  if that holds here these three keys are how you reach them. If you do land on one, the
  selectors read as radio buttons, "Clean amplifier" or "Rhythm cabinet", and the link button
  says "Amp and cab link, linked" or "unlinked".
- **Pre Effects.** Four pedals, left to right. The **Compressor** has Compression, Compressor
  level and Compressor attack, a switch that says "Smooth" or "Snappy". **Overdrive 1** has
  drive, level and tone, and a bright switch that says "on" or "off". **Delay 1** has mix,
  feedback, time and tone, and a sync switch that says "note" or "milliseconds". On "note" the
  delay follows the tempo, the time knob becomes Delay 1 note, and its values are note lengths
  such as "eighth note". **Overdrive 2** has gain, level, bass and treble. Each pedal's stomp is
  called by the pedal's name, "Compressor pedal", "Overdrive 1 pedal" and so on. It says "on"
  or "off", read from the pedal's lamp, and Enter presses it.
- **Post Effects.** **Delay 2** has a sync selector with three positions, "free", "DAW sync"
  and "tap sync", a ping pong switch, mix, feedback, low cut, time, mod and high cut. With
  sync on DAW or tap the time knob becomes Delay 2 note, and Delay 2 tempo is said in beats
  per minute. The cuts are said in hertz. **Reverb** has mix, decay, low cut and high cut, with
  the decay said in seconds. Their stomps are Delay 2 pedal and Reverb pedal.
- **EQ.** A graphic equaliser with nine bands, named by the frequencies printed under them,
  which change with the voicing: "Band 75 hertz" to "Band 12 kilohertz" on Nolly's mod, "Band
  65 hertz" to "Band 16 kilohertz" on Original. Each says its gain in decibels, from minus 12
  to 12. At the ends are
  a High pass filter and a Low pass filter, which say "OFF" at the end of their travel where
  they do nothing. EQ voicing is a switch between the "Original" voicing and "Nolly's mod".
  Enter on it changes to the other voicing and says which one is on.
  EQ power switches the equaliser on or off. Each amplifier has its own equaliser settings.
- **Cab.** Two microphones, left and right, laid out as on the Petrucci X. Each side has
  previous and next microphone buttons, the microphone list, a microphone switch that says
  "on" or "off", position, distance, mic level and pan knobs, a room send switch with its
  level knob, and a phase button that says "normal" or "inverted". In the middle is a small
  copy of the amplifier's own knobs. **NVDA+Shift+E** on a microphone selector loads your own
  impulse response file, as on the Petrucci X.
- **Moving between modules.** The brackets step through the top bar and then the modules of
  the section you are in. In Pre Effects those are Compressor, Overdrive 1, Delay 1 and
  Overdrive 2. In Post Effects, Delay 2 and Reverb. In Cab, Left microphone, Amplifier and
  Right microphone. The Amp and EQ sections are one module each.
- **What Tab passes over.** The pedals' lamps, the little rockers beside GATE, DOUBLER and ROOM
  SEND (the caption is the switch and says the state), the value boxes under knobs, the
  delays' note displays, the two captions beside the EQ voicing switch, the EQ's HPF and LPF
  captions and the frequency printed under each band, and backgrounds, the top bar's
  included, so Tab goes from a section's last control straight to GATE. None of them does
  anything that the control beside it does not. In the EQ, Tab goes from EQ voicing straight
  to the first band, and from EQ power straight to the top bar.
- **What has not been tried yet.** Every switch reading was worked out from the plugin's own
  two pictures of that switch, and matched the real screen in the one position the switch
  happened to be in. The other position has not been seen on screen for any of them. The
  readings most likely to say nothing at another window size are the four small toggles on
  the pedals (Compressor attack, Overdrive 1 bright, Delay 1 sync and Delay 2 ping pong). If a
  switch says the wrong word or no word, NVDA's log has the figures it read. Also not yet seen
  on this plugin are the tuner, the MIDI mappings window, the list of presets, a microphone
  list, either delay with its sync off, the Tap tempo button, and the standalone application.
  All of those run on the same code as the Petrucci X's.

## The Mesa Boogie Mark IIC+ Suite

Five views: **Pedals, Amp, Cab, EQ, Post FX** (1 to 5 on the number row). Everything below is specific
to this amplifier.

The plugin reports all of its controls to the accessibility system, but leaves each control's
name blank with the label hidden in a field screen readers do not announce; the add-on promotes
those labels to names. Knob values are spoken in useful units, amp knobs on the amp's own 0 to
10 dial scale.

- **The view keys open the view and land on it.** The plugin's five view buttons open their
  view only on a mouse click, so 1 to 5 click the button for you. After the click, focus goes
  to the view's first control in the plugin's Tab order, which says the view's name first,
  for example "Amp view, Bright pull switch, pushed". Tab carries on through the view from
  there. Pressing the key of the view you are already in goes back to that first control
  without clicking anything. If the add-on cannot tell that the view has opened, focus stays
  on the view's button and you hear the view's name.
- **Each view is a section that can be switched off whole.** Pedals, Amp, Cab, EQ and Post FX
  are five sections of the signal chain, and the plugin can take any of them out. A section
  that is off does nothing to the sound, whatever its own switches say. The add-on tells you
  when one is off. Its view button says "EQ view, section off", and landing in its view says
  "EQ view, section off" before the first control. A section that is on adds nothing to what
  you hear. **To switch a section on or off, Tab to its view button and press Enter.** That
  is the plugin's own key for it, and the add-on then says "EQ section, on" or "EQ section,
  off". The view buttons are in the Tab order after the top bar's value boxes.
- **Before version 0.11.1 the view keys switched sections off by mistake.** They sent Enter to
  the view button, which never showed the view and switched its section instead, off on one
  press and on again on the next. If the Mesa has sounded wrong since you started using this
  add-on, with no cabinet, no effects or no EQ, this is the likely reason. Go round the five
  view buttons once with Tab and switch on any that say "section off".
- **Moving between modules.** The right bracket moves to the next module of the view you are
  in and the left bracket to the previous one, round and round. Focus lands on the module's
  first named control, and the module's name is said first unless the control's own name
  already starts with it. The modules are the Compressor, Overdrive 1, Overdrive 2 and Chorus
  pedals in Pedals, the Left microphone, the Amplifier (the miniature amp) and the Right
  microphone in Cab, and the Delay and the Reverb in Post FX. Amp and EQ are one module each.
  The top bar counts as a module in every view and lands on Input. From the bottom of the
  window (the amp and cab selectors, MIDI, Tuner) the right bracket goes to the top bar and
  the left one to the view's last module.
- **A switches between the two amplifiers**, the Mark II C+ and the Mark II C++, from any
  view. NVDA says "Mark II C++ amplifier" and focus stays where it was. In the Amp view, and
  on the miniature amp in the Cab view, the knob you were on belongs to the old amplifier, so
  focus goes to the view's first control, which says the amplifier's name first.
- **D switches the doubler** and says "Doubler, on" or "Doubler, off". Focus does not move.
- **G moves to the Gate knob**, because this amplifier has no gate switch. **R** moves to
  Transpose.
- **P opens the preset menu.** It moves to the Preset menu display and clicks it. The menu is
  the plugin's own, and NVDA reads it as a menu. If focus is outside the plugin when the menu
  closes, the add-on puts it back on the Preset menu display.

- **Switch positions are announced**: the pull switches say "pulled" or "pushed" (the amp's own
  words - pulled means engaged), the amp on/off switch says "amp on" or "amp off", and Amp Type
  and Cab Type are radio buttons. Pressing Enter on a switch speaks its new position once the
  plugin repaints. If the window is minimised or covered a position cannot be read, and the
  add-on stays silent rather than guessing.
- **The pedals, the EQ and the Cab view say their switches too.** A pedal's footswitch is
  called by the pedal's name and says on or off, read from the pedal's lamp, for example
  "Compressor pedal, off". That covers the Compressor, Overdrive 1, Overdrive 2 and Chorus
  pedals, the Delay and Reverb pedals in Post FX, and the EQ. The small lever switches say
  the word printed on the side the lever points to. Compressor attack says slow or fast,
  Delay mode says single or dual, and Delay time type says milliseconds or note. The
  Overdrive 2 peak switch has two signs printed beside it and no words, so it says left or
  right. In the Cab view each microphone says on or off, its phase says normal or inverted,
  and its room says on or off.
- **Enter on those switches is a click.** The plugin ignores Enter on every button of the
  Pedals, Cab, EQ and Post FX views and Windows rings its error sound. The add-on clicks the
  button for you and says the new state once the plugin has redrawn it.
- The two levers marked STANDBY and POWER are **one parameter, not two**: the plugin wires both
  to the single switch that takes the whole amp block in and out. They announce as "Amp on off
  switch, standby lever" and "... power lever".
- The **preset controls** are the Preset menu display (Enter opens the plugin's preset menu),
  Save, Import, Open presets folder, and Previous and Next. The loaded preset's name is not
  exposed by this plugin at all, so preset changes are made blind. A Delete button appears only
  for deletable presets; Enter on it warns first and needs a second Enter within ten seconds to
  confirm, because this amplifier cannot even tell you which preset you would be deleting.
- Two stops in the top bar announce as **decorative divider** - real buttons in the plugin's Tab
  order that do nothing at all. They are named so you know you have not missed anything.
- The **audio settings** (standalone only). Tab to the audio settings button and press Enter to
  open them. Enter on that button again closes them, and Escape does not. Whether Tab still
  reaches the button while the settings are open has not been tried. Focus lands on the device type, and Tab moves through the devices, the Test tone
  button, the input and output channel lists, sample rate and buffer size. In the channel lists
  the arrows move between channels, Space or Enter toggles a channel and announces "ticked" or
  "not ticked" with its position, and Tab leaves the list. Channel names are read with Windows
  character recognition and can be imperfect ("Anelogue 2"); the row position is always exact.
  The plugin refuses to switch off the last channel still on - the add-on says so.
- Not named yet: in the Cab view the microphone selector, its two arrows and two dividers, and
  in the top bar the five value boxes, all of which are Tab stops. The EQ view's nine band
  sliders and the amp's five have no value and cannot be adjusted from the keyboard yet.
- Known limitations: the loaded preset's name cannot be announced; the five graphic EQ band
  sliders announce their frequency but report no value and cannot be adjusted from the keyboard
  yet; the level meters and the resize button have no Tab stop of their own; when the lead
  channel is off, the four lead-only controls genuinely leave the Tab order - pull the Lead
  switch and they return.

## Why these plugins seemed completely inaccessible

They are not as closed as they appear. Both generations expose a full accessibility tree and
move focus with Tab; the Mesa generation merely leaves names in the wrong field, and the X
generation names some controls, hides others' labels, and leaves its knobs anonymous - while its
buttons only respond to genuine mouse clicks. The add-on fills exactly those gaps: names,
values in real units, switch positions read from the screen where nothing else exposes them, and
keyboard adjustment for the knobs.
