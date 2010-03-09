# -*- coding: utf-8 -*-

# Description: DirectoryView_DocumentType class

from DocumentType import DocumentType
from TagParsers.Empty_TagParser import Empty_TagParser
from Common import changeExtension 

class DirectoryView_DocumentType(DocumentType):
    def __init__(self):
        None

    def parseTags(self, fileName, lines = 100):
        parser = Empty_TagParser()
        return parser.parse(fileName)
        
    def generateMarkdown(self, fileName):
        return ['[[description]]',
                '===',
                '',
                '[[Index]]',]
         
    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')