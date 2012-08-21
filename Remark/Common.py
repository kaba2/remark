# -*- coding: utf-8 -*-

# Description: Common stuff used in Remark
# Documentation: core_stuff.txt

import os.path
import string
import codecs
import shutil

globalOptions_ = None

def setGlobalOptions(options):
    global globalOptions_
    globalOptions_ = options

def globalOptions():
    return globalOptions_;

def remarkVersion():
    return '1.5.0'

def asciiMathMlName():
    return 'ASCIIMathMLwFallback.js'

def linkAddress(fromDirectory, toFile):
    relativeName = os.path.relpath(toFile, fromDirectory)
    return unixDirectoryName(relativeName)

def openFileUtfOrLatin(fileName):
    try:
        file = codecs.open(fileName, mode = 'rU', encoding = 'utf-8-sig')
    except UnicodeDecodeError:
        print 'Warning: file \'' + fileName + '\' is not UTF-8 encoded. Assuming Latin-1 encoding.'
        file = codecs.open(fileName, mode = 'rU', encoding = 'latin-1')

    return file    

def readFile(fileName):
    fileSize = os.path.getsize(fileName)
    maxSize = 2**18
    if fileSize >= maxSize:
        print
        print 'Warning: file \'' + fileName + '\' is larger than ', 
        print maxSize, ' bytes (', fileSize, 'bytes) . Ignoring it.'
        return []
        
    # Read the file into memory
    text = []
    try:
        with openFileUtfOrLatin(fileName) as file:
            text = file.readlines()
    except UnicodeDecodeError:
        print
        print 'Warning: file \'' + fileName + '\' ',
        print 'could not be read because of a unicode decode error. ',
        print 'Ignoring it.'
        return []

    # Remove possible newlines from the ends of the lines.
    for i in range(0, len(text)):
        text[i] = text[i].rstrip('\r\n')
            
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

def copyIfNecessary(inputRelativeName, inputDirectory, 
                    outputRelativeName, outputDirectory):

    inputFilePath = os.path.join(inputDirectory, inputRelativeName)
    outputFilePath = os.path.join(outputDirectory, outputRelativeName)

    # If the output directory does not exist, create it.
    finalOutputDirectory = os.path.split(outputFilePath)[0];
    if not os.path.exists(finalOutputDirectory):
        os.makedirs(finalOutputDirectory)

    if not os.path.exists(inputFilePath):
        print 'Error: the file ' + inputRelativeName + ' does not exist. Ignoring it.'
        return

    # The output file is up-to-date if it exists and has a 
    # modification time-stamp not later than with the input file.
    fileUpToDate = \
        (os.path.exists(outputFilePath) and 
        os.path.getmtime(inputFilePath) <= os.path.getmtime(outputFilePath))

    if not fileUpToDate:
        if globalOptions().verbose:
            print 'Copying', inputRelativeName, '...'
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

def fileExtension(fileName):
    return os.path.splitext(fileName)[1]

def withoutFileExtension(fileName):
    return os.path.splitext(fileName)[0]

def changeExtension(fileName, newExtension):
    return withoutFileExtension(fileName) + newExtension

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
        tableRows = (links + tableColumns - 1) / tableColumns

        tableRow = 0
        tableColumn = 0
        text.append('<table class = "learn-more">')
        
        while tableRow < tableRows:
            tableIndex = tableRow + tableColumn * tableRows
            tableEntry = ''
            if tableIndex < links:
                link = linkSet[tableIndex] 
                linkTarget = link[0]
                linkDescription = link[1]
                tableEntry = '<a href="' + linkTarget + '">' + linkDescription + '</a>'

            if tableColumn == 0:
                text.append('<tr>')
               
            text.append('<td>' + tableEntry + '</td>')                                
                
            tableColumn += 1
            if tableColumn == tableColumns:
                text.append('</tr>')
                tableRow += 1
                tableColumn = 0             

        text.append('</table>')
    return text
    
