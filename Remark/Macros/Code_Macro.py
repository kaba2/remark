# -*- coding: utf-8 -*-

# Description: Code macro
# Detail: Generates colored html from many kinds of source code.

import string

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import readFile, unixDirectoryName

from pygments import highlight
from pygments.lexers import guess_lexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter

class Code_Macro(object):
    def name(self):
        return 'Code'

    def expand(self, parameter, remark):
        document = remark.document
        
        scope = remark.scopeStack.top()
        codeType = scope.getString('Code.type', '')

        lexer = None
        if codeType != '':
            # The code-type was given explicitly.
            # See if we can find a corresponding pygments lexer.
            try:
                lexer = get_lexer_by_name(codeType)
            except:
                remark.reporter.reportWarning(
                    'The code-type ' + codeType + ' is not recognized by Pygments. ' +
                    'Guessing code-type from content.', 'invalid-input')

        # Prepare for Pygments input.
        inputText = '\n'.join(parameter)

        if lexer == None:
            # Try to guess the type of the code.
            lexer = guess_lexer(inputText)
        
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


