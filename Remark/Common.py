# -*- coding: utf-8 -*-

# Description: Common stuff used in Remark
# Documentation: core_stuff.txt

import os.path
import string
import codecs
import shutil
import fnmatch
import re

globalOptions_ = None

def splitPath(p):
    """Split a pathname.

    This is a bug-fixed version of os.path.split() from
    Python 2.7.3. It used os.path.splitdrive() which does not correctly
    handle long-UNC paths. This is fixed by using os.path.splitunc()
    instead.

    returns: 
    tuple (head, tail) where tail is everything after the final slash.
    Either part may be empty."""

    d, p = os.path.splitunc(p)
    # set i to index beyond p's last slash
    i = len(p)
    while i and p[i-1] not in '/\\':
        i = i - 1
    head, tail = p[:i], p[i:]  # now tail has no slashes
    # remove trailing slashes from head, unless it's all slashes
    head2 = head
    while head2 and head2[-1] in '/\\':
        head2 = head2[:-1]
    head = head2 or head
    return d + head, tail

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

def globToRegex(glob):
    if not isinstance(glob, basestring):
        regexSet = []
        for line in glob:
            regexSet.append(globToRegex(line))
        return combineRegex(regexSet)

    return fnmatch.translate(glob.strip())

def combineRegex(regex):
    regexString = ''
    if isinstance(regex, basestring):
        regexString = regex
    else:
        regexSet = []
        for line in regex:
            regexSet.append(line.strip())
        if regexSet != []:
            # Join together as alternatives, grouped
            # in non-capturing parentheses.
            regexString = r'(?:' + r')|('.join(regexSet) + r')'
    return regexString

def escapeMarkdown(text):
    escapedText = ''
    escapeSet = set(['*', '_'])
    for c in text:
        if c in escapeSet:
            escapedText += '\\'
        escapedText += c
    return escapedText

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
        file = codecs.open(longPath(fileName), mode = 'rU', encoding = 'utf-8-sig')
    except UnicodeDecodeError:
        print
        print 'Warning:', fileName, 
        print 'is not UTF-8 encoded. Assuming Latin-1 encoding.'
        file = codecs.open(longPath(fileName), mode = 'rU', encoding = 'latin-1')

    return file    

def fileSize(fileName):
    '''
    Calls os.path.getsize(longPath(fileName)).
    '''
    return os.path.getsize(longPath(fileName))

def readFile(fileName, ignoreLargeFiles = True):
    '''
    Opens a file using openFileUtfOrLatin, and reads the contents 
    into a list of strings corresponding to the rows of the file.
    '''
    size = fileSize(fileName)
    maxSize = globalOptions().maxFileSize
    if size >= maxSize and ignoreLargeFiles:
        # If the file is very large, then it probably is not
        # part of the Remark documentation. Refuse to read
        # such files.
        print
        print 'Warning:', fileName, 
        print 'is larger than', maxSize, 'bytes (it is', size, 'bytes).',
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

def writeFile(text, outputFullName):
    '''
    Writes text into a file using utf-8 encoding.

    text (a list of strings):
    The text to write into the file.

    outputFullName (string):
    The name of the file to write to.
    '''
    # If the directories do not exist, create them.
    outputDirectory = os.path.split(outputFullName)[0]
    if not pathExists(outputDirectory):
        createDirectories(outputDirectory)

    # Save the text to a file.
    with codecs.open(longPath(outputFullName), mode = 'w', encoding = 'utf-8') as outputFile:
        for line in text:
            outputFile.write(line)
            outputFile.write('\n')

_documentTypeMap = dict()
_defaultDocumentType = None

def setDefaultDocumentType(documentType):
    global _defaultDocumentType
    _defaultDocumentType = documentType

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

def strictDocumentType(inputExtension):
    '''
    Returns the document-type object associated to a given
    filename-extension. If there is no such, None is
    returned instead. The filename-extension comparison is 
    case-insensitive.
    '''
    return _documentTypeMap.get(inputExtension.lower())

