# -*- coding: utf-8 -*-

# Description: Generic_TagParser class
# Documentation: tag_parsers.txt

import string
import codecs

class Generic_TagParser:
    def __init__(self, tagSet, maxLines = 100):
        self.tagSet = tagSet
        self.maxLines = maxLines

    def parse(self, document):
        with codecs.open(document.fullName, mode = 'rU', encoding = 'utf-8-sig') as file:
            lineNumber = 0
            for fileLine in file:
                for tagName, tagRegex in self.tagSet.iteritems():
                    match = tagRegex.match(fileLine)
                    if match != None:
                        if tagName in document.tagSet and document.tagSet[tagName] != '':
                            print 'Warning:', document.relativeName, 
                            print ': Multiple definitions for the tag', 
                            print tagName                         
                        else:
                            document.tagSet[tagName] = string.strip(match.group(1))
                        break
                lineNumber += 1
                if lineNumber >= self.maxLines:
                    # All tags must occur within 'maxLines' lines.
                    break
