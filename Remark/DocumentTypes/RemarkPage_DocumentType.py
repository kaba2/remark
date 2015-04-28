# -*- coding: utf-8 -*-

# Description: RemarkPage document-type

import re

from Remark.TagParsers.Remark_TagParser import Remark_TagParser
from Remark.FileSystem import changeExtension, globalOptions, fileUpToDate
from Remark.Conversion import saveRemarkToHtml

class RemarkPage_DocumentType(object):
    def __init__(self):
        self.tagParser = Remark_TagParser({'parent' : '[[Parent]]'})

    def name(self):
        return 'RemarkPage'

    def linkDescription(self, document):
        return document.tagString('description')

    def parseTags(self, fileName, reporter):
        return self.tagParser.parse(fileName, 
                                    globalOptions().maxTagLines, 
                                    reporter)
        
    def convert(self, document, documentTree, outputRootDirectory, reporter):
        remarkText = [
                 '[[set RemarkPage.mid_text]]',
                 '[[set RemarkPage.end_text]]',
                 '[[ParentList]]',
                 '[[+ReadFile]]: [[tag file_name]]',
                 '[[DocChildren]]',
                 '[[RemarkPage.mid_text]]',
                 '[[SourceChildren]]',
                 '[[RemarkPage.end_text]]',]

        saveRemarkToHtml(remarkText, document, documentTree, 
                         outputRootDirectory, reporter)
         
    def upToDate(self, document, documentTree, outputRootDirectory):
        return fileUpToDate(document.relativeName, documentTree.rootDirectory, 
                            self.outputName(document.relativeName), outputRootDirectory)

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')
