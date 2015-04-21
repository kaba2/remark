# -*- coding: utf-8 -*-

# Description: EquationSet macro
# Detail: Presents multiple equations.

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import markdownRegion

class EquationSet_Macro(object):
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
                equationText = remark.macro('Equation', [cleanLine])
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

registerMacro('EquationSet', EquationSet_Macro())



