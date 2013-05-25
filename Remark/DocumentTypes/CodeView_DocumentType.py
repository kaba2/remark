# -*- coding: utf-8 -*-

# Description: CodeView document-type

from Remark.FileSystem import escapeMarkdown, globalOptions, fileUpToDate
from Remark.Conversion import saveRemarkToHtml
from Remark.TagParsers.Dictionary_TagParser import Dictionary_TagParser 

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

    def parseTags(self, fileName, reporter):
        return self.tagParser.parse(fileName, globalOptions().maxTagLines, reporter)
        
    def convert(self, document, documentTree, outputRootDirectory, reporter):
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
                         outputRootDirectory, reporter)
         
    def upToDate(self, document, documentTree, outputRootDirectory):
        return fileUpToDate(document.relativeName, documentTree.rootDirectory, 
                            self.outputName(document.relativeName), outputRootDirectory)

    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return fileName + '.htm'
