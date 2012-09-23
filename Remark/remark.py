#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Description: Console executable
# Documentation: implementation.txt 

import sys

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
import time

from Document import Document
from DocumentTree import DocumentTree
from Cache import readCache, createCache

from Conversion import convertAll
from FileSystem import unixDirectoryName, unixRelativePath, readFile, writeFile
from FileSystem import documentType, associateDocumentType, remarkVersion, fileExtension
from FileSystem import asciiMathMlName, copyIfNecessary, setGlobalOptions, globalOptions
from FileSystem import setDefaultDocumentType, strictDocumentType, splitPath, pathExists
from FileSystem import globToRegex

from Reporting import Reporter, ScopeGuard

from time import clock

from Macros import *

if os.name == 'nt':
    # Apply the bug-fix for the os.path.split() to
    # support UNC-paths (bug present in Python 2.7.3).
    os.path.split = splitPath

def initializeRemark():
    '''
    Associates filename extensions with document types.
    '''
    
    from DocumentTypes.CppCodeView_DocumentType import CppCodeView_DocumentType
    from DocumentTypes.CodeView_DocumentType import CodeView_DocumentType
    from DocumentTypes.RemarkPage_DocumentType import RemarkPage_DocumentType
    from DocumentTypes.DirectoryView_DocumentType import DirectoryView_DocumentType
    from DocumentTypes.Orphan_DocumentType import Orphan_DocumentType
    from DocumentTypes.Copy_DocumentType import Copy_DocumentType

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

def createDocumentTree(inputDirectory, filesToCopySet, reporter):
    '''
    Inserts all matching files in the document tree root
    directory into the document tree.
    
    documentTree (DocumentTree):
    The document tree to insert the matching files into.

    filesToCopySet (iterable of glob strings):
    A set of glob strings each defining a set of acceptable 
    filenames.

    returns (DocumentTree):
    The document tree.
    '''

    # Construct an empty document-tree for the input directory.
    documentTree = DocumentTree(inputDirectory, reporter)

    filenameRegexString = globToRegex(filesToCopySet)
    filenameRegex = re.compile(filenameRegexString)
            
    for pathName, directorySet, fileNameSet in os.walk(documentTree.rootDirectory):
        for filename in fileNameSet:
            fullName = os.path.normpath(os.path.join(pathName, filename))
            relativeName = unixRelativePath(inputDirectory, fullName)
            if re.match(filenameRegex, filename) != None:
                # The file matches a pattern, take it in.
                documentTree.insertDocument(relativeName)

    # Generate a directory.remark-index virtual document to each
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

    return documentTree

def resolveRegeneration(documentTree, cacheDocumentTree):
    # Link changes due to removal of a document
    # -----------------------------------------

    # Find out which documents have been deleted.
    for cacheDocument in cacheDocumentTree:
        if cacheDocument.document != None:
            continue
        
        # The document can be found from the cache, 
        # but not from the current document-tree.
        # Therefore the document has been deleted.

        # Regenerate those documents which used to refer
        # to this document.
        for document in cacheDocument.incomingSet:
            # Link changes due to removal of a document
            # -----------------------------------------
            document.setRegenerate(True)

    # Find out which documents to regenerate.
    for document in documentTree:
        # Retrieve the corresponding cached document.
        cacheDocument = cacheDocumentTree.cacheDocument(document)
        if cacheDocument == None:
            # Document has been created
            # -------------------------
            # If the document can be found from the current
            # document tree, but can not be found from the
            # cache, then it was just created.
            document.setRegenerate(True)
            continue
           
        if not document.documentType.upToDate(document, documentTree, outputDirectory):
            # Document has been modified
            # --------------------------
            document.setRegenerate(True)
            continue

        for linkDocument in cacheDocument.outgoingSet:
            # A document is said to be modified if it is not up-to-date,
            # or is not found from the document-tree cache.
            if ((not (linkDocument.documentType.upToDate(linkDocument, documentTree, outputDirectory) and
                    linkDocument in cacheDocumentTree)) and
                    linkDocument.documentType.updateDependent()):
                # Linked-to document has been modified
                # ------------------------------------
                document.setRegenerate(True)
                break

    # Update the non-regenerated documents from the cache.        
    for document in documentTree:
        regenerate = globalOptions().regenerate or document.regenerate()
        if not regenerate:
            cacheDocument = cacheDocumentTree.cacheDocument(document)
            if cacheDocument != None:
                document.dependencySet.update(cacheDocument.dependencySet)

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
        help = """disables a specific warning (e.g. -dinvalid-input)""",
        metavar = 'WARNING')

    optionParser.add_option('-e', '--extensions',
        action="store_true", dest="extensions", default=False,
        help = """lists all file-extensions in the input-directory along with example files""")

    optionParser.add_option('-l', '--lines',
        dest = 'maxTagLines',
        type = 'int',
        default = 100,
        help = """sets maximum number of lines for a tag-parser to scan a file for tags (default 100)""",
        metavar = 'LINES')

    optionParser.add_option('-m', '--max-file-size',
        dest = 'maxFileSize',
        type = 'int',
        default = 2**18,
        help = """sets maximum file-size to load (in bytes, default 262144)""",
        metavar = 'SIZE')

    optionParser.add_option('-r', '--regenerate',
        action="store_true", dest="regenerate", default=False,
        help = """regenerates all files""")

    optionParser.add_option('-s', '--strict',
        action="store_true", dest="strict", default=False,
        help = """treats warnings as errors""")

    optionParser.add_option('-v', '--verbose',
        action="store_true", dest="verbose", default=False,
        help = """prints additional progress information""")

    options, args = optionParser.parse_args()
    
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

    # Get the input directory.
    inputDirectory = os.path.normpath(os.path.join(os.getcwd(), args[0]))

    # Get the output directory.
    outputDirectory = os.path.normpath(os.path.join(os.getcwd(), args[1]))

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

    if not pathExists(inputDirectory):
        reporter.reportError('Input directory ' + inputDirectory + ' does not exist.',
                             'invalid-input')
        sys.exit(1)

    setGlobalOptions(options)

    return inputDirectory, outputDirectory, filesToCopySet

