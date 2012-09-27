# -*- coding: utf-8 -*-

# Description: Link macro
# Detail: Generates a link to a document in the document tree.

from MacroRegistry import registerMacro
from FileSystem import unixRelativePath, outputDocumentName
from Document import documentRelativeName, Dependency

class Link_Macro(object):
    def name(self):
        return 'Link'

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

            text.append(remark.remarkLink(linkDocument.linkDescription(),
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

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Link', Link_Macro())
