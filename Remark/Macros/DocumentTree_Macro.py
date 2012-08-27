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

    def expand(self, parameter, remark):
        # Precomputation
        self.remark = remark
        self.document = remark.document
        self.documentTree = remark.documentTree
        scope = remark.scopeStack.top()

        # Variables
        self.minDepth = scope.getInteger('DocumentTree.min_depth', 1)
        self.maxDepth = scope.getInteger('DocumentTree.max_depth', 10)
        self.rootName = scope.getString('DocumentTree.root_document', self.document.fileName)
        self.className = scope.getString('DocumentTree.class_name', 'DocumentTree')
        self.includeGlob = scope.get('DocumentTree.include', ['file_name *'])
        self.includeRegex = scope.get('DocumentTree.include_regex')
        self.excludeGlob = scope.get('DocumentTree.exclude')
        self.excludeRegex = scope.get('DocumentTree.exclude_regex')

        self.includeMap = {}
        self._parse(self.includeGlob, self.includeMap, globToRegex)
        self._parse(self.includeRegex, self.includeMap, lambda x: x + r'\Z')

        self.includeFilter = {}
        for tagName, regex in self.includeMap.iteritems():
            self.includeFilter[tagName] = re.compile(combineRegex(regex))

        self.excludeMap = {}
        self._parse(self.excludeGlob, self.excludeMap, globToRegex)
        self._parse(self.excludeRegex, self.excludeMap, lambda x: x + r'\Z')

        self.excludeFilter = {}
        for tagName, regex in self.excludeMap.iteritems():
            self.excludeFilter[tagName] = re.compile(combineRegex(regex))

        rootDocument = self.documentTree.findDocument(self.rootName, 
                                                      self.document.relativeDirectory)
        if rootDocument == None:
            self.remark.reportWarning(
                'Document ' + self.rootName + ' was not found. Aborting.')
            return []

        # Start reporting the document-tree using the
        # current document as the root document.
        self.visitedSet = set()
        text = ['']
        self._workDocument(self.document, text, 0)

        if text == ['']:
            return []

        return htmlDiv(text, self.className)

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

    def _parse(self, globSet, map, transform):
        for line in globSet:
            pairSet = line.split()
            if len(pairSet) == 0:
                continue
            if len(pairSet) == 1:
                self.remark.reportWarning(
                     line + 
                     ' missing either tag-name or tag-value. Ignoring it.')
                continue;
            if len(pairSet) > 2:
                self.remark.reportWarning(
                     line + ' has too many parameters. Ignoring it.')
                continue
            tagName = pairSet[0].strip()
            tagValue = pairSet[1].strip()
            regex = transform(tagValue)
            if not tagName in map:
                map[tagName] = [regex]
            else:
                map[tagName].append(regex)

    def _workDocument(self, document, text, depth):
        # Limit the reporting to given maximum depth.
        if depth > self.maxDepth:
            return

        # Protect against self-recursion.
        selfRecursive = document in self.visitedSet
        if not selfRecursive:
            self.visitedSet.add(document)

        # Filter by exclusion.
        exclude = False
        for tagName, tagRegex in self.excludeFilter.iteritems():
            excludeValue = document.tagString(tagName).strip()
            if tagRegex.match(excludeValue) != None:
                exclude = True
                break

        # Filter by inclusion.
        include = False
        for tagName, tagRegex in self.includeFilter.iteritems():
            includeValue = document.tagString(tagName).strip()
            if tagRegex.match(includeValue) != None:
                include = True
                break

        report = False
        if (depth >= self.minDepth and 
            (not exclude) and include):
            # Add this document to the list of links.
            linkText = self.remark.remarkLink(
                    document.linkDescription(), 
                    self.document, document)
            listPrefix = '    ' * (depth - self.minDepth) + ' 1. '
            text.append(listPrefix + linkText)
            report = True

        # Sort the children by link-description.
        childSet = document.childSet.values()
        childSet.sort(lambda x, y: cmp(x.linkDescription(), y.linkDescription()))        

        # Recurse to output the children, but only
        # if we have not visited this document before.
        if not selfRecursive:
            for child in childSet:
                self._workDocument(child, text, depth + 1)
        
registerMacro('DocumentTree', DocumentTree_Macro())
