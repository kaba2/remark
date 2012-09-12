# -*- coding: utf-8 -*-

# Description: Converts Remark to Markdown and html
# Documentation: algorithms.txt

import re
import string
import os
import os.path
import datetime
import codecs
import copy

from MacroRegistry import findMacro
from FileSystem import changeExtension, outputDocumentName, documentType, unixDirectoryName, copyIfNecessary
from FileSystem import asciiMathMlName, remarkVersion, globalOptions, unixRelativePath, writeFile
from Reporting import Reporter

class Scope(object):
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.nameSet = dict()

    def name(self):
        return self.name
    
    def insert(self, name, data):
        #print 'Inserted', name, data
        self.nameSet[name] = data
        
    def append(self, name, data):
        result = self.search(name)
        if result != None:
            result += data
        else:
            self.insert(name, data)

    def parent(self):
        return self.parent
    
    def outer(self):
        if self.parent == None:
            return self
        return self.parent
    
    def shallowSearch(self, name):
        return self.nameSet.get(name)
    
    def search(self, name):
        #print 'Recursive search for', name
        result = self.shallowSearch(name)        
        if result != None:
            return result
        if self.parent != None:
            return self.parent.search(name)
        return None
    
    def searchScope(self, name):
        #print 'Recursive search for', name
        result = self.shallowSearch(name)        
        if result != None:
            return self
        if self.parent != None:
            return self.parent.searchScope(name)
        return self

    def get(self, name, defaultValue = []):
        variable = self.search(name)
        if variable == None:
            return defaultValue

        return variable

    def getString(self, name, defaultValue = '', joinString = ''):
        variable = self.get(name)

        if variable == []:
            return defaultValue

        return joinString.join(variable)

    def getInteger(self, name, defaultValue = 0):
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

class ScopeStack(object):
    def __init__(self):
        self.scopeStack = []
        
    def open(self, name):
        #print 'Scope opened.'
        parent = None
        if len(self.scopeStack) > 0:
            parent = self.top()                
        self.scopeStack.append(Scope(parent, name))
        
    def close(self):
        #print 'Scope closed.'
        self.scopeStack.pop()
        
    def top(self):
        return self.scopeStack[-1]
    
    def bottom(self):
        return self.scopeStack[0]

    def printScopes(self):
        print len(self.scopeStack)
        tabs = 0;
        for scope in self.scopeStack:
            print '\t' * tabs
            print scope.name, 'scope:'
            print
            for entry in scope.nameSet.iteritems():
                print entry[0], ':', entry[1]
            tabs += 1

class MacroInvocation(object):
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
        
