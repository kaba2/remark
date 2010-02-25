# -*- coding: utf-8 -*-

# Description: Macro expansion algorithm, variables, and html conversion.
# Documentation: core_stuff.txt

import re
import string
import os
import os.path
import datetime
import codecs
import copy

from MacroRegistry import findMacro
from Common import changeExtension, outputDocumentName, documentType, unixDirectoryName

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

    def getInteger(self, name, defaultValue):
        value = None
        text = self.search(name)
        
        if text != None and len(text) == 1:
            try:
                value = int(text[0])
            except ValueError:
                None
                
        if value == None:
            print 'Warning: Could not convert', name, 'to an integer. Using default.'
            value = defaultValue
            
        return value

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

class RemarkConverter:
    def __init__(self, document, template, documentTree, 
                 inputRootDirectory, targetRootDirectory):
        self.scopeStack = ScopeStack()
        self.scopeStack.open()
        self.document = document
        self.documentTree = documentTree
        self.linkIndex = 0
        self.linkSet = []
        self.usedMacroSet = []
        self.currentLine = 0
        self.text = []
        self.template = template
        self.inputRootDirectory = inputRootDirectory
        self.targetRootDirectory = targetRootDirectory
        self.used = False
        
    def linkId(self):
        result = self.linkIndex
        self.linkIndex += 1
        return result
        
    def remarkLink(self, description, target):
        # The automatically generated Markdown
        # links are named as 'RemarkLink_x' where
        # x is an integer that runs from 0 upwards
        # as new links are retrieved.        
        name = 'RemarkLink_' + str(self.linkId())
        
        # Form the Markdown link.
        text = ['[' + description + '][' + name + ']']
        
        # We defer defining the link because the link
        # could be an inline link. Instead we store the
        # definitions so that we can output them to the
        # end of the document. 
         
        self.linkSet.append((name, unixDirectoryName(target)))
        
        return text
    
    def reportWarning(self, text):
        print 'Warning:', self.document.relativeName, ':'
        print text 
    
    def extractMacro(self, matchBegin, matchEnd, 
                     wholeGroup, identifierGroup, 
                     inlineGroup, externalGroup):
        # This function finds out the parameter
        # of the macro and then removes the macro
        # invocation from 'text'.

        # There are four possibilities for the
        # macro invocation:
        #
        # 1) There is no parameter. In this case the
        # entry is of the form '[[Macro]]'.
        #
        # 2) There is an inline parameter. In this case
        # the entry is of the form '[[Macro: parameter here]]'.
        #
        # 3) There is a one-line parameter. In this case
        # the entry is of the form '[[Macro]]: parameter here'.
        #
        # 4) There is a multi-line parameter. In this case
        # the entry is of the form:
        # [[Macro]]:
        #     Parameters
        #     here
        #
        #     More parameters
        #
        # Options 3 and 4 are together called external parameters.
        
        # Macros that give an external parameter
        # are required to start at the beginning of the line.
        hasExternalParameters = (externalGroup != None)        
        if hasExternalParameters and matchBegin != 0:
            self.reportWarning(wholeGroup + ': ' + 
                          'Macro invocation with an external parameter must start at the ' +
                          'beginning of the line. Ignoring the macro.')
            self.currentLine += 1
            return None
        
        #print 'Found macro:', match.group(1)
        parameterSet = []
        
        hasInlineParameters = (inlineGroup != None)

        # Macros that give both an external parameter and
        # an inline parameter are disallowed.
        if hasInlineParameters and hasExternalParameters:
            self.reportWarning(wholeGroup + ': ' + 
                               'Inline parameters and external parameters can not be used together. ' +
                               'Ignoring the macro.')
            self.currentLine += 1
            return None
        
        # Extract an inline parameter.
        if hasInlineParameters:
            parameter = string.strip(inlineGroup)
            parameterSet.append(parameter)

        # Extract a one-line parameter.
        hasOnelineParameter = False
        if hasExternalParameters:
            # If the parameter consists of all
            # whitespace, it is a multi-line parameter
            # so ignore that case here.
            parameter = string.strip(externalGroup)
            if parameter != '':
                # One-line parameter
                hasOnelineParameter = True
                parameterSet.append(parameter)
        
        # A macro invocation has parameters if
        # it has either an inline parameter or
        # an external parameter.
        hasParameters = hasInlineParameters or hasExternalParameters 
        
        if hasOnelineParameter:
            # Remove the macro from further expansion.
            # Note that the macro is required to start
            # the line and thus no other text is destroyed here.
            self.text[self.currentLine : self.currentLine + 1] = []
            
        if hasInlineParameters or not hasParameters:
            # Macro invocations with no parameters or with an
            # inline parameter do not necessarily have to be
            # placed at the start of the line.  

            # Store the text before and after the macro.
            textBefore = self.text[self.currentLine][0 : matchBegin]
            textAfter = self.text[self.currentLine][matchEnd : ]
            #print textBefore
            #print textAfter
            
            # Add the text after if its not all whitespace. 
            if string.strip(textAfter) != '':
                self.text[self.currentLine + 1 : self.currentLine + 1] = [textAfter] 
                #print textAfter

            # Remove the macro from the text.
            if string.strip(textBefore) != '':
                self.text[self.currentLine] = textBefore
                #print textBefore
                self.currentLine += 1
            else:
                self.text[self.currentLine : self.currentLine + 1] = []

        # A parameter is multi-line if its external but
        # not one-line.
        hasMultilineParameter = (hasExternalParameters and not hasOnelineParameter)         
                
        if hasMultilineParameter: 
            # The parameter is multi-line.
            # Find out the extent of the parameter.
            endLine = self.currentLine + 1
            while endLine < len(self.text):
                # The end of a multi-line parameter
                # is marked by a line which is not all whitespace
                # and has no indentation (relative to the
                # indentation of the macro). 
                if _leadingTabs(self.text[endLine]) == 0 and string.strip(self.text[endLine]) != '':
                    break
                endLine += 1
                
            # Copy the parameter and remove the indentation from it.
            parameterSet = [_removeLeadingTabs(line, 1) for line in self.text[self.currentLine + 1 : endLine]]
        
            # Remove the macro from further expansion.
            self.text[self.currentLine : endLine] = []
            
            # Remove the possible empty trailing parameter lines.
            nonEmptyLines = len(parameterSet)
            while nonEmptyLines > 0:
                if string.strip(parameterSet[nonEmptyLines - 1]) == '':
                    nonEmptyLines -= 1
                else:
                    break
            parameterSet = parameterSet[0 : nonEmptyLines]
        
        return parameterSet            

    def addText(self, newText, skipExpansion = False):
        self.text[self.currentLine : self.currentLine] = newText
        if skipExpansion:
            self.currentLine += len(newText)

    def addDummyHtmlNewLines(self, htmlText):
        for j in range(0, len(htmlText)):
            if string.strip(htmlText[j]) == '':
                # The Markdown syntax interprets
                # empty lines as ending the html
                # block. This tricks avoids that
                # behaviour. Note that it is not
                # equivalent to simply remove the 
                # line.
                htmlText[j] = '<span class="p"></span>'

    def expandMacro(self, macroIdentifier, parameterSet):
        # This function expands the given macro in
        # the current position.
        scope = self.scopeStack.top()
        
        macroHandled = False
        macroPartSet = string.split(macroIdentifier)
        macroName = macroPartSet[0]        
      
        if macroName == 'set':
            # Setting a scope variable.
            if len(macroPartSet) < 2:
                self.reportWarning('set command is missing the variable name. Ignoring it.')
            else:
                scope.insert(macroPartSet[1], parameterSet)
            macroHandled = True
        elif macroName == 'set_many':
            prefix = ''
            if len(macroPartSet) >= 2:
                prefix = macroPartSet[1] + '.'
            # Setting to many scope variables.
            for line in parameterSet:
                if line.strip() != '':
                    nameValue = line.split(None, 1)
                    if len(nameValue) == 2:
                        scope.insert(prefix + nameValue[0].strip(), [nameValue[1].strip()])
                    else:
                        self.reportWarning('set_many: variable ' + nameValue[0] + 
                                           'has no assigned value. Ignoring it.')
            macroHandled = True
        elif macroName == 'add':
            # Appending to a scope variable.
            if len(macroPartSet) < 2:
                self.reportWarning('add command is missing the variable name. Ignoring it.')
            else:
                scope.append(macroPartSet[1], parameterSet)
            macroHandled = True
        elif macroName == 'get':
            # Getting a scope variable.
            if len(macroPartSet) < 2:
                self.reportWarning('get command is missing the variable name. Ignoring it.')
            else:
                result = scope.recursiveSearch(macroPartSet[1])
                if result != None:
                    self.addText(result)
                else:
                    None
                    #print 'Warning:', document.relativeName, 
                    #print ': get: Variable \'' + macroPartSet[1] + '\' not found. Ignoring it.'
            macroHandled = True
        else:
            macro = findMacro(macroName)
            suppressList = scope.recursiveSearch('suppress_calls_to')
            if suppressList == None:
                suppressList = []
            if macro != None:
                if not macroName in suppressList:
                    expandedText = macro.expand(parameterSet, self)
                    self.usedMacroSet.append(macro)
                    if macro.outputType() == 'html':
                        self.addDummyHtmlNewLines(expandedText)
                    self.addText(expandedText, macro.pureOutput())                    
                macroHandled = True
                #print 'Applying', macroName, 'yields:'
                #for line in text:
                #    print line

        if not macroHandled:
            self.reportWarning('Don\'t know how to handle macro ' + macroIdentifier + '. Ignoring it.')

    def convert(self):
        if self.used:
            print 'Error: RemarkConverter object was already used.'
            return []
            
        # Mark this converter as used.    
        self.used = True

        # In case the template is empty, we have nothing
        # to do.
        if self.template == []:
            return []

        # The 'text' variable will be our working
        # area for the conversion. The conversion is
        # started from the given template text.
        self.text = self.template[:]
        
        # Here we form regular expressions to identify
        # Remark macro invocations in the text.
        macroIdentifier = r'([a-zA-Z_. ][a-zA-Z0-9_. ]*)'
        whitespace = r'[ \t]*'
        optionalInlineParameter = r'(?::' + whitespace + r'((?:(?!]]).)*))?'
        optionalOneLineParameter = r'(?::' + whitespace + r'(.*))?'
        macroRegex = re.compile(r'\[\[' + macroIdentifier + optionalInlineParameter + r'\]\]' + optionalOneLineParameter)
        #macroText = r'((?:(?!]]).)*)'
        #macroRegex = re.compile(r'\[\[' + macroText + r'\]\]' + optionalOneLineParameter)
        
        wholeGroupId = 0
        identifierGroupId = 1
        inlineGroupId = 2
        externalGroupId = 3
        
        # Our strategy is to trace the 'text' line
        # by line while expanding the macros to new
        # text. In this process 'text' shrinks and
        # expands so it is important to iterate
        # by index.
        
        self.currentLine = 0
        while self.currentLine < len(self.text):
            line = self.text[self.currentLine]
            
            # Indented stuff is copied verbatim.
            if len(line) > 0 and line[0] == '\t':
                self.currentLine += 1
                continue
            
            # See if there is a macro somewhere on the line.
            match = re.search(macroRegex, line)
            if match == None:
                # There is no macro on the line: 
                # copy the line verbatim.
                self.currentLine += 1
                continue
    
            # There is at least one macro on the line.
            macroIdentifier = match.group(identifierGroupId)
            
            # Find out its parameter and remove the macro
            # from 'text'.
            parameterSet = self.extractMacro(match.start(0), match.end(0),
                                             match.group(wholeGroupId),
                                             macroIdentifier,
                                             match.group(inlineGroupId),
                                             match.group(externalGroupId))
    
            # The macros in the parameter are _not_ recursively
            # expanded. This would lead to problems in those
            # cases where macro expansion is not meant to happen.

            # Expand the macro to the current position.
            self.expandMacro(macroIdentifier, parameterSet)
        
        # Add link definitions
        for link in self.linkSet:
            self.text += ['[' + link[0] + ']: ' + link[1]]
            
        for macro in self.usedMacroSet:
            macro.postConversion(self.inputRootDirectory, 
                                 self.targetRootDirectory)
        
        return self.text
    
    def htmlHeader(self):
        htmlText = []
        for macro in self.usedMacroSet:
            htmlText += macro.htmlHead(self)
        return htmlText                                

