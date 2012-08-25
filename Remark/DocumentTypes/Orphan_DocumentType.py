# -*- coding: utf-8 -*-

# Description: Orphan_DocumentType class

from DocumentType import DocumentType
from Common import changeExtension 

class Orphan_DocumentType(DocumentType):
    def name(self):
        return 'Orphan'

    def linkDescription(self, document):
        return document.tagString('description')

    def parseTags(self, fileName, lines = 100):
        return {}
        
    def generateMarkdown(self, fileName):
        return ['[[ParentList]]',
                '',
                'Orphans',
                '=======',
                '',
                '[[DocChildren]]',
                '[[SourceChildren]]',]
         
    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')
