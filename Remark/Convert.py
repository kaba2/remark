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
from Common import changeExtension, outputDocumentName, documentType, unixDirectoryName, copyIfNecessary

class Scope:
    def __init__(self, parent, name):
        self.parent_ = parent
        self.name_ = name
        self.nameSet_ = dict()
        
    def name(self):
        return self.name_
    
    def insert(self, name, data):
        #print 'Inserted', name, data
        self.nameSet_[name] = data
        
    def append(self, name, data):
        result = self.search(name)
        if result != None:
            result += data
        else:
            self.insert(name, data)

    def parent(self):
        return self.parent_
    
    def outer(self):
        if self.parent_ == None:
            return self
        return self.parent_
    
    def shallowSearch(self, name):
        if name in self.nameSet_:
            return self.nameSet_[name]
        return None
    
    def search(self, name):
        #print 'Recursive search for', name
        result = self.shallowSearch(name)        
        if result != None:
            return result
        if self.parent_ != None:
            return self.parent_.search(name)
        return None
    
    def searchScope(self, name):
        #print 'Recursive search for', name
        result = self.shallowSearch(name)        
        if result != None:
            return self
        if self.parent_ != None:
            return self.parent_.searchScope(name)
        return self

    def getInteger(self, name, defaultValue):
        value = None
        text = self.search(name)
        
        if text != None:
            if len(text) == 1:
                try:
                    value = int(text[0])
                except ValueError:
                    value = None
        else:
            value = defaultValue
        
        if value == None:
            print 'Warning: Could not convert', name, 'to an integer. Using default.'
            value = defaultValue
            
        return value

class ScopeStack:
    def __init__(self):
        self.stack_ = []
        
    def open(self, name):
        #print 'Scope opened.'
        parent = None
        if len(self.stack_) > 0:
            parent = self.top()                
        self.stack_.append(Scope(parent, name))
        
    def close(self):
        #print 'Scope closed.'
        self.stack_.pop()
        
    def top(self):
        return self.stack_[-1]
    
    def bottom(self):
        return self.stack_[0]  

class MacroInvocation:
    def __init__(self, name,
                 parameterSet,
                 outputExpansion,
                 parameterExpansion,
                 beginRow, beginColumn,
                 endRow, endColumn):
        self.name = name
        self.parameterSet = parameterSet
        self.outputExpansion = outputExpansion
        self.parameterExpansion = parameterExpansion
        self.beginRow = beginRow
        self.beginColumn = beginColumn
        self.endRow = endRow
        self.endColumn = endColumn
        
