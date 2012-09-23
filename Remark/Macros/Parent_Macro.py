# -*- coding: utf-8 -*-

# Description: Parent macro
# Detail: Generates a link to the parent documentation.

from MacroRegistry import registerMacro
from FileSystem import unixRelativePath, outputDocumentName

class Parent_Macro(object):
    def name(self):
        return 'Parent'

    def expand(self, parameter, remark):
        text = []
        dependencySet = set()

        document = remark.document
        parent = document.parent

        text = [remark.remarkLink('Back to ' + parent.linkDescription(),
                                  document, parent)]
        dependencySet.add((parent.relativeName, parent.relativeName, self.name()))

        return text, dependencySet

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

    def findDependency(self, searchName, document, documentTree, parameter = ''):
        parent = document.parent
        if searchName == parent.relativeName:
            return parent, True
        return None, True

registerMacro('Parent', Parent_Macro())

