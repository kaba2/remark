# -*- coding: utf-8 -*-

# Description: EquationSet macro
# Detail: Embeds each line into '' and a div-block.

from MacroRegistry import registerMacro

class EquationSet_Macro(object):
    def name(self):
        return 'EquationSet'

    def expand(self, parameter, remark):
        text = []
        dependencySet = set()

        for line in parameter:
            cleanLine = line.strip()
            if cleanLine != '':
                newText, ignore = remark.macro('Equation', [cleanLine]);
                text += newText

        return text, dependencySet

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('EquationSet', EquationSet_Macro())



