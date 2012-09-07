# -*- coding: utf-8 -*-

# Description: CppCode macro
# Detail: Generates colored html from C++ source code. 

import string
import re

from MacroRegistry import registerMacro

from Common import unixRelativePath, unixDirectoryName

from pygments import highlight
from pygments.lexers import CppLexer
from pygments.formatters import HtmlFormatter

def _linkConverter(regexMatch, remark):
    document = remark.document
    documentTree = remark.documentTree 
        
    searchName = unixDirectoryName(regexMatch.group(2))
    includeName = regexMatch.group(2)
    
    # First interpret the include filename as
    # a relative path w.r.t. the current directory.
    linkDocument = documentTree.findDocumentLocal(searchName, document.relativeDirectory)
    
    if linkDocument == None:
        # No file was found. Now interpret the
        # include filename as a relative path w.r.t.
        # the input root directory.
        linkDocument = documentTree.findDocumentByRelativeName(searchName)
        
    if linkDocument == None:
        # Still no file was found. Try hard.
        linkDocument, unique = documentTree.findDocument(searchName, document.relativeDirectory)
        if not unique:
            # We don't accept ambiguous links.
            remark.reportWarning('Include filename ' + searchName + 
                                          ' is ambiguous. Skipping linking.')
            linkDocument = None
        
    if linkDocument == None:
        # No file was found. Skip linking.
        return regexMatch.group(0)

    linkName = unixRelativePath(document.relativeDirectory, linkDocument.relativeName) + '.htm'
    return regexMatch.group(1) + '<a href = "' + linkName + '">' + includeName + '</a>' + string.rstrip(regexMatch.group(3))
    
class CppCode_Macro(object):
    def name(self):
        return 'CppCode'

    def expand(self, parameter, remark):
        # Hilight the text.
        hilightedText = highlight(string.join(parameter, '\n'), CppLexer(), HtmlFormatter())

        # Prepare for Remark output.
        hilightedText = string.split(hilightedText, '\n')
        
        # Copy the source and replace the includes with links.
        includeRegex = re.compile(r'(#include[ \t]+(?:(?:&quot)|(?:&lt));)(.*)((?:(?:&quot)|(?:&gt));)')
        replacer = lambda match: _linkConverter(match, remark)
        convertedText = []
        for line in hilightedText:
            # Replace include file names with links to source files.
            convertedText.append(re.sub(includeRegex, replacer, line))
        
        return convertedText

    def outputType(self):
        return 'html'

    def pureOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('CppCode', CppCode_Macro())
