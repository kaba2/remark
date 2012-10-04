# -*- coding: utf-8 -*-

# Description: DirectoryView document-type

from FileSystem import changeExtension, fileExists
from Conversion import saveRemarkToHtml

class DirectoryView_DocumentType(object):
    def name(self):
        return 'DirectoryView'

    def linkDescription(self, document):
        return document.tagString('description')

    def parseTags(self, fileName, reporter):
        return {}
        
    def convert(self, document, documentTree, outputRootDirectory, reporter):
        remarkText = ['[[ParentList]]',
                '',
                '[[tag link_description]]',
                '===',
                '',
                '[[Index]]',]

        saveRemarkToHtml(remarkText, document, documentTree, 
                         outputRootDirectory, reporter)

    def upToDate(self, document, documentTree, outputRootDirectory):
        return False

    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')
