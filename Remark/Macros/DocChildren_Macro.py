# Description: DocChildren_Macro class
# Detail: Generates links to documentation children.

from MacroRegistry import registerMacro
from Common import linkAddress

class DocChildren_Macro:
    def expand(self, parameter, document, documentTree, scope):
        targetDirectory = document.relativeDirectory
        
        childSet = [child for child in document.childSet.itervalues() if child.extension == '.txt']
        
        if len(childSet) == 0:
            return []

        title = 'Learn more'
        
        scopeTitle = scope.search('DocChildren:title')
        if scopeTitle != None:
            if len(scopeTitle) != 1:
                print 'Warning: DocChildren: \'DocChildren:title\' should be a one-line parameter. Ignoring it and using the default.'
            else:
                title = scopeTitle[0]
            
        ignoreList = scope.search('DocChildren:no_links_for')
        if ignoreList == None:
            ignoreList = []            
        ignoreSet = set(ignoreList)
            
        text = ['\n' + title, '-' * len(title) + '\n']
        
        text.append('[[Link]]:')
        
        childSet.sort(lambda x, y: cmp(x.tag('description'), y.tag('description')))        
        for child in childSet:
            if not child.fileName in ignoreSet:
                linkTarget = linkAddress(targetDirectory, child.relativeName)
                text.append('\t' + linkTarget)
                
        return text

    def pureOutput(self):
        return False

registerMacro('DocChildren', DocChildren_Macro())
