# -*- coding: utf-8 -*-

# Description: Comment_Macro class
# Detail: Consumes its input and produces no output.

from MacroRegistry import registerMacro

class Comment_Macro:
    def expand(self, parameter, remarkConverter):
        # This macro simply eats its parameter. This allows
        # for commenting.
        return []

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Comment', Comment_Macro())
