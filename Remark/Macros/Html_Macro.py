# -*- coding: utf-8 -*-

# Description: Html macro
# Detail: Copies the input to output and treats it as html.

from MacroRegistry import registerMacro

class Html_Macro(object):
    def name(self):
        return 'Html'

    def expand(self, parameter, remark):
        text = parameter
        dependencySet = set()
        return text, dependencySet

    def outputType(self):
        return 'html'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

    def findDependency(self, searchName, document, documentTree, parameter = ''):
        return None, True

registerMacro('Html', Html_Macro())
