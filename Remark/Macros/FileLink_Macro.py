# -*- coding: utf-8 -*-

# Description: FileLink macro
# Detail: Generates a link to a document in the document tree.

from MacroRegistry import registerMacro
from Common import unixRelativePath, outputDocumentName, escapeMarkdown

class FileLink_Macro(object):
    def name(self):
        return 'FileLink'

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
                text.append(remark.remarkLink(escapeMarkdown(linkDocument.fileName),
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

registerMacro('FileLink', FileLink_Macro())
