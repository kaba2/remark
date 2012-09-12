# -*- coding: utf-8 -*-

# Description: Comment macro
# Detail: Consumes its input and produces no output.

from MacroRegistry import registerMacro

class Comment_Macro(object):
    def name(self):
        return 'Comment'

    def expand(self, parameter, remark):
        # This macro simply eats its parameter. This allows
        # for commenting.
        text = []
        dependencySet = set()
        return text, dependencySet

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Comment', Comment_Macro())