class Remark(object):
    def __init__(self, document, documentTree, 
                 inputRootDirectory, outputRootDirectory,
                 reporter = Reporter()):
        self.scopeStack = ScopeStack()
        self.scopeStack.open('global')
        self.document = document
        self.documentTree = documentTree
        self.linkIndex = 0
        self.linkSet = []
        self.usedMacroSet = []
        self.inputRootDirectory = inputRootDirectory
        self.outputRootDirectory = outputRootDirectory
        self.reporter = reporter

        # Here we form regular expressions to identify
        # Remark macro invocations in the text.

        # This matches a macro-identifier. The macro
        # identifier is the string between [[ and ]].
        # It may include characters a to z, A to Z,
        # 0 to 9, the - and the _.
        # Examples: 'set some-variable', 'Gallery'.
        self.macroIdentifier = r'([a-zA-Z_.\- ][a-zA-Z0-9_.\- ]*)'
        
        # This matches whitespace, which to us means
        # spaces and tabs.
        self.whitespace = r'[ \t]*'

        # This matches an optional inline parameter.
        # Starting from the outside, the whole thing is optional.
        # The first parentheses (?: ) are just for grouping. The
        # inline parameter must start with ':', following by optional
        # whitespace. If something is left, the inline parameter is
        # that what becomes before ]].
        self.optionalInlineParameter = r'(?::' + self.whitespace + r'((?:(?!\]\]).)*))?'
        
        # The one-line parameter starts with a ':' and continues to
        # to end of the line. The dot . matches anything except \n. 
        # The leading white-space is eaten away.
        self.optionalOneLineParameter = r'(?::' + self.whitespace + r'(.*))?'

        self.optionalOutputExpansion = r'(\+|\-)?'
        self.optionalParameterExpansion = r'(\+|\-)?'

        # Piece together the whole regex for macro-invocation.
        # It is something which start with [[, ends with ]],
        # has expansion-signs either none, +, -, ++, +-, -+, or --,
        # has a macro identifier, and then an optional inline
        # parameter. Finally, there is an optional one-line paramater
        # after the ]].
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
        self.used = False

    def linkId(self):
        result = self.linkIndex
        self.linkIndex += 1
        return result

    def remarkLink(self, description, 
                   fromDocument, toDocument):
        # Add an internal dependency.
        fromDocument.addDependency(toDocument)

        fromDirectory = fromDocument.relativeDirectory
        toFile = outputDocumentName(toDocument.relativeName)
        linkTarget = unixRelativePath(fromDirectory, toFile)
        return self.markdownLink(description, linkTarget)

    def markdownLink(self, description, htmlLink):
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
        self.linkSet.append((name, unixDirectoryName(htmlLink)))
        
        return text
    
    def reportWarning(self, text, type):
        self.reporter.reportWarning(text, type)
        
    def reportError(self, text, type):
        self.reporter.reportError(text, type)

    def report(self, text, type):
        self.reporter.report(text, type)
        
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

    def expandBuiltInMacro(self, macroNameSet, parameterSet, scope):
        macroName = macroNameSet[0]
        document = self.document
        
        macroText = ['']    
        macroHandled = False
        getCommand = False

        if not macroHandled and macroName == 'set':
            # Sets a scope variable, e.g.
            # [[set variable]]: some input
            if len(macroNameSet) < 2:
                self.reportWarning('set command is missing the variable name. Ignoring it.',
                                   'invalid-input')
            else:
                variableName = macroNameSet[1]
                if parameterSet != []:                 
                    scope.insert(variableName, parameterSet)
                else:
                    scope.insert(variableName, [''])
            macroHandled = True

        if not macroHandled and macroName == 'set_tag':
            # Sets a document tag, e.g.
            # [[set_tag some-tag]]: some input
            if len(macroNameSet) < 2:
                self.reportWarning('set-tag command is missing the tag-name. Ignoring it.',
                                   'invalid-input')
            else:
                tagName = macroNameSet[1]
                document.setTag(tagName, parameterSet)
            macroHandled = True

        if not macroHandled and macroName == 'tag':
            # Retrieves a tag, e.g.
            # [[tag some-tag]]
            if len(macroNameSet) < 2:
                self.reportWarning('tag command is missing the tag-name. Ignoring it.',
                                   'invalid-input')
            else:
                tagName = macroNameSet[1]
                if tagName in document.tagSet:
                    macroText = document.tag(tagName)
                else:
                    self.reportWarning('Tag ' + tagName + 
                                       ' has not been defined. Ignoring it.',
                                       'undefined-tag')
            macroHandled = True

        if not macroHandled and macroName == 'set_outer':
            # Setting a variable at outer scope, e.g.
            # [[set_outer variable]]: some input
            if len(macroNameSet) < 2:
                self.reportWarning('set_outer command is missing the variable name. Ignoring it.',
                                   'invalid-input')
            else:
                variableName = macroNameSet[1]
                if scope.outer() == scope:
                    self.reportWarning('set_outer: already at global scope.',
                                       'invalid-input')
                outerScope = scope.outer().searchScope(variableName)
                if parameterSet != []:
                    outerScope.insert(variableName, parameterSet)
                else:
                    outerScope.insert(variableName, [''])
            macroHandled = True

        if not macroHandled and macroName == 'set_many':
            # Setting to many scope variables, e.g.
            # [[set_many Gallery]]:
            #       width 250
            #       height 500
            prefix = ''
            if len(macroNameSet) >= 2:
                prefix = macroNameSet[1] + '.'
            for line in parameterSet:
                if line.strip() != '':
                    nameValue = line.split(None, 1)
                    variable = prefix + nameValue[0].strip()
                    if len(nameValue) == 2:
                        scope.insert(variable, [nameValue[1].strip()])
                    else:
                        scope.insert(variable, [''])
            macroHandled = True

        if not macroHandled and macroName == 'add':
            # Appending to a scope variable, e.g.
            # [[add variable]]: some new input
            if len(macroNameSet) < 2:
                self.reportWarning('add command is missing the variable name. Ignoring it.',
                                   'invalid-input')
            else:
                variableName = macroNameSet[1]
                scope.append(variableName, parameterSet)
            macroHandled = True

        if not macroHandled and macroName == 'add_outer':
            # Adding a new line to a variable at outer scope, e.g.
            # [[add_outer variable]]: some new input
            if len(macroNameSet) < 2:
                self.reportWarning('add_outer command is missing the variable name. Ignoring it.',
                                   'invalid-input')
            else:
                variableName = macroNameSet[1]
                outerScope = scope.outer().searchScope(variableName)
                if parameterSet != []:
                    outerScope.append(variableName, parameterSet)
                else:
                    outerScope.append(variableName, [''])
            macroHandled = True

        if not macroHandled and (macroName == 'outer' or macroName == 'get_outer'):
            # Getting a global variable, e.g.
            # [[outer variable]]
            if len(macroNameSet) < 2:
                self.reportWarning(macroName + ' command is missing the variable name. Ignoring it.',
                                   'invalid-input')
            else:
                getCommand = True
                getName = macroNameSet[1]
                getScope = scope.outer().searchScope(macroNameSet[1])
            macroHandled = True

        # This needs to be handled last, so that one can use
        # built-in macros without parameters, such as
        # [[set_many]].
        if not macroHandled and len(macroNameSet) == 1:
            # Getting a scope variable, main form, e.g.
            # [[variable]]
            getName = macroName
            getCommand = True
            getScope = scope
            macroHandled = True

        # This part takes care of actually fetching a variable.
        # It is shared between get (both forms), outer, and get_outer.
        if getCommand:
            # Get the variable.
            result = getScope.search(getName)
            if result != None:
                macroText = result
            else:
                self.reportWarning('get: variable ' + getName + 
                                   ' has not been defined. Ignoring it.', 
                                   'undefined-variable')

        return macroText, macroHandled

    def expandMacro(self, macroInvocation):
        # This is where we will gather the expanded
        # contents of the macro.
        macroText = ['']
        macroHandled = False

        self.recursionDepth += 1

        # This function expands the given macro in
        # the current position.
        scope = self.scopeStack.top()
        
        # By default, the output will be expanded. 
        # If a proper macro is invoked, then its
        # decision overrides this default.
        expandMore = True

        # Retrieve the macro names and parameters.
        macroNameSet = string.split(macroInvocation.name)
        macroName = macroNameSet[0]
        parameterSet = macroInvocation.parameterSet
        
        if len(macroNameSet) == 1:
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
                    self.reporter.openScope(macro.name())
                    macroText = macro.expand(parameterSet, self)
                    self.reporter.closeScope(macro.name())
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

        # Handle built-in macros.
        # Note that this has to be done after the external
        # macros, since otherwise the variable retrieval
        # [[variable]] would match those macros.
        if not macroHandled:
            macroText, macroHandled = self.expandBuiltInMacro(
                macroNameSet, parameterSet, scope)

        # If no macro was recognized, report a warning and continue.
        if not macroHandled:
            self.reportWarning('Don\'t know how to handle macro "' + 
                               macroInvocation.name + '". Ignoring it.',
                               'invalid-input')

        # The invocation can override the decision 
        # whether to expand the output.
        if macroInvocation.outputExpansion != None:
            expandMore = macroInvocation.outputExpansion

        if macroHandled and expandMore:
            # Expand recursively.
            self.scopeStack.open(macroInvocation.name)
            self.scopeStack.top().insert('parameter', macroInvocation.parameterSet)
            macroText = self.convert(macroText)
            self.scopeStack.close()
       
        self.recursionDepth -= 1

        return macroText            

    def postConversion(self):
        text = []
        
        # Add link definitions
        for link in self.linkSet:
            text.append('[' + link[0] + ']: ' + link[1])
            
        for macro in self.usedMacroSet:
            macro.postConversion(self.inputRootDirectory, 
                                 self.outputRootDirectory)
        return text

    def convert(self, text):
        # Our strategy is to trace the 'text' line
        # by line while expanding the macros to 'newText'.

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
                macroInvocation.parameterSet = self.convert(macroInvocation.parameterSet)
                self.scopeStack.close()

            # Recursively expand the macro.
            macroText = self.expandMacro(macroInvocation)
            
            #print 'I write:'
            #for line in macroText:
            #    print line
           
            # Append the first line to the end of the
            # latest line.
            newText[-1] += macroText[0]
            # Append the other lines on the following lines.
            newText += macroText[1 :]
            
            # Move on.
            row = macroInvocation.endRow
            column = macroInvocation.endColumn
        
        # The last '' is extraneous.
        if newText[-1] == '':
            return newText[0 : -1]
        
        return newText
    
    def macro(self, macroName, macroParameter = ''):
        text = ['[[' + macroName + ']]']
        if isinstance(macroParameter, basestring):
            if macroParameter.strip() != '':
                text[0] += ': ' + macroParameter
        elif len(macroParameter) > 0:
            text[0] += ':'
            for line in macroParameter:
                text.append('\t' + line)
        return self.convert(text)

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
    asciiMathML = unixDirectoryName(os.path.normpath(os.path.join(remarkDirectory, asciiMathMlName())))
            
    htmlText = []
    htmlText.append('<!DOCTYPE html>')
    htmlText.append('<html>')
    htmlText.append('<head>')
    htmlText.append('<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
    htmlText.append('<title>' + document.linkDescription() + '</title>')
    htmlText.append('<link rel="stylesheet" type="text/css" href="' + remarkCss + '" />')
    htmlText.append('<link rel="stylesheet" type="text/css" href="' + pygmentsCss + '" />')

    if includeAsciiMathML:
        htmlText.append('<script type="text/javascript" src="' + asciiMathML + '"></script>')
    htmlText += htmlHead
    htmlText.append('</head>')
    htmlText.append('<body>')
    htmlText.append('<div id = "remark-all">')
    htmlText.append('<div id = "remark">')
    htmlText += text
    htmlText.append('</div>')
    htmlText.append('<div id="remark-footer">')
    htmlText.append('<p><a href="http://kaba.hilvi.org/remark">Remark ' + remarkVersion() + '</a> - Page generated ' + timeText + '.</p>')
    htmlText.append('</div>')
    htmlText.append('</div>')
    htmlText.append('</body>')
    htmlText.append('</html>')

    return htmlText

def convertRemarkToMarkdown(remarkText, document, documentTree, 
                            inputRootDirectory, outputRootDirectory,
                            reporter = Reporter()):
    '''
    Converts Remark text to Markdown text. 

    remarkText (list of strings):
    The Remark text to convert, string per row.

    returns (list of strings):
    The converted Markdown text.
    '''

    remark = Remark(document, documentTree, 
                    inputRootDirectory, outputRootDirectory,
                    reporter)

    # Convert Remark to Markdown.
    markdownText = remark.convert(remarkText)
    markdownText += remark.postConversion()

    # Return the resulting Markdown text.
    return markdownText

def convertRemarkToHtml(remarkText, document, documentTree, 
                        outputRootDirectory,
                        reporter = Reporter()):
    '''
    Converts Remark text to html.

    remarkText (list of strings):
    The Remark text to convert, string per row.

    returns (list of strings):
    The converted html text.
    '''
     
    remark = Remark(document, documentTree, 
                    documentTree.rootDirectory, 
                    outputRootDirectory,
                    reporter)

    # Convert Remark to Markdown
    markdownText = remark.convert(remarkText)
    markdownText += remark.postConversion()
    
    # Convert Markdown to html.
    htmlText = convertMarkdownToHtml(markdownText)
    
    # Create the html head-section.
    headText = remark.htmlHeader()
    headText += document.tag('html_head')

    # Add html boilerplate.
    htmlText = addHtmlBoilerPlate(htmlText, document, headText)

    # Return the resulting html-text.      
    return htmlText

def saveRemarkToHtml(remarkText, document, documentTree, 
                     outputRootDirectory,
                     reporter = Reporter()):
    # Convert Remark to html.
    htmlText = convertRemarkToHtml(
            remarkText, document, documentTree, 
            outputRootDirectory, reporter)

    # Find out some names.
    outputRelativeName = outputDocumentName(document.relativeName)
    outputFullName = os.path.join(outputRootDirectory, outputRelativeName)

    # Write the resulting html.
    writeFile(htmlText, outputFullName)

def convertAll(documentTree, outputRootDirectory, reporter = Reporter()):
    
    outputRootDirectory = os.path.normpath(outputRootDirectory)

    # We wish to convert the files in alphabetical order
    # by their relative-name (in the map they are in hashed order).
    sortedDocumentSet = documentTree.documentMap.values()
    sortedDocumentSet.sort(lambda x, y: cmp(x.relativeName, y.relativeName))
   
    for document in sortedDocumentSet:
        # Find out the document-type.
        type = documentType(document.extension)

        # Only generate documentation if needed; force
        # generation if that was specified at command-line.
        regenerate = globalOptions().regenerate or document.regenerate()
        if not regenerate:
            continue

        reporter.report('Generating ' + document.relativeName + '...',
                        'verbose')

        reporter.openScope(document.relativeName)
        
        # Let the document-type convert the document.
        type.convert(document, documentTree, outputRootDirectory,
                     reporter)
        
        reporter.closeScope(document.relativeName)
    
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
