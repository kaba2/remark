# -*- coding: utf-8 -*-

# Description: Copy document-type

import re

from FileSystem import escapeMarkdown, fileUpToDate, copyIfNecessary
from TagParsers.Dictionary_TagParser import Dictionary_TagParser 

class Copy_DocumentType(object):
    def name(self):
        return 'Copy'

    def linkDescription(self, document):
        return escapeMarkdown(document.fileName)

    def parseTags(self, fileName, reporter):
        return {}

    def convert(self, document, documentTree, outputRootDirectory, reporter):
        # Find out the output-name.
        outputRelativeName = self.outputName(document.relativeName)

        # Copy the file if necessary.
        copyIfNecessary(document.relativeName, documentTree.rootDirectory, 
                        outputRelativeName, outputRootDirectory)
        
    def upToDate(self, document, documentTree, outputRootDirectory):
        return fileUpToDate(document.relativeName, documentTree.rootDirectory, 
                            self.outputName(document.relativeName), outputRootDirectory)

    def updateDependent(self):
        # No information is gathered from copied files.
        # Therefore there is no need to update dependent documents.
        return False

    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return fileName
