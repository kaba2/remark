# -*- coding: utf-8 -*-

# Description: Html macro
# Detail: Copies the input to output and treats it as html.

from MacroRegistry import registerMacro

class Html_Macro(object):
    def name(self):
        return 'Html'

    def expand(self, parameter, remarkConverter):
        return parameter

    def outputType(self):
        return 'html'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Html', Html_Macro())
