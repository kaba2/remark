# -*- coding: utf-8 -*-

# Description: DocumentTree macro
# Detail: Generates a Remark file to traverse the document-tree directly. 

from MacroRegistry import registerMacro
from Common import htmlDiv

class DocumentTree_Macro(object):
    def expand(self, parameter, remarkConverter):
        scope = remarkConverter.scopeStack.top()
        className = scope.getString('DocumentTree.class-name', 'DocumentTree')

        # Start reporting the document-tree using the
        # current document as the root document.
        text = []
        self._workDocument(remarkConverter.document, remarkConverter, text, 0)

        return htmlDiv(text, className)

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

    def _workDocument(self, document, remarkConverter, text, level):
        documentTree = remarkConverter.documentTree

        listPrefix = '\t' * level + ' * '

        # Add this document to the list of links.
        linkText = remarkConverter.remarkLink(
             document.tag('description'), 
             remarkConverter.document, document)
        text.append(listPrefix + linkText)

        # Recurse to output the children.
        for child in document.childSet.itervalues():
            # Only list the documentation children.
            if child.documentType().name() == 'RemarkPage':
                self._workDocument(child, remarkConverter, text, level + 1)
        
registerMacro('DocumentTree', DocumentTree_Macro())
