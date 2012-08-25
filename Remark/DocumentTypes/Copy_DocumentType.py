# -*- coding: utf-8 -*-

# Description: Copy document-type

import re

from Common import copyIfNecessary
from DocumentType import DocumentType
from TagParsers.Dictionary_TagParser import Dictionary_TagParser 

class Copy_DocumentType(DocumentType):
    def name(self):
        return 'Copy'

    def linkDescription(self, document):
        return document.fileName

    def parseTags(self, fileName, lines = 100):
        return {}

    def convert(self, document, documentTree, outputRootDirectory):
        # Find out the output-name.
        outputRelativeName = self.outputName(document.relativeName)

        # Copy the file if necessary.
        copyIfNecessary(document.relativeName, documentTree.rootDirectory, 
                        outputRelativeName, outputRootDirectory)
        
    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return fileName + '.htm'
