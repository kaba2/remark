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
import traceback
import time

from Remark.Version import remarkVersion
from Remark.Macro_Registry import findMacro
from Remark.FileSystem import changeExtension, unixDirectoryName, copyIfNecessary
from Remark.FileSystem import globalOptions, unixRelativePath, writeFile
from Remark.Reporting import Reporter, ScopeGuard
from Remark.DocumentType_Registry import documentType, outputDocumentName
from Remark.DocumentTree import createDocumentTree

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
    '''
    Converts Remark to Markdown.
    '''

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
        # It is something which starts with [[, ends with ]],
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

        # Set default variables.
        self.scopeStack.top().insert('indent', ['Verbatim'])
        self.scopeStack.top().insert('remark_version', [remarkVersion()])

    def linkId(self):
        '''
        Generates a unique integer for a new link.

        This integer is used to make the generated Markdown links unique.
        
        returns (integer):
        A unique integer.        
        '''
        result = self.linkIndex
        self.linkIndex += 1
        return result

    def remarkLink(self, description, 
                   fromDocument, toDocument):
        '''
        Generates a Markdown-link from a document to another.

        description (string):
        The description for the link.
        
        fromDocument (Document):
        The document to generate the link from.

        toDocument (Document):
        The document to generate the link to.

        returns (string):
        The generated link in Markdown. As a side-effect 
        the actual link-address is stored for listing the
        link-definition later at the end of the document.
        '''
        fromDirectory = fromDocument.relativeDirectory
        toFile = outputDocumentName(toDocument.relativeName)
        linkTarget = unixRelativePath(fromDirectory, toFile)
        return self.markdownLink(description, linkTarget)

    def markdownLink(self, description, htmlLink):
        '''
        Generates a Markdown-link to the given URL.

        description (string):
        The description for the link.
        
        htmlLink (string):
        The URL of the link.

        returns (string):
        The generated link in Markdown. As a side-effect 
        the actual link-address is stored for listing the
        link-definition later at the end of the document.
        '''
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

    def reportDebug(self, text, type):
        self.reporter.reportDebug(text, type)

    def report(self, text, type):
        self.reporter.report(text, type)
        
    def extractMacro(self, row, match, text):
        '''
        Extracts the information from a macro invocation.
        '''

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
        
        # The parameter is multi-line. Extract that parameter,
        # and find out its extent.
        parameterSet = self.extractMultilineParameter(text, row + 1)
        nonEmptyLines = len(parameterSet)
            
        return MacroInvocation(macroName,
                               parameterSet,
                               outputExpansion,
                               parameterExpansion,                                   
                               row, matchBegin,
                               row + nonEmptyLines, len(text[row + nonEmptyLines]))        

    def extractMultilineParameter(self, text, startRow):
        endRow = startRow
        while endRow < len(text):
            # The end of a multi-line parameter
            # is marked by a line which is not all whitespace
            # and has no indentation. 
            if (_leadingTabs(text[endRow], globalOptions().tabSize)[0] == 0 and 
                string.strip(text[endRow]) != ''):
                break
            endRow += 1
            
        # Copy the parameter and remove the indentation from it.
        parameterSet = [_removeLeadingTabs(line, globalOptions().tabSize, 1) 
            for line in text[startRow : endRow]]
    
        # Remove the possible empty trailing parameter lines.
        nonEmptyLines = len(parameterSet)
        while nonEmptyLines > 0:
            if string.strip(parameterSet[nonEmptyLines - 1]) == '':
                nonEmptyLines -= 1
            else:
                break
            
        parameterSet[nonEmptyLines :] = []

        return parameterSet

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
        '''
        Expands a built-in macro.

        macroNameSet (list of strings):
        The macro-name split into whitespace-separated words.

        parameterSet (list of strings):
        The parameter of the macro.

        scope (Scope):
        The current variable-scope.
        '''
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
        '''
        Expands the given macro invocation.

        macroInvocation (MacroInvocation):
        The information about the macro invocation.

        returns (list of strings, set of document-objects):
        The text the macro expands to.
        '''
        # This is where we will gather the expanded
        # contents of the macro.
        macroText = ['']
        macroHandled = False

        self.recursionDepth += 1

        # maxRecursionDepth = 100
        # if self.recursionDepth > maxRecursionDepth:
        #     self.reportDebug(
        #         'Macro expansion recursion exceeded ' + 
        #         str(maxRecursionDepth) + 
        #         ' levels.', 
        #         'debug-recursion')
        #     sys.exit(0)

        # This function expands the given macro in
        # the current position.
        scope = self.scopeStack.top()
        
        # By default, the output will be expanded. 
        # If a proper macro is invoked, then its
        # decision overrides this default.
        expandOutput = True

        # Retrieve the macro names and parameters.
        macroNameSet = string.split(macroInvocation.name)
        macroName = macroNameSet[0]
        parameterSet = macroInvocation.parameterSet
        
        # Handle external macros.
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
                    with ScopeGuard(self.reporter, macro.name()):
                        macroText = macro.expand(parameterSet, self)

                    if macroText == []:
                        macroText = ['']
                    
                    # Mark the macro as used.
                    self.usedMacroSet.append(macro)
                    
                    # The output of the macro is either
                    # recursively expanded or not.
                    # The macro suggests a default for this
                    # behavior.
                    expandOutput = macro.expandOutput()
                    
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
            self.reportWarning('Don\'t know how to handle macro ' + 
                               macroInvocation.name + '. Ignoring it.',
                               'unknown-macro')

        # The invocation can override the decision 
        # whether to expand the output.
        if macroInvocation.outputExpansion != None:
            expandOutput = macroInvocation.outputExpansion

        if macroHandled and expandOutput:
            # Expand recursively.
            self.scopeStack.open(macroInvocation.name)
            self.scopeStack.top().insert('parameter', macroInvocation.parameterSet)
            macroText = self.convert(macroText)
            self.scopeStack.close()
       
        self.recursionDepth -= 1

        return macroText

    def postConversion(self):
        '''
        Runs through the post-conversions of used macros and
        returns a text containing all link-definitions in
        Markdown syntax.

        returns (list of strings):
        The link-definitions in Markdown syntax.
        '''
        
        # Run through the post-conversions of all used macros.    
        for macro in self.usedMacroSet:
            macro.postConversion(self)

        # Generate the link definitions.
        text = []
        for link in self.linkSet:
            text.append('[' + link[0] + ']: ' + link[1])

        return text

    def convert(self, text):
        '''
        Converts Remark text to Markdown text.
        
        text (list of strings):
        The Remark text to convert.
        
        returns (list of strings):
        The converted Markdown text.
        '''

        # The strategy in this function is to trace the 'text' 
        # line by line while expanding the macros to 'newText'.

        row = 0
        column = 0
        newText = ['']
        while row < len(text):
            # Replace the first characters with spaces
            # so that the previous macros won't interfere
            # with the rest of the processing.
            line = ' ' * column + text[row][column :]
            
            # The indentation macro is invoked if and only if
            # * a non-empty line starts with a tab, and
            # * the line in 1 is preceded by a row of whitespace.
            indentationMacro = (len(line) > 0 and 
                                line[0] == '\t' and 
                                line.strip() != '' and
                                row > 0 and
                                text[row - 1].strip() == '')

            if indentationMacro:
                # There is an indentation-macro invocation here.

                # Add an empty line.
                newText.append('')

                # Gather the multiline parameter.
                parameterSet = self.extractMultilineParameter(text, row)

                # Get the name of the indentation macro.
                macroName= self.scopeStack.top().getString('indent').strip()

                switches = 0;
                
                outputExpansion = None
                parameterExpansion = None
                if len(macroName) >= 1:
                   if macroName[0] == '+':
                       outputExpansion = True
                       parameterExpansion = True
                       switches += 1
                   elif macroName[0] == '-':
                       outputExpansion = False
                       parameterExpansion = False
                       switches += 1
                
                if len(macroName) >= 2 and switches == 1:
                    if macroName[1] == '+':
                        parameterExpansion = True
                        switches += 1
                    elif macroName[1] == '-':
                        parameterExpansion = False
                        switches += 1
                
                macroName = macroName[switches : ]

                macroInvocation = MacroInvocation(
                     macroName,
                     parameterSet,
                     outputExpansion,
                     parameterExpansion,
                     row, 0,
                     row + len(parameterSet), 0)
            else:
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

            # Debug-report the macro-invocation.
            underlining = '-' * len(macroInvocation.name)

            invocationText = []
            invocationText.append(
                macroInvocation.name + ' ' +
                '(' + 
                    str(macroInvocation.beginRow) + 
                    ', ' +
                    str(macroInvocation.beginColumn) + 
                ')' +
                ' -> ' +
                '(' + 
                    str(macroInvocation.endRow) + 
                    ', ' +
                    str(macroInvocation.endColumn) + 
                ')')
            invocationText.append(underlining)
            invocationText += macroInvocation.parameterSet
            invocationText.append(underlining)
            self.reportDebug(invocationText, 'debug-macro-invocation')

            # See if the user requests the macro parameter to be 
            # expanded before the macro.
            if macroInvocation.parameterExpansion:
                # The parameter should be expanded before the macro.
                self.scopeStack.open(macroInvocation.name)
                macroInvocation.parameterSet = self.convert(macroInvocation.parameterSet)
                self.scopeStack.close()

            # Recursively expand the macro.
            macroText = self.expandMacro(macroInvocation)

            # Debug-report the result of the macro-expansion.
            self.reportDebug([underlining] + macroText + [underlining], 'debug-macro-expansion')

            # Append the first line of the macro expansion to 
            # the end of the latest line.
            newText[-1] += macroText[0]
            # Append the other lines of the macro expansion to
            # the following lines.
            newText += macroText[1 :]

            # Move on.
            row = macroInvocation.endRow
            column = macroInvocation.endColumn
        
        # The last '' is extraneous.
        if newText[-1] == '':
            newText[-1 :] = []

        return newText
    
    def macro(self, macroName, macroParameter = ''):
        '''
        Expands a macro with the given parameter.

        macroName (string):
        The name of the macro.

        macroParameter (list of strings):
        The parameter of the macro.

        returns (list of strings):
        The output of the macro.
        '''
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
        '''
        Returns the join of all htmlHead()'s of used macros.

        returns (list of strings):
        The join of all htmlHead()'s of used macros.
        '''
        htmlText = []
        for macro in self.usedMacroSet:
            htmlText += macro.htmlHead(self)
        return htmlText                                

