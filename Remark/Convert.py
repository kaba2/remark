# Description: Macro expansion algorithm, variables, and html conversion.
# Documentation: implementation.txt

import re
import string
import os
import os.path
import datetime

from Remark.MacroRegistry import findMacro
from Remark.Common import changeExtension, outputDocumentName, resetLinkId

class Scope:
    def __init__(self, parent):
        self.parent_ = parent
        self.nameSet_ = dict()
        
    def insert(self, name, data):
        self.nameSet_[name] = data
        
    def append(self, name, data):
        result = self.recursiveSearch(name)
        if result != None:
            result += data
        else:
            self.insert(name, data)

    def parent(self):
        return self.parent_
    
    def search(self, name):
        if name in self.nameSet_:
            return self.nameSet_[name]
        return None
    
    def recursiveSearch(self, name):
        #print 'Recursive search for', name
        result = self.search(name)        
        if result != None:
            return result
        if self.parent_ != None:
            return self.parent_.recursiveSearch(name)
        return None     

class ScopeStack:
    def __init__(self):
        self.stack_ = []
        
    def open(self):
        #print 'Scope opened.'
        parent = None
        if len(self.stack_) > 0:
            parent = self.top()                
        self.stack_.append(Scope(parent))
        
    def close(self):
        #print 'Scope closed.'
        self.stack_.pop()
        
    def top(self):
        return self.stack_[-1]        

_scopeStack = ScopeStack()

def expandMacros(template, document, documentTree):
    if template == []:
        return []
    
    global _scopeStack
    
    text = template[:]
    macroText = r'((?:(?!]]).)*)'
    optionalOneLineParameter = r'(?::[ \t]*(.*))?'
    macroRegex = re.compile(r'\[\[' + macroText + r'\]\]' + optionalOneLineParameter)
    i = 0
    while i < len(text):
        line = text[i]
        
        # Indented stuff is copied verbatim.
        if len(line) > 0 and line[0] == '\t':
            i += 1
            continue
        
        # See if there is a macro somewhere on the line.
        match = re.search(macroRegex, line)
        if match == None:
            # There is no macro on the line: 
            # copy the line verbatim.
            i += 1
            continue

        # Check that the macro begins the line.
        if match.start() != 0:
            print 'Warning:', document.relativeName, ': macro', match.group(0), 
            print 'has bad indentation. Ignoring it.'
            i += 1
            continue

        # Next we want to determine the parameter
        # of the macro. There are three possibilities:
        #
        # 1) There is no parameter. In this case the
        # entry is of the form '[[Macro]]'.
        #
        # 2) There is a one-line parameter. In this case
        # the entry is of the form '[[Macro]]: parameter here'.
        #
        # 3) There is a multi-line parameter. In this case
        # the entry is of the form:
        # [[Macro]]:
        #     Parameters
        #     here
        #
        #     More parameters
        
        #print 'Found macro:', match.group(1)
        parameterSet = []
        
        # Whether a macro has parameters is given by
        # whether there is a ':' after the macro.        
        hasParameters = (match.group(2) != None)
        
        # Check whether the parameter is one-line.
        if hasParameters:
            # A parameter is one-line if:
            # 1) The regex matched the group 2.
            # 2) The group 2 is not all whitespace.
            parameter = string.strip(match.group(2))
            if parameter != '':
                # One-line parameter
                parameterSet.append(parameter)
        
        # Check whether the parameter is multi-line.
        # This must be the case if there is a parameter,
        # but no one-line parameter was given.        
        endLine = i + 1
        if hasParameters and parameterSet == []:
            # The parameter is multi-line.
            # Next we need to see which lines are 
            # part of the parameter.
            
            # Find out the extent of the parameter.
            while endLine < len(text):
                # The end of a multi-line parameter
                # is marked by a line which is not all whitespace
                # and has no indentation (relative to the
                # indentation of the macro). 
                if _leadingTabs(text[endLine]) == 0 and string.strip(text[endLine]) != '':
                    break
                endLine += 1
                
            # Copy the parameter and remove the indentation from it.
            parameterSet = [_removeLeadingTabs(line, 1) for line in text[i + 1 : endLine]]
        
        # Remove the macro from further expansion.
        text[i : endLine] = []
        
        # Remove the possible empty trailing parameter lines.
        nonEmptyLines = len(parameterSet)
        while nonEmptyLines > 0:
            if string.strip(parameterSet[nonEmptyLines - 1]) == '':
                nonEmptyLines -= 1
            else:
                break
        parameterSet = parameterSet[0 : nonEmptyLines]            
        
        # The macros in the parameter are _not_ recursively
        # expanded. This would lead to problems in those
        # cases where macro expansion is not meant to happen.
        
        # Expand the macro.
        macroHandled = False
        macroName = match.group(1)
        macroPartSet = string.split(macroName)
        
        scope = _scopeStack.top()
       
        if len(macroPartSet) == 1:
            macro = findMacro(macroName)
            suppressList = scope.recursiveSearch('suppress_calls_to')
            if suppressList == None:
                suppressList = []
            if macro != None:
                if not macroName in suppressList:
                    expandedText = macro.expand(parameterSet, document, documentTree, scope)
                    text[i : i] = expandedText
                    if macro.pureOutput():
                        i += len(expandedText) 
                macroHandled = True
                #print 'Applying', macroName, 'yields:'
                #for line in text:
                #    print line
        elif len(macroPartSet) == 2:
            #print macroPartSet
            if string.lower(macroPartSet[0]) == 'set':
                # Setting a scope variable.
                #print 'Setting stuff!', parameterSet
                scope.insert(macroPartSet[1], parameterSet)
                macroHandled = True
            elif string.lower(macroPartSet[0]) == 'add':
                # Appending to a scope variable.
                scope.append(macroPartSet[1], parameterSet)
                macroHandled = True
            elif string.lower(macroPartSet[0]) == 'get':
                # Getting a scope variable.
                result = scope.recursiveSearch(macroPartSet[1])
                if result != None:
                    #print result
                    text[i : i] = result
                else:
                    print 'Warning:', document.relativeName, ': get: Variable \'' + macroPartSet[1] + '\' not found. Ignoring it.'
                macroHandled = True

        if not macroHandled:
            print 'Warning:', document.relativeName, ': Don\'t know how to handle macro', match.group(0), '. Ignoring it.'
            i += 1
            continue
        
