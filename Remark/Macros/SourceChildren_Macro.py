
# -*- coding: utf-8 -*-

# Description: SourceChildren macro
# Detail: Generates links to source code children.

import os.path
import string

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import unixRelativePath, escapeMarkdown
from Remark.FileSystem import withoutFileExtension, markdownRegion
from Remark.DocumentType_Registry import outputDocumentName

class SourceChildren_Macro(object):
    def name(self):
        return 'SourceChildren'

    def expand(self, parameter, remark):
        document = remark.document
        documentTree = remark.documentTree
        scope = remark.scopeStack.top()

        # Variables
        self.rootName = scope.getString('SourceChildren.root_document', document.fileName)
        self.className = scope.getString('SourceChildren.class_name', 'SourceChildren')
        self.title = scope.getString('SourceChildren.title', 'Files')

        text = []

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
            # There are no source files.
            return text

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
        # joined together with a preceding described group, on the condition 
        # that without extensions the names in the preceding group are 
        # prefixes of the names in the following group.
        i = 1
        while i < len(groupSet):
            joined = False;
            for j in range(i - 1, -1, -1):
                if groupSet[i][0] == '' and prefixOf(groupSet[j][2][0].relativeName, groupSet[i][2][0].relativeName):
                    #print 'Join', groupSet[j][2][0].relativeName, groupSet[i][2][0].relativeName
                    groupSet[j][2] += groupSet[i][2]
                    groupSet[i : i + 1] = []
                    joined = True;
                    break;
            if not joined: 
                i += 1

        # Set default descriptions for those
        # groups that do not have a description.
        for group in groupSet:
            if group[0] == '':
                message = ['Description missing for the document-group']
                for child in group[2]:
                    message.append(child.fileName)
                remark.reportWarning(message, 'missing-description')

        # Find the first group that has no description.
        i = 0
        while i < len(groupSet):
            if groupSet[i][0] == '':
                break
            i += 1

        # Join all groups without a description to the
        # first such group.
        if i < len(groupSet):
            j = i + 1
            while j < len(groupSet):
                if groupSet[j][0] == '':
                    groupSet[i][2] += groupSet[j][2]
                    groupSet[j : j + 1] = []
                else:
                    j += 1;

        # Output the groups
        #for group in groupSet:
        #    for child in group[2]:
        #        print child.relativeName
        #    print ''
       
        # Order the groups in alphabetical order w.r.t.
        # their descriptions. 
        groupSet.sort(lambda x, y: cmp(x[0], y[0]))

        # Move the unnamed group to the end.
        if len(groupSet) > 0 and groupSet[0][0] == '':
            groupSet.append(groupSet[0])
            groupSet[0 : 1] = []

        defaultDescription = '?';

        # Output the links in the groups together
        # with a description for the group.

        # The title is output only if its non-empty.
        if len(self.title.strip()) > 0:
            # Output the title
            text.append('')
            text.append(self.title)
            text.append('---')

        text.append('')
        for group in groupSet:
            # Output description for the group.
            description = group[0]
            if description == '':
                description = defaultDescription

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

            # Output the links in the group as a list.
            for child in group[2]:
                text.append('* ' + remark.remarkLink(escapeMarkdown(child.fileName),
                            document, child))
            
        return markdownRegion(
            remark.convert(text), 
            {'class' : self.className});

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        return []                

    def postConversion(self, remark):
        None

registerMacro('SourceChildren', SourceChildren_Macro())
