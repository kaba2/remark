# -*- coding: utf-8 -*-

# Description: Generic_TagParser class
# Documentation: tag_parsers.txt

from Common import openFileUtfOrLatin

import string

class Generic_TagParser:
    def __init__(self, tagRegexMap, maxLines = 100):
        self.tagRegexMap = tagRegexMap
        self.maxLines = maxLines

    def parse(self, fileName):
        tagSet = {}
        with openFileUtfOrLatin(fileName) as file:
            lineNumber = 0
            for fileLine in file:
                for tagName, tagRegex in self.tagRegexMap.iteritems():
                    match = tagRegex.search(fileLine)
                    if match != None:
                        if tagName in tagSet and tagSet[tagName] != '':
                            print 'Warning:', fileName, 
                            print ': Multiple definitions for the tag', 
                            print tagName                         
                        else:
                            tagSet[tagName] = string.strip(match.group(1))
                        break
                lineNumber += 1
                if lineNumber >= self.maxLines:
                    # All tags must occur within 'maxLines' lines.
                    break
        return tagSet
