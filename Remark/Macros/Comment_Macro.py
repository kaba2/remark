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
        return []

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Comment', Comment_Macro())
