# -*- coding: utf-8 -*-

# Description: CodeView document-type

from Common import escapeMarkdown, globalOptions
from Convert import saveRemarkToHtml
from TagParsers.Dictionary_TagParser import Dictionary_TagParser 

class CodeView_DocumentType(object):
    def __init__(self):
        tagMap = {'description' : 'Description',
                  'detail' : 'Detail',
                  'parent' : 'Documentation',
                  'parentOf' : 'DocumentationOf',
                  'author' : 'Author'}
        
        self.tagParser = Dictionary_TagParser(tagMap)

    def name(self):
        return 'CodeView'

    def linkDescription(self, document):
        return escapeMarkdown(document.fileName)

    def parseTags(self, fileName):
        return self.tagParser.parse(fileName, globalOptions().maxTagLines)
        
    def convert(self, document, documentTree, outputRootDirectory):
        remarkText = [
                '[[ParentList]]',
                '',
                '[[tag link_description]]',
                '===',
                '',
                '[[Parent]]',
                '',
                '[[Link]]: directory.remark-index',
                '',
                '[[-+Code]]: [[-Body]]']

        saveRemarkToHtml(remarkText, document, documentTree, 
                         outputRootDirectory)
         
    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return fileName + '.htm'
