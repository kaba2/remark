import os.path
import string
import re

from Remark.MacroRegistry import registerMacro
from Remark.Common import readFile, remarkLink, unixDirectoryName

from pygments import highlight
from pygments.lexers import CppLexer
from pygments.formatters import HtmlFormatter

def _linkConverter(regexMatch, documentTree, document):
    searchName = os.path.normpath(regexMatch.group(2))
    includeName = regexMatch.group(2)
    #print "Include name:", includeName
    #print "My name:", document.relativeName
    linkDocument = documentTree.findDocumentByName(searchName)
    if linkDocument != None:
        linkName = os.path.normpath(os.path.relpath(linkDocument.relativeName, document.relativeDirectory)) + '.htm'
        return regexMatch.group(1) + '<a href = "' + linkName + '">' + includeName + '</a>' + string.rstrip(regexMatch.group(3))
    return regexMatch.group(0)

class CppCode_Macro:
    def expand(self, parameter, document, documentTree):
        # If no parameter is given, then the
        # code is read from the document's file.
        # Otherwise, the parameter is assumed to        
        # contain C++ code.
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
            convertedText.append('\n')
            
            # Create parent link.
            convertedText.append('[Parent]\n')
        
            # Create directory link.
            convertedText += remarkLink(unixDirectoryName(document.relativeDirectory) + '/', 'directory.index.htm')
        
        # This 'div' allows, for example, to create
        # a box around the code.
        convertedText.append('<div class = "codehilite">')

        includeRegex = re.compile(r'(#include[ \t]+(?:(?:&quot)|(?:&lt));)(.*)((?:(?:&quot)|(?:&gt));)')

        # Copy the source.
        replacer = lambda match: _linkConverter(match, documentTree, document)
        hilightedText = highlight(string.join(text, '\n'), CppLexer(), HtmlFormatter())
        hilightedText = string.split(hilightedText, '\n')
        for line in hilightedText:
            if string.strip(line) == '':
                # Empty line. Generate something dummy.
                # This needs to be done because Markdown
                # thinks the html-markup ends in a blank line.
                convertedText.append('<span class="p"></span>')
            else:
                # Replace include file names with links to source files.
                convertedText.append(re.sub(includeRegex, replacer, line))
                                
        convertedText.append('</div>\n')
        
        return convertedText

registerMacro('CppCode', CppCode_Macro())
