# -*- coding: utf-8 -*-

# Description: Ref macro
# Detail: Finds the relative output name of a file in document tree.

import os.path

from MacroRegistry import registerMacro
from Common import linkAddress, outputDocumentName

class Ref_Macro(object):
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        documentTree = remarkConverter.documentTree
        
        text = []
        
        for linkFileName in parameter:
            linkDocument, unique = documentTree.findDocument(linkFileName, document.relativeDirectory)
            if not unique:
                remarkConverter.reportWarning('Ref: "' + linkFileName + '" is ambiguous. Picking arbitrarily.')
            
            if linkDocument != None:
                linkTarget = linkAddress(document.relativeDirectory, linkDocument.relativeName)
                text.append(outputDocumentName(linkTarget))
                if len(parameter) > 1:                
                    text += ['']
            else:
                remarkConverter.reportWarning('Ref: "' + linkFileName + '" not found. Ignoring it.')
            
        return text
    
    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Ref', Ref_Macro())
