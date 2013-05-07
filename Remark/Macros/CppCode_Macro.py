# -*- coding: utf-8 -*-

# Description: CppCode macro
# Detail: Generates colored html from C++ source code. 

import string
import re

from Macro_Registry import registerMacro
from FileSystem import unixRelativePath, unixDirectoryName, globalOptions

from pygments import highlight
from pygments.lexers import CppLexer
from pygments.formatters import HtmlFormatter
    
class CppCode_Macro(object):
    def name(self):
        return 'CppCode'

    def expand(self, parameter, remark):
        # Extract the documentation for types and functions.
        text = self._extractDocumentation(parameter)
        
        # Hilight the text.
        hilightedText = highlight(string.join(parameter, '\n'), CppLexer(), HtmlFormatter())

        # Prepare for Remark output.
        hilightedText = string.split(hilightedText, '\n')

        # Copy the source and replace the includes with links.
        includeRegex = re.compile(r'(#include[ \t]+(?:(?:&quot)|(?:&lt));)(.*)((?:(?:&quot)|(?:&gt));)')
        replacer = lambda match: self._linkConverter(match, remark)

        for line in hilightedText:
            # Replace include file names with links to source files.
            text.append(re.sub(includeRegex, replacer, line))
        
        return text

    def outputType(self):
        return 'html'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

    def _extractDocumentation(self, text):
        text = []

        # linearText = "\n".join(text)
        # linearText.expandtabs(globalOptions().tabSize)

        # oneLineRegexStr = r'(?://!(.*)\n)'
        # multiLineRegexStr = r'(?:/\*![ \t]*(.*)\*/)'
        # documentRegex = re.compile( 
        #    oneLineRegexStr + r'|' +
        #    multiLineRegexStr)

        return text

    def _linkConverter(self, regexMatch, remark):
        document = remark.document
        documentTree = remark.documentTree 
        
        searchName = unixDirectoryName(regexMatch.group(2))
        includeName = regexMatch.group(2)
    
        linkDocument, unique = documentTree.findDocument(searchName, document.relativeDirectory, 
                                                         checkShorter = False)

        if not unique:
            # We don't accept ambiguous links.
            remark.reportWarning('Include filename ' + searchName + 
                                 ' is ambiguous. Skipping linking.', 
                                 'ambiguous-include')
            linkDocument = None
        
        if linkDocument == None:
            # No file was found. Skip linking.
            return regexMatch.group(0)

        linkName = unixRelativePath(document.relativeDirectory, linkDocument.relativeName) + '.htm'
        return regexMatch.group(1) + '<a href = "' + linkName + '">' + includeName + '</a>' + string.rstrip(regexMatch.group(3))

registerMacro('CppCode', CppCode_Macro())
