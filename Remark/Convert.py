import re
import string
import os
import os.path

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
        parent = None
        if len(self.stack_) > 0:
            parent = self.top()                
        self.stack_.append(Scope(parent))
        
    def close(self):
        self.stack_.pop()
        
    def top(self):
        return self.stack_[-1]        

_scopeStack = ScopeStack()

def expandMacros(template, document, documentTree, level = 0):
    maxLevel = 10
    if level > maxLevel:
        print 'Error: Remark expansion exceeded recursion limit of', maxLevel
        print 'Check for infinite recursions!'
        return []
    
    if template == []:
        return []
    
    global _scopeStack
    
    _scopeStack.open()   
    scope = _scopeStack.top()
    
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
            print 'Warning:', document.relativeName, ': macro', match.group(0), ' has bad indentation. Ignoring it.'
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
        
        #print 'Found macro:', match.group(2)
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
            # The parameter is a multi-line.
            # Next we need to see which of the following
            # lines are part of the parameter.
            
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
        
        # Recursively expand the parameter to get the raw parameter.
        rawParameterSet = []
        if parameterSet != []:
            rawParameterSet = expandMacros(parameterSet, document, documentTree, level + 1)
        
        # Now expand the macro with the raw parameter.
        macroHandled = False
        macroName = match.group(1)
        macroPartSet = string.split(macroName)

        if len(macroPartSet) == 1:
            macro = findMacro(macroName)
            suppressList = scope.recursiveSearch('suppress_calls_to')
            if suppressList == None:
                suppressList = []
            if macro != None:
                if not macroName in suppressList:
                    text[i : i] = macro.expand(rawParameterSet, document, documentTree, scope)
                macroHandled = True
                #print 'Applying', macroName, 'yields:'
                #for line in text:
                #    print line
        elif len(macroPartSet) == 2:
            #print macroPartSet
            if string.lower(macroPartSet[0]) == 'set':
                # Setting a scope variable.
                scope.parent().insert(macroPartSet[1], rawParameterSet)
                macroHandled = True
            if string.lower(macroPartSet[0]) == 'add':
                # Appending to a scope variable.
                scope.parent().append(macroPartSet[1], rawParameterSet)
                macroHandled = True
            elif string.lower(macroPartSet[0]) == 'get':
                # Getting a scope variable.
                result = scope.parent().recursiveSearch(macroPartSet[1])
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
                       
    _scopeStack.close()   
    return text

def convert(template, document, documentTree, targetRootDirectory):
    #print document.relativeName, '...'
    
    if document.fileName != 'documentation.txt':
        return
    
    resetLinkId()
              
    # Expand macros.
    text = expandMacros(template, document, documentTree)

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
