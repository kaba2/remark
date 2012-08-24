# -*- coding: utf-8 -*-

# Description: DocumentTree macro
# Detail: Generates a Remark file to traverse the document-tree directly. 

from MacroRegistry import registerMacro
from Common import htmlDiv

class DocumentTree_Macro(object):
    def expand(self, parameter, remarkConverter):
        scope = remarkConverter.scopeStack.top()

        self.className = scope.getString('DocumentTree.class_name', 'DocumentTree')
        self.minDepth = scope.getInteger('DocumentTree.min_depth', 1)
        self.maxDepth = scope.getInteger('DocumentTree.max_depth', 10)
        self.excludeTag = scope.getString('DocumentTree.exclude_tag', 'document_type')
        self.excludeSet = scope.get('DocumentTree.exclude_set', [''])
        self.remarkConverter = remarkConverter
        self.document = remarkConverter.document
        self.documentTree = remarkConverter.documentTree

        # Start reporting the document-tree using the
        # current document as the root document.
        text = []
        self._workDocument(self.document, text, 0)

        return htmlDiv(text, self.className)

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

    def _workDocument(self, document, text, depth):
        # Limit the reporting to given depth-interval.
        if depth > self.maxDepth:
            return

        # Exclude those whose tags are in the exclusion set.
        tag = document.tagString(self.excludeTag, None)
        if tag in self.excludeSet: 
            return

        listPrefix = '    ' * (depth - self.minDepth) + ' 1. '

        if depth >= self.minDepth:
            # Add this document to the list of links.
            linkText = self.remarkConverter.remarkLink(
                 document.linkDescription(), 
                 self.document, document)
            text.append(listPrefix + linkText)

        # Recurse to output the children.
        for child in document.childSet.itervalues():
            self._workDocument(child, text, depth + 1)
        
registerMacro('DocumentTree', DocumentTree_Macro())
