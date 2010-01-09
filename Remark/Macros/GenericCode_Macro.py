# -*- coding: utf-8 -*-

# Description: GenericCode_Macro class
# Detail: Generates colored html from many kinds of source code.

import os.path
import string

from MacroRegistry import registerMacro
from Common import readFile, remarkLink, unixDirectoryName

from pygments import highlight
from pygments.lexers import guess_lexer, guess_lexer_for_filename
from pygments.formatters import HtmlFormatter

class GenericCode_Macro:
    def expand(self, parameter, document, documentTree, scope):
        # If no parameter is given, then the
        # code is read from the document's file.
        # Otherwise, the parameter is assumed to        
        # contain some source code.
        if parameter == []:
            text = readFile(document.fullName)
        else:
            text = parameter

        fileName = os.path.split(document.relativeName)[1]
        
        convertedText = []

        # In the case the code is read from a file,
        # we want to include a title, a back-link,
        # and a directory link.
        if parameter == []:
            # Create the title
            convertedText.append(fileName)
            convertedText.append('=' * len(fileName))
            convertedText.append('')
            
            # Create parent link.
            convertedText.append('[[Parent]]')
            convertedText.append('')
        
            # Create directory link.
            convertedText += remarkLink(unixDirectoryName(document.relativeDirectory) + '/', 'directory.htm')
            convertedText.append('')
        
        # This 'div' allows, for example, to create
        # a box around the code.
        convertedText.append('[[SkipExpansion]]:')
        convertedText.append('\t<div class = "codehilite">')

        # Try to guess the type of the code.
        inputText = string.join(text, '\n')
        lexer = None
        if parameter == []:
            # In the case the code was loaded from a file, we
            # primarily use its extension to guess the type
            # of the code file. If this does not succeed,
            # then the content of the code is examined.
            lexer = guess_lexer_for_filename(document.fileName, inputText)
        else:
            # Otherwise we can only examine the code. 
            lexer = guess_lexer(inputText)
        
        # Highlight the code.
        hilightedText = highlight(inputText, lexer, HtmlFormatter())
        hilightedText = string.split(hilightedText, '\n')
        
        # Replace every empty line with dummy html.
        for line in hilightedText:
            if string.strip(line) == '':
                # Empty line. Generate something dummy.
                # This needs to be done because Markdown
                # thinks the html-markup ends in a blank line.
                convertedText.append('\t<span class="p"></span>')
            else:
                convertedText.append('\t' + line)
                                
        convertedText.append('\t</div>\n')
        
        return convertedText

    def pureOutput(self):
        return False

registerMacro('GenericCode', GenericCode_Macro())
