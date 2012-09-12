# -*- coding: utf-8 -*-

# Description: Copy macro
# Detail: Copies the input to output.

from MacroRegistry import registerMacro

class Copy_Macro(object):
    def name(self):
        return 'Copy'

    def expand(self, parameter, remark):
        return parameter, set()

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Copy', Copy_Macro())
