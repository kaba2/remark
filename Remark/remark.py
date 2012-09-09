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

from Document import Document
from DocumentTree import DocumentTree
from Cache import readCache, createCache

from DocumentTypes.CppCodeView_DocumentType import CppCodeView_DocumentType
from DocumentTypes.CodeView_DocumentType import CodeView_DocumentType
from DocumentTypes.RemarkPage_DocumentType import RemarkPage_DocumentType
from DocumentTypes.DirectoryView_DocumentType import DirectoryView_DocumentType
from DocumentTypes.Orphan_DocumentType import Orphan_DocumentType
from DocumentTypes.Copy_DocumentType import Copy_DocumentType

from TransitiveClosure import transitiveClosure

from Conversion import convertAll
from FileSystem import unixDirectoryName, unixRelativePath, readFile, writeFile
from FileSystem import documentType, associateDocumentType, remarkVersion, fileExtension
from FileSystem import asciiMathMlName, copyIfNecessary, setGlobalOptions, globalOptions
from FileSystem import setDefaultDocumentType, strictDocumentType, splitPath, pathExists
from optparse import OptionParser

from Reporting import Reporter

from time import clock

from Macros import *

from TransitiveClosure import testTransitiveClosure

if os.name == 'nt':
    # Apply the bug-fix for the os.path.split() to
    # support UNC-paths (bug present in Python 2.7.3).
    os.path.split = splitPath

