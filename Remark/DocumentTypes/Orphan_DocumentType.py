# -*- coding: utf-8 -*-

# Description: Orphan document-type

from FileSystem import changeExtension 
from Conversion import saveRemarkToHtml

class Orphan_DocumentType(object):
    def name(self):
        return 'Orphan'

    def linkDescription(self, document):
        return document.tagString('description')

    def parseTags(self, fileName, lines = 100):
        return {}
        
    def convert(self, document, documentTree, outputRootDirectory, reporter):
        remarkText = ['[[ParentList]]',
                '',
                'Orphans',
                '=======',
                '',
                '[[DocChildren]]',
                '[[SourceChildren]]',]

        saveRemarkToHtml(remarkText, document, documentTree, 
                         outputRootDirectory, reporter)
        
    def upToDate(self, document, documentTree, outputRootDirectory):
        return False

    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')
