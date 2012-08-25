# -*- coding: utf-8 -*-

# Description: CodeView_DocumentType class

import re

from DocumentType import DocumentType
from TagParsers.Dictionary_TagParser import Dictionary_TagParser 

class CodeView_DocumentType(DocumentType):
    def name(self):
        return 'CodeView'

    def linkDescription(self, document):
        return document.fileName

    def parseTags(self, fileName, lines = 100):
        tagMap = {'description' : 'Description',
                  'detail' : 'Detail',
                  'parent' : 'Parent',
                  'parentOf' : 'DocumentationOf',
                  'author' : 'Author'}
        
        parser = Dictionary_TagParser(tagMap, lines)
        return parser.parse(fileName)
        
    def generateMarkdown(self, fileName):
        return ['[[ParentList]]',
                '',
                '[[tag file_name]]',
                '===',
                '',
                '[[Parent]]',
                '',
                '[[Link]]: directory.remark-index',
                '',
                '[[-+Code]]: [[-Body]]',]
         
    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return fileName + '.htm'
