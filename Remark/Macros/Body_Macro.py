# -*- coding: utf-8 -*-

# Description: Body macro
# Detail: Reads a document from file.

from FileSystem import readFile
from MacroRegistry import registerMacro

class Body_Macro(object):
    def name(self):
        return 'Body'

    def expand(self, parameter, remark):
        document = remark.document
        fileName = remark.documentTree.fullName(document);
        return readFile(fileName)
    
    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True
    
    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Body', Body_Macro())
