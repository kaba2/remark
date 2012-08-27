# -*- coding: utf-8 -*-

# Description: Link macro
# Detail: Generates a link to a document in the document tree.

import os.path

from MacroRegistry import registerMacro
from Common import unixRelativePath, outputDocumentName

class Link_Macro(object):
    def name(self):
        return 'Link'

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
                text.append(remark.remarkLink(linkDocument.linkDescription(),
                                                       document, linkDocument))

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

registerMacro('Link', Link_Macro())
