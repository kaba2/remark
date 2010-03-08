# -*- coding: utf-8 -*-

# Description: Copy_Macro class
# Detail: Copies the input to output.

from MacroRegistry import registerMacro

class Copy_Macro:
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
