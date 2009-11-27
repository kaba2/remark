from Remark.MacroRegistry import registerMacro
from Remark.Common import linkAddress

class DocChildren_Macro:
    def expand(self, parameter, document, documentTree):
        targetDirectory = document.relativeDirectory
        
        childSet = [child for child in document.childSet.itervalues() if child.extension == '.txt']
        
        if len(childSet) == 0:
            return []
        
        if parameter == []:
            title = '\nLearn more'
        else:
            title = parameter[0]
            
        text = [title, '-' * (len(title) - 1) + '\n']
        
        childSet.sort(lambda x, y: cmp(x.tag('description'), y.tag('description')))        
        for child in childSet:
            linkTarget = linkAddress(targetDirectory, child.relativeName)
            text.append('[Link]: ' + linkTarget)
                
        return text

registerMacro('DocChildren', DocChildren_Macro())
