# -*- coding: utf-8 -*-

# Description: Caching for the document-tree
# Documentation: data_structures.txt

import os
from FileSystem import readFile, pathExists
from xml.etree import ElementTree
from xml.dom import minidom

class Cache_Document(object):
    def __init__(self, document):
        self.document = document
        self.parent = None
        self.tagSet = {}
        self.incomingSet = set()
        self.outgoingSet = set()
        self.dependencySet = set()

class Cache_DocumentTree(object):
    def __init__(self):
        self.documentMap = {}

    def __contains__(self, document):
        return document in self.documentMap

    def __iter__(self):
        return self.documentMap.itervalues()

    def add(self, document):
        self.documentMap[document] = Cache_Document(document)
        return self.documentMap[document]

    def cacheDocument(self, document):
        return self.documentMap.get(document)

def createCache(documentTree):
    '''
    Returns the document-tree in xml.

    returns (a list of strings):
    The document-tree in xml, row by row.
    '''
    xml = ElementTree.TreeBuilder()

    xml.start('remark', {})
    for document in documentTree:
        xml.start('document', {'name' : document.relativeName})
            
        xml.start('links_to', {})
        for dependency in document.dependencySet:
            propertyMap = {}
            if dependency[1] != document.relativeName:
                propertyMap['directory'] = dependency[1]
            if dependency[2] != 'search':
                propertyMap['type'] = dependency[2]
            xml.start('name', propertyMap)
            xml.data(dependency[0])
            xml.end('name')
        xml.end('links_to')

        xml.start('tags', {})
        for tagName, tagText in document.tagSet.iteritems():
            xml.start('tag', {'name' : tagName})
            xml.data('\n'.join(tagText))
            xml.end('tag')
        xml.end('tags')

        xml.end('document')

    xml.end('remark')

    root = xml.close()

    # Convert the element-tree to an xml-string.
    uglyText = ElementTree.tostring(root, 'utf-8')

    # Make the xml pretty.
    reparsed = minidom.parseString(uglyText)
    prettyText = reparsed.toprettyxml(encoding = 'utf-8')
        
    # Convert to a list-of-strings form.
    return prettyText.split('\n')

def readCache(filePath, documentTree):
    cacheDocumentTree = Cache_DocumentTree()

    # Form the full path to the cache file.
    if not pathExists(filePath):
        return cacheDocumentTree

    # Read the document-tree cache xml-file.
    cacheText = readFile(filePath, ignoreLargeFiles = False)

    # For each document element...
    remarkElement = ElementTree.fromstringlist(cacheText)
    for documentElement in remarkElement.iter('document'):

        # Get the relative-name of the document.
        relativeName = documentElement.get('name')

        # Find the corresponding document.
        document = documentTree.findDocumentByRelativeName(relativeName)
        if document == None:
            # The document does not exist anymore. In this
            # case we do not create a cache document either.
            continue

        # Create a new cache-document for this document.
        cacheDocument = cacheDocumentTree.add(document)

        # For each tags element...
        for tagsElement in documentElement.iter('tags'):

            # For each tag element...
            for tagElement in tagsElement.iter('tag'):

                # Get the tag-name.
                tagName = tagElement.get('name')

                # Get the tag-text.
                tagText = tagElement.text

                # Add the tag to the cache if it has some text.
                if tagText != None:
                    cacheDocument.tagSet[tagName] = tagText.split('\n')

        # Find the cached parent document.
        if 'parent' in cacheDocument.tagSet:
            cacheDocument.parent = documentTree.findDocumentByRelativeName(''.join(cacheDocument.tagSet['parent']))

    for documentElement in remarkElement.getchildren():

        # Get the relative-name of the document.
        relativeName = documentElement.get('name')

        # Find the corresponding document.
        document = documentTree.findDocumentByRelativeName(relativeName)
        if document == None:
            continue

        cacheDocument = cacheDocumentTree.cacheDocument(document)
        assert cacheDocument != None

        # For each links-to element...
        for linksToElement in documentElement.iter('links_to'):

            # For each name element...
            for name in linksToElement.iter('name'):
                
                # Get the search path.
                searchPath = name.text

                # Get the search directory.
                searchDirectory = name.get('directory', document.relativeDirectory)

                # Get the search type.
                searchType = name.get('type', 'search')
                
                cacheDocument.dependencySet.add((searchPath, searchDirectory, searchType))

                # Find the corresponding document.
                toDocument = None
                if searchType == 'search':
                    toDocument, unique = documentTree.findDocument(searchPath, searchDirectory, False)
                elif searchType == 'exact':
                    toDocument = documentTree.findDocumentLocal(searchPath, searchDirectory)
                
                if toDocument == None:
                    # The target document does not exist anymore.
                    continue

                # Find the corresponding cache-document.
                toCacheDocument = cacheDocumentTree.cacheDocument(toDocument)
                
                # Add the dependencies.
                if toCacheDocument != None:
                    #print document.relativeName, '-->', toDocument.relativeName
                    toCacheDocument.incomingSet.add(document)
                    cacheDocument.outgoingSet.add(toDocument)
        
    return cacheDocumentTree


