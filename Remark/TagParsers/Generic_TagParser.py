import string

class Generic_TagParser:
    def __init__(self, tagSet):
        self.tagSet = tagSet

    def parse(self, document):
        with open(document.fullName, 'r') as file:
            for fileLine in file:
                for tagName, tagRegex in self.tagSet.iteritems():
                    match = tagRegex.search(fileLine)
                    if match != None:
                        if tagName in document.tagSet and document.tagSet[tagName] != '':
                            print 'Warning:', document.relativeName, 
                            print ': Multiple definitions for the tag', 
                            print tagName                         
                        else:
                            document.tagSet[tagName] = string.strip(match.group(1))
                        break