def _leadingTabs(text, tabSize, tabsAtMost = -1):
    '''
    Returns the number of leading tabs.
    If there are 'tabSize' number of consecutive spaces, 
    then this will interpreted as a single tab.

    text (string):
    The text from which to count the leading tabs from.

    tabSize (integer):
    The number of spaces in a tab.

    tabsAtMost (integer):
    The number of leading tabs to count at most.
    If this is negative, then the number of tabs
    to count is not limited.

    returns (integer, integer):
    The first number of is the number of leading tabs,
    as defined above. The second number is the number
    of leading characters taking part to this count.
    '''
    tabs = 0
    consecutiveSpaces = 0
    characters = 0;
    for c in text:
        if c == '\t':
            tabs += 1
            characters += consecutiveSpaces + 1
            consecutiveSpaces = 0
        elif c == ' ':
            consecutiveSpaces += 1
            if consecutiveSpaces == tabSize:
                # Interpret the spaces as a single tab.
                tabs += 1
                characters += consecutiveSpaces
                consecutiveSpaces = 0
        else:
            break

        if tabsAtMost >= 0 and tabs == tabsAtMost:
            break
    
    return tabs, characters

def _removeLeadingTabs(text, tabSize, tabsAtMost = -1):
    '''
    Removes at most a given number of leading tabs from the text.

    If there are less leading tabs than the given number, then all 
    the leading tabs are removed.

    text (string):
    The text from which to remove the leading tabs from.

    tabSize (integer):
    The number of spaces in a tab.

    tabsAtMost (integer):
    The number of leading tabs to remove at most. If this is negative,
    then all leading tabs will be removed.

    returns (string):
    The text with leading tabs removed.
    '''

    tabs, characters = _leadingTabs(text, tabSize, tabsAtMost)
    return text[characters :]

