# -*- coding: utf-8 -*-

# Description: FileLink_Macro class
# Detail: Generates a link to a document in the document tree.

import os.path

from MacroRegistry import registerMacro
from Common import linkAddress, outputDocumentName

class FileLink_Macro:
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        documentTree = remarkConverter.documentTree
        
        if parameter == []:
            return []
        
        text = []
        
        for linkFileName in parameter:
            linkDocument, unique = documentTree.findDocumentHard(linkFileName, document.relativeDirectory)
            if not unique:
                remarkConverter.reportWarning('FileLink: "' + linkFileName + '" is ambiguous. Picking arbitrarily.')
            
            if linkDocument != None:
                linkDescription = linkDocument.fileName
                linkTarget = linkAddress(document.relativeDirectory, linkDocument.relativeName)
                text.append(remarkConverter.remarkLink(linkDescription, outputDocumentName(linkTarget)))
                if len(parameter) > 1:                
                    text += ['']
            else:
                remarkConverter.reportWarning('FileLink: "' + linkFileName + '" not found. Ignoring it.')
            
        return text
    
    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('FileLink', FileLink_Macro())
