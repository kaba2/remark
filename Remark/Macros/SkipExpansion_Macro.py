# -*- coding: utf-8 -*-

# Description: SkipExpansion_Macro class
# Detail: Copies the input to output and skips macro expansion.

from MacroRegistry import registerMacro

class SkipExpansion_Macro:
    def expand(self, parameter, remarkConverter):
        return parameter

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        return []                

registerMacro('SkipExpansion', SkipExpansion_Macro())
