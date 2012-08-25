# -*- coding: utf-8 -*-

# Description: FileLink macro
# Detail: Generates a link to a document in the document tree.

import os.path

from MacroRegistry import registerMacro
from Common import unixRelativePath, outputDocumentName

class FileLink_Macro(object):
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        documentTree = remarkConverter.documentTree
        
        if parameter == []:
            return []
        
        text = []
        
        for linkFileName in parameter:
            linkDocument, unique = documentTree.findDocument(linkFileName, document.relativeDirectory)
            if not unique:
                remarkConverter.reportWarning('FileLink: "' + linkFileName + '" is ambiguous. Picking arbitrarily.')
            
            if linkDocument != None:
                text.append(remarkConverter.remarkLink(linkDocument.fileName,
                                                       document, linkDocument))
                if len(parameter) > 1:                
                    text.append('')
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
