# -*- coding: utf-8 -*-

# Description: Ref macro
# Detail: Finds the relative output name of a file in document tree.

from MacroRegistry import registerMacro
from FileSystem import unixRelativePath, outputDocumentName
from Document import documentRelativeName, Dependency

class Ref_Macro(object):
    def name(self):
        return 'Ref'

    def expand(self, parameter, remark):
        document = remark.document
        documentTree = remark.documentTree
        
        text = []
        dependencySet = set()        
        for linkFileName in parameter:
            linkDocument, unique = self.findDependency(linkFileName, document, documentTree)
            dependencySet.add(Dependency(linkFileName, documentRelativeName(linkDocument), self.name()))

            if not unique:
                remark.reporter.reportAmbiguousDocument(linkFileName)
            
            if linkDocument == None:
                remark.reporter.reportMissingDocument(linkFileName)
                continue

            linkTarget = unixRelativePath(document.relativeDirectory, linkDocument.relativeName)
            text.append(outputDocumentName(linkTarget))
            if len(parameter) > 1:                
                text += ['']
            
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

registerMacro('Ref', Ref_Macro())
