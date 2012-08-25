# -*- coding: utf-8 -*-

# Description: RemarkPage_DocumentType class

import re

from DocumentType import DocumentType
from TagParsers.Remark_TagParser import Remark_TagParser
from Common import changeExtension 

class RemarkPage_DocumentType(DocumentType):
    def name(self):
        return 'RemarkPage'

    def linkDescription(self, document):
        return document.tagString('description')

    def parseTags(self, fileName, lines = 100):
        parser = Remark_TagParser({'parent' : '[[Parent]]'}, lines)
        return parser.parse(fileName)
        
    def generateMarkdown(self, fileName):
        return  ['[[set RemarkPage.mid_text]]',
                 '[[set RemarkPage.end_text]]',
                 '[[ParentList]]',
                 '[[Body]]',
                 '[[DocChildren]]',
                 '[[RemarkPage.mid_text]]',
                 '[[SourceChildren]]',
                 '[[RemarkPage.end_text]]',]
         
    def mathEnabled(self):
        return True

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')
