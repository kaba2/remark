# -*- coding: utf-8 -*-

# Description: DocumentTree macro
# Detail: Generates a Remark file to traverse the document-tree directly. 

import fnmatch
import re

from MacroRegistry import registerMacro
from Common import htmlDiv

class DocumentTree_Macro(object):
    def name(self):
        return 'DocumentTree'

    def expand(self, parameter, remarkConverter):
        scope = remarkConverter.scopeStack.top()

        # Variables
        self.className = scope.getString('DocumentTree.class_name', 'DocumentTree')
        self.minDepth = scope.getInteger('DocumentTree.min_depth', 1)
        self.maxDepth = scope.getInteger('DocumentTree.max_depth', 10)
        self.filterTag = scope.getString('DocumentTree.filter_tag', 'document_type')
        self.filter = scope.getString('DocumentTree.filter', '*', ' ')
        self.regexFilter = scope.getString('DocumentTree.regex_filter', '', r'\n')

        # Precomputation
        self.remarkConverter = remarkConverter
        self.document = remarkConverter.document
        self.documentTree = remarkConverter.documentTree

        if self.regexFilter != '':
            # Use the regular expression for filtering.
            self.filterRegex = re.compile(self.regexFilter)
        else:
            # Use the glob for filtering.
            self.filterRegex = re.compile(fnmatch.translate(self.filter))

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

        # Only report those documents which match the
        # filter.
        tag = document.tagString(self.filterTag, None)
        if self.filterRegex.match(tag) == None: 
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