if __name__ == '__main__':

    optionParser = OptionParser(usage = """\
%prog [options] inputDirectory outputDirectory [filesToCopy...]

The filesToCopy-list contains a list of those files which
should be copied if they are not converted. This list can 
use wildcards (e.g. *.png).""")
    
    optionParser.add_option('-l', '--lines',
        dest = 'maxTagLines',
        type = 'int',
        default = 100,
        help = """maximum number of lines for a tag-parser to scan a file for tags (default 100)""")

    optionParser.add_option('-v', '--verbose',
        action="store_true", dest="verbose", default=False,
        help = """whether to print additional progress information.""")

    optionParser.add_option('-s', '--strict',
        action="store_true", dest="strict", default=False,
        help = """whether to treat warnings as errors (returns a non-zero error-code).""")

    optionParser.add_option('-i', '--incremental',
        action="store_false", dest="regenerate", default=True,
        help = """whether to skip generating files if the cache
shows they have not been changed.""")

    optionParser.add_option('-m', '--max-file-size',
        dest = 'maxFileSize',
        type = 'int',
        default = 2**18,
        help = """maximum file size to load (default 262144 bytes)""")

    options, args = optionParser.parse_args()
    
    if len(args) < 2:
        optionParser.print_help()
        sys.exit(1)
        
    reporter = Reporter()

    if options.maxTagLines <= 0:
        reporter.reportError('The maximum number of lines to scan for tags must be at least 1.',
                             'invalid-input')
        sys.exit(1)

    setGlobalOptions(options)
    
    reporter.openScope('Remark')
    
    startTime = time.clock()
    
    inputDirectory = args[0]
    outputDirectory = args[1]
    filesToCopySet = args[2:]
    
    inputDirectory = os.path.normpath(os.path.join(os.getcwd(), inputDirectory))
    outputDirectory = os.path.normpath(os.path.join(os.getcwd(), outputDirectory))
    
    if not pathExists(inputDirectory):
        reporter.reportError('Input directory ' + inputDirectory + ' does not exist.',
                             'invalid-input')
        sys.exit(1)

    reporter.report(['Input directory: ' + inputDirectory,
                     'Output directory: ' + outputDirectory], 
                    'verbose')

    # Associate document types with filename extensions.
    
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
    
    # If there are no .css files already in the target directory,
    # copy the default ones there. Note that it is important that
    # these files are moved before generating the documents.
    # This is because one wants to see changes in a style file
    # as early as possible.

    # This is the directory which contains 'remark.py'.
    scriptDirectory = sys.path[0]
    
    copyIfNecessary('./remark_files/remark.css', scriptDirectory, 
                    './remark_files/remark.css', outputDirectory)
    copyIfNecessary('./remark_files/pygments.css', scriptDirectory, 
                    './remark_files/pygments.css', outputDirectory)
    copyIfNecessary('./remark_files/' + asciiMathMlName(), scriptDirectory, 
                    './remark_files/' + asciiMathMlName(), outputDirectory)

    # Construct an empty document-tree from the input directory.
    documentTree = DocumentTree(inputDirectory)

    # Recursively gather files starting from the input directory.
    reporter.openScope('Gathering files')

    for pathName, directorySet, fileNameSet in os.walk(inputDirectory):
        for fileName in fileNameSet:
            fullName = os.path.normpath(os.path.join(pathName, fileName))
            relativeName = unixRelativePath(inputDirectory, fullName)
            if strictDocumentType(fileExtension(fileName)) != None:
                # The file has an associated document type, take it in.            
                documentTree.insertDocument(relativeName)
            else: 
                for filenamePattern in filesToCopySet:
                    if fnmatch.fnmatch(fileName, filenamePattern):
                        # The file matches a pattern for copying,
                        # take it in.
                        documentTree.insertDocument(relativeName)
                        break

    reporter.report(['', 'Done.'], 'verbose')
    reporter.closeScope('Gathering files')


    # Insert virtual documents.

    reporter.openScope('Inserting virtual documents')

    # Generates a directory.remark-index virtual document to each
    # directory. This provides the directory listings.
    for directory in documentTree.directorySet:
        # Form the relative name of the document.
        relativeName = os.path.join(directory, 'directory.remark-index')
            
        # Insert a document with that relative name.
        document = documentTree.insertDocument(relativeName)
            
        # Give the document the description from the unix-style
        # directory name combined with a '/' to differentiate 
        # visually that it is a directory.
        description = unixDirectoryName(document.relativeDirectory) + '/'

        # Add the description to the document.
        document.setTag('description', [description])

    reporter.report(['', 'Done.'], 'verbose')
    reporter.closeScope('Inserting virtual documents')

    reporter.openScope('Reading document-tree cache')

    cacheRelativeName = './remark_files/document-tree.xml'
    cacheFullName = os.path.join(outputDirectory, cacheRelativeName)
    cacheDocumentTree = readCache(cacheFullName, documentTree)

    reporter.report(['', 'Done.'], 'verbose')
    reporter.closeScope('Reading document-tree cache')

    # Parse the tags.
    reporter.openScope('Parsing tags')

    for document in documentTree:
        try:
            type = document.documentType

            # If the document is up-to-date, and it can be found from
            # the cache, then use the cached tags instead.
            if (type.upToDate(document, documentTree, outputDirectory) and
                document in cacheDocumentTree):
                cacheDocument = cacheDocumentTree.cacheDocument(document)
                #print cacheDocument.tagSet
                document.tagSet.update(cacheDocument.tagSet)
                continue

            # Otherwise parse the tags.
            if globalOptions().verbose:
                print 'Parsing tags for', document.relativeName, '...'
            tagSet = type.parseTags(documentTree.fullName(document))
            document.tagSet.update(tagSet)
            document.setTag('link_description', [type.linkDescription(document)])
                
            #print
            #print document.relativeName + ':'
            #for tagName, tagText in tagSet.iteritems():
            #    print tagName, ':', tagText

        except UnicodeDecodeError:
            reporter.reportWarning(document.relativeName + 
                                   ': Tag parsing failed because of a unicode decode error.')

    reporter.report(['', 'Done'], 'verbose')
    reporter.closeScope('Parsing tags')

    # Resolve parent links.
    documentTree.resolveParentLinks()

    def forEachDomain(visit):
        for document in documentTree:
            visit(document)

    def forEachRelated(document, visit):
        cacheDocument = cacheDocumentTree.cacheDocument(document)
        if cacheDocument == None:
            return
        
        for linkDocument in cacheDocument.outgoingSet:
            #if linkDocument.extension == '.remark-orphan':
                #print 'Links to orphan:', document.relativeName
            visit(linkDocument)

    def codomainOperator(left, right):
        #left.update(right)
        #return left
        return left or right

    def function(document):
        #return set([document])

        regenerate = not (document.documentType.upToDate(document, documentTree, outputDirectory) and
                    document in cacheDocumentTree)

        #if regenerate:
        #    print 'Regenerate:', document.relativeName

        return regenerate

    def report(document, regenerate):
        #if document.relativeName == 'remark.txt':
        #    print
        #    print document.relativeName
        #    for toDocument in documentSet:
        #        print toDocument.relativeName
        document.setRegenerate(regenerate)

    identity = False
    #identity = set()
    transitiveClosure(identity, forEachDomain, forEachRelated, function,
                      codomainOperator, report, True)

    #sys.exit(1)

    #for document in documentTree:
    #    #print document.regenerate(), 
    #    print document.documentType.upToDate(document, documentTree, outputDirectory),
    #    print document in cacheDocumentTree, 
    #    print document.regenerate(),
    #    print document.relativeName

    #sys.exit(1)

    for document in documentTree:
        regenerate = globalOptions().regenerate or document.regenerate()
        if not regenerate:
            cacheDocument = cacheDocumentTree.cacheDocument(document)
            if cacheDocument != None:
                #print cacheDocument.incomingSet
                document.incomingSet.update(cacheDocument.incomingSet)
                document.outgoingSet.update(cacheDocument.outgoingSet)

    reporter.openScope('Generating documents')
    
    convertAll(documentTree, outputDirectory, reporter)

    reporter.report(['', 'Done'], 'verbose')
    reporter.closeScope('Generating documents')

    # Save the document-tree as xml.
    writeFile(createCache(documentTree), cacheFullName)

    # Output the time taken to produce the documentation.
    endTime = time.clock()

    reporter.report(str(round(endTime, 2)) + ' seconds.', 'verbose')
    reporter.report(str(reporter.errors()) + ' errors.', 'verbose')
    reporter.report(str(reporter.warnings()) + ' warnings.', 'verbose')
    reporter.report(['', "That's all!"], 'verbose')
    reporter.closeScope('Remark')

