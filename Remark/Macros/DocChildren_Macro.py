# -*- coding: utf-8 -*-

# Description: DocChildren macro
# Detail: Generates links to documentation children.

from MacroRegistry import registerMacro
from Common import unixRelativePath, outputDocumentName, htmlDiv

class DocChildren_Macro(object):
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        documentTree = remarkConverter.documentTree
        scope = remarkConverter.scopeStack.top()

        # Variables
        className = scope.getString('DocChildren.class_name', 'DocChildren')
        title = scope.getString('DocChildren.title', 'Learn more')
        
        # Construct the ignore set.
        ignoreList = scope.search('DocChildren.no_links_for')
        if ignoreList == None:
            ignoreList = []

        # The files to ignore are given by relative names
        # and may use the implicit parent directory search.
        # Therefore we need to first find the document which
        # is meant.
        for i in range(0, len(ignoreList)):
            ignoreDocument = documentTree.findDocumentUpwards(ignoreList[i], document.relativeDirectory)
            if ignoreDocument != None:
                # Only now do we have a comparable relative name.
                ignoreList[i] = ignoreDocument.relativeName
            else:
                ignoreList[i] = None 
        ignoreSet = set(ignoreList)

        # Only accept those child documents which are not on the ignore set.
        childSet = [child for child in document.childSet.itervalues() 
                    if child.extension == '.txt' and not child.relativeName in ignoreSet]
        if len(childSet) == 0:
            return []

        # Create the title.
        text = []
        text.append('')
        text.append(title)
        text.append('---')
        text.append('')
       
        # Sort the links alphabetically by their desciption.        
        childSet.sort(lambda x, y: cmp(x.linkDescription(), y.linkDescription()))        
        
        for child in childSet:
            linkText = remarkConverter.remarkLink(child.linkDescription(),
                                                  document, child)
            text.append('1. ' + linkText)
        
        text.append('')
                               
        return htmlDiv(text, className)

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('DocChildren', DocChildren_Macro())
