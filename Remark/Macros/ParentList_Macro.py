# -*- coding: utf-8 -*-

# Description: ParentList macro
# Detail: Generates a list of parent documents up to the root.

from MacroRegistry import registerMacro
from Common import htmlDiv

class ParentList_Macro(object):
    def name(self):
        return 'ParentList'

    def expand(self, parameter, remarkConverter):
        scope = remarkConverter.scopeStack.top()
        className = scope.getString('ParentList.class_name', 'ParentList')

        # Gather document's parents one by one.
        parentSet = []
        document = remarkConverter.document
        while document != document.parent:
            parentSet.append(document)
            document = document.parent

        # Report the parents in reverse order
        # (the root document first).
        level = 1
        text = []
        for document in reversed(parentSet):
            linkText = remarkConverter.remarkLink(
                document.linkDescription(), 
                remarkConverter.document, document)

            # Strictly speaking, Markdown does not
            # use the actual numbers, so we could
            # as well set them all to 1. However,
            # the numbers might be useful for debugging
            # the intermediate output later on.
            text.append(repr(level) + '. ' + linkText)
            level += 1

        return htmlDiv(text, className)

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('ParentList', ParentList_Macro())


