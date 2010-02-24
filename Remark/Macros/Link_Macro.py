# -*- coding: utf-8 -*-

# Description: Link_Macro class
# Detail: Generates a link to a document based on relative filename.

import os.path

from MacroRegistry import registerMacro
from Common import linkAddress, remarkLink, outputDocumentName

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
                if len(parameter) > 1:                
                    text += ['']
            else:
                print 'Warning:', document.relativeName, ': manual link',
                print linkFileName, 'not found. Ignoring it.'
            
        return text

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

registerMacro('Link', Link_Macro())
