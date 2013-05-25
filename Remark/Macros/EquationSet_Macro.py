# -*- coding: utf-8 -*-

# Description: EquationSet macro
# Detail: Presents multiple equations.

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import htmlDiv

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
                text.append(' 1. [[Equation]]: ' + cleanLine);

        text = htmlDiv(text, className)

        text.append('')
        text.append('<div class = "remark-end-list"></div>')
        text.append('')

        return text

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('EquationSet', EquationSet_Macro())



