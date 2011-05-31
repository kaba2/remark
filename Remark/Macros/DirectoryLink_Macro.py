# -*- coding: utf-8 -*-

# Description: DirectoryLink_Macro class
# Detail: Generates a relative link to the containing directory.

import os.path

from MacroRegistry import registerMacro
from Common import linkAddress, outputDocumentName

class DirectoryLink_Macro:
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        documentTree = remarkConverter.documentTree
        
        if parameter == []:
            return []
        
        text = []
        
        for linkFileName in parameter:
            linkDocument, unique = documentTree.findDocumentHard(linkFileName, document.relativeDirectory)
            if not unique:
                remarkConverter.reportWarning('DirectoryLink: "' + linkFileName + '" is ambiguous. Picking arbitrarily.')
            
            if linkDocument != None:
                linkDescription = linkDocument.relativeDirectory + '/'
                linkTarget = linkAddress(document.relativeDirectory, 
                                         os.path.join(linkDocument.relativeDirectory, 'directory.index'))
                text.append(remarkConverter.remarkLink(linkDescription, outputDocumentName(linkTarget)))
                if len(parameter) > 1:
                    text += ['']
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
