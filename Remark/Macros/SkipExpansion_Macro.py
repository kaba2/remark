# Description: SkipExpansion_Macro class
# Detail: Copies the input to output and skips macro expansion.

from MacroRegistry import registerMacro

class SkipExpansion_Macro:
    def expand(self, parameter, document, documentTree, scope):
        return parameter

    def pureOutput(self):
        return True

registerMacro('SkipExpansion', SkipExpansion_Macro())