class RemarkConverter:
    def __init__(self, document, template, documentTree, 
                 inputRootDirectory, targetRootDirectory):
        self.scopeStack = ScopeStack()
        self.scopeStack.open('global')
        self.document = document
        self.documentTree = documentTree
        self.linkIndex = 0
        self.linkSet = []
        self.usedMacroSet = []
        self.template = template
        self.inputRootDirectory = inputRootDirectory
        self.targetRootDirectory = targetRootDirectory

        # Here we form regular expressions to identify
        # Remark macro invocations in the text.
        self.macroIdentifier = r'([a-zA-Z_. ][a-zA-Z0-9_. ]*)'
        self.whitespace = r'[ \t]*'
        self.optionalInlineParameter = r'(?::' + self.whitespace + r'((?:(?!]]).)*))?'
        self.optionalOneLineParameter = r'(?::' + self.whitespace + r'(.*))?'
        self.optionalOutputExpansion = r'(\+|-)?'
        self.optionalParameterExpansion = r'(\+|-)?'
        self.macroRegex = re.compile(r'\[\[' + 
                                     self.optionalOutputExpansion +
                                     self.optionalParameterExpansion + 
                                     self.macroIdentifier + 
                                     self.optionalInlineParameter + 
                                     r'\]\]' + 
                                     self.optionalOneLineParameter)
        
        #macroText = r'((?:(?!]]).)*)'
        #macroRegex = re.compile(r'\[\[' + macroText + r'\]\]' + optionalOneLineParameter)
        self.wholeGroupId = 0
        self.outputExpansionGroupId = 1
        self.parameterExpansionGroupId = 2
        self.identifierGroupId = 3
        self.inlineGroupId = 4
        self.externalGroupId = 5
        self.recursionDepth = 0
        
        scope = self.scopeStack.top() 
        # All the tags that a parser collects
        # are available as variables for Remark.
        for key, value in document.tagSet.items(): 
            scope.insert(key, [value])
        
        scope.insert('file_name', [document.fileName])
        scope.insert('relative_name', [document.relativeName])
        scope.insert('parent_file_name', [document.parent.fileName])
        scope.insert('parent_relative_name', [document.parent.relativeName])
        
        self.lastReportFrom = ''
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
        text = '[' + description + '][' + name + ']'
        
        # We defer defining the link because the link
        # could be an inline link. Instead we store the
        # definitions so that we can output them to the
        # end of the document. 
         
        self.linkSet.append((name, unixDirectoryName(target)))
        
        return text
    
    def reportWarning(self, text):
        if self.lastReportFrom != self.document.relativeName:
            self.lastReportFrom = self.document.relativeName
            print
            print self.document.relativeName, ':'
            
        print 'Warning:', text
        
    def report(self, text):
        if self.lastReportFrom != self.document.relativeName:
            self.lastReportFrom = self.document.relativeName
            print
            print self.document.relativeName, ':'
    
        print text
        
    def extractMacro(self, row, match, text): 
        # This function extracts the information from
        # a macro invocation.

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
        
        matchBegin = match.start(self.wholeGroupId)
        matchEnd = match.end(self.wholeGroupId)
        macroName = match.group(self.identifierGroupId) 
        inlineParameter = match.group(self.inlineGroupId)
        onelineParameter = match.group(self.externalGroupId)
        outputExpansion = match.group(self.outputExpansionGroupId)
        if outputExpansion != None:
            if outputExpansion == '+':
                outputExpansion = True
            else:
                outputExpansion = False
        parameterExpansion = match.group(self.parameterExpansionGroupId)
        if parameterExpansion != None:
            if parameterExpansion == '+':
                parameterExpansion = True
            else:
                parameterExpansion = False
        else:
            if outputExpansion != None: 
                parameterExpansion = outputExpansion
            else:
                parameterExpansion = False
        
        hasExternalParameters = (onelineParameter != None)
                
        parameterSet = []
        
        hasInlineParameters = (inlineParameter != None)

        # Extract an inline parameter.
        if hasInlineParameters:
            parameter = string.strip(inlineParameter)
            parameterSet.append(parameter)

        # Extract a one-line parameter.
        hasOnelineParameter = False
        if hasExternalParameters:
            # If the parameter consists of all
            # whitespace, it is a multi-line parameter
            # so ignore that case here.
            parameter = string.strip(onelineParameter)
            if parameter != '':
                # One-line parameter
                hasOnelineParameter = True
                parameterSet.append(parameter)
        
        # A parameter is multi-line if its external but
        # not one-line.
        hasMultilineParameter = (hasExternalParameters and not hasOnelineParameter)

        # If the parameter is not multi-line, we are done.
        if not hasMultilineParameter:
            return MacroInvocation(macroName,
                                   parameterSet,
                                   outputExpansion,
                                   parameterExpansion,                                   
                                   row, matchBegin,
                                   row, matchEnd)
        
        # The parameter is multi-line.
        # Find out the extent of the parameter.
        endRow = row + 1
        while endRow < len(text):
            # The end of a multi-line parameter
            # is marked by a line which is not all whitespace
            # and has no indentation. 
            if _leadingTabs(text[endRow]) == 0 and string.strip(text[endRow]) != '':
                break
            endRow += 1
            
        # Copy the parameter and remove the indentation from it.
        parameterSet = [_removeLeadingTabs(line, 1) for line in text[row + 1 : endRow]]
    
        # Remove the possible empty trailing parameter lines.
        nonEmptyLines = len(parameterSet)
        while nonEmptyLines > 0:
            if string.strip(parameterSet[nonEmptyLines - 1]) == '':
                nonEmptyLines -= 1
            else:
                break
            
        parameterSet[nonEmptyLines :] = []
            
        return MacroInvocation(macroName,
                               parameterSet,
                               outputExpansion,
                               parameterExpansion,                                   
                               row, matchBegin,
                               row + nonEmptyLines, len(text[row + nonEmptyLines]))        

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

    def expandMacro(self, macroInvocation):
        # This function expands the given macro in
        # the current position.
        scope = self.scopeStack.top()
        
        macroHandled = False
        macroNameSet = string.split(macroInvocation.name)
        macroName = macroNameSet[0]
        parameterSet = macroInvocation.parameterSet
        getCommand = False
        
        # By default, the output will be expanded. 
        # If a proper macro is invoked, then its
        # decision overrides this default.
        expandMore = True
        
        macroText = ['']        
      
        if macroName == 'set':
            # Setting a scope variable.
            if len(macroNameSet) < 2:
                self.reportWarning('set command is missing the variable name. Ignoring it.')
            else:
                variableName = macroNameSet[1]
                if parameterSet != []:                 
                    scope.insert(variableName, parameterSet)
                else:
                    scope.insert(variableName, [''])
            macroHandled = True
        
        if macroName == 'set_outer':
            # Setting a variable at outer scope.
            if len(macroNameSet) < 2:
                self.reportWarning('set_outer command is missing the variable name. Ignoring it.')
            else:
                variableName = macroNameSet[1]
                outerScope = scope.outer().searchScope(variableName)
                if parameterSet != []:
                    outerScope.insert(variableName, parameterSet)
                else:
                    outerScope.insert(variableName, [''])
            macroHandled = True

        if not macroHandled and macroName == 'set_many':
            prefix = ''
            if len(macroNameSet) >= 2:
                prefix = macroNameSet[1] + '.'
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
        
        if not macroHandled and macroName == 'add':
            # Appending to a scope variable.
            if len(macroNameSet) < 2:
                self.reportWarning('add command is missing the variable name. Ignoring it.')
            else:
                scope.append(macroNameSet[1], parameterSet)
            macroHandled = True
        
        if not macroHandled and macroName == 'get':
            # Getting a scope variable, alternative form.
            if len(macroNameSet) < 2:
                self.reportWarning('get command is missing the variable name. Ignoring it.')
            else:
                getCommand = True
                getName = macroNameSet[1]
                getScope = scope
            macroHandled = True
        
        if not macroHandled and macroName == 'outer':
            # Getting a global variable.
            if len(macroNameSet) < 2:
                self.reportWarning('outer command is missing the variable name. Ignoring it.')
            else:
                getCommand = True
                getName = macroNameSet[1]
                getScope = scope.outer().searchScope(macroNameSet[1])
            macroHandled = True

        if not macroHandled and len(macroNameSet) == 1:
            # Search for the macro.
            macro = findMacro(macroName)

            # Get the macro suppress list.
            suppressList = scope.search('suppress_calls_to')
            if suppressList == None:
                suppressList = []
            
            if macro != None:
                # The macro is not run if it is
                # in suppress list.
                if not macroName in suppressList:
                    # Run the actual macro.
                    macroText = macro.expand(parameterSet, self)
                    if macroText == []:
                        macroText = ['']
                    
                    # Mark the macro as used.
                    self.usedMacroSet.append(macro)
                    
                    # If the output is meant to be html,
                    # we need to add some dummy html newlines
                    # for Markdown.
                    if macro.outputType() == 'html':
                        self.addDummyHtmlNewLines(macroText)

                    # The output of the macro is either
                    # recursively expanded or not.
                    # The macro suggests a default for this
                    # behavior.
                    expandMore = not macro.pureOutput()
                    
                macroHandled = True

        if not macroHandled and len(macroNameSet) == 1:
            # Getting a scope variable.
            getName = macroName
            getCommand = True
            getScope = scope
            macroHandled = True
            
        if getCommand:
            # Getting a scope variable.
            result = getScope.search(getName)
            if result != None:
                macroText = result
            else:
                self.reportWarning('Variable \'' + getName + 
                                   '\' not found. Ignoring it.')

        if not macroHandled:
            self.reportWarning('Don\'t know how to handle macro "' + 
                               macroInvocation.name + '". Ignoring it.')

        # The invocation can override the decision 
        # whether to expand the output.
        if macroInvocation.outputExpansion != None:
            expandMore = macroInvocation.outputExpansion

        if macroHandled and expandMore:
            # Expand recursively.
            self.scopeStack.open(macroInvocation.name)
            self.scopeStack.top().insert('parameter', macroInvocation.parameterSet)
            macroText = self.convertRecurse(macroText)
            self.scopeStack.close()
       
        return macroText            

    def convert(self, text):
        if self.used:
            self.reportWarning('The conversion object was already used.')
            return []
        
        newText = self.convertRecurse(text)
        
        # Add link definitions
        for link in self.linkSet:
            # Note, the link target is wrapped in angle brackets
            # so that it also works with URLs that have a space
            # in them.
            newText.append('[' + link[0] + ']: ' + link[1])
            
        for macro in self.usedMacroSet:
            macro.postConversion(self.inputRootDirectory, 
                                 self.targetRootDirectory)

        self.used = True
        return newText

    def convertRecurse(self, text):
        # Our strategy is to trace the 'text' line
        # by line while expanding the macros to 'newText'.
        self.recursionDepth += 1
        
        newText = ['']
        row = 0
        column = 0
        while row < len(text):
            # Replace the first characters with spaces
            # so that the previous macros won't interfere
            # with the rest of the processing.
            line = ' ' * column + text[row][column :]
            
            # Indented stuff is copied verbatim.
            if len(line) > 0 and line[0] == '\t':
                newText[-1] += line
                newText.append('')
                row += 1
                column = 0              
                continue
            
            # See if there is a macro somewhere on the line.
            match = re.search(self.macroRegex, line)
            if match == None:
                # There is no macro on the line: 
                # copy the line verbatim.
                newText[-1] += line[column :]
                newText.append('')
                row += 1
                column = 0              
                continue
    
            #print 'I read:'
            #print match.group(0)

            # Yes, there is a macro on the line.
            # First copy the possible verbatim content.
            matchBegin = match.start(0)
            newText[-1] += line[column : matchBegin]
            column = matchBegin
            
            # Find out the whole macro invocation.
            macroInvocation = self.extractMacro(row, match, text)
            #print 'Macro invocation:'
            #print macroInvocation.name
            #print macroInvocation.beginRow, macroInvocation.beginColumn
            #print macroInvocation.endRow, macroInvocation.endColumn
            #for parameterLine in macroInvocation.parameterSet:
            #    print parameterLine

            # The parameter of the macro will be expanded 
            # before invocation only if the user explicitly 
            # requests so.
            if macroInvocation.parameterExpansion:
                self.scopeStack.open(macroInvocation.name)
                macroInvocation.parameterSet = self.convertRecurse(macroInvocation.parameterSet)
                self.scopeStack.close()

            # Recursively expand the macro.
            macroText = self.expandMacro(macroInvocation)
            
            #print 'I write:'
            #for line in macroText:
            #    print line
           
            # Append the resulting text to 'newText'.
            newText[-1] += macroText[0]
            newText += macroText[1 :]
            
            # Move on.
            row = macroInvocation.endRow
            column = macroInvocation.endColumn
        
        self.recursionDepth -= 1
            
        # The last '' is extraneous.
        if newText[-1] == '':
            return newText[0 : -1]
        
        return newText
    
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
    htmlText.append('<div id = "remark">')
    htmlText += text
    htmlText.append('</div>')
    htmlText.append('<div id="footer">')
    htmlText.append('<p><a href="http://kaba.hilvi.org/remark">Remark</a> documentation system - Page generated ' + timeText + '.</p>')
    htmlText.append('</div>')
    htmlText.append('</div>')
    htmlText.append('</body>')
    htmlText.append('</html>')

    return htmlText


