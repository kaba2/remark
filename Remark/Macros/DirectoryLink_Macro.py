# -*- coding: utf-8 -*-

# Description: DirectoryLink macro
# Detail: Generates a relative link to the containing directory.

from MacroRegistry import registerMacro
from FileSystem import unixRelativePath, outputDocumentName, escapeMarkdown

class DirectoryLink_Macro(object):
    def name(self):
        return 'DirectoryLink'

    def expand(self, parameter, remark):
        document = remark.document
        documentTree = remark.documentTree
        dependencySet = set()
        
        text = []
        # For each link-row of the parameter...
        for linkFileName in parameter:
            # Find out the document given on the link-row.
            linkDocument, unique = documentTree.findDocument(linkFileName, document.relativeDirectory)
            dependencySet.add((linkFileName, document.relativeDirectory, 'search'))

            if not unique:
                remark.reporter.reportAmbiguousDocument(linkFileName)
            
            if linkDocument != None:
                # Find out the directory-index of the given document.
                directoryIndexName = 'directory.remark-index'
                linkTarget = documentTree.findDocument(directoryIndexName, 
                                                       linkDocument.relativeDirectory)
                dependencySet.add((directoryIndexName, linkDocument.relativeDirectory, 'search'))
                assert linkTarget != None

                # Name it in the form directory/, to emphasize it is a directory.
                # Note that we escape the possible Markdown meta-characters.
                linkDescription = escapeMarkdown(linkDocument.relativeDirectory + '/')

                # Create the directory-link.
                text.append(remark.remarkLink(linkDescription,
                                              document, linkTarget))

                # If there are multiple links, we want them on their own rows.
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

registerMacro('DirectoryLink', DirectoryLink_Macro())
