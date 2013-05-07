#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Description: Console executable
# Documentation: implementation.txt 

import sys
import os
import shutil
from time import clock

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

try: 
    import pygments
except ImportError:
    print 'Error: Pygments library missing. Please install it first.'
    sys.exit(1)

from Macro_Registry import findMacro
from Document import Document
from DocumentTree import DocumentTree

from Conversion import convertDirectory
from FileSystem import unixDirectoryName, unixRelativePath, readFile, writeFile
from FileSystem import remarkVersion, fileExtension
from FileSystem import asciiMathMlName, copyIfNecessary, setGlobalOptions, globalOptions
from FileSystem import splitPath

from Reporting import Reporter, ScopeGuard

from Macros import *

from DocumentType_Registry import setDefaultDocumentType, associateDocumentType
from DocumentType_Registry import documentType

from DocumentTypes.CppCodeView_DocumentType import CppCodeView_DocumentType
from DocumentTypes.CodeView_DocumentType import CodeView_DocumentType
from DocumentTypes.RemarkPage_DocumentType import RemarkPage_DocumentType
from DocumentTypes.DirectoryView_DocumentType import DirectoryView_DocumentType
from DocumentTypes.Orphan_DocumentType import Orphan_DocumentType
from DocumentTypes.Copy_DocumentType import Copy_DocumentType

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
%prog [options] inputDirectory outputDirectory [files...]

The 'files' is a list of those files which should be converted;
globs are allowed (e.g. *.txt *.py).""")
    
    optionParser.add_option('-d', '--disable',
        dest = 'disableSet',
        type = 'string',
        action = 'append',
        default = [],
        help = """disables a specific warning (e.g. -d invalid-input)""",
        metavar = 'WARNING')

    optionParser.add_option('-i', '--include',
        dest = 'includeSet',
        type = 'string',
        action = 'append',
        default = [],
        help = """includes files into the input set (default *) """,
        metavar = 'FILES')

    optionParser.add_option('-x', '--exclude',
        dest = 'excludeSet',
        type = 'string',
        action = 'append',
        default = [],
        help = """excludes files from the input set (default "") """,
        metavar = 'FILES')

    optionParser.add_option('-I', '--include_directory',
        dest = 'includeDirectorySet',
        type = 'string',
        action = 'append',
        default = [],
        help = """includes directories into the input set (default *) """,
        metavar = 'FILES')

    optionParser.add_option('-X', '--exclude_directory',
        dest = 'excludeDirectorySet',
        type = 'string',
        action = 'append',
        default = [],
        help = """excludes directories from the input set (default "") """,
        metavar = 'FILES')

    optionParser.add_option('-e', '--extensions',
        action="store_true", dest="extensions", default=False,
        help = """lists all file-extensions in the input-directory along with example files""")

    optionParser.add_option('-l', '--lines',
        dest = 'maxTagLines',
        type = 'int',
        default = 200,
        help = """sets maximum number of lines for a tag-parser to scan a file for tags (default 200)""",
        metavar = 'LINES')

    optionParser.add_option('-m', '--max-file-size',
        dest = 'maxFileSize',
        type = 'int',
        default = 2**18,
        help = """sets maximum file-size to load (in bytes, default 262144)""",
        metavar = 'SIZE')

    optionParser.add_option('-q', '--quick',
        action="store_true", dest="quick", default=False,
        help = """regenerates only modified documents and their parents. Note: only use for quick previews of edits; this process leaves many documents out-of-date. """)

    optionParser.add_option('-s', '--strict',
        action="store_true", dest="strict", default=False,
        help = """treats warnings as errors""")

    optionParser.add_option('-v', '--verbose',
        action="store_true", dest="verbose", default=False,
        help = """prints additional progress information""")

    options, args = optionParser.parse_args()
    
    options.tabSize = 4;

    if len(args) < 2:
        optionParser.print_help()
        sys.exit(1)
        
    if options.maxTagLines <= 0:
        reporter.reportError('The maximum number of lines to scan for tags must be at least 1.',
                             'invalid-input')
        sys.exit(1)

    if not options.verbose:
        # Disable the verbose reports.
        reporter.disable('verbose')

    # Disable the report-types given by the -d switch.
    for reportType in options.disableSet:
        reporter.disable(reportType)

    # Get the working directory.
    workingDirectory = os.getcwd()

    # Get the input directory.
    # It is given relative to the working directory.
    inputDirectory = os.path.normpath(os.path.join(workingDirectory, args[0]))

    # Get the output directory.
    # It is given relative to the working directory.
    outputDirectory = os.path.normpath(os.path.join(workingDirectory, args[1]))

    # Get the files.
    filesToCopySet = args[2:]

    if options.extensions:
        extensionSet = {}
        for pathName, directorySet, filenameSet in os.walk(inputDirectory):
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

    setGlobalOptions(options)

    return inputDirectory, outputDirectory, filesToCopySet

if __name__ == '__main__':
    reporter = Reporter()
    reporter.openScope('Remark ' + remarkVersion())

    # This is the directory which contains 'remark.py'.
    scriptDirectory = os.path.normpath(sys.path[0])

    # Parse the command-line options.
    inputDirectory, outputDirectory, filesToCopySet = parseArguments(reporter)

    # Do everything.
    errors, warnings = convertDirectory(inputDirectory, outputDirectory, scriptDirectory,
                                        filesToCopySet, reporter)

    # Wrap things up.
    reporter.report(['', "That's all!"], 'verbose')
    reporter.closeScope('Remark ' + remarkVersion())

    if errors > 0 or (warnings > 0 and globalOptions().strict):
        # Indicate the presence of errors by a non-zero error-code.
        sys.exit(1)

