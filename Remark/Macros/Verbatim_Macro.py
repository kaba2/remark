# -*- coding: utf-8 -*-

# Description: Verbatim macro
# Detail: Reinterprets input as preformatted text.

from MacroRegistry import registerMacro

class Verbatim_Macro(object):
    def name(self):
        return 'Verbatim'

    def expand(self, parameter, remark):
        text = []
        
        for line in parameter:
            text.append('\t' + line)
        
        return text

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Verbatim', Verbatim_Macro())
