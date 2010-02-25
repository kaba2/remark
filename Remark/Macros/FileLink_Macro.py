# -*- coding: utf-8 -*-

# Description: FileLink_Macro class
# Detail: Generates a link to a document based on relative filename.

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
            linkDocument = documentTree.findDocument(linkFileName, document.relativeDirectory)
            
            if linkDocument != None:
                linkDescription = linkDocument.fileName
                linkTarget = linkAddress(document.relativeDirectory, linkDocument.relativeName)
                text += remarkConverter.remarkLink(linkDescription, outputDocumentName(linkTarget))
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

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('FileLink', FileLink_Macro())
