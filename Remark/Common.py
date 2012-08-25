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

def htmlDiv(enclosedText, className = ''):
    '''
    Encloses the given text in a <div> block and gives it a
    html-class, so that it can be styled with CSS.

    className:
    The name of the html-class to give to the div block.
    '''
    text = []
    text.append('')
    
    if className != '':
        text.append('<div class = "' + className + '">')
    else:
        text.append('<div>')
    
    # Note that this empty line is essential for Markdown
    # not to interpret the following stuff as html.
    text.append('')
    text += enclosedText
    text.append('')
    text.append('</div>')
    text.append('')
    text.append('<div class = "remark-end-list"></div>')
    text.append('')

    return text


def unixRelativePath(fromRelativeDirectory, toRelativePath):
    '''
    Forms a unix-style relative-path from the given relative
    directory to the given relative path.

    fromRelativeDirectory:
        The relative directory in which the link resides.

    toRelativePath:
        A relative path to link to.
    '''
    relativePath = os.path.relpath(toRelativePath, fromRelativeDirectory)
    return unixDirectoryName(relativePath)

def openFileUtfOrLatin(fileName):
    '''
    Opens a file for reading as utf-8 decoded.
    If the decoding fails, opens the file for reading 
    as latin-1 decoded (then every character is legal).
    '''
    try:
        file = codecs.open(fileName, mode = 'rU', encoding = 'utf-8-sig')
    except UnicodeDecodeError:
        print
        print 'Warning:', fileName, 
        print 'is not UTF-8 encoded. Assuming Latin-1 encoding.'
        file = codecs.open(fileName, mode = 'rU', encoding = 'latin-1')

    return file    

def readFile(fileName):
    '''
    Opens a file using openFileUtfOrLatin, and reads the contents 
    into a list of strings correponding to the rows of the file.
    '''
    fileSize = os.path.getsize(fileName)
    maxSize = globalOptions().maxFileSize
    if fileSize >= maxSize:
        # If the file is very large, then it probably is not
        # part of the Remark documentation. Refuse to read
        # such files.
        print
        print 'Warning:', fileName, 
        print 'is larger than', maxSize, 'bytes (it is', fileSize, 'bytes).',
        print 'Ignoring it.'
        return []
        
    # Read the file into memory
    text = []
    try:
        with openFileUtfOrLatin(fileName) as file:
            text = file.readlines()
    except UnicodeDecodeError:
        print
        print 'Warning:', fileName,
        print 'could not be read because of a unicode decode error.',
        print 'Ignoring it.'
        return []

    # Remove possible newlines from the ends of the lines.
    # The lines are encoded by the list-structure instead.
    for i in range(0, len(text)):
        text[i] = text[i].rstrip('\r\n')
            
    return text

_documentTypeMap = dict()

def associateDocumentType(inputExtension, documentType):
    '''
    Associates the given filename-extension to the given document-type
    object. The filename-extension-key is always stored lower-case,
    so that we can be case-insensitive for it.
    '''
    global _documentTypeMap
    _documentTypeMap[inputExtension.lower()] = documentType

def documentType(inputExtension):
    '''
    Returns the document-type object associated to a given
    filename-extension. The association can be set by the
    associateDocumentType() function. The filename-extension
    comparison is case-insensitive.
    '''
    global _documentTypeMap
    return _documentTypeMap.get(inputExtension.lower())

def copyIfNecessary(inputRelativeName, inputDirectory, 
                    outputRelativeName, outputDirectory):

    inputFilePath = os.path.join(inputDirectory, inputRelativeName)
    outputFilePath = os.path.join(outputDirectory, outputRelativeName)

    # If the output directory does not exist, create it.
    finalOutputDirectory = os.path.split(outputFilePath)[0];
    if not os.path.exists(finalOutputDirectory):
        os.makedirs(finalOutputDirectory)

    if not os.path.exists(inputFilePath):
        print 'Error: CopyIfNecessary: the file ' + inputRelativeName + ' does not exist. Ignoring it.'
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

