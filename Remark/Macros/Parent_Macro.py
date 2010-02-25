# -*- coding: utf-8 -*-

# Description: Parent_Macro class
# Detail: Generates a link to the parent documentation.

from MacroRegistry import registerMacro
from Common import linkAddress, outputDocumentName

class Parent_Macro:
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        
        parent = document.parent
        linkTarget = linkAddress(document.relativeDirectory, parent.relativeName)

        return remarkConverter.remarkLink('Back to ' + parent.tag('description'), 
                                          outputDocumentName(linkTarget))

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Parent', Parent_Macro())

