# -*- coding: utf-8 -*-

# Description: Index macro
# Detail: Generates a html file to traverse the directory tree directly. 

import string
import os.path

from Common import unixRelativePath, htmlDiv
from Common import outputDocumentName, unixDirectoryName
from MacroRegistry import registerMacro

class Index_Macro(object):
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        documentTree = remarkConverter.documentTree
        scope = remarkConverter.scopeStack.top()

        # Variables
        className = scope.getString('Index.class_name', 'Index')
        
        fullPath = os.path.join(documentTree.rootDirectory, document.relativeDirectory)
        entrySet = ['..'] + os.listdir(fullPath)
     
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
            directoryDocument = documentTree.findDocumentLocal('directory.remark-index', linkDirectory)
            text.append(' 1. ' + remarkConverter.remarkLink(directory + '/',
                                                   document, directoryDocument))
        
        # Create links for the files.
        for fileName in fileSet:
            fileDocument = documentTree.findDocumentLocal(fileName, document.relativeDirectory)
            text.append(' 1. ' + remarkConverter.remarkLink(fileName,
                                                   document, fileDocument))
                    
        text.append('')

        return htmlDiv(text, className)

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None
        
registerMacro('Index', Index_Macro())
        