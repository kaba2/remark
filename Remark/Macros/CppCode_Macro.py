# -*- coding: utf-8 -*-

# Description: CppCode_Macro class
# Detail: Generates colored html from C++ source code. 

import os.path
import string
import re

from MacroRegistry import registerMacro
from Common import readFile, remarkLink, unixDirectoryName

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
        return regexMatch.group(1) + '<a href = "' + unixDirectoryName(linkName) + '">' + includeName + '</a>' + string.rstrip(regexMatch.group(3))
    return regexMatch.group(0)

class CppCode_Macro:
    def expand(self, parameter, document, documentTree, scope):
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
            convertedText.append('')
            
            # Create parent link.
            convertedText.append('[[Parent]]')
            convertedText.append('')
            #convertedText += expandMacros(['[[Parent]]\n'], document, documentTree)
        
            # Create directory link.
            convertedText += remarkLink(unixDirectoryName(document.relativeDirectory) + '/', 'directory.htm')
            convertedText.append('')
        
        # This 'div' allows, for example, to create
        # a box around the code.
        convertedText.append('[[Html]]:')
        convertedText.append('\t<div class = "codehilite">')

        includeRegex = re.compile(r'(#include[ \t]+(?:(?:&quot)|(?:&lt));)(.*)((?:(?:&quot)|(?:&gt));)')

        # Copy the source.
        replacer = lambda match: _linkConverter(match, documentTree, document)
        hilightedText = highlight(string.join(text, '\n'), CppLexer(), HtmlFormatter())
        hilightedText = string.split(hilightedText, '\n')
        for line in hilightedText:
            # Replace include file names with links to source files.
            convertedText.append('\t' + re.sub(includeRegex, replacer, line))
                                
        convertedText.append('\t</div>\n')
        
        return convertedText

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

registerMacro('CppCode', CppCode_Macro())
