# -*- coding: utf-8 -*-

# Description: CppCode macro
# Detail: Generates colored html from C++ source code. 

import string
import re

from MacroRegistry import registerMacro
from FileSystem import unixRelativePath, unixDirectoryName
from Document import documentRelativeName, Dependency

from pygments import highlight
from pygments.lexers import CppLexer
from pygments.formatters import HtmlFormatter
    
class CppCode_Macro(object):
    def name(self):
        return 'CppCode'

    def expand(self, parameter, remark):
        text = []
        dependencySet = set()
        
        # Hilight the text.
        hilightedText = highlight(string.join(parameter, '\n'), CppLexer(), HtmlFormatter())

        # Prepare for Remark output.
        hilightedText = string.split(hilightedText, '\n')

        # Copy the source and replace the includes with links.
        includeRegex = re.compile(r'(#include[ \t]+(?:(?:&quot)|(?:&lt));)(.*)((?:(?:&quot)|(?:&gt));)')
        replacer = lambda match: self._linkConverter(match, remark, dependencySet)
        
        for line in hilightedText:
            # Replace include file names with links to source files.
            text.append(re.sub(includeRegex, replacer, line))
        
        return text, dependencySet

    def outputType(self):
        return 'html'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

    def findDependency(self, searchName, document, documentTree, parameter = ''):
        linkDocument, unique = documentTree.findDocument(searchName, document.relativeDirectory, 
                                                         checkShorter = False)
        return linkDocument, unique

    def _linkConverter(self, regexMatch, remark, dependencySet):
        document = remark.document
        documentTree = remark.documentTree 
        
        searchName = unixDirectoryName(regexMatch.group(2))
        includeName = regexMatch.group(2)
    
        linkDocument, unique = self.findDependency(searchName, document, documentTree)
        dependencySet.add(Dependency(searchName, documentRelativeName(linkDocument), self.name()))

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
