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
        return  ['[[set mid_text]]',
                 '[[set end_text]]',
                 '[[Body]]',
                 '[[DocChildren]]',
                 '[[mid_text]]',
                 '[[SourceChildren]]',
                 '[[end_text]]',]
         
    def mathEnabled(self):
        return True

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')
