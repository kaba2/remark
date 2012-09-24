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
        dependencySet = set()
        for linkFileName in parameter:
            linkDocument, unique = self.findDependency(linkFileName, document, documentTree)
            dependencySet.add(Dependency(linkFileName, documentRelativeName(document), self.name()))

            if not unique:
                remark.reporter.reportAmbiguousDocument(linkFileName)
            
            if linkDocument == None:
                remark.reporter.reportMissingDocument(linkFileName)
                continue

            text.append(remark.remarkLink(linkDocument.linkDescription(),
                                            document, linkDocument))

            if len(parameter) > 1:                
                text.append('')
            
        return text, dependencySet

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

    def findDependency(self, searchName, document, documentTree, parameter = ''):
        linkDocument, unique = documentTree.findDocument(searchName, document.relativeDirectory)
        return linkDocument, unique

registerMacro('Link', Link_Macro())
