# -*- coding: utf-8 -*-

# Description: Example macro

from MacroRegistry import registerMacro

class Example_Macro(object):
    def name(self):
        return 'Example'

    def expand(self, parameter, remark):
        text = []
        
        text.append('')
        text.append('This')
        text.append('')
        text.append('[[Verbatim]]:')
        for line in parameter:
            text.append('\t' + line)
        text.append('produces this')
        text.append('')
        text += parameter
        text.append('')

        return text

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Example', Example_Macro())
