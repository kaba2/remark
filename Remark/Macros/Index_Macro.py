# -*- coding: utf-8 -*-

# Description: Index macro
# Detail: Generates a html file to traverse the directory tree directly. 

import string
import os.path

from Remark.FileSystem import unixRelativePath, htmlDiv, escapeMarkdown
from Remark.FileSystem import unixDirectoryName, listDirectory
from Remark.Macro_Registry import registerMacro
from Remark.DocumentType_Registry import outputDocumentName

class Index_Macro(object):
    def name(self):
        return 'Index'

    def expand(self, parameter, remark):
        document = remark.document
        documentTree = remark.documentTree
        scope = remark.scopeStack.top()

        # Variables
        className = scope.getString('Index.class_name', 'Index')
        
        fullPath = os.path.join(documentTree.rootDirectory, document.relativeDirectory)
        entrySet = ['..'] + listDirectory(fullPath)
     
        # Gather the files and directories in the
        # document's directory.
        fileSet = []
        directorySet = []
        for entry in entrySet:
            relativeName = os.path.join(document.relativeDirectory, entry)
            fullName = os.path.join(documentTree.rootDirectory, relativeName)
            relativeName = unixDirectoryName(relativeName)
            if os.path.isdir(fullName):
                if relativeName in documentTree.directorySet:
                    directorySet.append(entry)
            elif documentTree.findDocumentByRelativeName(relativeName):
                fileSet.append(entry)
        
        # Create links for the directories.
        text = []
        for directory in directorySet:
            linkDirectory = os.path.join(document.relativeDirectory, directory)
            directoryIndexName = 'directory.remark-index'
            directoryDocument = documentTree.findDocumentLocal(directoryIndexName, linkDirectory)
            assert directoryDocument != None

            text.append(' 1. ' + remark.remarkLink(escapeMarkdown(directory + '/'),
                                                   document, directoryDocument))
        
        # Create links for the files.
        for fileName in fileSet:
            fileDocument = documentTree.findDocumentLocal(fileName, document.relativeDirectory)
            assert fileDocument != None

            text.append(' 1. ' + remark.remarkLink(escapeMarkdown(fileName),
                                                   document, fileDocument))
                    
        text.append('')

        text = htmlDiv(text, className)

        text.append('')
        text.append('<div class = "remark-end-list"></div>')
        text.append('')

        return text

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None
        
registerMacro('Index', Index_Macro())
        