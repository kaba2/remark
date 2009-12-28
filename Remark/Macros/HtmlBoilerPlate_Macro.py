# Description: HtmlBoilerPlate_Macro class
# Detail: Generates surrounding html code to include css-stylesheets etc.
# Documentation: macros.txt

import os.path
import datetime

from Remark.MacroRegistry import registerMacro

class HtmlBoilerPlate_Macro:
    def expand(self, parameter, document, documentTree, scope):
        text = parameter
        remarkDirectory = os.path.relpath('remark', document.relativeDirectory)
        
        # Add boilerplate code.
        
        now = datetime.datetime.now()
        timeText = now.strftime("%d.%m.%Y %H:%M")
                
        htmlText = []
        htmlText.append('<?xml version="1.0" encoding="UTF-8"?>')
        htmlText.append('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
        htmlText.append('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-US" lang="en-US">')
        htmlText.append('<head>')
        htmlText.append('<title>' + document.tag('description') + '</title>')
        htmlText.append('<link rel="stylesheet" type="text/css" href="' + os.path.join(remarkDirectory, 'global.css') + '" />')
        htmlText.append('<link rel="stylesheet" type="text/css" href="' + os.path.join(remarkDirectory, 'pygments.css') + '" />')
        htmlText.append('<meta http-equiv="Content-Type" content="text/html; charset=utf-8"></meta>')
        htmlText.append('<script type="text/javascript" src="' + os.path.join(remarkDirectory, 'ASCIIMathMLwFallback.js') + '"></script>')
        htmlText.append('</head>')
        htmlText.append('<body>')
        htmlText.append('<div id = "container">')
        htmlText.append('<div id = "mark">')
        htmlText += text
        htmlText.append('</div>')
        htmlText.append('<div id="footer">')
        htmlText.append('<p>Remark documentation system - Page generated ' + timeText + '.</p>')
        htmlText.append('</div>')
        htmlText.append('</div>')
        htmlText.append('</body>')
        htmlText.append('</html>')
    
        return htmlText

registerMacro('HtmlBoilerPlate', HtmlBoilerPlate_Macro())
