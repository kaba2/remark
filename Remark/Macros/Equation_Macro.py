# -*- coding: utf-8 -*-

# Description: Equation macro
# Detail: Embeds the parameter into '' and a div-block.

from MacroRegistry import registerMacro

class Equation_Macro(object):
    def __init__(self):
        self.equationNumber = 1

    def name(self):
        return 'Equation'

    def expand(self, parameter, remark):
        text = []
        dependencySet = set()

        text.append('<div class = "equation">')
        text.append('<span class = "equation-body">' + "''")
        text += parameter
        text.append("''" + '</span>')
        text.append('<span class = "equation-number">' + 
                    str(self.equationNumber) + 
                    '</span>')
        text.append('</div>')
        self.equationNumber += 1

        return text, dependencySet

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Equation', Equation_Macro())





