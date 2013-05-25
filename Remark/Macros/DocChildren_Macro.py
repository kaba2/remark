# -*- coding: utf-8 -*-

# Description: DocChildren macro
# Detail: Generates links to documentation children.

from Remark.Macro_Registry import registerMacro, findMacro
from Remark.FileSystem import unixRelativePath, htmlDiv
from Remark.DocumentType_Registry import outputDocumentName

class DocChildren_Macro(object):
    def name(self):
        return 'DocChildren'

    def expand(self, parameter, remark):
        document = remark.document
        documentTree = remark.documentTree
        scope = remark.scopeStack.top()

        # Variables
        self.rootName = scope.getString('DocChildren.root_document', document.fileName)
        self.className = scope.getString('DocChildren.class_name', 'DocChildren')
        self.title = scope.getString('DocChildren.title', 'Learn more')
        self.includeGlob = scope.get('DocChildren.include', ['document_type RemarkPage'])
        self.includeRegex = scope.get('DocChildren.include_regex')
        self.excludeGlob = scope.get('DocChildren.exclude')
        self.excludeRegex = scope.get('DocChildren.exclude_regex')

        # We will run the following in advance
        # because we want to know whether the
        # DocumentTree gives any output or not.

        remark.macro('set_many DocumentTree',
                     ['min_depth 1',
                     'max_depth 1',
                     'class_name ' + self.className,
                     'root_document ' + self.rootName])

        remark.macro('set DocumentTree.include',
                     self.includeGlob)

        remark.macro('set DocumentTree.include_regex',
                     self.includeRegex)

        remark.macro('set DocumentTree.exclude',
                     self.excludeGlob)

        remark.macro('set DocumentTree.exclude_regex',
                     self.excludeRegex)
      
        treeText = remark.macro('DocumentTree')

        text = []
        # Only create the title if at least 
        # one link was produced.
        if (treeText != ['']):

            # Create the title.
            text.append('')
            if (self.title != ''):
                text.append(self.title)
                text.append('---')
                text.append('')
            
            # Append the links.
            text += treeText

        return text

    def outputType(self):
        return 'remark'

    def expandOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('DocChildren', DocChildren_Macro())
