# -*- coding: utf-8 -*-

# Description: Html macro
# Detail: Copies the input to output and treats it as html.

from Remark.Macro_Registry import registerMacro

class Html_Macro(object):
    def name(self):
        return 'Html'

    def expand(self, parameter, remark):
        text = parameter
        return text

    def outputType(self):
        return 'html'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Html', Html_Macro())
