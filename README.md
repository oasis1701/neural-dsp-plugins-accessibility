# Neural DSP Plugins Accessibility

This NVDA add-on makes Neural DSP guitar amplifier plug-ins usable with the NVDA screen reader. It works with the standalone applications and with the VST3 plug-ins inside a host such as REAPER. It covers three plug-ins.

- Archetype Petrucci X
- Archetype Nolly X
- Mesa Boogie Mark IIC+ Suite

The plug-ins report their controls to Windows but leave most of them without names, so a screen reader has little to say. The add-on names the controls, speaks knob values in their real units, reads switch positions off the screen, and lets you turn knobs with the arrow keys. It also adds keys for things a mouse user does at a glance. Those include switching sections, stepping through presets, running the tuner and checking input and output levels.

This is an early release. It has been tested with NVDA 2026.3.1 and with the plug-ins inside REAPER. The standalone applications use the same code as the plug-ins. The Mesa's and the Petrucci X's standalones were tried early on, before most of the recent work, and the Nolly X's has not been tried yet.

Only the X versions of the two Archetypes are covered. The add-on does not recognise the original Archetype: Petrucci or Archetype: Nolly and leaves them alone.

## Installing

Download the `.nvda-addon` file from the [Releases page](https://github.com/oasis1701/neural-dsp-plugins-accessibility/releases), open it, confirm the installation in NVDA, and restart NVDA when it asks.

## User guide

The full guide, with every key, is in [addon/doc/en/readme.md](addon/doc/en/readme.md). After installing, the add-on's Help action in NVDA's Add-on Store opens the same guide. Every command is listed under "Neural DSP Plugins Accessibility" in NVDA's Input Gestures dialog, where you can reassign it.

## Building from source

Run `build.ps1` in PowerShell from the repository folder. The package is written to the `dist` folder.

## License and trademarks

The add-on is released under the GNU General Public License, version 2. See [LICENSE](LICENSE).

This add-on is an independent project. It is not made by, affiliated with or endorsed by Neural DSP. Neural DSP and the other product names here are trademarks of their owners.
