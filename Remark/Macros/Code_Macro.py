# -*- coding: utf-8 -*-

# Description: Code macro
# Detail: Generates colored html from many kinds of source code.

import string

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import readFile, unixDirectoryName, htmlInject

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
            try:
                lexer = guess_lexer(inputText)
            except:
                remark.reporter.reportWarning(
                    'The code-type cannot be guessed from the content by Pygments. ' + 
                    'Setting code-type to text.', 'invalid-input')
                lexer = get_lexer_by_name('text')
        
        # Highlight the code.
        hilightedText = highlight(inputText, lexer, HtmlFormatter())

        # Prepare for Remark output.
        hilightedText = string.split(hilightedText, '\n')
       
        return htmlInject(hilightedText)

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('Code', Code_Macro())
registerMacro('GenericCode', Code_Macro())


