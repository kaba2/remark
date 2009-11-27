from Remark.MacroRegistry import registerMacro
from Remark.Common import remarkLink, linkAddress, outputDocumentName

class Parent_Macro:
    def expand(self, parameter, document, documentTree):
        parent = document.parent
        linkTarget = linkAddress(document.relativeDirectory, parent.relativeName)
        return remarkLink('Back to ' + parent.tag('description'), 
                          outputDocumentName(linkTarget))

registerMacro('Parent', Parent_Macro())

