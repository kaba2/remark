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
        result = self.search(name)
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
    macroRegex = re.compile(r'(\t*)\[\[' + macroText + r'\]\]' + optionalOneLineParameter)
    i = 0
    while i < len(text):
        line = text[i]
        match = re.search(macroRegex, line)
        if match == None:
            i += 1
            continue

        if match.start() != 0:
            print 'Warning:', document.relativeName, ': macro', match.group(0), ' has bad indentation. Ignoring it.'
            i += 1
            continue
   
        endLine = i + 1
        #print 'Found macro:', match.group(2)
        parameterSet = []
        hasParameters = (match.group(3) != None)
        if hasParameters:
            parameter = string.strip(match.group(3))
            if parameter != '':
                # One-line parameter
                parameterSet.append(parameter)
                
        if hasParameters and parameterSet == []:
            # Multi-line parameter
            # Find out the extent of the parameter.
            indentation = len(match.group(1))
            while endLine < len(text):
                # The end of a multi-line parameter
                # is marked by a line which is not all whitespace
                # and has indentation level less than or equal to 
                # 'indentation'.
                if _leadingTabs(text[endLine]) <= indentation and string.strip(text[endLine]) != '':
                    break
                endLine += 1
                
            # Copy the parameter and remove the indentation from it.
            parameterSet = [_removeLeadingTabs(line, indentation + 1) for line in text[i + 1 : endLine]]
            
        # Remove the macro from further expansion.
        text[i : endLine] = []
        
        # Remove the empty parameter lines from the end.
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
        macroName = match.group(2)
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
        else: 
            i = 0

#    if len(scope.nameSet_) > 0:
#        print 'I has scope variables! They are:'
#        for (name, data) in scope.nameSet_.iteritems():
#            print name, ':'
#            print data
                       
    _scopeStack.close()   
    return text

def convert(template, document, documentTree, targetRootDirectory):
    #print document.relativeName, '...'
    
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
