# -*- coding: utf-8 -*-

# Description: RemarkPage document-type

import re

from TagParsers.Remark_TagParser import Remark_TagParser
from Common import changeExtension, globalOptions, fileUpToDate
from Convert import saveRemarkToHtml

class RemarkPage_DocumentType(object):
    def __init__(self):
        self.tagParser = Remark_TagParser({'parent' : '[[Parent]]'})

    def name(self):
        return 'RemarkPage'

    def linkDescription(self, document):
        return document.tagString('description')

    def parseTags(self, fileName):
        return self.tagParser.parse(fileName, globalOptions().maxTagLines)
        
    def convert(self, document, documentTree, outputRootDirectory):
        remarkText = ['[[set RemarkPage.mid_text]]',
                 '[[set RemarkPage.end_text]]',
                 '[[ParentList]]',
                 '[[Body]]',
                 '[[DocChildren]]',
                 '[[RemarkPage.mid_text]]',
                 '[[SourceChildren]]',
                 '[[RemarkPage.end_text]]',]

        saveRemarkToHtml(remarkText, document, documentTree, 
                         outputRootDirectory)
         
    def upToDate(self, document, documentTree, outputRootDirectory):
        return fileUpToDate(document.relativeName, documentTree.rootDirectory, 
                            self.outputName(document.relativeName), outputRootDirectory)

    def mathEnabled(self):
        return True

    def outputName(self, fileName):
        return changeExtension(fileName, '.htm')
