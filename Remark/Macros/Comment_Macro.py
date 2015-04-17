# -*- coding: utf-8 -*-

# Description: Comment macro
# Detail: Consumes its input and produces no output.

from Remark.Macro_Registry import registerMacro

class Comment_Macro(object):
    def name(self):
        return 'Comment'

    def expand(self, parameter, remark):
        # This macro simply eats its parameter. This allows
        # for commenting.
        text = []
        return text

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Comment', Comment_Macro())
