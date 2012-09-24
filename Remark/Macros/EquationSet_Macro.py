# -*- coding: utf-8 -*-

# Description: EquationSet macro
# Detail: Presents multiple equations.

from MacroRegistry import registerMacro
from FileSystem import htmlDiv

class EquationSet_Macro(object):
    def name(self):
        return 'EquationSet'

    def expand(self, parameter, remark):
        text = []
        dependencySet = set()

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

        return text, dependencySet

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

    def findDependency(self, searchName, document, documentTree, parameter = ''):
        return None, True

registerMacro('EquationSet', EquationSet_Macro())



