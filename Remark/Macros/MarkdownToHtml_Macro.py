import string

from Remark.Common import readFile
from Remark.MacroRegistry import registerMacro

import markdown

markdownConverter = markdown.Markdown()

class MarkdownToHtml_Macro:
    def expand(self, parameter, document, documentTree):
        text = parameter
        
        # Convert Markdown to html
        
        htmlString = markdownConverter.convert(string.join(text, '\n'))
        htmlText = string.split(htmlString, '\n')
            
        return htmlText

registerMacro('MarkdownToHtml', MarkdownToHtml_Macro())
