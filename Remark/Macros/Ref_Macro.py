# -*- coding: utf-8 -*-

# Description: Ref macro
# Detail: Finds the relative output name of a file in document tree.

from MacroRegistry import registerMacro
from FileSystem import unixRelativePath, outputDocumentName

class Ref_Macro(object):
    def name(self):
        return 'Ref'

    def expand(self, parameter, remark):
        document = remark.document
        documentTree = remark.documentTree
        
        text = []
        dependencySet = set()        
        for linkFileName in parameter:
            linkDocument, unique = documentTree.findDocument(linkFileName, document.relativeDirectory)
            if not unique:
                remark.reporter.reportAmbiguousDocument(linkFileName)
            
            if linkDocument != None:
                linkTarget = unixRelativePath(document.relativeDirectory, linkDocument.relativeName)
                text.append(outputDocumentName(linkTarget))
                dependencySet.add(linkDocument)
                if len(parameter) > 1:                
                    text += ['']
            else:
                remark.reporter.reportMissingDocument(linkFileName)
            
        return text, dependencySet
    
    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Ref', Ref_Macro())
