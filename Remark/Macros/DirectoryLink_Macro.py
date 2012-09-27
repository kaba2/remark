# -*- coding: utf-8 -*-

# Description: DirectoryLink macro
# Detail: Generates a relative link to the containing directory.

from MacroRegistry import registerMacro
from FileSystem import unixRelativePath, outputDocumentName, escapeMarkdown
from Document import documentRelativeName, Dependency

class DirectoryLink_Macro(object):
    def name(self):
        return 'DirectoryLink'

    def expand(self, parameter, remark):
        text = []

        document = remark.document
        documentTree = remark.documentTree
       
        # For each link-row of the parameter...
        for linkFileName in parameter:
            # Find out the document given on the link-row.
            linkDocument, unique = documentTree.findDocument(linkFileName, document.relativeDirectory)
            if linkDocument == None:
                return None, True

            directoryIndexName = 'directory.remark-index'
            linkTarget = documentTree.findDocumentLocal(directoryIndexName, 
                                                        linkDocument.relativeDirectory)
            
            if not unique:
                remark.reporter.reportAmbiguousDocument(linkFileName)

            if linkTarget == None:
                remark.reporter.reportMissingDocument(linkFileName)
                continue

            # Name it in the form directory/, to emphasize it is a directory.
            # Note that we escape the possible Markdown meta-characters.
            linkDescription = escapeMarkdown(linkTarget.relativeDirectory + '/')

            # Create the directory-link.
            text.append(remark.remarkLink(linkDescription,
                                          document, linkTarget))

            # If there are multiple links, we want them on their own rows.
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

registerMacro('DirectoryLink', DirectoryLink_Macro())
