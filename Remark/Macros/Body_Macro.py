# -*- coding: utf-8 -*-

# Description: Body macro
# Detail: Reads a document from file.

from Remark.FileSystem import readFile
from Remark.Macro_Registry import registerMacro

class Body_Macro(object):
    def name(self):
        return 'Body'

    def expand(self, parameter, remark):
        document = remark.document
        fileName = remark.documentTree.fullName(document);

        text = readFile(fileName)

        return text
    
    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True
    
    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Body', Body_Macro())
