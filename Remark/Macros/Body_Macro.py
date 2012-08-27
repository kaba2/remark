# -*- coding: utf-8 -*-

# Description: Body macro
# Detail: Reads a document from file.

from Common import readFile
from MacroRegistry import registerMacro

import os.path 

class Body_Macro(object):
    def name(self):
        return 'Body'

    def expand(self, parameter, remark):
        document = remark.document
        fileName = remark.documentTree.fullName(document);
        return readFile(fileName)
    
    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False
    
    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Body', Body_Macro())
