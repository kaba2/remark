# -*- coding: utf-8 -*-

# Description: Equation macro
# Detail: Presents mathematics.

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import markdownRegion

class Equation_Macro(object):
    def __init__(self, leftSymbol, rightSymbol):
        self.leftSymbol = leftSymbol
        self.rightSymbol = rightSymbol

    def name(self):
        return 'Equation'

    def expand(self, parameter, remark):
        text = parameter

        if len(text) >  0:
            text[0] = self.leftSymbol + text[0]
            text[-1] += self.rightSymbol

        return text

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Equation', Equation_Macro("''", "''"))
registerMacro('Equation_Latex', Equation_Macro('$', '$'))
registerMacro('Equation_Latex_D', Equation_Macro('$$', '$$'))
