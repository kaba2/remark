#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Description: Console executable
# Documentation: implementation.txt 

'''
Remark documentation system
Started on 16.11.2009
@author: Kalle Rutanen
'''

import re
import sys
import os
import shutil

from DocumentTree import Document
from DocumentTree import DocumentTree
from TagParsers.Generic_TagParser import Generic_TagParser
from TagParsers.Markdown_TagParser import Markdown_TagParser
from TagParsers.Empty_TagParser import Empty_TagParser
from Convert import convertAll
from Common import registerDocumentType

from Macros import *

def commentParserTags(comment):
    return {'description' : re.compile(r'[ \t]*' + comment + '[ \t]*Description[ \t]*:[ \t]*(.*)'),
            'detail' : re.compile(r'[ \t]*' + comment + '[ \t]*Detail[ \t]*:[ \t]*(.*)'),
            'parent' : re.compile(r'[ \t]*' + comment + '[ \t]*Documentation[ \t]*:[ \t]*(.*)')}

if __name__ == '__main__':
    print 'Remark documentation system'
    print '===========================\n'

    if len(sys.argv) != 3:
        print 'Usage:'
        print 'remark.py inputDirectory outputDirectory'
        sys.exit(1)
    
    inputDirectory = sys.argv[1]
    outputDirectory = sys.argv[2]
    
    inputDirectory = os.path.normpath(os.path.join(os.getcwd(), inputDirectory))
    outputDirectory = os.path.normpath(os.path.join(os.getcwd(), outputDirectory))
    
    if not os.path.exists(inputDirectory):
        print 'Error: Input directory \'' + inputDirectory + '\' does not exist.'
        sys.exit(1)

    print 'Input directory:', inputDirectory
    print 'Output directory:', outputDirectory

    cppParser = Generic_TagParser(commentParserTags('//'))
    matlabParser = Generic_TagParser(commentParserTags('%'))
    pythonParser = Generic_TagParser(commentParserTags('#'))
    emptyParser = Empty_TagParser()
    
    txtParser = Markdown_TagParser({'parent' : re.compile(r'\[\[Parent\]\]:[ \t]*(.*)')})
    
    docTemplate = \
    ['[[Body]]',
    '[[DocChildren]]',
    '[[get mid_text]]',
    '[[SourceChildren]]',
    '[[get end_text]]',]

    cppTemplate = \
    ['[[CppCode]]',]
    
    genericCodeTemplate = \
    ['[[GenericCode]]',]

    indexTemplate = \
    ['[[Index]]',]
    
    orphanTemplate = \
    ['Orphans',
    '=======',
    '[[DocChildren]]',
    '[[SourceChildren]]',]
    
    registerDocumentType('.txt', '.htm', docTemplate, txtParser)
    registerDocumentType('.cpp', '.cpp.htm', cppTemplate, cppParser)
    registerDocumentType('.cc', '.cc.htm', cppTemplate, cppParser)
    registerDocumentType('.c', '.c.htm', cppTemplate, cppParser)
    registerDocumentType('.h', '.h.htm', cppTemplate, cppParser)
    registerDocumentType('.hh', '.hh.htm', cppTemplate, cppParser)
    registerDocumentType('.hpp', '.hpp.htm', cppTemplate, cppParser)
    registerDocumentType('.py', '.py.htm', genericCodeTemplate, pythonParser)
    registerDocumentType('.m', '.m.htm', genericCodeTemplate, matlabParser)
    
    # Construct a document tree from the input directory.
    documentTree = DocumentTree(inputDirectory)
    #display(documentTree)

    # We wish to generate an index to each directory in the
    # directory tree.
    
    for directory in documentTree.directorySet:
        relativeName = os.path.join(directory, 'directory.index')
        fullName = os.path.join(documentTree.rootDirectory, relativeName)
        documentTree.insertDocument(Document(relativeName, fullName))
    
    registerDocumentType('.index', '.htm', indexTemplate, emptyParser)
    registerDocumentType('.orphan', '.htm', orphanTemplate, emptyParser)

    print '\nGenerating documents'
    print '--------------------\n'
    
    convertAll(documentTree, outputDirectory)

    # Those files which don't have an associated document type
    # are simply copied.
   
    print '\nMoving files with no associated document type'
    print '---------------------------------------------\n'

    otherFileSet = documentTree.otherFileSet
    
    for relativeName in otherFileSet:
        targetName = os.path.join(outputDirectory, relativeName);
        targetDirectory = os.path.split(targetName)[0]
        if not os.path.exists(targetDirectory):
            os.makedirs(targetDirectory)
        if not os.path.exists(targetName):
            print relativeName
            sourceName = os.path.join(inputDirectory, relativeName)
            shutil.copy(sourceName, targetDirectory)
                   
    print 'Done.'

    # If there are no .css files already in the target directory,
    # copy the default ones there.

    print '\nMoving style files and AsciiMathML'
    print '----------------------------------\n'

    remarkDirectory = os.path.join(outputDirectory, 'remark_files')
    if not os.path.exists(remarkDirectory):
        os.makedirs(remarkDirectory)

    if not os.path.exists(os.path.join(remarkDirectory, 'remark.css')):
        print 'remark.css'
        shutil.copy('./remark_files/remark.css', remarkDirectory)

    if not os.path.exists(os.path.join(remarkDirectory, 'pygments.css')):
        print 'pygments.css'
        shutil.copy('./remark_files/pygments.css', remarkDirectory)

    if not os.path.exists(os.path.join(remarkDirectory, 'ASCIIMathMLwFallback.js')):
        print 'ASCIIMathMLwFallback.js'
        shutil.copy('./remark_files/ASCIIMathMLwFallback.js', remarkDirectory)

    print 'Done.'
    
    print "\nThat's all!"
