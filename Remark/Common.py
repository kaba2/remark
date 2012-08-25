# -*- coding: utf-8 -*-

# Description: Common stuff used in Remark
# Documentation: core_stuff.txt

import os.path
import string
import codecs
import shutil

globalOptions_ = None

def setGlobalOptions(options):
    '''
    Sets the global options object. The global options 
    can then be accessed by globalOptions().
    '''
    global globalOptions_
    globalOptions_ = options

def globalOptions():
    '''
    Returns the global options object.
    '''
    return globalOptions_;

def remarkVersion():
    '''
    Returns the version of Remark as a string.
    '''
    return '1.5.0'

def asciiMathMlName():
    '''
    Returns the name of the Javascript file to
    use for AsciiMathML.
    '''
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
    into a list of strings corresponding to the rows of the file.
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

    inputExtension (string or list-of-strings):
    The file-extensions to associate to the given document-type.
    '''
    global _documentTypeMap
    if isinstance(inputExtension, basestring):
        _documentTypeMap[inputExtension.lower()] = documentType
    else:
        for extension in inputExtension:
            associateDocumentType(extension, documentType)            

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
    '''
    Copies an input-file only if the output-file does not exist,
    or the input-file has a modification time-stamp later than 
    with the output-file. If the input-file does not exist,
    nothing is done.

    inputRelativeName (string):
    The name of the input-file, relative to the input-directory.

    inputDirectory (string):
    The input-directory.

    outputRelativeName (string):
    The name of the output-file, relative to the output-directory.

    inputDirectory (string):
    The output-directory.

    returns:
    A boolean stating if the file was actually copied.
    '''
    inputFilePath = os.path.join(inputDirectory, inputRelativeName)
    outputFilePath = os.path.join(outputDirectory, outputRelativeName)

    # If the output directory does not exist, create it.
    finalOutputDirectory = os.path.split(outputFilePath)[0];
    if not os.path.exists(finalOutputDirectory):
        os.makedirs(finalOutputDirectory)

    if not os.path.exists(inputFilePath):
        print 'Error: CopyIfNecessary: the file ' + inputRelativeName + ' does not exist. Ignoring it.'
        return False

    # The output file is up-to-date if it exists and has a 
    # modification time-stamp not later than with the input file.
    fileUpToDate = \
        (os.path.exists(outputFilePath) and 
        os.path.getmtime(inputFilePath) <= os.path.getmtime(outputFilePath))

    if not fileUpToDate:
        if globalOptions().verbose:
            print 'Copying', inputRelativeName, '...'
        shutil.copy(inputFilePath, outputFilePath)

    return not fileUpToDate

def outputDocumentName(name):
    '''
    Returns the name of the output-document given the input-document
    filename. This is given by the document-type associated to the 
    filename-extension of the given filename. If the file does not
    have a document-type, then the name is returned as it is.
    '''
    inputExtension = os.path.splitext(name)[1]
    type = documentType(inputExtension)
    outputName = name
    if type != None:
        outputName = type.outputName(name)
    return unixDirectoryName(outputName) 

def unixDirectoryName(name):
    '''
    Returns a normalized unix-style directory-name of the given 
    directory-name (unix-style or not).
    '''
    return string.replace(os.path.normpath(name), '\\', '/')                

def fileExtension(fileName):
    '''
    Returns the filename-extensions of the the filename.
    '''
    return os.path.splitext(fileName)[1]

def withoutFileExtension(fileName):
    '''
    Returns the filename without the filename-extension.
    '''
    return os.path.splitext(fileName)[0]

def changeExtension(fileName, newExtension):
    '''
    Changes the filename-extension to another.
    '''
    return withoutFileExtension(fileName) + newExtension

