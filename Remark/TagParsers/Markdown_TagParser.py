# -*- coding: utf-8 -*-

# Description: Markdown_TagParser class
# Documentation: tag_parsers.txt

from Generic_TagParser import Generic_TagParser

import string
import re
import codecs
         
class Markdown_TagParser:
    def __init__(self, tagSet, maxLines):
        self.genericParser = Generic_TagParser(tagSet, maxLines)
        self.maxLines = maxLines
        
    def parse(self, document):
        # Let the generic parser handle those tags
        # which can be found via regular expressions.
        
        self.genericParser.parse(document)
        
        # This way we only have to handle the description.
        # The description is a file line which precedes
        # a row of equality signs. 
                
        lineRegex = re.compile(r'[ \t]*((==+=)|(--+-))')
        previousLine = ''
        
        with codecs.open(document.fullName, mode = 'rU', encoding = 'utf-8-sig') as file:
            lineNumber = 0
            for fileLine in file:
                # Search for a description
                
                match = lineRegex.search(fileLine)
                if match != None:
                    # We have found a header!
                    document.tagSet['description'] = string.strip(previousLine)
                    return
                    
                # We want to remember the previous line
                # to be able to give the description when
                # we detect a header line.
                
                previousLine = fileLine
                lineNumber += 1
                if lineNumber >= self.maxLines:
                    # All tags must appear within 'maxLines' lines. 
                    break
