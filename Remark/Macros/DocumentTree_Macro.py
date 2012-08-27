# -*- coding: utf-8 -*-

# Description: DocumentTree macro
# Detail: Generates a Remark file to traverse the document-tree directly. 

import fnmatch
import re

from MacroRegistry import registerMacro
from Common import htmlDiv, globToRegex, combineRegex

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
        self.includeGlob = scope.get('DocumentTree.include', ['*'])
        self.includeRegex = scope.get('DocumentTree.include_regex')
        self.excludeTag = scope.getString('DocumentTree.exclude_tag', 'document_type')
        self.excludeGlob = scope.get('DocumentTree.exclude')
        self.excludeRegex = scope.get('DocumentTree.exclude_regex')

        # Precomputation
        self.remarkConverter = remarkConverter
        self.document = remarkConverter.document
        self.documentTree = remarkConverter.documentTree

        # Find out the include filter.
        if self.includeRegex == []:
            self.includeRegex = globToRegex(self.includeGlob)
        else:
            self.includeRegex = combineRegex(self.includeRegex) + r'\Z'
        self.includeFilter = re.compile(self.includeRegex)

        # Find out the exclude filter.
        if self.excludeRegex == []:
            self.excludeRegex = globToRegex(self.excludeGlob)
        else:
            self.excludeRegex = combineRegex(self.excludeRegex) + r'\Z'
        self.excludeFilter = re.compile(self.excludeRegex)

        print combineRegex(self.excludeRegex)

        # Start reporting the document-tree using the
        # current document as the root document.
        text = ['']
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
        # Limit the reporting to given maximum depth.
        if depth > self.maxDepth:
            return

        excludeValue = document.tagString(self.excludeTag).strip()
        includeValue = document.tagString(self.includeTag).strip()

        # Filter by inclusion, exclusion, and depth.

        exclude = (self.excludeFilter.match(excludeValue) == None)
        include = (self.includeFilter.match(includeValue) != None)

        report = False
        if (depth >= self.minDepth and 
            (not exclude) and include):
            # Add this document to the list of links.
            linkText = self.remarkConverter.remarkLink(
                    document.linkDescription(), 
                    self.document, document)
            listPrefix = '    ' * (depth - self.minDepth) + ' 1. '
            text.append(listPrefix + linkText)
            report = True

        newDepth = depth
        if report:
            newDepth = depth + 1
    
        # Sort the children by link-description.
        childSet = document.childSet.values()
        childSet.sort(lambda x, y: cmp(x.linkDescription(), y.linkDescription()))        

        # Recurse to output the children.
        for child in childSet:
            self._workDocument(child, text, newDepth)
        
registerMacro('DocumentTree', DocumentTree_Macro())
