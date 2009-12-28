# Description: Comment_Macro class
# Detail: Consumes its input and produces no output.
# Documentation: macros.txt

from Remark.MacroRegistry import registerMacro

class Comment_Macro:
    def expand(self, parameter, document, documentTree, scope):
        # This macro simply eats its parameter. This allows
        # for commenting.
        return []

registerMacro('Comment', Comment_Macro())
