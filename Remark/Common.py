# -*- coding: utf-8 -*-

# Description: Common stuff used in Remark
# Documentation: core_stuff.txt

import os.path
import string
import codecs
import shutil

def linkAddress(fromDirectory, toFile):
    relativeName = os.path.relpath(toFile, fromDirectory)
    return unixDirectoryName(relativeName)

def readFile(fileName):
    text = []
    
    fileSize = os.path.getsize(fileName)
    maxSize = 2**18
    if fileSize >= maxSize:
        print
        print 'readFile: file \'' + fileName + '\' is larger than ', 
        print maxSize, ' bytes (', fileSize, 'bytes) . Ignoring it.'
        return text 
        
    # Read the file into memory
    try:
        with codecs.open(fileName, mode = 'rU', encoding = 'utf-8-sig') as file:
            text = file.readlines()
    except UnicodeDecodeError:
        print 'Warning: file \'' + fileName + '\' is not UTF-8 encoded. Assuming Latin-1 encoding.'
        with codecs.open(fileName, mode = 'rU', encoding = 'latin-1') as file:
            text = file.readlines()
            
    # Remove possible newlines from the ends of the lines.
    for i in range(0, len(text)):
        if text[i][-1] == '\n':
            text[i] = text[i][0 : -1]
            
    return text

_documentTypeMap = dict()

def associateDocumentType(inputExtension, documentType):
    global _documentTypeMap
    _documentTypeMap[inputExtension] = documentType

def documentType(inputExtension):
    global _documentTypeMap
    if inputExtension in _documentTypeMap:
        return _documentTypeMap[inputExtension]
    return None

def copyIfNecessary(inputFilePath, outputFilePath):
    targetDirectory = os.path.split(outputFilePath)[0]
    if not os.path.exists(targetDirectory):
        os.makedirs(targetDirectory)
    if not os.path.exists(outputFilePath):
        shutil.copy(inputFilePath, outputFilePath)

def outputDocumentName(name):
    inputExtension = os.path.splitext(name)[1]
    type = documentType(inputExtension)
    outputName = name
    if type != None:
        outputName = type.outputName(name)
    return unixDirectoryName(outputName) 

def unixDirectoryName(name):
    return string.replace(os.path.normpath(name), '\\', '/')                

def changeExtension(fileName, newExtension):
    return os.path.splitext(fileName)[0] + newExtension

def linkTable(linkSet):
    text = []
    links = len(linkSet)
    if links <= 4:
        # If there are at most 4 documentation
        # children, they are simply listed below each other.
        for link in linkSet:
            linkTarget = link[0]
            linkDescription = link[1]
            # For some reason the <p></p> has to be there, or
            # otherwise the result is garbage. I think it's
            # Python Markdown which can't digest it without
            # them.
            tableEntry = '<p><a href="' + linkTarget + '">' + linkDescription + '</a></p>'
            text.append(tableEntry)
    else:
        # Otherwise the children are shown
        # using a table of 2 or 3 columns. 

        tableColumns = 2
        if links > 8:
            tableColumns = 3
            
        tableRows = (links + tableColumns - 1) / tableColumns

        tableRow = 0
        tableColumn = 0
        text.append('<table class = "division">')
        text.append('<tr class = "division">')
        
        while tableRow < tableRows:
            tableIndex = tableRow + tableColumn * tableRows
            tableEntry = ''
            if tableIndex < links:
                link = linkSet[tableIndex] 
                linkTarget = link[0]
                linkDescription = link[1]
                tableEntry = '<a href="' + linkTarget + '">' + linkDescription + '</a>'
            text.append('<td class = "division">' + tableEntry + '</td>')                                
                
            tableColumn += 1
            if tableColumn == tableColumns:
                text.append('</tr>')
                text.append('<tr>')
                tableRow += 1
                tableColumn = 0             
        text.append('</tr>')
        text.append('</table>')
    return text
    
