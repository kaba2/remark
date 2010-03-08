# -*- coding: utf-8 -*-

# Description: CppCode_Macro class
# Detail: Generates colored html from C++ source code. 

import os.path
import string
import re

from MacroRegistry import registerMacro

from Common import linkAddress

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
        #linkName = os.path.normpath(os.path.relpath(linkDocument.relativeName, document.relativeDirectory)) + '.htm'
        #linkName = unixDirectoryName(linkName)
        linkName = linkAddress(document.relativeDirectory, linkDocument.relativeName) + '.htm'
        return regexMatch.group(1) + '<a href = "' + linkName + '">' + includeName + '</a>' + string.rstrip(regexMatch.group(3))
    return regexMatch.group(0)

class CppCode_Macro:
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        documentTree = remarkConverter.documentTree 
        
        # Hilight the text.
        hilightedText = highlight(string.join(parameter, '\n'), CppLexer(), HtmlFormatter())

        # Prepare for Remark output.
        hilightedText = string.split(hilightedText, '\n')
        
        # Copy the source and replace the includes with links.
        includeRegex = re.compile(r'(#include[ \t]+(?:(?:&quot)|(?:&lt));)(.*)((?:(?:&quot)|(?:&gt));)')
        replacer = lambda match: _linkConverter(match, documentTree, document)
        convertedText = []
        for line in hilightedText:
            # Replace include file names with links to source files.
            convertedText.append(re.sub(includeRegex, replacer, line))
        
        return convertedText

    def outputType(self):
        return 'html'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('CppCode', CppCode_Macro())
