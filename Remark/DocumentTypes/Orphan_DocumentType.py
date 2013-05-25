# -*- coding: utf-8 -*-

# Description: Orphan document-type

from Remark.FileSystem import changeExtension 
from Remark.Conversion import saveRemarkToHtml

class Orphan_DocumentType(object):
    def name(self):
        return 'Orphan'

    def linkDescription(self, document):
        return document.tagString('description')

    def parseTags(self, fileName, reporter):
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
