# -*- coding: utf-8 -*-

# Description: File-system abstractions
# Documentation: algorithms.txt

import os.path
import string
import codecs
import shutil
import fnmatch
import re

globalOptions_ = None

def remarkDirectory():
    '''
    Returns the directory containing the Remark package.
    '''
    return os.path.dirname(os.path.realpath(__file__))

remarkScriptpath_ = ''
def remarkScriptPath():
    '''
    Returns the path to the remark.py command-line script.
    This is non-empty only if Remark is used from the
    command-line, and not as a module.
    '''
    global remarkScriptPath_
    return remarkScriptPath_

def setRemarkScriptPath(path):
    global remarkScriptPath_
    remarkScriptPath_ = os.path.normpath(path)

def findMatchingFiles(inputDirectory, includeSet, excludeSet):
    '''
    Finds each file in the given directory whose relative-name 
    matches an inclusion-glob and does not match an exclusion-glob.

    inputDirectory (string):
    Path to the directory.

    includeSet (iterable of strings):
    A set of inclusion-globs.

    excludeSet (iterable of strings):
    A set of exclusion-globs.

    returns (list of strings):
    The set of relative-names of matching files.
    '''

    # Construct the matching regex strings.
    includeRegexString = globToRegex(includeSet)
    excludeRegexString = globToRegex(excludeSet)

    # Compile the regex strings into regexes.
    includeRegex = re.compile(includeRegexString)
    excludeRegex = re.compile(excludeRegexString)
    
    # Gather the specified files.
    relativeNameSet = []
    for pathName, directorySet, fileNameSet in os.walk(inputDirectory):
        for filename in fileNameSet:
            fullName = os.path.normpath(os.path.join(pathName, filename))
            relativeName = unixRelativePath(inputDirectory, fullName)
            if (re.match(includeRegex, relativeName) != None and
                not re.match(excludeRegex, relativeName)):
                # The relative-name of the file matches 
                # the inclusion-glob, and does not match 
                # the exclusion-glob; take it in.
                relativeNameSet.append(relativeName)

    # Return the set of matching files.
    return relativeNameSet

