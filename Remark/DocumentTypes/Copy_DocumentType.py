# -*- coding: utf-8 -*-

# Description: Copy document-type

from Remark.FileSystem import escapeMarkdown, fileUpToDate, copyIfNecessary
from Remark.TagParsers.Dictionary_TagParser import Dictionary_TagParser 
from Remark.DocumentType_Registry import registerDocumentType

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

    def outputName(self, fileName):
        return fileName

registerDocumentType('Copy', Copy_DocumentType())