#    if len(scope.nameSet_) > 0:
#        print 'I has scope variables! They are:'
#        for (name, data) in scope.nameSet_.iteritems():
#            print name, ':'
#            print data
                       
    return text

import markdown

markdownConverter = markdown.Markdown()

def convertMarkdownToHtml(text):
    global markdownConverter
    
    htmlString = markdownConverter.convert(string.join(text, '\n'))
    htmlText = string.split(htmlString, '\n')
        
    return htmlText

def addHtmlBoilerPlate(text, document):
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


def convert(template, document, documentTree, targetRootDirectory):
    print document.relativeName, '...'
    
    #if document.fileName != 'pastel.txt':
    #    return
    
    resetLinkId()
              
    # Expand macros.
    global _scopeStack
    _scopeStack.open()
    text = expandMacros(template, document, documentTree)
    _scopeStack.close()
    
    # Convert Markdown to html.
    text = convertMarkdownToHtml(text)
    
    # Add html boilerplate.
    text = addHtmlBoilerPlate(text, document)

    # Find out some names.
    targetRootDirectory = os.path.normpath(targetRootDirectory)
    targetRelativeName = outputDocumentName(document.relativeName)
    targetFullName = os.path.join(targetRootDirectory, targetRelativeName)

    # If the directories do not exist, create them.
    targetDirectory = os.path.split(targetFullName)[0]
    if not os.path.exists(targetDirectory):
        os.makedirs(targetDirectory)
        
    # Save the text to a file.
    with open(targetFullName, 'w') as outputFile:
        for line in text:
            outputFile.write(line)
            outputFile.write('\n')

def convertAll(documentTree, targetRootDirectory, templateMap):
    for document in documentTree.documentMap.itervalues():
        template = templateMap[document.extension]
        if not document.extension in templateMap:
            continue
        convert(template, document, documentTree, targetRootDirectory)

def _leadingTabs(text):
    tabs = 0
    for c in text:
        if c == '\t':
            tabs += 1
        else:
            break
    return tabs

def _removeLeadingTabs(text, tabs):
    i = 0
    while i < len(text) and text[i] == '\t' and i < tabs:
        i += 1
    return text[i :]
