# -*- coding: utf-8 -*-

# Description: Verbatim macro
# Detail: Reinterprets input as preformatted text.

from MacroRegistry import registerMacro

class Verbatim_Macro(object):
    def name(self):
        return 'Verbatim'

    def expand(self, parameter, remark):
        text = []
        dependencySet = set()

        for line in parameter:
            # Add a tab to each line.
            text.append('\t' + line)
        
        return text, dependencySet

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Verbatim', Verbatim_Macro())
