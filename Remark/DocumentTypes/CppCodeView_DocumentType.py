# -*- coding: utf-8 -*-

# Description: CppCodeView document-type

from FileSystem import escapeMarkdown, globalOptions, fileUpToDate
from Conversion import saveRemarkToHtml
from TagParsers.Dictionary_TagParser import Dictionary_TagParser 

class CppCodeView_DocumentType(object):
    def __init__(self):
        tagMap = {'description' : 'Description',
                  'detail' : 'Detail',
                  'parent' : 'Documentation',
                  'parentOf' : 'DocumentationOf',
                  'author' : 'Author'}
        
        self.tagParser = Dictionary_TagParser(tagMap)

    def name(self):
        return 'CppCodeView'

    def linkDescription(self, document):
        return escapeMarkdown(document.fileName)

    def parseTags(self, fileName, reporter):
        return self.tagParser.parse(fileName, 
                                    globalOptions().maxTagLines,
                                    reporter)
        
    def convert(self, document, documentTree, outputRootDirectory, reporter):
        remarkText = ['[[ParentList]]',
                '',
                '[[tag link_description]]',
                '===',
                '',
                '[[Parent]]',
                '',
                '[[Link]]: directory.remark-index',
                '',
                '[[-+CppCode]]: [[-Body]]',]

        saveRemarkToHtml(remarkText, document, documentTree, 
                         outputRootDirectory, reporter)
        
    def upToDate(self, document, documentTree, outputRootDirectory):
        return fileUpToDate(document.relativeName, documentTree.rootDirectory, 
                            self.outputName(document.relativeName), outputRootDirectory)
                
    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return fileName + '.htm'

    