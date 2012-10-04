# -*- coding: utf-8 -*-

# Description: DocumentTree macro
# Detail: Generates a hierarchical link-tree of the document-tree. 

import fnmatch
import re

from Macro_Registry import registerMacro
from FileSystem import htmlDiv, globToRegex, combineRegex

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
        self.compact = scope.getInteger('DocumentTree.compact', 1)

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

        rootDocument, unique = self.documentTree.findDocument(self.rootName, 
                                                      self.document.relativeDirectory)
        if rootDocument == None:
            self.remark.reporter.reportMissingDocument(self.rootName)
            return []
        
        if not unique:
            self.remark.reporter.reportAmbiguousDocument(self.rootName)
            
        # Start reporting the document-tree using the
        # given root document.
        self.visitedSet = set()
        text = ['']
        self._workDocument(rootDocument, text, 0)

        if text == ['']:
            return []

        text = htmlDiv(text, self.className)

        text.append('')
        text.append('<div class = "remark-end-list"></div>')
        text.append('')

        return text

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True

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
                     ' missing either tag-name or tag-value. Ignoring it.',
                     'invalid-input')
                continue;
            if len(pairSet) > 2:
                self.remark.reportWarning(
                     line + ' has too many parameters. Ignoring it.',
                     'invalid-input')
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
            return False, False

        # Protect against self-recursion.
        selfRecursive = document in self.visitedSet
        if not selfRecursive:
            self.visitedSet.add(document)

        # Sort the children by link-description.
        childSet = document.childSet.values()
        childSet.sort(lambda x, y: cmp(x.linkDescription(), y.linkDescription()))        

        # Recurse to output the children, but only
        # if we have not visited this document before.
        localText = []
        childMatches = 0
        usefulBranches = 0
        if not selfRecursive:
            for child in childSet:
                match, useful = self._workDocument(child, localText, depth + 1)
                if match:
                    childMatches += 1
                if useful:
                    usefulBranches += 1

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

        match = (not exclude) and include

        # In the non-compacting mode,
        # we will report a document if and only if
        #
        # * it has the proper depth, and 
        # * it matches or it has matching descendants.
        #
        # This retains the parent-child relation.
        report = ((match or usefulBranches > 0) and 
                  depth >= self.minDepth)

        if self.compact != 0:
            # In the compacting mode, we will report 
            # a document if and only if
            #
            # * it has the proper depth, and
            # * it matches, or its child matches, or it
            #   has at least two children which have
            #   matching descendants.
            #
            # This retains the ancestor-descendant 
            # relation, but not the parent-child relation.
            report = ((match or 
                      childMatches > 0 or
                      usefulBranches > 1) and
                      depth >= self.minDepth)
        
        if report:
            # Add this document to the list of links.
            linkText = self.remark.remarkLink(
                    document.linkDescription(), 
                    self.document, document)
            text.append(' 1. ' + linkText)

            #text.append('')
            for line in localText:
                text.append('\t' + line)
        else:
            text += localText

        return match, (usefulBranches > 0 or match)

               
registerMacro('DocumentTree', DocumentTree_Macro())
