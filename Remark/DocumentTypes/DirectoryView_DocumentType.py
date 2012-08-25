# -*- coding: utf-8 -*-

# Description: DirectoryView_DocumentType class

from DocumentType import DocumentType
from Common import changeExtension 

class DirectoryView_DocumentType(DocumentType):
    def __init__(self):
        None

    def name(self):
        return 'DirectoryView'

    def linkDescription(self, document):
        return document.tagString('description')

    def parseTags(self, fileName, lines = 100):
        return {}
        
    def generateMarkdown(self, fileName):
        return ['[[ParentList]]',
                '',
                '[[tag description]]',
                '===',
                '',
                '[[Index]]',]
         
    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')
