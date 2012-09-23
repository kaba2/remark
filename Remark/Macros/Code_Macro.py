# -*- coding: utf-8 -*-

# Description: Code macro
# Detail: Generates colored html from many kinds of source code.

import string

from MacroRegistry import registerMacro
from FileSystem import readFile, unixDirectoryName

from pygments import highlight
from pygments.lexers import guess_lexer, guess_lexer_for_filename
from pygments.formatters import HtmlFormatter

class Code_Macro(object):
    def name(self):
        return 'Code'

    def expand(self, parameter, remark):
        document = remark.document
        dependencySet = set()
        
        # Prepare for Pygments input.
        inputText = '\n'.join(parameter)

        # Try to guess the type of the code.
        lexer = guess_lexer_for_filename(document.fileName, inputText)
        
        # Highlight the code.
        hilightedText = highlight(inputText, lexer, HtmlFormatter())

        # Prepare for Remark output.
        hilightedText = string.split(hilightedText, '\n')
       
        return hilightedText, dependencySet

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

registerMacro('Code', Code_Macro())
registerMacro('GenericCode', Code_Macro())


