# -*- coding: utf-8 -*-

# Description: DirectoryLink macro
# Detail: Generates a relative link to the containing directory.

import os.path

from MacroRegistry import registerMacro
from Common import unixRelativePath, outputDocumentName, escapeMarkdown

class DirectoryLink_Macro(object):
    def name(self):
        return 'DirectoryLink'

    def expand(self, parameter, remark):
        document = remark.document
        documentTree = remark.documentTree
        
        if parameter == []:
            return []
        
        text = []
        
        for linkFileName in parameter:
            linkDocument, unique = documentTree.findDocument(linkFileName, document.relativeDirectory)
            if not unique:
                remark.reportWarning('Document ' + linkFileName + ' is ambiguous. Picking arbitrarily.')
            
            if linkDocument != None:
                linkTarget = documentTree.findDocumentLocal('directory.remark-index', 
                                                       linkDocument.relativeDirectory)

                text.append(remark.remarkLink(escapeMarkdown(linkDocument.relativeDirectory + '/'),
                                                       document, linkTarget))

                if len(parameter) > 1:
                    text.append('')
            else:
                remark.reportWarning('Document ' + linkFileName + ' not found. Ignoring it.')
            
        return text
    
    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('DirectoryLink', DirectoryLink_Macro())
