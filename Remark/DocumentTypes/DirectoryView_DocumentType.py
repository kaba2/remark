# -*- coding: utf-8 -*-

# Description: DirectoryView document-type

from FileSystem import changeExtension, fileExists
from Conversion import saveRemarkToHtml

class DirectoryView_DocumentType(object):
    def name(self):
        return 'DirectoryView'

    def linkDescription(self, document):
        return document.tagString('description')

    def parseTags(self, fileName, lines = 100):
        return {}
        
    def convert(self, document, documentTree, outputRootDirectory):
        remarkText = ['[[ParentList]]',
                '',
                '[[tag link_description]]',
                '===',
                '',
                '[[Index]]',]

        saveRemarkToHtml(remarkText, document, documentTree, 
                         outputRootDirectory)

    def upToDate(self, document, documentTree, outputRootDirectory):
        return True
        #return fileExists(document.documentType.outputName(document.relativeName), outputRootDirectory)

    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')
