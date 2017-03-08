# -*- coding: utf-8 -*-

# Description: Command-line argument parsing
# Documentation: command_line.txt

from __future__ import print_function
from Remark.Version import remarkVersion

import sys
import os
import optparse

from Remark.FileSystem import (
    fileExists, 
    unixDirectoryName, 
    readFile,
    fileExtension)

def constructOptionParser():
    optionParser = optparse.OptionParser(usage = """\
%prog inputDirectory outputDirectory (option|file-glob)*

Note: On Unix-based operating systems a glob must be placed in 
double quotes to prevent glob-expansion from taking place before
reaching Remark; write "*.txt" instead of *.txt.""")
    
    optionParser.add_option('-b', '--bug',
        action="store_true", dest="debug", default=False,
        help = """enables debug-reporting.""")

    optionParser.add_option('-c', '--config',
        dest = 'configFileSet',
        type = 'string',
        action = 'append',
        default = ['remark_config.json'],
        help = """reads a JSON configuration file (if it exists).
If the file path is relative, it is relative to the input directory.
The file `remark_config.json` is always included as a config-file, 
if it exists.""",
        metavar = 'FILEPATH')

    optionParser.add_option('-d', '--disable',
        dest = 'disableSet',
        type = 'string',
        action = 'append',
        default = [],
        help = """disables a specific warning (e.g. -d invalid-input).""",
        metavar = 'WARNING')

    optionParser.add_option('-e', '--extensions',
        action = "store_true", 
        dest = "extensions", 
        default = False,
        help = """lists all extensions in the input directory together with examples.""")

    optionParser.add_option('-g', '--generate-markdown',
        action = 'store_true',
        dest = 'generateMarkdown',
        default = False,
        help = """generates the Markdown source for each file. This is useful for debugging Remark.""")

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
        default = -1,
        help = """sets maximum file-size to load (in bytes, default -1 to ignore).""",
        metavar = 'SIZE')

    optionParser.add_option('-o', '--options',
        dest = 'optionFileSet',
        type = 'string',
        action = 'append',
        default = ['remark_options'],
        help = """reads command-line options from an option-file (if it exists).
An option-file is a plain-text file, with one option per line.
If the file path is relative, it is relative to the input directory.
The file `remark_options` is always included as an option-file, 
if it exists.""",
        metavar = 'FILEPATH')

    optionParser.add_option('-q', '--quick',
        action="store_true", dest="quick", default=False,
        help = """regenerates only modified documents and their parents. Note: only use for quick previews of edits; this process leaves many documents out-of-date. """)

    optionParser.add_option('-r', '--version',
        action="store_true", dest="version", default=False,
        help = """prints the version number.""")

    optionParser.add_option('-s', '--strict',
        action="store_true", dest="strict", default=False,
        help = """treats warnings as errors.""")

    optionParser.add_option('-u', '--unknowns',
        action="store_true", dest="unknowns", default=False,
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

    return optionParser

def parseArguments(argumentSet, args, reporter):
    '''
    Parses the command-line arguments given to Remark.
    '''

    # Positional arguments
    # --------------------
        
    # Get the working directory.
    workingDirectory = os.getcwd()

    if len(args) >= 1:
        # Get the input directory.
        # It is given relative to the working directory.
        argumentSet.inputDirectory = (
            os.path.normpath(os.path.join(workingDirectory, args[0])))
    else:
        argumentSet.inputDirectory = None

    if len(args) >= 2:
        # Get the output directory.
        # It is given relative to the working directory.
        argumentSet.outputDirectory = (
            os.path.normpath(os.path.join(workingDirectory, args[1])))
    else:
        argumentSet.outputDirectory = None

    # This is the directory which contains 'remark.py'.
    argumentSet.scriptDirectory = os.path.normpath(sys.path[0])

    # Interpret the rest of the positional arguments
    # as including files, i.e. the same
    # as the -i option.
    argumentSet.includeSet += args[2:]

    if not argumentSet.inputDirectory:
        # Option-files are relative to the input-directory.
        # Since input-directory was not given, we cannot
        # read option-files either.
        return argumentSet

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
                optionText = readFile(optionFilePath, maxOptionFileSize)
                # Parse the new command-line arguments.
                argumentSet, args = optionParser.parse_args(optionText, argumentSet)
                argumentSet.includeSet += args

    return argumentSet
