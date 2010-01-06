# -*- coding: utf-8 -*-

# Description: Body_Macro class
# Detail: Reads a document from file.

from Common import readFile
from MacroRegistry import registerMacro

class Body_Macro:
    def expand(self, parameter, document, documentTree, scope):
        text = readFile(document.fullName)
                        
        return text
    
    def pureOutput(self):
        return False

registerMacro('Body', Body_Macro())
