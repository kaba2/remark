# -*- coding: utf-8 -*-

# Description: FileLink macro
# Detail: Generates a link to a document in the document tree.

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import unixRelativePath, escapeMarkdown
from Remark.DocumentType_Registry import outputDocumentName

class FileLink_Macro(object):
    def name(self):
        return 'FileLink'

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

            linkDescription = escapeMarkdown(linkDocument.fileName)
            text.append(remark.remarkLink(linkDescription,
                                          document, linkDocument))

            if len(parameter) > 1:                
                text.append('')
            
        return text
    
    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('FileLink', FileLink_Macro())
