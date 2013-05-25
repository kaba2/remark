# -*- coding: utf-8 -*-

# Description: Code macro
# Detail: Generates colored html from many kinds of source code.

import string

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import readFile, unixDirectoryName

from pygments import highlight
from pygments.lexers import guess_lexer, guess_lexer_for_filename
from pygments.formatters import HtmlFormatter

class Code_Macro(object):
    def name(self):
        return 'Code'

    def expand(self, parameter, remark):
        document = remark.document
        
        # Prepare for Pygments input.
        inputText = '\n'.join(parameter)

        # Try to guess the type of the code.
        lexer = guess_lexer_for_filename(document.fileName, inputText)
        
        # Highlight the code.
        hilightedText = highlight(inputText, lexer, HtmlFormatter())

        # Prepare for Remark output.
        hilightedText = string.split(hilightedText, '\n')
       
        return hilightedText

    def outputType(self):
        return 'html'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Code', Code_Macro())
registerMacro('GenericCode', Code_Macro())


