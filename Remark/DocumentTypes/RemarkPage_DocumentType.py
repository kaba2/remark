# -*- coding: utf-8 -*-

# Description: RemarkPage_DocumentType class

import re

from DocumentType import DocumentType
from TagParsers.Markdown_TagParser import Markdown_TagParser
from Common import changeExtension 

class RemarkPage_DocumentType(DocumentType):
    def __init__(self):
        None

    def parseTags(self, fileName, lines = 100):
        parser = Markdown_TagParser({'parent' : re.compile(r'\[\[Parent\]\]:[ \t]*(.*)')}, lines)
        return parser.parse(fileName)
        
    def generateMarkdown(self, fileName):
        return  ['[[Body]]',
                 '[[DocChildren]]',
                 '[[get mid_text]]',
                 '[[SourceChildren]]',
                 '[[get end_text]]',]
         
    def mathEnabled(self):
        return True

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')
