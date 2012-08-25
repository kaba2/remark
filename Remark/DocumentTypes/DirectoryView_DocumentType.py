# -*- coding: utf-8 -*-

# Description: DirectoryView document-type

from DocumentType import DocumentType
from Common import changeExtension 
from Convert import saveRemarkToHtml

class DirectoryView_DocumentType(DocumentType):
    def name(self):
        return 'DirectoryView'

    def linkDescription(self, document):
        return document.tagString('description')

    def parseTags(self, fileName, lines = 100):
        return {}
        
    def convert(self, document, documentTree, outputRootDirectory):
        remarkText = ['[[ParentList]]',
                '',
                '[[tag description]]',
                '===',
                '',
                '[[Index]]',]

        saveRemarkToHtml(remarkText, document, documentTree, 
                         outputRootDirectory)

    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')
