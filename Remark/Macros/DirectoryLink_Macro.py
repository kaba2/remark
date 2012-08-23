# -*- coding: utf-8 -*-

# Description: DirectoryLink macro
# Detail: Generates a relative link to the containing directory.

import os.path

from MacroRegistry import registerMacro
from Common import linkAddress, outputDocumentName

class DirectoryLink_Macro(object):
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        documentTree = remarkConverter.documentTree
        
        if parameter == []:
            return []
        
        text = []
        
        for linkFileName in parameter:
            linkDocument, unique = documentTree.findDocument(linkFileName, document.relativeDirectory)
            if not unique:
                remarkConverter.reportWarning('DirectoryLink: "' + linkFileName + '" is ambiguous. Picking arbitrarily.')
            
            if linkDocument != None:
                linkTarget = documentTree.findDocumentLocal('directory.remark-index', 
                                                       linkDocument.relativeDirectory)

                text.append(remarkConverter.remarkLink(linkDocument.relativeDirectory + '/',
                                                       document, linkTarget))

                if len(parameter) > 1:
                    text.append('')
            else:
                remarkConverter.reportWarning('DirectoryLink: "' + linkFileName + '" not found. Ignoring it.')
            
        return text
    
    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('DirectoryLink', DirectoryLink_Macro())
