# -*- coding: utf-8 -*-

# Description: Ref macro
# Detail: Finds the relative output name of a file in document tree.

from MacroRegistry import registerMacro
from Common import unixRelativePath, outputDocumentName

class Ref_Macro(object):
    def name(self):
        return 'Ref'

    def expand(self, parameter, remark):
        document = remark.document
        documentTree = remark.documentTree
        
        text = []
        
        for linkFileName in parameter:
            linkDocument, unique = documentTree.findDocument(linkFileName, document.relativeDirectory)
            if not unique:
                remark.reportWarning('Document ' + linkFileName + ' is ambiguous. Picking arbitrarily.')
            
            if linkDocument != None:
                linkTarget = unixRelativePath(document.relativeDirectory, linkDocument.relativeName)
                text.append(outputDocumentName(linkTarget))
                if len(parameter) > 1:                
                    text += ['']
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

registerMacro('Ref', Ref_Macro())
