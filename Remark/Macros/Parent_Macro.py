# Description: Parent_Macro class
# Detail: Generates a link to the parent documentation.
# Documentation: macros.txt

from Remark.MacroRegistry import registerMacro
from Remark.Common import remarkLink, linkAddress, outputDocumentName

class Parent_Macro:
    def expand(self, parameter, document, documentTree, scope):
        parent = document.parent
        linkTarget = linkAddress(document.relativeDirectory, parent.relativeName)
        return remarkLink('Back to ' + parent.tag('description'), 
                          outputDocumentName(linkTarget))

registerMacro('Parent', Parent_Macro())

