# -*- coding: utf-8 -*-

# Description: Code macro
# Detail: Generates colored html from many kinds of source code.

import os.path
import string

from MacroRegistry import registerMacro
from Common import readFile, unixDirectoryName

from pygments import highlight
from pygments.lexers import guess_lexer, guess_lexer_for_filename
from pygments.formatters import HtmlFormatter

class Code_Macro(object):
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        
        # Prepare for Pygments input.
        inputText = string.join(parameter, '\n')

        # Try to guess the type of the code.
        lexer = guess_lexer_for_filename(document.fileName, inputText)
        
        # Highlight the code.
        hilightedText = highlight(inputText, lexer, HtmlFormatter())

        # Prepare for Remark output.
        hilightedText = string.split(hilightedText, '\n')
        
        return hilightedText

    def outputType(self):
        return 'html'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('Code', Code_Macro())
registerMacro('GenericCode', Code_Macro())

