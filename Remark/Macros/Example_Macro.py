# -*- coding: utf-8 -*-

# Description: Example macro

from MacroRegistry import registerMacro

class Example_Macro(object):
    def expand(self, parameter, remarkConverter):
        
        text = []
        text.append('')
        text.append('This')
        text.append('')
        text.append('[[Verbatim]]:')
        for line in parameter:
            text.append('\t' + line)
            print text[-1]
        text.append('produces this')
        text.append('')
        text += parameter
        text.append('')

        return text

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Example', Example_Macro())
