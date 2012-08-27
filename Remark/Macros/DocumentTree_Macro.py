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
        self.includeTag = scope.getString('DocumentTree.include_tag', 'document_type')
        self.includeGlob = scope.getString('DocumentTree.include', '*', ' ')
        self.includeRegex = scope.getString('DocumentTree.include_regex', '', r'\n')
        self.excludeTag = scope.getString('DocumentTree.exclude_tag', 'document_type')
        self.excludeGlob = scope.getString('DocumentTree.exclude', '', ' ')
        self.excludeRegex = scope.getString('DocumentTree.exclude_regex', '', r'\n')

        # Precomputation
        self.remarkConverter = remarkConverter
        self.document = remarkConverter.document
        self.documentTree = remarkConverter.documentTree

        if self.includeRegex != '':
            # Use the regular expression for filtering.
            self.includeFilter = re.compile(self.includeRegex)
        else:
            # Use the glob for filtering.
            self.includeFilter = re.compile(fnmatch.translate(self.includeGlob))

        if self.excludeRegex != '':
            # Use the regular expression for filtering.
            self.excludeFilter = re.compile(self.excludeRegex)
        else:
            # Use the glob for filtering.
            self.excludeFilter = re.compile(fnmatch.translate(self.excludeGlob))

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
        excludeValue = document.tagString(self.excludeTag)
        if self.excludeFilter.match(excludeValue) != None:
            return

        includeValue = document.tagString(self.includeTag)
        if self.includeFilter.match(includeValue) == None: 
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
