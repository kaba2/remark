# -*- coding: utf-8 -*-

# Description: ReadFile macro
# Detail: Reads a plain-text file.

import os

from Remark.FileSystem import readFile, globalOptions
from Remark.Macro_Registry import registerMacro

class ReadFile_Macro(object):
    def name(self):
        return 'ReadFile'

    def expand(self, parameter, remark):
        document = remark.document
        reporter = remark.reporter
        
        # Find out the relative-name of the file
        # to be read.

        if len(parameter) == 0:
            # No file-paths were given.
            return []

        if len(parameter) > 1:
            reporter.reportWarning(
                ['Multiple file-paths given:'] + parameter + ['Using the first.'], 'invalid-input')

        searchName = parameter[0]

        # Search for the file in the document-tree.
        input, unique = remark.documentTree.findDocument(
            searchName, document.relativeDirectory)

        if not unique:
            # There are many matching image files with the given name.
            # Report a warning, pick one arbitrarily, and continue.
            remark.reporter.reportAmbiguousDocument(searchName)

        if input == None:
            # The file was not found. 
            remark.reporter.reportMissingDocument(searchName)
            return []

        # Form the absolute-path to the file.
        inputPath = os.path.join(remark.inputRootDirectory, input.relativeName)

        # Read the file.
        text = readFile(inputPath, globalOptions().maxFileSize)

        return text
    
    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True
    
    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('ReadFile', ReadFile_Macro())
