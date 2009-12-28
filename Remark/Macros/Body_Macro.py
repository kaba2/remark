# Description: Body_Macro class
# Detail: Reads a document file to memory.
# Documentation: macros.txt

from Remark.Common import readFile
from Remark.MacroRegistry import registerMacro

class Body_Macro:
    def expand(self, parameter, document, documentTree, scope):
        text = readFile(document.fullName)
            
        return text

registerMacro('Body', Body_Macro())
