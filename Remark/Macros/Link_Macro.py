import os.path

from Remark.MacroRegistry import registerMacro
from Remark.Common import linkAddress, remarkLink, outputDocumentName

class Link_Macro:
    def expand(self, parameter, document, documentTree, scope):
        if parameter == []:
            return []
        
        linkFileName = parameter[0] 
        linkDocument = documentTree.findDocument(linkFileName, document.relativeDirectory)
        
        text = []
        if linkDocument != None:
            linkDescription = linkDocument.tag('description')
            linkTarget = linkAddress(document.relativeDirectory, linkDocument.relativeName)
            text = remarkLink(linkDescription, outputDocumentName(linkTarget))
        else:
            print 'Warning:', document.relativeName, ': manual link',
            print linkFileName, 'not found. Ignoring it.'
            
        return text

registerMacro('Link', Link_Macro())