def documentType(inputExtension):
    '''
    Returns the document-type object associated to a given
    filename-extension. If there is no such, the default
    document-type object is returned instead. The 
    filename-extension comparison is case-insensitive.
    '''
    return _documentTypeMap.get(inputExtension.lower(), _defaultDocumentType)

def createDirectories(name):
    '''
    Calls os.makedirs(longPath(name)).
    '''
    os.makedirs(longPath(name))

def pathExists(path):
    '''
    Calls os.path.exists(longPath(path))
    '''
    return os.path.exists(longPath(path))

def copyTree(inputDirectory, outputDirectory):
    '''
    Calls shutil.copytree(longPath(inputDirectory), longPath(outputDirectory)).
    '''
    shutil.copytree(longPath(inputDirectory), longPath(outputDirectory))
    
def copyFile(inputRelativeName, inputDirectory, 
             outputRelativeName, outputDirectory):
    '''
    Copies an input-file to the output-file. Creates
    the needed input directories if they do not exist.
    If the input-file does not exist, nothing is done.

    inputRelativeName (string):
    The name of the input-file, relative to the input-directory.

    inputDirectory (string):
    The input-directory.

    outputRelativeName (string):
    The name of the output-file, relative to the output-directory.

    inputDirectory (string):
    The output-directory.
    '''
    inputFilePath = os.path.join(inputDirectory, inputRelativeName)
    outputFilePath = os.path.join(outputDirectory, outputRelativeName)

    # If the output directory does not exist, create it.
    finalOutputDirectory = os.path.split(outputFilePath)[0];
    if not pathExists(finalOutputDirectory):
        createDirectories(finalOutputDirectory)

    # Copy the file.
    shutil.copy(longPath(inputFilePath), longPath(outputFilePath))

def longPath(path):
    '''
    Returns the input path with a possible long-UNC-prefix //?/.
    
    returns:
    The input path prefixed with //?/, if under Windows, or the
    input path unchanged under other operating systems.
    '''
    # Windows has a limit of 260 characters for standard paths.
    # Longer paths need to use a special long-UNC notation which is 
    # denoted by a prefix //?/. 
    if os.name == 'nt':
        return '//?/' + path

    return path

def copyIfNecessary(inputRelativeName, inputDirectory, 
                    outputRelativeName, outputDirectory):
    '''
    Copies an input-file to an output file if and only if
    the output file is not up-to-date as determined by
    fileUpToDate().

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
    upToDate = fileUpToDate(inputRelativeName, inputDirectory, 
                            outputRelativeName, outputDirectory)

    if not upToDate:
        copyFile(inputRelativeName, inputDirectory,
                 outputRelativeName, outputDirectory)

    return not upToDate

def listDirectory(path):
    '''
    Returns os.listdir(longPath(path)).
    '''
    return os.listdir(longPath(path))

def fileModificationTime(filePath):
    '''
    Returns os.path.getmtime(longPath(filePath)).
    '''
    return os.path.getmtime(longPath(filePath))

def fileExists(inputRelativeName, inputDirectory):
    '''
    Returns pathExists(os.path.join(inputDirectory, inputRelativeName)).
    '''
    return pathExists(os.path.join(inputDirectory, inputRelativeName))

def fileUpToDate(inputRelativeName, inputDirectory,
                 outputRelativeName, outputDirectory):
    '''
    Returns whether the output-file is up-to-date.

    returns:
    Whether the output file exists and has a modification 
    time-stamp not later than with the input file.
    '''
    inputFilePath = os.path.join(inputDirectory, inputRelativeName)
    outputFilePath = os.path.join(outputDirectory, outputRelativeName)

    if not pathExists(inputFilePath):
        print 'Error: fileUpToDate: the input file ' + inputRelativeName + ' does not exist.'
        return False

    # The output file is up-to-date if it exists and has a 
    # modification time-stamp not later than with the input file.
    return (pathExists(outputFilePath) and 
        fileModificationTime(inputFilePath) <= fileModificationTime(outputFilePath))

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

