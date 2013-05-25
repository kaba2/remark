# -*- coding: utf-8 -*-

# Description: Ref macro
# Detail: Finds the relative output name of a file in document tree.

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import unixRelativePath
from Remark.DocumentType_Registry import outputDocumentName

class Ref_Macro(object):
    def name(self):
        return 'Ref'

    def expand(self, parameter, remark):
        document = remark.document
        documentTree = remark.documentTree
        
        text = []
        for linkFileName in parameter:
            linkDocument, unique = documentTree.findDocument(linkFileName, document.relativeDirectory)

            if not unique:
                remark.reporter.reportAmbiguousDocument(linkFileName)
            
            if linkDocument == None:
                remark.reporter.reportMissingDocument(linkFileName)
                continue

            linkTarget = unixRelativePath(document.relativeDirectory, linkDocument.relativeName)
            text.append(outputDocumentName(linkTarget))
            if len(parameter) > 1:                
                text += ['']
            
        return text
    
    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Ref', Ref_Macro())
