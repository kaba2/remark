# -*- coding: utf-8 -*-

# Description: Example macro

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import htmlDiv

class Example_Macro(object):
    def name(self):
        return 'Example'

    def expand(self, parameter, remark):
        scope = remark.scopeStack.top()

        className = scope.getString('Example.class_name', 'Example')

        text = []

        text.append('')
        text.append('[[Verbatim]]:')
        for line in parameter:
            text.append('\t' + line)
        text.append('')
        text += htmlDiv(parameter, className)
        text.append('')

        return text;

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Example', Example_Macro())
