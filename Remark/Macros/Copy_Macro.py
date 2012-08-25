# -*- coding: utf-8 -*-

# Description: Copy macro
# Detail: Copies the input to output.

from MacroRegistry import registerMacro

class Copy_Macro(object):
    def name(self):
        return 'Copy'

    def expand(self, parameter, remarkConverter):
        return parameter

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Copy', Copy_Macro())