def splitPath(p):
    '''
    Splits a pathname.

    This is a bug-fixed version of os.path.split() from
    Python 2.7.3. It used os.path.splitdrive() which does not correctly
    handle long-UNC paths. This is fixed by using os.path.splitunc()
    instead.

    returns: 
    tuple (head, tail) where tail is everything after the final slash.
    Either part may be empty.
    '''

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
    Sets the global-options object. The global options 
    can then be accessed by globalOptions().
    '''
    global globalOptions_
    globalOptions_ = options

def globalOptions():
    '''
    Returns the global-options object.
    '''
    return globalOptions_;

def htmlInject(text):
    def injectString(line):
        return '<!--RemarkInject' + line + 'RemarkInject-->'

    if type(text) == 'str' or type(text) == 'unicode':
        return injectString(text)

    if len(text) == 0:
        return text
        
    # Wrap the text into an html-comment.
    # This makes Python Markdown to pass them
    # as html as they are. The RemarkInject
    # is a keyword which Remark uses to remove
    # the comments later from the generated html.

    injectedText = []
    for line in text:
        injectedText.append(injectString(line))

    # Why not pass html as text? Because the Python
    # Markdown postprocessor converts symbols to
    # html entities. Python Markdown itself circumvents
    # this by replacing embedded html with placeholders,
    # and then expanding those placeholders after entity
    # replacement. We cannot currently use the same technique,
    # since it requires access to Markdown parsers
    # self.htmlStash. So instead we turn the data to
    # an embedded html-comment.

    return injectedText

def htmlRegion(htmlText):
    # We need to wrap the html into a region to avoid
    # it being wrapped into a <p> element.
    keySet = {
        'class' : 'html', 
        'remark-content' : 'remark-no-p'}

    return markdownRegion(htmlInject(htmlText), keySet)

def markdownRegion(enclosedText, keySet = dict(), elementName = 'div'):
    '''
    Encloses the given text in a Markdown region (Remark extension)

    !!! <elementName aKey="aValue" bKey="bValue" ...>
        enclosedText

    enclosedText (list of strings):
    The text to enclose.

    keySet (string:string):
    A set of key-value pairs to apply to the region.

    elementName (string):
    The name of the region element.
    '''

    regionText = '!!! <' 
    regionText += elementName

    for (key, value) in keySet.iteritems():
        regionText += ' ' + key.strip() + ' = "' + value + '"'

    regionText += '>'
    
    text = []
    text.append(regionText)

    for line in enclosedText:
        text.append('\t' + line)

    return text

def globToRegex(glob):
    '''
    Converts a glob or a set of globs to a regular expression.

    If glob is a string, then it is simply converted to a 
    regular expression. Otherwise glob is assumed to be iterable,
    and each string in glob is converted to a regular expression, 
    which are then combined as alternatives into a single regular 
    expression. If the iterable is empty, then a regex is generated
    which matches nothing.

    glob (string or an iterable of strings):
    A glob or a set of globs to convert to a regular expression.

    returns (string):
    The converted regular expression.
    '''
    if not isinstance(glob, basestring):
        regexSet = []
        for line in glob:
            regexSet.append(globToRegex(line))
        if len(regexSet) == 0:
            # Match nothing.
            regexSet.append(r'(?!)')
        return combineRegex(regexSet)

    return fnmatch.translate(glob.strip())

def combineRegex(regex):
    '''
    Combines a regular expression or a set of regular expression 
    as alternatives into a single regular expression.

    If the regular expression is a string, it is returned as it is.
    Otherwise each regular expression is grouped into a non-capturing
    parenthesis and these groups are combined as alternatives.

    regex (string or an iterable of strings):
    The regular expression or a set of regular expression to 
    combine. Whitespace will be removed from both sides of
    each regular expression.

    returns (string):
    The combined regular expression.
    '''
    regexString = ''
    if isinstance(regex, basestring):
        regexString = regex.strip()
    else:
        regexSet = []
        for line in regex:
            regexSet.append(line.strip())
        if regexSet != []:
            if len(regexSet) > 1:
                # Join together as alternatives, grouped
                # in non-capturing parentheses.
                regexString = r'(?:' + r')|('.join(regexSet) + r')'
            else:
                # Use the regex as it is.
                regexString = regexSet[0]
    return regexString

def escapeMarkdown(text):
    '''
    Escapes the * and _ Markdown meta-characters by \* and \_.

    text (string):
    The text to escape.

    returns (string):
    The text with * and _ replaced with \* and \_, respectively.
    '''
    escapedText = ''
    escapeSet = set(['*', '_'])
    for c in text:
        if c in escapeSet:
            escapedText += '\\'
        escapedText += c
    return escapedText

def pathSuffixSet(relativePath):
    '''
    Returns the set of path-suffixes of a given relative-path.

    relativePath (string):
    The relative-path to compute the path-suffixes for.

    returns (list of strings):
    The set of path-suffixes for the relative-path.
    '''
    path = unixDirectoryName(relativePath)
    n = len(path)
    index = n
    lastStart = index
    suffixSet = []
    while index > 0:
        index -= 1
        if (relativePath[index] == '/' and index < n):
            suffixSet.append(relativePath[index + 1 : ])
    return suffixSet

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

def openFileUtf8(fileName):
    '''
    Opens a file for reading as utf-8 decoded.
    Decoding errors are treated by 'replace'.

    fileName (string):
    The file to open.

    returns:
    A handle to the opened file.
    '''
    file = codecs.open(longPath(fileName),
                       mode = 'rU', encoding = 'utf-8-sig', 
                       errors = 'replace')

    return file    

def fileSize(fileName):
    '''
    Returns os.path.getsize(longPath(fileName)).
    '''
    return os.path.getsize(longPath(fileName))

def readFile(fileName, maxSize = -1):
    '''
    Opens a file using openFileUtf8, and reads the contents 
    into a list of strings corresponding to the rows of the file.
    The form-feeds and newlines are stripped off from the end of
    each line. 

    fileName (string):
    The file to read.

    maxSize (integer):
    Maximum size of a file to read. Use a negative number
    for unbounded size.
    
    returns (list of strings):
    The rows of the file, if the file is not skipped. Otherwise
    the empty list [].
    '''
    size = fileSize(fileName)
    if maxSize >= 0 and size >= maxSize:
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
        with openFileUtf8(fileName) as file:
            text = file.readlines()
    except:
        print
        print 'Warning:', fileName,
        print ' could not be read for some reason.',
        print ' Ignoring it.'
        return []

    for i in range(0, len(text)):
        # Remove possible newlines from the ends of the lines.
        # The lines are encoded by the list-structure instead.
        # Note that this should have been done by 
        # file.readlines(keepends = False). However, it is a bug 
        # in Python 2.7.3 that the keepends argument is missing. 
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
        # Note that we can't use outputFile.writelines() because it would
        # concatenate the lines without the new-line at the end.
        for line in text:
            outputFile.write(line)
            outputFile.write('\n')

def createDirectories(name):
    '''
    Calls os.makedirs(longPath(name)).
    '''
    os.makedirs(longPath(name))

def pathExists(path):
    '''
    Returns os.path.exists(longPath(path))
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
    Returns the input path with a possible long-UNC-prefix \\?\.
    
    returns:
    The input path prefixed with \\?\, if under Windows and
    the path is longer than 259 characters. Otherwise the input
    path unchanged.
    '''
    # Windows has a limit of 260 characters for the length of 
    # standard paths, including the null-character at the end.
    # Longer paths need to use a special long-UNC notation which is 
    # denoted by a prefix \\?\. 
    
    # You would hope that this fixed the long-path problems with 
    # Windows, but this unfortunately is not the case. For example, 
    # the CreateDirectoryW function of the Windows API does not 
    # support long-paths even by the \\?\-prefix, contrary to its 
    # documentation. So why we bother here? The reason is that oddly 
    # this trick works to support slightly longer paths with network-
    # mapped drives, which use some kind of path-compression to 
    # artifically produce longer path-names (but the compressed path 
    # also needs to be <= 259 characters). In particular, this 
    # situation comes by when the mapped-drive is a Linux file 
    # system, and contains paths longer than 259 characters.

    # It is essential that the \\?\ is only prefixed
    # for paths longer than 259 characters. The reason is related to
    # Python's handling of directories, e.g. in listdir implemented
    # in posixmodule.c, which uses a / as a separator to append a
    # /*.* path-suffix. The \\?\ has the effect, in Windows API, of
    # disabling any string-processing for the path, including the
    # replacement of / with \. Therefore using the \\?\-prefix for
    # shorter paths leads to invalid path-names. But why then
    # is the \\?\-prefix ok with paths longer than 259 characters?
    # I have no idea, but in our tests, the / suddenly becomes 
    # acceptable as a separator after this breakpoint.

    # To be consistent with Python, you might be thinking of using
    # the //?/-prefix instead. This has the effect of not disabling
    # the string-processing in Windows API, and the result is that
    # / are converted to \, leading to the \\?\-prefix, and also
    # avoiding the invalid path-names. However, for some unimaginable 
    # reasons, this is not equivalent to the \\?\-prefix, and does 
    # not work to support those long path-names in network-mapped 
    # drives.

    if os.name == 'nt' and len(path) > 259:
        return '\\\\?\\' + path

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

def unixDirectoryName(name):
    '''
    Returns a normalized unix-style directory-name of the given 
    directory-name (unix-style or not).
    '''
    return string.replace(os.path.normpath(name), '\\', '/')                

def fileExtension(fileName):
    '''
    Returns the filename-extension of the the filename.
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

