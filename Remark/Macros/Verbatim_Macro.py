# -*- coding: utf-8 -*-

# Description: Verbatim macro
# Detail: Reinterprets input as preformatted text.

from MacroRegistry import registerMacro

class Verbatim_Macro(object):
    def expand(self, parameter, remarkConverter):
        text = []
        
        for line in parameter:
            text.append('\t' + line)
        
        return text

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Verbatim', Verbatim_Macro())
