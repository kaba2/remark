# -*- coding: utf-8 -*-

# Description: Index macro
# Detail: Generates a html file to traverse the directory tree directly. 

import string
import os.path

from Common import linkAddress, linkTable
from Common import outputDocumentName, unixDirectoryName
from MacroRegistry import registerMacro

class Index_Macro(object):
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
        documentTree = remarkConverter.documentTree
        
        fullPath = os.path.join(documentTree.rootDirectory, document.relativeDirectory)
        entrySet = ['..'] + os.listdir(fullPath)

        text = []
      
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
        
        linkSet = []        
        
        for directory in directorySet:
            linkDescription = directory + '/'
            linkTarget = os.path.join(directory, 'directory.index')
            linkSet.append((outputDocumentName(linkTarget), linkDescription))
       
        for fileName in fileSet:
            linkTarget = outputDocumentName(fileName)
            linkDescription = fileName
            linkSet.append((linkTarget, linkDescription))
            
        text += linkTable(linkSet)
                    
        text.append('')

        return text

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return False

    def htmlHead(self, remarkConverter):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None
        
registerMacro('Index', Index_Macro())
        