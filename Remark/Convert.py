import re
import string
import os
import os.path

from Remark.MacroRegistry import findMacro
from Remark.Common import changeExtension, outputDocumentName, resetLinkId

def expandMacros(template, document, documentTree, level = 0):
    maxLevel = 10
    if level > maxLevel:
        print 'Error: Remark expansion exceeded recursion limit of', maxLevel
        print 'Check for infinite recursions!'
        return []
    
    if template == []:
        return []
    
    text = template[:]
    remarkRegex = re.compile(r'(\t*)\[(.*)\](?::[ \t]*(.*))?')
    i = 0
    while i < len(text):
        line = text[i]
        match = re.search(remarkRegex, line)
        if match != None:
            macroName = match.group(2)
            macro = findMacro(macroName)
            if macro != None and match.start() != 0:
                print 'Warning:', document.relativeName, ': remark', match.group(0), ' has bad indentation. Ignoring it.'
            if macro != None and match.start() == 0:
                endLine = i + 1
                #print 'Found remark:', macroName
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
                        # Two types of lines continue the span of the
                        # parameter:
                        # 1) Those that have tabs at least of 'indentation' amount.
                        # 2) Lines that contain only whitespace.
                        if _leadingTabs(text[endLine]) < indentation and string.strip(text[endLine]) != '':
                            break
                        endLine += 1
                        
                    # Copy the parameter and remove one level of indentation from it.
                    parameterSet = [_removeLeadingTabs(line, indentation) for line in text[i + 1 : endLine]]
                    
                # Remove the remark from further expansion.
                text[i : endLine] = []
                
                # Recursively expand the parameter to get the raw parameter.
                rawParameterSet = []
                if parameterSet != []:
                    rawParameterSet = expandMacros(parameterSet, document, documentTree, level + 1)
                
                # Now expand the remark with the raw parameter.
                text[i : i] = macro.expand(rawParameterSet, document, documentTree)
                #print 'Applying', macroName, 'yields:'
                #for line in text:
                #    print line
                i = 0
            else:
                i += 1
        else: 
            i += 1

    return text

def convert(template, document, documentTree, targetRootDirectory):
    #print document.relativeName, '...'
    
    resetLinkId()
              
    # Expand remarks.
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
