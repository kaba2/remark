# -*- coding: utf-8 -*-

# Description: Common stuff used in Remark
# Documentation: core_stuff.txt

import os.path
import string
import codecs

def linkAddress(fromDirectory, toFile):
    relativeName = os.path.relpath(toFile, fromDirectory)
    return unixDirectoryName(relativeName)

def readFile(fileName):
    text = []

    # Read the file into memory
    try:
        with codecs.open(fileName, mode = 'rU', encoding = 'utf-8-sig') as file:
            text = file.readlines()
    except UnicodeDecodeError:
        print 'Warning: file \'' + fileName + '\' is not UTF-8 encoded. Assuming Latin-1 encoding.'
        with codecs.open(fileName, mode = 'rU', encoding = 'latin-1') as file:
            text = file.readlines()
            
    # Remove possible newlines from the ends of the lines.
    for i in range(0, len(text)):
        if text[i][-1] == '\n':
            text[i] = text[i][0 : -1]
            
    return text

class DocumentType:
    def __init__(self, inputExtension, outputExtension, template, parser, mathEnabled):
        self.inputExtension = inputExtension
        self.outputExtension = outputExtension
        self.template = template
        self.parser = parser
        self.mathEnabled = mathEnabled

_documentTypeMap = dict()

def registerDocumentType(inputExtension, outputExtension,
                         template, parser, mathEnabled):
    global _documentTypeMap
    _documentTypeMap[inputExtension] = DocumentType(inputExtension,
                                                    outputExtension,
                                                    template,
                                                    parser,
                                                    mathEnabled)

def documentType(inputExtension):
    global _documentTypeMap
    if inputExtension in _documentTypeMap:
        return _documentTypeMap[inputExtension]
    return None

def outputDocumentName(name):
    inputExtension = os.path.splitext(name)[1]
    outputExtension = documentType(inputExtension).outputExtension
    return changeExtension(name, outputExtension)

def unixDirectoryName(name):
    return string.replace(os.path.normpath(name), '\\', '/')                

def changeExtension(fileName, newExtension):
    return os.path.splitext(fileName)[0] + newExtension
