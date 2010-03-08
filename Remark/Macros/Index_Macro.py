# -*- coding: utf-8 -*-

# Description: Index_Macro class
# Detail: Generates a html file to traverse the documentation tree directly. 

import string
import os.path

from Common import linkAddress
from Common import outputDocumentName, unixDirectoryName
from MacroRegistry import registerMacro

class Index_Macro:
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
            elif documentTree.findDocumentByName(relativeName):
                fileSet.append(entry)
                
        for directory in directorySet:
            linkDescription = directory + '/'
            linkTarget = os.path.join(directory, 'directory.index')
            text.append('* ' + remarkConverter.remarkLink(linkDescription, outputDocumentName(linkTarget)))
       
        for entry in fileSet:
            text.append('* [[FileLink]]: ' + entry)
            
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
        