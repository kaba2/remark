# -*- coding: utf-8 -*-

# Description: SourceChildren_Macro class
# Detail: Generates links to source code children.

import os.path
import string

from MacroRegistry import registerMacro
from Common import linkAddress, outputDocumentName

class SourceChildren_Macro:
    def expand(self, parameter, remarkConverter):
        document = remarkConverter.document
                
        def prefixOf(left, right):
            return string.find(os.path.splitext(right)[0], os.path.splitext(left)[0]) == 0
        
        def same(left, right):
            return os.path.splitext(left)[0] == os.path.splitext(right)[0]

        # Gather the list of source files.
        
        sortedMap = [x for x in document.childSet.itervalues() if x.extension != '.txt']
        
        if len(sortedMap) == 0:
            return []

        # Sort the list alphabetically w.r.t. the relative file names.
        
        sortedMap.sort(lambda x, y: cmp(x.relativeName, y.relativeName))
     
        # Given an alphabetically sorted list of source files,
        # group all files that have the same name without
        # extension. The group shares the same description.
       
        targetDirectory = document.relativeDirectory
        beginIndex = 0
        groupSet = []
        description = ''
        detail = ''
        for i in range(0, len(sortedMap)):
            document = sortedMap[i]
            reference = sortedMap[beginIndex]
            
            desc = document.tag('description')
            if desc == None: 
                desc = ''
            desc = string.strip(desc)
            if desc != '':
                # If there are multiple descriptions, one is chosen
                # arbitrarily and a warning is emitted.
                if description != '':
                    print 'Warning:', document.relativeName, ': multiple descriptions for a group.'                     
                description = desc

            det = document.tag('detail')
            if det == None: 
                det = ''
            det = string.strip(det)
            if det != '':
                # If there are multiple details, one is chosen
                # arbitrarily and a warning is emitted.
                if detail != '':
                    print 'Warning:', document.relativeName, ': multiple details for a group.'                     
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
                group[0] = 'No description'
        
        # Order the groups in alphabetical order w.r.t.
        # their descriptions. 
        
        groupSet.sort(lambda x, y: cmp(x[0], y[0]))
        
        # Output the links in the groups together
        # with a description for the group. 

        if parameter == []:
            title = '\nFiles'
        else:
            title = parameter[0]
            
        text = [title, '-' * (len(title) - 1) + '\n']
        for group in groupSet:
            # Output description for the group.
            description = group[0]
            detail = group[1]
            text.append('\n### ' + description + '\n')
            if detail != '': 
                text.append('\n_' + detail + '_\n')
                
            # Output the links in the group.
            for child in group[2]:
                #detail = child.tag('detail')
                #if detail != '':
                #    text.append('\n####' + detail + '\n')
                linkDescription = child.fileName
                linkTarget = linkAddress(targetDirectory, child.relativeName)
                text += remarkConverter.remarkLink(linkDescription, outputDocumentName(linkTarget))
                text.append('')
            
        return text

    def outputType(self):
        return 'remark'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        return []                

registerMacro('SourceChildren', SourceChildren_Macro())
