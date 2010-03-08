# -*- coding: utf-8 -*-

# Description: DocChildren_Macro class
# Detail: Generates links to documentation children.

from MacroRegistry import registerMacro
from Common import linkAddress, outputDocumentName, linkTable

class DocChildren_Macro:
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        documentTree = remarkConverter.documentTree
        scope = remarkConverter.scopeStack.top()
        
        targetDirectory = document.relativeDirectory

        # Construct the ignore set.
        ignoreList = scope.search('DocChildren.no_links_for')
        if ignoreList == None:
            ignoreList = []
        # The files to ignore are given by relative names
        # and may use the implicit parent directory search.
        # Therefore we need to first find the document which
        # is meant.
        for i in range(0, len(ignoreList)):
            ignoreDocument = documentTree.findDocumentOutwards(ignoreList[i], document.relativeDirectory)
            if ignoreDocument != None:
                # Only now do we have a comparable relative name.
                ignoreList[i] = ignoreDocument.relativeName
            else:
                ignoreList[i] = None 
        ignoreSet = set(ignoreList)

        childSet = [child for child in document.childSet.itervalues() if child.extension == '.txt' and not child.relativeName in ignoreSet]
        
        if len(childSet) == 0:
            return []

        title = 'Learn more'
        
        scopeTitle = scope.search('DocChildren.title')
        if scopeTitle != None:
            if len(scopeTitle) != 1:
                remarkConverter.reportWarning('DocChildren: \'DocChildren.title\' should be a one-line parameter. Ignoring it and using the default.')
            else:
                title = scopeTitle[0]
            
           
        text = ['\n' + title, '-' * len(title) + '\n']
        
        linkSet = []
                
        childSet.sort(lambda x, y: cmp(x.tag('description'), y.tag('description')))        
        for child in childSet:
            linkTarget = linkAddress(targetDirectory, child.relativeName)
            linkDescription = child.tag('description')
            linkSet.append((outputDocumentName(linkTarget), linkDescription))
            
        text += linkTable(linkSet)
                               
        return text

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('DocChildren', DocChildren_Macro())
