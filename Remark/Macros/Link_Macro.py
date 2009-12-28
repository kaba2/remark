# Description: Link_Macro class
# Detail: Generates a link to another document based on relative filename.
# Documentation: macros.txt

import os.path

from Remark.MacroRegistry import registerMacro
from Remark.Common import linkAddress, remarkLink, outputDocumentName

class Link_Macro:
    def expand(self, parameter, document, documentTree, scope):
        if parameter == []:
            return []
        
        text = []
        for linkFileName in parameter:
            linkDocument = documentTree.findDocument(linkFileName, document.relativeDirectory)
            
            if linkDocument != None:
                linkDescription = linkDocument.tag('description')
                linkTarget = linkAddress(document.relativeDirectory, linkDocument.relativeName)
                text += remarkLink(linkDescription, outputDocumentName(linkTarget))
            else:
                print 'Warning:', document.relativeName, ': manual link',
                print linkFileName, 'not found. Ignoring it.'
            
        return text

    def pureOutput(self):
        return True

registerMacro('Link', Link_Macro())
