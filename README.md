# Neural DSP Plugins Accessibility

This NVDA add-on makes two Neural DSP guitar plug-ins usable with a screen reader, the Archetype Petrucci X and the Archetype Nolly X. It names their controls, says knob values and switch positions, and adds single keys for things a mouse user does at a glance, such as switching sections, stepping through presets, running the tuner and checking levels.

For the best results, install the VST3 versions of the plug-ins and use them inside REAPER. That is where the add-on is tested. The standalone applications are still being worked on and tested.

This is an early release, tested with NVDA 2026.3.1.

## Installing

Download the `.nvda-addon` file from the [latest release](https://github.com/oasis1701/neural-dsp-plugins-accessibility/releases/latest), open it, confirm the installation in NVDA, and restart NVDA when it asks.

In REAPER, open the plug-in's FX window and press NVDA+Shift+A to step into the plug-in. Press it again to step back out.

## User guide

The [user guide](addon/doc/en/readme.md) lists every key. After installing, the add-on's Help action in NVDA's Add-on Store opens the same guide.

## Building from source

Run `build.ps1` in PowerShell from the repository folder. The package is written to the `dist` folder.

## License and trademarks

The add-on is released under the GNU General Public License, version 2. See [LICENSE](LICENSE).

This add-on is an independent project. It is not made by, affiliated with or endorsed by Neural DSP. Neural DSP and the other product names here are trademarks of their owners.
