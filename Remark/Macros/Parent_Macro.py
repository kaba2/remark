# -*- coding: utf-8 -*-

# Description: Parent macro
# Detail: Generates a link to the parent documentation.

from MacroRegistry import registerMacro
from FileSystem import unixRelativePath, outputDocumentName

class Parent_Macro(object):
    def name(self):
        return 'Parent'

    def expand(self, parameter, remark):
        document = remark.document
        parent = document.parent
       
        return [remark.remarkLink('Back to ' + parent.linkDescription(),
                                           document, parent)]

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Parent', Parent_Macro())

