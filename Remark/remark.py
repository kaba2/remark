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
    
    txtParser = Markdown_TagParser({'parent' : re.compile(r'[ \t]*\[\[Parent\]\]:[ \t]*(.*)')})
    
    docTemplate = \
    ['[[Body]]',
    '[[DocChildren]]',
    '[[SourceChildren]]',]

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
    registerDocumentType('.index', '.htm', indexTemplate, emptyParser)
    registerDocumentType('.orphan', '.htm', orphanTemplate, emptyParser)
    
    # Construct a document tree from the input directory.
    documentTree = DocumentTree(inputDirectory)
    #display(documentTree)

    # We wish to generate an index to each directory in the
    # directory tree.
    
    for directory in documentTree.directorySet:
        relativeName = os.path.join(directory, 'directory.index')
        fullName = os.path.join(documentTree.rootDirectory, relativeName)
        documentTree.insertDocument(Document(relativeName, fullName))
    
    print '\nExpanding macros and writing to files'
    print '-------------------------------------\n'
    
    convertAll(documentTree, outputDirectory)

    print '\nStyle files and AsciiMathML'
    print '---------------------------\n'
    
    # If there are no .css files already in the target directory,
    # copy the default ones there.
    
    remarkDirectory = os.path.join(outputDirectory, 'remark_files');
    
    if not os.path.exists(remarkDirectory):
        os.makedirs(remarkDirectory)
    
    if not os.path.exists(os.path.join(remarkDirectory, 'global.css')):
        print 'Moving global.css...'
        shutil.copy('./remark_files/global.css', remarkDirectory)
                   
    if not os.path.exists(os.path.join(remarkDirectory, 'pygments.css')):
        print 'Moving pygments.css...'
        shutil.copy('./remark_files/pygments.css', remarkDirectory)

    if not os.path.exists(os.path.join(remarkDirectory, 'ASCIIMathMLwFallback.js')):
        print 'Moving ASCIIMathMLwFallback.js...'
        shutil.copy('./remark_files/ASCIIMathMLwFallback.js', remarkDirectory)

    print 'Done.'
    
    print "\nThat's all!"
