#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Description: Console executable
# Documentation: implementation.txt 

import sys
import os
import shutil
from time import clock

# Older versions of Markdown (e.g. 2.0.0 which we need), have
# the following bug. The command-line script is named `markdown.py`,
# and the package is named `markdown`. When `import markdown` is
# issued in the same directory as `markdown.py` (or `markdown.pyc`), 
# the import refers to the script module, and not the package as it should.
# Python uses the sys.path as a list of directories to search for modules 
# to import. Therefore we fix this problem by removing those directories from 
# sys.path which refer to the same directory as where the remark.py script 
# is located.

# This is where remark.py is located.
scriptDirectory = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))

# Remove 'scriptDirectory' from sys.path.
newSysPath = []
for i in range(len(sys.path)):
    # The paths in sys.path are relative to the script directory
    # (or they are absolute paths).
    # Note that sys.path may contain the script directory in multiple 
    # different forms, e.g. '/usr/local/bin', '../bin', or ''. 
    path = os.path.normpath(os.path.join(scriptDirectory, sys.path[i]))
    if path != scriptDirectory:
        newSysPath.append(path)
    else:
        #print 'Removed', sys.path[i], ' from Python path.'
        None
sys.path = newSysPath

# Test that the Markdown library is present.
try:
    import markdown
except ImportError:
    print 'Error: Python Markdown library missing. Please install it first.'
    sys.exit(1)

if not (markdown.version == '2.0'):
    # The later versions of Markdown do not support Markdown in html-blocks.
    # This makes Remark work incorrectly, so we will check the version here.
    print 'Error: Python Markdown must be of version 2.0. Now it is ' + markdown.version + '.',
    sys.exit(1)

# Test that the Pygments library is present.
try: 
    import pygments
except ImportError:
    print 'Error: Pygments library missing. Please install it first.'
    sys.exit(1)

from Remark.Macro_Registry import findMacro
from Remark.Document import Document
from Remark.DocumentTree import DocumentTree

from Remark.Conversion import convertDirectory
from Remark.FileSystem import unixDirectoryName, unixRelativePath, readFile, writeFile
from Remark.FileSystem import remarkVersion, fileExtension
from Remark.FileSystem import asciiMathMlName, copyIfNecessary, setGlobalOptions, globalOptions
from Remark.FileSystem import splitPath, findMatchingFiles, fileExists

from Remark.Reporting import Reporter, ScopeGuard

from Remark.Macros import *

from Remark.DocumentType_Registry import setDefaultDocumentType, associateDocumentType
from Remark.DocumentType_Registry import documentType

from Remark.DocumentTypes.CppCodeView_DocumentType import CppCodeView_DocumentType
from Remark.DocumentTypes.CodeView_DocumentType import CodeView_DocumentType
from Remark.DocumentTypes.RemarkPage_DocumentType import RemarkPage_DocumentType
from Remark.DocumentTypes.DirectoryView_DocumentType import DirectoryView_DocumentType
from Remark.DocumentTypes.Orphan_DocumentType import Orphan_DocumentType
from Remark.DocumentTypes.Copy_DocumentType import Copy_DocumentType

if os.name == 'nt':
    # Apply the bug-fix for the os.path.split() to
    # support UNC-paths (bug present in Python 2.7.3).
    os.path.split = splitPath

remarkPageType = RemarkPage_DocumentType()
cppCodeViewType = CppCodeView_DocumentType()
directoryViewType = DirectoryView_DocumentType()
codeViewType= CodeView_DocumentType()
orphanType = Orphan_DocumentType()
copyType = Copy_DocumentType()

remarkPageSet = ['.txt']
cppCodeViewSet = ['.cpp', '.cc', '.h', '.hh', '.hpp']
codeViewSet = ['.py', '.m', '.pm', '.pl', '.css', '.js', '.lua']
       
