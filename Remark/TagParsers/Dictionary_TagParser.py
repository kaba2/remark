# -*- coding: utf-8 -*-

# Description: Dictionary tag parser
# Detail: Searches for tags based on tag-key : tag-text patterns.
# Documentation: tag_parsers.txt

from Common import openFileUtfOrLatin

import re
import string

class Dictionary_TagParser(object):
    def __init__(self, tagMap, maxLines = 100):
        '''
        Searches for tag-definitions of the form tag-key : tag-text
        where tag-key and tag-text are both strings and the tag-text 
        reaches to the end of the line. There can be optional 
        whitespace surrounding the colon.

        tagMap (string --> string):
        A map from a tag-name to a tag-key. The map has to
        invertible; there is a unique tag-name for each tag-key.        
        For example: {'description' : 'Description', ...}

        maxLines:
        Maximum number of lines to parse.
        '''
        self.maxLines = maxLines
        
        # Construct a regex of the form
        # (tag1|tag2|tag3|...) : text
        # the parentheses capture the tag-key,
        # while text captures the tag-text.
        tags = 0

        # This is meant to cover for the possible comment mark.
        # By excluding preceding numbers and letters we cut off
        # the possibility of it being something else than a
        # tag-key : tag-text pattern.
        regex = r'^[^a-zA-Z0-9:]*'
        #regex = r'^.*'
                
        # The tag-key (captured).
        regex += r'('
        for tagKey in tagMap.itervalues():
            # The tag-name may contain characters that
            # are meta-characters in a regular expression.
            # Therefore we need to escape the tag-names.
            regex += re.escape(tagKey.strip())
            if tags > 0 and tags < len(tagMap) - 1:
                regex += r'|'
            tags +=1
        regex += r')'
        
        # The :, but not ::, surrounded by whitespace.
        # The :: is common in C++. For example, I had
        # a source-code line which began with 'Detail::'.
        regex += r'[ \t]*:(?!:)[ \t]*'
        
        # The tag-text (captured). It extends to the end of the line.
        regex += r'(.*)'

        # Compile the regex to a regex-object.
        self.tagRegex = re.compile(regex)

        # Construct a mapping from keys to tag-names.
        # This is needed because the regex searches
        # for the tag-keys.
        self.tagKeyMap = {}
        for tagName, tagKey in tagMap.items():
            self.tagKeyMap[tagKey] = tagName
                
    def parse(self, fileName):
        tagSet = {}
        with openFileUtfOrLatin(fileName) as file:
            lineNumber = 0
            for fileLine in file:
                match = self.tagRegex.match(fileLine)
                if match != None:
                    # The first group is the tag-name.
                    tagKey = match.group(1)
                    # The second group is the tag-text.
                    tagText = match.group(2).strip()
                    
                    # Find out the corresponding tag-name.
                    tagName = self.tagKeyMap.get(tagKey)
                    assert tagName != None

                    # See if the tag has already been defined.
                    if tagSet.get(tagName, [''])[0] != '':
                        # The tag has already been defined.
                        # Ignore the later definition.
                        print
                        print 'Warning:', fileName, 
                        print ": Extraneous definition for the tag '" + tagName + "'"
                        print 'Current:', tagSet[tagName][0]
                        print 'New:', tagText
                    else:
                        tagSet[tagName] = [tagText]

                lineNumber += 1
                if lineNumber >= self.maxLines:
                    # All tags must occur within 'maxLines' lines.
                    break
        return tagSet


