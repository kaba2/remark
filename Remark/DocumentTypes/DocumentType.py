# -*- coding: utf-8 -*-

# Description: DocumentType base-class
# Documentation: document_types.txt

class DocumentType:
    def __init__(self):
        None        
        
    def parseTags(self, fileName, lines = 100):
        None         
        
    def generateMarkdown(self, fileName):
        return []
        
    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return fileName + '.htm'
    