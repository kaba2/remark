# -*- coding: utf-8 -*-

# Description: FileLink macro
# Detail: Generates a link to a document in the document tree.

from MacroRegistry import registerMacro
from FileSystem import unixRelativePath, outputDocumentName, escapeMarkdown

class FileLink_Macro(object):
    def name(self):
        return 'FileLink'

    def expand(self, parameter, remark):
        document = remark.document
        documentTree = remark.documentTree
        
        text = []
        dependencySet = set()
        for linkFileName in parameter:
            linkDocument, unique = documentTree.findDocument(linkFileName, document.relativeDirectory)
            dependencySet.add((linkFileName, document.relativeDirectory, 'search'))

            if not unique:
                remark.reporter.reportAmbiguousDocument(linkFileName)
            
            if linkDocument != None:
                linkDescription = escapeMarkdown(linkDocument.fileName)
                text.append(remark.remarkLink(linkDescription,
                                              document, linkDocument))

                if len(parameter) > 1:                
                    text.append('')
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

registerMacro('FileLink', FileLink_Macro())
