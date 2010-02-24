# -*- coding: utf-8 -*-

# Description: Index_Macro class
# Detail: Generates a html file to traverse the documentation tree directly. 

import string
import os.path

from Common import linkAddress, remarkLink, getLinkId
from Common import outputDocumentName, unixDirectoryName
from MacroRegistry import registerMacro

class Index_Macro:
    def expand(self, parameter, document, documentTree, scope):
        fullPath = os.path.join(documentTree.rootDirectory, document.relativeDirectory)
        entrySet = ['..'] + os.listdir(fullPath)
        
        title = unixDirectoryName(document.relativeDirectory) + '/'
        text = [title,
                '====']
        
        fileSet = []
        directorySet = []
        for entry in entrySet:
            relativeName = os.path.normpath(os.path.join(document.relativeDirectory, entry))
            fullName = os.path.join(documentTree.rootDirectory, relativeName)
            if os.path.isdir(fullName) and relativeName in documentTree.directorySet:
                directorySet.append(entry)
            elif documentTree.findDocumentByName(relativeName):
                fileSet.append(entry)
                
        linkSet = []
        for directory in directorySet:
            linkId = getLinkId()
            text.append('* [' + directory + '/][RemarkLink_' + str(linkId) + ']')
            linkName = unixDirectoryName(os.path.join(directory, 'directory.htm'))
            linkSet.append('[RemarkLink_' + str(linkId) + ']: ' + linkName)
       
        for entry in fileSet:
            linkId = getLinkId()
            text.append('* [' + entry + '][RemarkLink_' + str(linkId) + ']')
            linkName = outputDocumentName(entry)
            linkSet.append('[RemarkLink_' + str(linkId) + ']: ' + linkName)

        text += linkSet

        return text

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True
        
registerMacro('Index', Index_Macro())
        