if __name__ == '__main__':

    startTime = time.clock()

    reporter = Reporter()
    reporter.openScope('Remark ' + remarkVersion())

    # Parse the command-line options.
    inputDirectory, outputDirectory, filesToCopySet = parseArguments(reporter)

    # Create associations to document types.
    initializeRemark()
    
    # This is the directory which contains 'remark.py'.
    scriptDirectory = sys.path[0]

    reporter.report(['',
                     'Input directory: ' + inputDirectory,
                     'Output directory: ' + outputDirectory], 
                    'verbose')

    # Create the document tree.
    documentTree = createDocumentTree(inputDirectory, filesToCopySet, reporter)

    # Note that these files are copied _after_ gathering the files
    # and directories. This is to avoid gathering these files
    # in case the input directory is the same as the output directory.
    # It is also important that these files are copied as early as
    # possible, since we want to see the changes in the .css files
    # as early as possible.
    copyIfNecessary('./remark_files/remark.css', scriptDirectory, 
                    './remark_files/remark.css', outputDirectory)
    copyIfNecessary('./remark_files/pygments.css', scriptDirectory, 
                    './remark_files/pygments.css', outputDirectory)
    copyIfNecessary('./remark_files/' + asciiMathMlName(), scriptDirectory, 
                    './remark_files/' + asciiMathMlName(), outputDirectory)

    #with ScopeGuard(reporter, 'Reading document-tree cache')

    if not globalOptions().regenerate:
        cacheRelativeName = './remark_files/document-tree.xml'
        cacheFullName = os.path.join(outputDirectory, cacheRelativeName)
        cacheDocumentTree = readCache(cacheFullName, documentTree)

    #reporter.report(['', 'Done.'], 'verbose')

    # Parse the tags.
    with ScopeGuard(reporter, 'Parsing tags'):
        for document in documentTree:
            try:
                type = document.documentType

                if not globalOptions().regenerate:
                    # If the document is up-to-date, and it can be found from
                    # the cache, then use the cached tags instead.
                    if (type.upToDate(document, documentTree, outputDirectory) and
                        document in cacheDocumentTree):
                        cacheDocument = cacheDocumentTree.cacheDocument(document)
                        #print cacheDocument.tagSet
                        document.tagSet.update(cacheDocument.tagSet)
                        continue

                # Otherwise parse the tags.
                with ScopeGuard(reporter, document.relativeName):
                    tagSet = type.parseTags(documentTree.fullName(document), reporter)

                document.tagSet.update(tagSet)
                document.setTag('link_description', [type.linkDescription(document)])
                
                #print
                #print document.relativeName + ':'
                #for tagName, tagText in tagSet.iteritems():
                #    print tagName, ':', tagText

            except UnicodeDecodeError:
                reporter.reportWarning(document.relativeName + 
                                       ': Tag parsing failed because of a unicode decode error.')

        reporter.report(['', 'Done.'], 'verbose')

    # Resolve parent links.
    documentTree.resolveParentLinks()

    if not globalOptions().regenerate:
        resolveRegeneration(documentTree, cacheDocumentTree)

    # Generate documents.
    with ScopeGuard(reporter, 'Generating documents'):
        convertAll(documentTree, outputDirectory, reporter)
        reporter.report(['', 'Done.'], 'verbose')

    if not globalOptions().regenerate:
        # Save the document-tree as xml.
        writeFile(createCache(documentTree), cacheFullName)

    # Find out statistics.
    seconds = round(time.clock() - startTime, 2)
    errors = reporter.errors()
    warnings = reporter.warnings()

    # Report the statistics.
    with ScopeGuard(reporter, 'Summary'):
        reporter.report(['',
                         str(seconds) + ' seconds,',
                         str(errors) + ' errors,',
                         str(warnings) + ' warnings.'], 
                        'summary')

    # Wrap things up.
    reporter.report(['', "That's all!"], 'verbose')
    reporter.closeScope('Remark ' + remarkVersion())

    if errors > 0 or (warnings > 0 and globalOptions().strict):
        # Indicate the presence of errors by a non-zero error-code.
        sys.exit(1)

