# -*- coding: utf-8 -*-

# Description: Verbatim macro
# Detail: Reinterprets input as preformatted text.

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import markdownRegion

class Verbatim_Macro(object):
    def name(self):
        return 'Verbatim'

    def expand(self, parameter, remark):
        scope = remark.scopeStack.top()

        className = scope.getString('Verbatim.class_name', 'Verbatim')

        text = []
        for line in parameter:
            text.append('\t' + line)

        return markdownRegion(
            text, 
            {'class' : className})

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Verbatim', Verbatim_Macro())
