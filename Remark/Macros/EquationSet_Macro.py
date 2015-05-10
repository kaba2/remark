# -*- coding: utf-8 -*-

# Description: EquationSet macro
# Detail: Presents multiple equations.

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import markdownRegion

class EquationSet_Macro(object):
    def __init__(self, wrapMacro):
        self.wrapMacro = wrapMacro

    def name(self):
        return 'EquationSet'

    def expand(self, parameter, remark):
        text = []

        # Variables
        scope = remark.scopeStack.top()
        className = scope.getString('EquationSet.class_name', 'EquationSet')

        for line in parameter:
            cleanLine = line.strip()
            if cleanLine != '':
                # An ordered list of equations.
                equationText = remark.macro(self.wrapMacro, [cleanLine])
                if len(equationText) > 0:
                    equationText[0] = '1. ' + equationText[0]
                text += equationText

        text =  markdownRegion(text, {'class' : className})

        return text

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('EquationSet', EquationSet_Macro('Equation'))
registerMacro('EquationSet_Latex', EquationSet_Macro('Equation_Latex'))
registerMacro('EquationSet_Latex_D', EquationSet_Macro('Equation_Latex_D'))
