from Remark.Common import readFile
from Remark.MacroRegistry import registerMacro

class Body_Macro:
    def expand(self, parameter, document, documentTree):
        text = readFile(document.fullName)
            
        return text

registerMacro('Body', Body_Macro())