setDefaultDocumentType(copyType)
associateDocumentType(remarkPageSet, remarkPageType)
associateDocumentType(cppCodeViewSet, cppCodeViewType)
associateDocumentType(codeViewSet, codeViewType)
associateDocumentType('.remark-index', directoryViewType)
associateDocumentType('.remark-orphan', orphanType)

def parseArguments(reporter):
    '''
    Parses the command-line arguments given to Remark.
    '''
    from optparse import OptionParser

    optionParser = OptionParser(usage = """\
%prog inputDirectory outputDirectory (option|file-glob)*

Note: On Unix-based operating systems a glob must be placed in 
double quotes to prevent glob-expansion from taking place before
reaching Remark; write "*.txt" instead of *.txt.
""")
    
    optionParser.add_option('-d', '--disable',
        dest = 'disableSet',
        type = 'string',
        action = 'append',
        default = [],
        help = """disables a specific warning (e.g. -d invalid-input).""",
        metavar = 'WARNING')

    optionParser.add_option('-e', '--extensions',
        action="store_true", dest="extensions", default=False,
        help = """lists all extensions in the input directory together with examples.""")

    optionParser.add_option('-i', '--include',
        dest = 'includeSet',
        type = 'string',
        action = 'append',
        default = [],
        help = """includes files by their relative-paths (e.g. "*.txt").
This is equivalent to writing the file-glob directly as a positional argument.""",
        metavar = 'GLOB')

    optionParser.add_option('-l', '--lines',
        dest = 'maxTagLines',
        type = 'int',
        default = 200,
        help = """sets maximum number of lines for a tag-parser to scan a file for tags (default 200).""",
        metavar = 'LINES')

    optionParser.add_option('-m', '--max-file-size',
        dest = 'maxFileSize',
        type = 'int',
        default = 2**18,
        help = """sets maximum file-size to load (in bytes, default 262144).""",
        metavar = 'SIZE')

    optionParser.add_option('-o', '--options',
        dest = 'optionFileSet',
        type = 'string',
        action = 'append',
        default = ['remark_options'],
        help = """reads command-line options from an option-file (if present).
If the file path is relative, it is relative to the input directory.
The file `remark_options` is always included.""",
        metavar = 'FILEPATH')

    optionParser.add_option('-q', '--quick',
        action="store_true", dest="quick", default=False,
        help = """regenerates only modified documents and their parents. Note: only use for quick previews of edits; this process leaves many documents out-of-date. """)

    optionParser.add_option('-s', '--strict',
        action="store_true", dest="strict", default=False,
        help = """treats warnings as errors.""")

    optionParser.add_option('-u', '--unknowns',
        action="store_true", dest="unknown", default=False,
        help = """lists all files which are neither included or excluded.""")

    optionParser.add_option('-v', '--verbose',
        action="store_true", dest="verbose", default=False,
        help = """prints additional progress information.""")

    optionParser.add_option('-x', '--exclude',
        dest = 'excludeSet',
        type = 'string',
        action = 'append',
        default = [],
        help = """excludes files by their relative-paths (e.g "*CMake*").
Exclusion takes priority over inclusion.""",
        metavar = 'GLOB')

    # Parse the command-line arguments
    # --------------------------------

    argumentSet, args = optionParser.parse_args(sys.argv[1:])

    if len(args) < 2:
        # There were not enough arguments;
        # at least the input directory and the
        # output directory must be given.
        # Print the help and quit.
        optionParser.print_help()
        sys.exit(1)

    # Positional arguments
    # --------------------
        
    # Get the working directory.
    workingDirectory = os.getcwd()

    # Get the input directory.
    # It is given relative to the working directory.
    argumentSet.inputDirectory = (
        os.path.normpath(os.path.join(workingDirectory, args[0])))

    # Get the output directory.
    # It is given relative to the working directory.
    argumentSet.outputDirectory = (
        os.path.normpath(os.path.join(workingDirectory, args[1])))

    # This is the directory which contains 'remark.py'.
    argumentSet.scriptDirectory = os.path.normpath(sys.path[0])

    # Interpret the rest of the positional arguments
    # as including files, i.e. the same
    # as the -i option.
    argumentSet.includeSet += args[2:]

    # Option files
    # ------------

    # Limit the size of the option files, to avoid
    # reading lots of stuff if an incorrect option file
    # is given.
    maxOptionFileSize = 2**16;

    # An option file may recursively specify other
    # option files. We read them all, but avoid reading
    # any option file twice.
    readOptionFileSet = []
    while len(argumentSet.optionFileSet) > 0:
        # We copy the optionFileSet because the inner
        # parse_args() may modify argumentSet.optionFileSet.
        optionFileSet = argumentSet.optionFileSet
        # Clear the list of option files, so that we
        # know which ones are given as new ones in
        # this option file.
        argumentSet.optionFileSet = []
        for optionFile in optionFileSet:
            if optionFile in readOptionFileSet:
                # This option file has already been read.
                # Skip reading it again.
                continue;

            # Mark the option file as read.
            readOptionFileSet.append(optionFile)

            # An option file is physically read only if its present.
            if fileExists(optionFile, argumentSet.inputDirectory):
                # An option-file path is relative to the input directory.
                optionFilePath = unixDirectoryName(os.path.join(argumentSet.inputDirectory, optionFile))
                # Read the option file.
                reporter.report('Reading option file ' + optionFilePath + '...', 'verbose')
                optionText = readFile(optionFilePath, maxOptionFileSize)
                # Parse the new command-line arguments.
                argumentSet, args = optionParser.parse_args(optionText, argumentSet)
                argumentSet.includeSet += args

    # Act on options
    # --------------

    argumentSet.tabSize = 4;
    if argumentSet.maxTagLines <= 0:
        reporter.reportError('The maximum number of lines to scan for tags must be at least 1.',
                             'invalid-input')
        sys.exit(1)

    if not argumentSet.verbose:
        # Disable the verbose reports.
        reporter.disable('verbose')

    # Disable the report-types given by the -d switch.
    for reportType in argumentSet.disableSet:
        reporter.disable(reportType)

    if argumentSet.unknown:
        relativeNameSet = findMatchingFiles(
            argumentSet.inputDirectory,
            ["*"],
            argumentSet.includeSet + argumentSet.excludeSet)

        # Sort to an alphabetical order by relative-path.
        relativeNameSet.sort()

        # Print the unknown files.
        print
        for relativeName in relativeNameSet:
            print relativeName

        sys.exit(0)

    if argumentSet.extensions:
        extensionSet = {}
        for pathName, directorySet, filenameSet in os.walk(argumentSet.inputDirectory):
            for filename in filenameSet:
                extension = fileExtension(filename)
                if not extension in extensionSet:
                    extensionSet[extension] = filename

        # Sort to an alphabetical order by extension.
        sortedSet = extensionSet.keys()
        sortedSet.sort()

        # Print the extensions and their example files.
        print
        for extension in sortedSet:
            print extension, extensionSet[extension]

        sys.exit(0)

    return argumentSet

if __name__ == '__main__':
    reporter = Reporter()
    reporter.openScope('Remark ' + remarkVersion())

    # Parse the command-line arguments.
    argumentSet = parseArguments(reporter)

    # Set the global options. 
    # I should get get rid of this, and pass
    # around the argumentSet locally instead.
    setGlobalOptions(argumentSet)

    # Do everything.
    errors, warnings = convertDirectory(argumentSet, reporter)

    # Wrap things up.
    reporter.report(['', "That's all!"], 'verbose')
    reporter.closeScope('Remark ' + remarkVersion())

    if errors > 0 or (warnings > 0 and argumentSet.strict):
        # Indicate the presence of errors by a non-zero error-code.
        sys.exit(1)
