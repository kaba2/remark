# -*- coding: utf-8 -*-

# Description: Example macro

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import markdownRegion

class Example_Macro(object):
    def name(self):
        return 'Example'

    def expand(self, parameter, remark):
        scope = remark.scopeStack.top()

        className = scope.getString('Example.class_name', 'Example')

        text = remark.macro('Verbatim', parameter)

        text += markdownRegion(
            remark.convert(parameter), 
            {'class' : className})

        return text

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Example', Example_Macro())
