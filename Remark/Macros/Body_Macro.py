# -*- coding: utf-8 -*-

# Description: Body_Macro class
# Detail: Reads a document from file.

from Common import readFile
from MacroRegistry import registerMacro

class Body_Macro:
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        text = readFile(document.fullName)                        
        return text
    
    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False
    
    def htmlHead(self, remarkConverter):
        return []                

registerMacro('Body', Body_Macro())
