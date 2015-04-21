# -*- coding: utf-8 -*-

# Description: ParentList macro
# Detail: Generates a list of parent documents up to the root.

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import markdownRegion

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
        for i in reversed(range(0, len(parentSet))):
            document = parentSet[i]
            linkText = remark.remarkLink(
                document.linkDescription(), 
                remark.document, document)

            # Strictly speaking, Markdown does not
            # use the actual numbers, so we could
            # as well set them all to 1. However,
            # the numbers might be useful for debugging
            # the intermediate output later on.
            text.append(repr(level) + '. ' + linkText)
            level += 1
            
        return markdownRegion(
            remark.convert(text), 
            {'class' : className})

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('ParentList', ParentList_Macro())


