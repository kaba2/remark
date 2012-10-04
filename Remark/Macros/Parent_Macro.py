# -*- coding: utf-8 -*-

# Description: Parent macro
# Detail: Generates a link to the parent documentation.

from Macro_Registry import registerMacro
from FileSystem import unixRelativePath
from DocumentType_Registry import outputDocumentName

class Parent_Macro(object):
    def name(self):
        return 'Parent'

    def expand(self, parameter, remark):
        text = []

        document = remark.document
        parent = document.parent

        text = [remark.remarkLink('Back to ' + parent.linkDescription(),
                                  document, parent)]

        return text

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Parent', Parent_Macro())

