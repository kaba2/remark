# -*- coding: utf-8 -*-

# Description: Copy document-type

import re

from Common import escapeMarkdown
from Common import copyIfNecessary
from TagParsers.Dictionary_TagParser import Dictionary_TagParser 

class Copy_DocumentType(object):
    def name(self):
        return 'Copy'

    def linkDescription(self, document):
        return escapeMarkdown(document.fileName)

    def parseTags(self, fileName):
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
        return fileName
