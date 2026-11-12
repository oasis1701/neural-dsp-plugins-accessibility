# neuralAccess - the shared app module for every Neural DSP STANDALONE application.
#
# There is almost nothing here, and that is deliberate. Everything neuralAccess knows about the
# amplifiers lives in globalPlugins\neuralAccess\, and the overlay classes are put in front of
# their controls by the global plugin, which is called for every object in every process.
#
# That matters because the same editors are reachable two entirely different ways. A standalone
# is a process with an executable name, so an app module can be keyed to it. A VST3 plug-in is a
# DLL inside whatever host loaded it and has no executable of its own, so it cannot be - and
# keying an app module to reaper.exe would claim bare arrows, Tab, Enter and the space bar across
# the whole of REAPER. One body of knowledge, two doors into it, and the global plugin is the
# door that opens in both cases.
#
# The global plugin registers every standalone's executable spellings against this one module,
# so one file serves the Mesa Boogie, the Archetype Petrucci X, and whatever comes next.
#
# What is left here is the one thing a global plugin cannot do: isGoodUIAWindow is an app module
# hook, and it is how NVDA is told to use UI Automation for these applications' windows rather
# than working it out for itself. The plug-ins need no equivalent - their windows advertise a
# server side UIA provider, which is the test NVDA falls back on for a window class it does not
# recognise.

import appModuleHandler


class AppModule(appModuleHandler.AppModule):

    # These applications provide native UI Automation and nothing else, so always say yes.
    def isGoodUIAWindow(self, hwnd):
        return True