import markdown

markdownConverter = markdown.Markdown(extensions = ['tables', 'abbr', 'def_list',])

def convertMarkdownToHtml(text):
    global markdownConverter
    
    htmlString = markdownConverter.convert(string.join(text, '\n'))
    htmlText = string.split(htmlString, '\n')
            
    return htmlText

def addHtmlBoilerPlate(text, document, htmlHead):
    remarkDirectory = os.path.relpath('remark_files', document.relativeDirectory)
    
    # Add boilerplate code.
    
    includeAsciiMathML = False
    if documentType(document.extension).mathEnabled:
        # Search the text for mathematical expressions.
        # The AsciiMathML script is only included if the
        # page contains at least one expression.
        for line in text:
            if line.find("''") != -1:
                includeAsciiMathML = True
                break
    
    now = datetime.datetime.now()
    timeText = now.strftime("%d.%m.%Y %H:%M")
    
    remarkCss = unixDirectoryName(os.path.normpath(os.path.join(remarkDirectory, 'remark.css')))
    pygmentsCss = unixDirectoryName(os.path.normpath(os.path.join(remarkDirectory, 'pygments.css')))
    asciiMathML = unixDirectoryName(os.path.normpath(os.path.join(remarkDirectory, 'ASCIIMathMLwFallback.js')))
            
    htmlText = []
    htmlText.append('<?xml version="1.0" encoding="UTF-8"?>')
    htmlText.append('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
    htmlText.append('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-US" lang="en-US">')
    htmlText.append('<head>')
    htmlText.append('<title>' + document.tag('description') + '</title>')
    htmlText.append('<link rel="stylesheet" type="text/css" href="' + remarkCss + '" />')
    htmlText.append('<link rel="stylesheet" type="text/css" href="' + pygmentsCss + '" />')
    htmlText.append('<meta http-equiv="Content-Type" content="text/html; charset=utf-8"></meta>')
    if includeAsciiMathML:
        htmlText.append('<script type="text/javascript" src="' + asciiMathML + '"></script>')
    htmlText += htmlHead
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


def convert(template, document, documentTree, 
            inputRootDirectory, targetRootDirectory):
    print document.relativeName, '...'

    # Convert Remark to Markdown
    remarkConverter = RemarkConverter(document, template, documentTree, 
                                      inputRootDirectory, targetRootDirectory)
    text = remarkConverter.convert()
    
    headText = remarkConverter.htmlHeader()
    
    userHeadText = remarkConverter.scopeStack.top().search('html_head')
    if userHeadText != None:
        headText += userHeadText
              
    # Convert Markdown to html.
    text = convertMarkdownToHtml(text)
    
    # Add html boilerplate.
    text = addHtmlBoilerPlate(text, document, headText)

    # Find out some names.
    targetRootDirectory = os.path.normpath(targetRootDirectory)
    targetRelativeName = outputDocumentName(document.relativeName)
    targetFullName = os.path.join(targetRootDirectory, targetRelativeName)

    # If the directories do not exist, create them.
    targetDirectory = os.path.split(targetFullName)[0]
    if not os.path.exists(targetDirectory):
        os.makedirs(targetDirectory)
        
    # Save the text to a file.
    with codecs.open(targetFullName, mode = 'w', encoding = 'utf-8') as outputFile:
        for line in text:
            outputFile.write(line)
            outputFile.write('\n')

def convertAll(documentTree, inputRootDirectory, targetRootDirectory):
    for document in documentTree.documentMap.itervalues():
        type = documentType(document.extension) 
        if type == None:
            continue
        convert(type.template, document, documentTree, 
                inputRootDirectory, targetRootDirectory)

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
