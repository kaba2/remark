# -*- coding: utf-8 -*-

# Description: Remark tag parser
# Detail: Parses the description-tag from the header, and tags based on names.
# Documentation: tag_parsers.txt

from Dictionary_TagParser import Dictionary_TagParser
from FileSystem import openFileUtf8, globalOptions

import string
import re
import codecs
         
class Remark_TagParser(object):
    def __init__(self, tagMap):
        self.dictionaryParser = Dictionary_TagParser(tagMap)
        
    def parse(self, fileName, maxLines, reporter):
        # Let the generic parser handle those tags
        # which can be found via regular expressions.
        tagSet = self.dictionaryParser.parse(fileName, maxLines, reporter)
        
        # This way we only have to handle the description.
        # The description is a file line which precedes
        # a row of equality signs.                 
        lineRegex = re.compile(r'[ \t]*((==+=)|(--+-))')
        previousLine = ''
        
        with openFileUtf8(fileName) as file:
            lineNumber = 0
            for fileLine in file:
                # Search for a description
                match = lineRegex.search(fileLine)
                if match != None:
                    # We have found a header!
                    tagSet['description'] = [string.strip(previousLine)]
                    break
                    
                # We want to remember the previous line
                # to be able to give the description when
                # we detect a header line.
                previousLine = fileLine
                lineNumber += 1
                if lineNumber >= maxLines:
                    # All tags must appear within 'maxLines' lines. 
                    break
        return tagSet
