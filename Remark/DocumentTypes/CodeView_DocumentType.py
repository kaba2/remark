# -*- coding: utf-8 -*-

# Description: CodeView document-type

from Remark.FileSystem import escapeMarkdown, globalOptions, fileUpToDate
from Remark.Conversion import saveRemarkToHtml
from Remark.TagParsers.Dictionary_TagParser import Dictionary_TagParser 

from pygments.lexers import get_lexer_for_filename, get_lexer_by_name

class CodeView_DocumentType(object):
    def __init__(self):
        tagMap = {'description' : 'Description',
                  'detail' : 'Detail',
                  'parent' : 'Documentation',
                  'parentOf' : 'DocumentationOf',
                  'author' : 'Author'}
        
        self.tagParser = Dictionary_TagParser(tagMap)

    def name(self):
        return 'CodeView'

    def linkDescription(self, document):
        return escapeMarkdown(document.fileName)

    def parseTags(self, fileName, reporter):
        return self.tagParser.parse(fileName, globalOptions().maxTagLines, reporter)
        
    def convert(self, document, documentTree, outputRootDirectory, reporter):
        lexerName = ''
        if document.extension == '.m':
            # The Linguist library, which Pygments uses,
            # associates the .m extension to Objective-C.
            # However, I need it to associate to Matlab.
            # I should make this configurable in the future,
            # but for now I will just override it.
            lexerName = 'matlab'
        
        if lexerName == '':
            try:
                # Choose the lexer primarily from the filename.
                lexer = get_lexer_for_filename(document.fileName)
                lexerName = lexer.aliases[0]
            except:
                None

        remarkText = [
                '[[ParentList]]',
                '',
                '[[tag link_description]]',
                '===',
                '',
                '[[Parent]]',
                '',
                '[[Link]]: directory.remark-index',
                '',
                '[[set Code.type]]: ' + lexerName,
                '[[-+Code]]: [[-Body]]']

        saveRemarkToHtml(remarkText, document, documentTree, 
                         outputRootDirectory, reporter)
         
    def upToDate(self, document, documentTree, outputRootDirectory):
        return fileUpToDate(document.relativeName, documentTree.rootDirectory, 
                            self.outputName(document.relativeName), outputRootDirectory)

    def mathEnabled(self):
        return False

    def outputName(self, fileName):
        return fileName + '.htm'
