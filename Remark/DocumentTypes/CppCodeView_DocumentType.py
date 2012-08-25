# -*- coding: utf-8 -*-

# Description: CppCodeView document-type

from Convert import saveRemarkToHtml
from DocumentType import DocumentType
from TagParsers.Dictionary_TagParser import Dictionary_TagParser 

class CppCodeView_DocumentType(DocumentType):
    def name(self):
        return 'CppCodeView'

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
        
    def convert(self, document, documentTree, outputRootDirectory):
        remarkText = ['[[ParentList]]',
                '',
                '[[tag file_name]]',
                '===',
                '',
                '[[Parent]]',
                '',
                '[[Link]]: directory.remark-index',
                '',
                '[[-+CppCode]]: [[-Body]]',]

        saveRemarkToHtml(remarkText, document, documentTree, 
                         outputRootDirectory)
         
    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return fileName + '.htm'

    