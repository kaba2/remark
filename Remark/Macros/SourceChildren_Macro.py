# -*- coding: utf-8 -*-

# Description: SourceChildren macro
# Detail: Generates links to source code children.

import os.path
import string

from MacroRegistry import registerMacro
from FileSystem import unixRelativePath, outputDocumentName, escapeMarkdown
from FileSystem import withoutFileExtension

class SourceChildren_Macro(object):
    def name(self):
        return 'SourceChildren'

    def expand(self, parameter, remark):
        document = remark.document
                
        def prefixOf(left, right):
            return string.find(withoutFileExtension(right), 
                               withoutFileExtension(left)) == 0
        
        def same(left, right):
            return withoutFileExtension(left) == withoutFileExtension(right)

        # Gather the list of source files.
        
        sortedMap = [x for x in document.childSet.itervalues() 
                    if (x.tagString('document_type') == 'CppCodeView' or
                        x.tagString('document_type') == 'CodeView')]

        if len(sortedMap) == 0:
            return []

        # Sort the list alphabetically w.r.t. the relative file names.
        
        sortedMap.sort(lambda x, y: cmp(x.relativeName, y.relativeName))
     
        # Given an alphabetically sorted list of source files,
        # group all files that have the same name without
        # extension. The group shares the same description.
       
        outputDirectory = document.relativeDirectory
        beginIndex = 0
        groupSet = []
        description = ''
        detail = ''
        for i in range(0, len(sortedMap)):
            sourceDocument = sortedMap[i]
            reference = sortedMap[beginIndex]
            
            # Note that it is really the _description_ we want to
            # use here, rather than the link description.
            desc = sourceDocument.tagString('description')
            if desc != '':
                # If there are multiple descriptions, one is chosen
                # arbitrarily and a warning is emitted.
                if description != '':
                    message = ['Multiple descriptions for a document-group.',
                              'Current: ' + description,
                              'New: ' + desc]
                    remark.reportWarning(message, 'ambiguous-input')
                description = desc

            det = sourceDocument.tagString('detail')
            if det != '':
                # If there are multiple details, one is chosen
                # arbitrarily and a warning is emitted.
                if detail != '':
                    message = ['Multiple details for a document-group. ',
                              'Current: ' + detail,
                              'New: ' + det]
                    remark.reportWarning(message, 'ambiguous-input')
                detail = det

            if i == len(sortedMap) - 1 or not same(sortedMap[i + 1].relativeName, reference.relativeName):
                groupSet.append([description, detail, sortedMap[beginIndex : i + 1]])
                beginIndex = i + 1
                description = ''
                detail = ''

        # If a group does not have a description, it can be
        # joined together with a preceding group, on the condition that
        # without extensions the names in the preceding group are 
        # prefixes of the names in the following group.

        i = 0
        while i < len(groupSet) - 1:
            if groupSet[i + 1][0] == '' and prefixOf(groupSet[i][2][0].relativeName, groupSet[i + 1][2][0].relativeName):
                    #print 'Join', groupSet[i][1][0].relativeName, groupSet[i + 1][1][0].relativeName
                    groupSet[i][2] += groupSet[i + 1][2]
                    groupSet[i + 1 : i + 2] = []
            else: 
                i += 1
        
        # Set default descriptions for those
        # groups that do not have a description.
        
        for group in groupSet:
            if group[0] == '':
                group[0] = '-'
                message = ['Description missing for the document-group']
                for child in group[2]:
                    message.append(child.fileName)
                remark.reportWarning(message, 'missing-input')
        
        # Order the groups in alphabetical order w.r.t.
        # their descriptions. 
        groupSet.sort(lambda x, y: cmp(x[0], y[0]))
        
        # Output the links in the groups together
        # with a description for the group.
        
        scope = remark.scopeStack.top()
        text = []
        text.append('')
        text.append(scope.getString('SourceChildren.title', 'Files'))
        text.append('---')
        text.append('')

        for group in groupSet:
            # Output description for the group.
            description = group[0]
            text.append('')
            text.append('### ' + description)
            text.append('')
            
            # Output detailed description for the group
            # if it's present.
            detail = group[1]
            if detail != '':
                text.append('')
                text.append('_' + detail + '_')
                text.append('')
                
            # Output the links in the group.
            for child in group[2]:
                text.append(remark.remarkLink(escapeMarkdown(child.fileName),
                                                       document,
                                                       child))
                text.append('')
            
        return text

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remark):
        return []                

    def postConversion(self, inputDirectory, outputDirectory):
        None

registerMacro('SourceChildren', SourceChildren_Macro())
