# -*- coding: utf-8 -*-

# Description: Html_Macro class
# Detail: Copies the input to output and treats it as html.

from MacroRegistry import registerMacro

class Html_Macro:
    def expand(self, parameter, document, documentTree, scope):
        return parameter

    def outputType(self):
        return 'html'

    def pureOutput(self):
        return True

registerMacro('Html', Html_Macro())
