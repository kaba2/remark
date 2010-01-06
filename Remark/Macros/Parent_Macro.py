# -*- coding: utf-8 -*-

# Description: Parent_Macro class
# Detail: Generates a link to the parent documentation.

from MacroRegistry import registerMacro
from Common import remarkLink, linkAddress, outputDocumentName

class Parent_Macro:
    def expand(self, parameter, document, documentTree, scope):
        parent = document.parent
        linkTarget = linkAddress(document.relativeDirectory, parent.relativeName)

        return remarkLink('Back to ' + parent.tag('description'), 
                          outputDocumentName(linkTarget))

    def pureOutput(self):
        return True

registerMacro('Parent', Parent_Macro())

