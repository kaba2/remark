#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Description: Console executable
# Documentation: implementation.txt 

import sys
import time

try:
    import markdown
except ImportError, e:
    print 'Error: Python Markdown library missing. Please install it first.'
    sys.exit(1)

try: 
    import pygments
except ImportError, e:
    print 'Error: Pygments library missing. Please install it first.'
    sys.exit(1)

import re
import os
import shutil
import fnmatch

from DocumentTree import Document
from DocumentTree import DocumentTree

from DocumentTypes.CppCodeView_DocumentType import CppCodeView_DocumentType
from DocumentTypes.GenericCodeView_DocumentType import GenericCodeView_DocumentType
from DocumentTypes.RemarkPage_DocumentType import RemarkPage_DocumentType
from DocumentTypes.DirectoryView_DocumentType import DirectoryView_DocumentType
from DocumentTypes.Orphan_DocumentType import Orphan_DocumentType

from TagParsers.Generic_TagParser import Generic_TagParser
from TagParsers.Markdown_TagParser import Markdown_TagParser
from TagParsers.Empty_TagParser import Empty_TagParser

from Convert import convertAll
from Common import unixDirectoryName, linkAddress, readFile
from Common import documentType, associateDocumentType, remarkVersion
from Common import asciiMathMlName, copyIfNecessary, setGlobalOptions, globalOptions
from optparse import OptionParser

from time import clock

from Macros import *

if __name__ == '__main__':
    
    optionParser = OptionParser(usage = """\
%prog [options] inputDirectory outputDirectory [filesToCopy...]

The filesToCopy-list contains a list of those files which
should be copied if they are not converted. This list can 
use wildcards (e.g. *.png).""")
    
    optionParser.add_option('-l', '--lines',
        dest = 'lines',
        type = 'int',
        default = 100,
        help = """maximum number of lines for a tag-parser to scan a file for tags (default 100)""")

    optionParser.add_option('-v', '--verbose',
        action="store_true", dest="verbose", default=False,
        help = """whether to print additional progress information""")

    optionParser.add_option('-m', '--max-file-size',
        dest = 'maxFileSize',
        type = 'int',
        default = 2**18,
        help = """maximum file size to load (default 262144 bytes)""")

    optionParser.add_option('-p', '--prologue',
        dest = 'prologueFileName',
        type = 'string',
        default = '',
        help = """file written in Remark syntax which should be merged to the beginning of each document template""")

    options, args = optionParser.parse_args()
    
    if len(args) < 2:
        optionParser.print_help()
        sys.exit(1)
        
    if options.lines <= 0:
        print 'Error: The maximum number of lines to scan for tags must be at least 1.'
        sys.exit(1)

    setGlobalOptions(options)
    
    # Possibly load the prologue file.

    prologueFileName = options.prologueFileName
    prologue = []
    if prologueFileName != '':
        try:
            prologue = readFile(prologueFileName)
        except IOError:
            print 'Error: The prologue file', prologueFileName, 'could not be read.'
            sys.exit(1)

    title = 'Remark ' + remarkVersion()

    print
    print title
    for i in range(0, len(title)):
        sys.stdout.write('=')
    print
    print

    startTime = time.clock()
    
    inputDirectory = args[0]
    outputDirectory = args[1]
    filesToCopySet = args[2:]
    
    inputDirectory = os.path.normpath(os.path.join(os.getcwd(), inputDirectory))
    outputDirectory = os.path.normpath(os.path.join(os.getcwd(), outputDirectory))
    
    if not os.path.exists(inputDirectory):
        print 'Error: Input directory \'' + inputDirectory + '\' does not exist.'
        sys.exit(1)

    print 'Input directory:', inputDirectory
    print 'Output directory:', outputDirectory

    # Associate document types with filename extensions.
    
    remarkPageType = RemarkPage_DocumentType()
    cppCodeViewType = CppCodeView_DocumentType()
    genericCodeViewType= GenericCodeView_DocumentType()
    directoryViewType = DirectoryView_DocumentType()
    orphanType = Orphan_DocumentType()
       
    associateDocumentType('.txt', remarkPageType)
    associateDocumentType('.cpp', cppCodeViewType)
    associateDocumentType('.cc', cppCodeViewType)
    associateDocumentType('.c', cppCodeViewType)
    associateDocumentType('.h', cppCodeViewType)
    associateDocumentType('.hh', cppCodeViewType)
    associateDocumentType('.hpp', cppCodeViewType)
    associateDocumentType('.py', genericCodeViewType)
    associateDocumentType('.m', genericCodeViewType)
    associateDocumentType('.index', directoryViewType)
    associateDocumentType('.orphan', orphanType)
    
    # Construct a document tree from the input directory.
    documentTree = DocumentTree(inputDirectory, options.lines)
    #display(documentTree)

    # Recursively gather files starting from the input directory.
    if globalOptions().verbose:
        print
        print 'Gathering files...',

    for pathName, directorySet, fileNameSet in os.walk(inputDirectory):
        for fileName in fileNameSet:
            fullName = os.path.normpath(os.path.join(pathName, fileName))
            relativeName = linkAddress(inputDirectory, fullName)
            if documentType(os.path.splitext(fileName)[1]) != None:
                # The file has an associated document type,
                # take it in.            
                documentTree.insertDocument(relativeName)
            else: 
                for filenamePattern in filesToCopySet:
                    if fnmatch.fnmatch(fileName, filenamePattern):
                        # The file matches a pattern for copying,
                        # take it in.
                        documentTree.insertDocument(relativeName)
                        break

    if globalOptions().verbose:
        print 'Done.'

    documentTree.compute()

    if globalOptions().verbose:
        print
        print 'Generating documents'
        print '--------------------'
        print
    
    convertAll(documentTree, inputDirectory, outputDirectory, prologue)

    # If there are no .css files already in the target directory,
    # copy the default ones there.

    if globalOptions().verbose:
        print 
        print 'Moving style files and AsciiMathML'
        print '----------------------------------'
        print

    # This is the directory which contains 'remark.py'.
    scriptDirectory = sys.path[0]
    
    copyIfNecessary('./remark_files/remark.css', scriptDirectory, 
                    './remark_files/remark.css', outputDirectory)
    copyIfNecessary('./remark_files/pygments.css', scriptDirectory, 
                    './remark_files/pygments.css', outputDirectory)
    copyIfNecessary('./remark_files/' + asciiMathMlName(), scriptDirectory, 
                    './remark_files/' + asciiMathMlName(), outputDirectory)

    if globalOptions().verbose:
        print 'Done.'

    # Output the time taken to produce the documentation.
    endTime = time.clock()
    print
    print str(round(endTime, 2)) + ' seconds.'
    
    if globalOptions().verbose:
        print
        print "That's all!"

