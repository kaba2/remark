# -*- coding: utf-8 -*-

# Description: DocChildren macro
# Detail: Generates links to documentation children.

from MacroRegistry import registerMacro
from Common import unixRelativePath, outputDocumentName, htmlDiv, macroCall

class DocChildren_Macro(object):
    def name(self):
        return 'DocChildren'

    def expand(self, parameter, remark):
        document = remark.document
        documentTree = remark.documentTree
        scope = remark.scopeStack.top()

        # Variables
        self.className = scope.getString('DocChildren.class_name', 'DocChildren')
        self.title = scope.getString('DocChildren.title', 'Learn more')
        self.includeGlob = scope.get('DocChildren.include', ['document_type RemarkPage'])
        self.includeRegex = scope.get('DocChildren.include_regex')
        self.excludeGlob = scope.get('DocChildren.exclude')
        self.excludeRegex = scope.get('DocChildren.exclude_regex')

        text = ['']
        text += macroCall('set_many DocumentTree',
                         ['min_depth 1',
                          'max_depth 1',
                          'class_name ' + self.className])

        text += macroCall('set DocumentTree.include',
                         self.includeGlob)

        text += macroCall('set DocumentTree.include_regex',
                         self.includeRegex)

        text += macroCall('set DocumentTree.exclude',
                          self.excludeGlob)

        text += macroCall('set DocumentTree.exclude_regex',
                          self.excludeRegex)
      
        remark.convert(text)
        treeText = remark.convert(['[[DocumentTree]]'])

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

    def pureOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('DocChildren', DocChildren_Macro())
