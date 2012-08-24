# -*- coding: utf-8 -*-

# Description: CodeView_DocumentType class

import re

from DocumentType import DocumentType
from TagParsers.Generic_TagParser import Generic_TagParser 

class CodeView_DocumentType(DocumentType):
    def __init__(self):
        None

    def name(self):
        return 'CodeView'

    def linkDescription(self, document):
        return document.fileName

    def parseTags(self, fileName, lines = 100):
        regexMap = {'description' : re.compile(r'[ \t]+Description:[ \t]+(.*)'),
                    'detail' : re.compile(r'[ \t]+Detail:[ \t]+(.*)'),
                    'parent' : re.compile(r'[ \t]+Documentation:[ \t]+(.*)'),
                    'parentOf' : re.compile(r'[ \t]+DocumentationOf:[ \t]+(.*)'),
                    'author' : re.compile(r'[ \t]+Author:[ \t]+(.*)')}
        
        parser = Generic_TagParser(regexMap, lines)
        return parser.parse(fileName)
        
    def generateMarkdown(self, fileName):
        return ['[[ParentList]]',
                '',
                '[[tag file_name]]',
                '===',
                '',
                '[[Parent]]',
                '',
                '[[Link]]: directory.remark-index',
                '',
                '[[-+Code]]: [[-Body]]',]
         
    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return fileName + '.htm'