def convert(template, document, documentTree, 
            inputRootDirectory, targetRootDirectory):
    # Find out some names.
    targetRootDirectory = os.path.normpath(targetRootDirectory)
    targetRelativeName = outputDocumentName(document.relativeName)
    targetFullName = os.path.join(targetRootDirectory, targetRelativeName)

    # If the directories do not exist, create them.
    targetDirectory = os.path.split(targetFullName)[0]
    if not os.path.exists(targetDirectory):
        os.makedirs(targetDirectory)

    # Convert Remark to Markdown
    remarkConverter = RemarkConverter(document, template, documentTree, 
                                      inputRootDirectory, targetRootDirectory)
    text = remarkConverter.convert(template)
    #for line in text:
    #    print line
    
    # Save the text to a file.
    #with codecs.open(targetFullName + '.txt', mode = 'w', encoding = 'utf-8') as outputFile:
    #    for line in text:
    #        outputFile.write(line)
    #        outputFile.write('\n')
    
    headText = remarkConverter.htmlHeader()
    
    userHeadText = remarkConverter.scopeStack.top().search('html_head')
    if userHeadText != None:
        headText += userHeadText
              
    # Convert Markdown to html.
    text = convertMarkdownToHtml(text)
    
    # Add html boilerplate.
    text = addHtmlBoilerPlate(text, document, headText)
       
    # Save the text to a file.
    with codecs.open(targetFullName, mode = 'w', encoding = 'utf-8') as outputFile:
        for line in text:
            outputFile.write(line)
            outputFile.write('\n')

def convertAll(documentTree, inputRootDirectory, targetRootDirectory, prologue):
    # We wish to convert the files in alphabetical order
    # (in the map they are in hashed order).
    sortedDocumentSet = documentTree.documentMap.values()
    sortedDocumentSet.sort(lambda x, y: cmp(x.relativeName, y.relativeName))
    for document in sortedDocumentSet:
        print '.',
        type = documentType(document.extension) 
        #if type == None or document.fileName != 'Body_Macro.txt':
        if type == None:
            # This file has no associated document type.
            # Simply copy it.
            #print 'Copying', document.relativeName, '...'
            copyIfNecessary(os.path.join(inputRootDirectory, document.relativeName),
                            os.path.join(targetRootDirectory, document.relativeName))
        else:
            #print 'Expanding', document.relativeName, '...'
            template = type.generateMarkdown(os.path.join(inputRootDirectory, document.relativeName))
            convert(prologue + template, document, documentTree, 
                    inputRootDirectory, targetRootDirectory)

    print ''
    
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
