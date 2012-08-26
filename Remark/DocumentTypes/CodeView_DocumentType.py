# -*- coding: utf-8 -*-

# Description: CodeView document-type

from Convert import saveRemarkToHtml
from TagParsers.Dictionary_TagParser import Dictionary_TagParser 

class CodeView_DocumentType(object):
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
        
    def convert(self, document, documentTree, outputRootDirectory):
        remarkText = [
                '[[ParentList]]',
                '',
                '[[tag file_name]]',
                '===',
                '',
                '[[Parent]]',
                '',
                '[[Link]]: directory.remark-index',
                '',
                '[[-+Code]]: [[-Body]]']

        saveRemarkToHtml(remarkText, document, documentTree, 
                         outputRootDirectory)
         
    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return fileName + '.htm'
