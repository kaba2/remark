# -*- coding: utf-8 -*-

# Description: DocumentTree macro
# Detail: Generates a Remark file to traverse the document-tree directly. 

from MacroRegistry import registerMacro
from Common import htmlDiv

class DocumentTree_Macro(object):
    def expand(self, parameter, remarkConverter):
        scope = remarkConverter.scopeStack.top()
        className = scope.getString('DocumentTree.class_name', 'DocumentTree')
        minDepth = scope.getInteger('DocumentTree.min_depth', 1)
        maxDepth = scope.getInteger('DocumentTree.max_depth', 10)

        # Start reporting the document-tree using the
        # current document as the root document.
        text = []
        self._workDocument(remarkConverter.document, remarkConverter, text, 
                           0, minDepth, maxDepth)

        return htmlDiv(text, className)

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

    def _workDocument(self, document, remarkConverter, text, 
                      depth, minDepth, maxDepth):
        # Limit the reporting to given depth-interval.
        if depth > maxDepth:
            return

        documentTree = remarkConverter.documentTree

        listPrefix = '    ' * (depth - minDepth) + ' 1. '

        if depth >= minDepth:
            # Add this document to the list of links.
            linkText = remarkConverter.remarkLink(
                 document.linkDescription(), 
                 remarkConverter.document, document)
            text.append(listPrefix + linkText)

        # Recurse to output the children.
        for child in document.childSet.itervalues():
            # Only list the documentation children.
            if child.documentType().name() == 'RemarkPage':
                self._workDocument(child, remarkConverter, text, 
                                   depth + 1, minDepth, maxDepth)
        
registerMacro('DocumentTree', DocumentTree_Macro())
