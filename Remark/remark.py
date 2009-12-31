#! /usr/bin/env python

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

from Remark.DocumentTree import Document
from Remark.DocumentTree import DocumentTree
from Remark.TagParsers.Generic_TagParser import Generic_TagParser
from Remark.TagParsers.Markdown_TagParser import Markdown_TagParser
from Remark.Convert import convertAll
from Remark.Common import registerOutputDocumentName

from Remark.Macros import *

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
    emptyParser = Generic_TagParser({})
    
    txtParser = Markdown_TagParser({'parent' : re.compile(r'[ \t]*\[\[Parent\]\]:[ \t]*(.*)')})
    
    parserMap = {'.txt' : txtParser,
                 '.c' : cppParser,
                 '.cc' : cppParser,
                 '.cpp' : cppParser,
                 '.h'  : cppParser,
                 '.hh'  : cppParser,
                 '.hpp' : cppParser,
                 '.py' : pythonParser,
                 '.m' : matlabParser,}
    
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
    
    registerOutputDocumentName('.txt', '.htm')
    registerOutputDocumentName('.cpp', '.cpp.htm')
    registerOutputDocumentName('.cc', '.cc.htm')
    registerOutputDocumentName('.c', '.c.htm')
    registerOutputDocumentName('.h', '.h.htm')
    registerOutputDocumentName('.hh', '.hh.htm')
    registerOutputDocumentName('.hpp', '.hpp.htm')
    registerOutputDocumentName('.py', '.py.htm')
    registerOutputDocumentName('.m', '.m.htm')
    registerOutputDocumentName('.index', '.htm')
    registerOutputDocumentName('.orphan', '.htm')
    
    templateMap = {'.txt' : docTemplate,   
                   '.cpp' : cppTemplate,
                   '.cc' : cppTemplate,
                   '.c' : cppTemplate,
                   '.h' : cppTemplate,
                   '.hh' : cppTemplate,
                   '.hpp' : cppTemplate,
                   '.py' : genericCodeTemplate,
                   '.m' : genericCodeTemplate,
                   '.index' : indexTemplate,
                   '.orphan' : orphanTemplate,}

    #print '\nConstructing document tree'
    #print '--------------------------\n'
    
    # Construct a document tree from the input directory.
    documentTree = DocumentTree(inputDirectory, parserMap)
    #display(documentTree)

    # We wish to generate an index to each directory in the
    # directory tree.
    
    for directory in documentTree.directorySet:
        relativeName = os.path.join(directory, 'directory.index')
        fullName = os.path.join(documentTree.rootDirectory, relativeName)
        documentTree.insertDocument(Document(relativeName, fullName))
    
    print '\nExpanding macros and writing to files'
    print '-------------------------------------\n'
    
    convertAll(documentTree, outputDirectory, templateMap)
                   
    print 'Done.'
    
    print "\nThat's all!"
