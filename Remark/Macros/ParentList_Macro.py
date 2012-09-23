# -*- coding: utf-8 -*-

# Description: ParentList macro
# Detail: Generates a list of parent documents up to the root.

from MacroRegistry import registerMacro
from FileSystem import htmlDiv

class ParentList_Macro(object):
    def name(self):
        return 'ParentList'

    def expand(self, parameter, remark):
        scope = remark.scopeStack.top()
        className = scope.getString('ParentList.class_name', 'ParentList')

        # Gather document's parents one by one.
        parentSet = []
        document = remark.document
        while document != document.parent:
            parentSet.append(document)
            document = document.parent

        # Report the parents in reverse order
        # (the root document first).
        level = 1
        text = []
        dependencySet = set()
        for i in reversed(range(0, len(parentSet))):
            document = parentSet[i]
            linkText = remark.remarkLink(
                document.linkDescription(), 
                remark.document, document)
            if i > 0:
                dependencySet.add((document.relativeName, document.relativeName, self.name()))

            # Strictly speaking, Markdown does not
            # use the actual numbers, so we could
            # as well set them all to 1. However,
            # the numbers might be useful for debugging
            # the intermediate output later on.
            text.append(repr(level) + '. ' + linkText)
            level += 1
            
            
        text = htmlDiv(text, className)

        text.append('')
        text.append('<div class = "remark-end-list"></div>')
        text.append('')

        return text, dependencySet

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

    def findDependency(self, searchName, document, documentTree, parameter = ''):
        linkDocument = document
        while linkDocument.parent != linkDocument:
            if linkDocument.relativeName == searchName:
                return linkDocument, True
        return None, True

registerMacro('ParentList', ParentList_Macro())


