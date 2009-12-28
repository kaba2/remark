# Description: Documents and documentation tree
# Detail: Deduction of parent-child relationships and their storage.
# Documentation: implementation.txt

import os.path
import string
import re

def fileSuffix(relativeName):
    index = string.rfind(relativeName, '.')
    return relativeName[index :]

def filePrefix(relativeName):
    index = string.rfind(relativeName, '.')
    return relativeName[0 : index]

class Document:
    def __init__(self, relativeName, fullName):
        self.fullName = os.path.normpath(fullName)
        self.relativeName = os.path.normpath(relativeName)
        self.relativeDirectory, self.fileName = os.path.split(relativeName)
        self.relativeDirectory = os.path.normpath(self.relativeDirectory)
        self.extension = os.path.splitext(self.fileName)[1]
        self.tagSet = dict({'description' : '', 'detail' : ''})
        self.parent = None
        self.childSet = dict()
        self.visible = True
        
    def insertChild(self, child):
        if child.parent != None:
            print 'Error: A child was already linked to a parent.'
        self.childSet[child.relativeName] = child
        child.parent = self
        
    def tag(self, name):
        if name in self.tagSet:
            return self.tagSet[name]
        return ''

class DocumentTree:
    def __init__(self, rootDirectory, parserMap):
        assert os.path.isdir(rootDirectory)
        
        self.rootDirectory = os.path.normpath(rootDirectory)
        self.root = Document('root', 'root')
        self.orphan = Document('orphan.orphan', 'orphan.orphan')
        self.documentMap = dict({'orphan.orphan' : self.orphan})

        print '\nGathering files...',
        self._gatherFiles(parserMap)
        print 'Done.'
        
        print '\nParsing tags'
        print '------------\n'
        self._parseTags(parserMap)
        print 'Done.'
        
        print '\nResolving explicit links'
        print '------------------------\n'
        self._resolveExplicitLinks()
        print 'Done.'
        
        print '\nResolving implicit links'
        print '------------------------\n'
        self._resolveImplicitLinks()
        print 'Done.'
        
        print '\nLinking orphans...',
        self._linkOrphans()
        print 'Done.'
        
    def insertDocument(self, document):
        self.documentMap[document.relativeName] = document

    def findDocument(self, documentName, relativeDirectory):
        '''
        Finds a document corresponding to the given filename 'documentName'.
        The document is only searched in the given relative directory 
        'relativeDirectory'. Example:
        documentTree.findDocument('spam.txt', 'eggs/bar/') 
        See also: findDocumentOutwards().
        '''
        #assert os.path.isdir(relativeDirectory)
        relativeName = os.path.normpath(os.path.join(relativeDirectory, documentName))
        if relativeName in self.documentMap:
            # Found the document file!
            return self.documentMap[relativeName]
        
        # Document file was not found.
        return None

    def findDocumentByName(self, relativeName):
        '''
        Finds a document corresponding to the given filename and 
        relative directory.
        Example:
        documentTree.findDocument('eggs/bar/spam.txt') 
        See also: findDocumentOutwards().
        '''
        if relativeName in self.documentMap:
            # Found the document file!
            return self.documentMap[relativeName]
        
        # Document file was not found.
        return None

    def findDocumentOutwards(self, documentName, relativeDirectory):
        '''
        Finds a document corresponding to the given filename 'documentName'.
        The search starts from the given relative directory 'relativeDirectory',
        and whenever unsuccessful, is continued outwards to
        parent directories until either the document is found
        or root directory is reached. Example:
        documentTree.findDocumentOutwards('spam.txt', 'eggs/bar/')         
        '''
        #assert os.path.isdir(relativeDirectory)
            
        while True:
            document = self.findDocument(documentName, relativeDirectory)
            if document != None:
                return document
            
            # Document file was not found, try the parent directory.
            parentDirectory = os.path.normpath(os.path.split(relativeDirectory)[0])
            if parentDirectory == relativeDirectory:
                # We are at the root, stop here.
                break
            relativeDirectory = parentDirectory
        
        # Document file was not found.
        return None                           

    # Private stuff
    
    def _fullName(self, relativeName):
        return os.path.normpath(os.path.join(self.path, relativeName))
    
    def _relativeName(self, fullName):
        return os.path.normpath(os.path.relpath(fullName, self.rootDirectory))
    
    def _gatherFiles(self, parserMap):
        '''
        Recursively gathers files starting from the root directory
        that was passed in the constructor. A Document object is created
        for each gathered file and stored in 'self.documentMap', a dictionary
        keyed with the relative file path of the file. Only files with
        a suffix with an associated parser are gathered.
        '''
        for pathName, directorySet, fileNameSet in os.walk(self.rootDirectory):
            for fileName in fileNameSet:
                if fileSuffix(fileName) in parserMap:
                    fullName = os.path.normpath(os.path.join(pathName, fileName))
                    relativeName = self._relativeName(fullName)               
                    self.documentMap[relativeName] = Document(relativeName, fullName)
        
        # Gather the set of directories that in which the files reside at
        # (and their parent directories).
        
        self.directorySet = set()
        for document in self.documentMap.itervalues():
            directory = document.relativeDirectory
            while True:
                self.directorySet.add(directory)
                newDirectory = os.path.normpath(os.path.split(directory)[0])
                if newDirectory == directory:
                    break
                directory = newDirectory
        
    def _parseTags(self, parserMap):
        '''
        For each document in 'self.documentMap', runs its
        associated parser.
        '''        
        for document in self.documentMap.itervalues():
            key = fileSuffix(document.relativeName)
            if key in parserMap:
                parser = parserMap[key]
                parser.parse(document)
            
    def _resolveExplicitLinks(self):
        '''
        Resolves the parent-child relationships between
        Document objects in those cases where a document file 
        explicitly specifies a parent file using a tag.
        '''
        for document in self.documentMap.itervalues():
            # If a document specifies a parent, then this
            # is handled the same whether it is a documentation file
            # or a source file. Simply find the specified parent.
            if 'parent' in document.tagSet:
                # The parent file path in the tag is given relative to 
                # the directory containing the document file.
                parentName = document.tagSet['parent']
                
                parent = self.findDocumentOutwards(parentName, 
                                                   document.relativeDirectory)
                if parent == None:
                    # If a parent file can't be found, it can be
                    # because of a typo in the tag or a missing file. 
                    # In any case we warn the user.
                    print 'Warning: parent file was not found for',
                    print document.relativeName, '. The search was for:', parentName
                else:
                    # Parent file was found. Update parent-child
                    # pointers.
                    parent.insertChild(document)
            elif document.extension == '.txt':
                # This file is a documentation file and it is
                # missing a parent tag. Warn about that.
                print 'Warning:', document.relativeName, 'does not specify a parent file.'
    
    def _resolveImplicitLinks(self):
        '''
        Resolves the parent-child relationships between
        Document objects in those cases where no 
        parent file has been specified explicitly.
        '''
        
        # An implicit parent file can be obtained in two
        # ways:
        # 1) As a documentation file (.txt) whose filename
        #    without the suffix is a prefix of the document's
        #    filename.
        # 2) As the parent of a source file whose filename
        #    without the suffix is a prefix of the document's
        #    filename _and_ whose parent has been specified
        #    explicitly.
        #
        # In this process, lengthier prefixes are favored
        # over shorter ones. Given prefixes of the same length,
        # documentation files (.txt) are favored over source
        # files. The search is restricted to the directory
        # containing the document. The implicit linking only
        # concerns source files. Documentation files (.txt)
        # without an explicit parent emit a warning.

        # Place the documents in an array sorted
        # by their relative file paths. This allows
        # us to find the prefix files. In addition
        # shorter filenames are listed before longer ones.
        
        def documentCompare(left, right):
            return cmp(left.relativeName, right.relativeName)
        
        sortedMap = []
        for document in self.documentMap.iteritems():
            sortedMap.append(document[1])
        sortedMap.sort(documentCompare)
        
        #for document in sortedMap:
        #    print document.fileName
        
        for i in range(0, len(sortedMap)):
            document = sortedMap[i]
            # The implicit linking is done when
            # a file does not explicitly specify
            # a parent.
            if document.parent == None:
                #print 'Implicit find for', document.relativeName
                searchDirectory = document.relativeDirectory
                searchName = filePrefix(document.fileName)
                # The implicit linking only concerns
                # source files. 
                if document.extension != '.txt':
                    # This is a source file.
             
                    # Find the last document in the array
                    # which has identical filename to the searched
                    # one, without considering suffixes.
                    # After doing this, all the candidates are
                    # located at lower indices, and they will
                    # come in shortening order.
                     
                    lastIndex = i + 1
                    while lastIndex < len(sortedMap):
                        thatDocument = sortedMap[lastIndex]
                        thatDirectory = thatDocument.relativeDirectory
                        # The search is restricted to the containing
                        # directory.
                        if thatDirectory != searchDirectory:
                            break
                        thatName = filePrefix(thatDocument.fileName)
                        if thatName != searchName:
                            break
                        lastIndex = lastIndex + 1
 
                    # Visit the documents in the array in decreasing order
                    # (decreasing prefix length).
                    
                    sourceMatches = set()
                    documentationMatches = set()
                    matchLength = 0
                    matchesFound = 0;
 
                    k = lastIndex - 1;
                    while k >= 0:
                        # The document itself is not accepted as
                        # its own parent.
                        if k != i:
                            thatDocument = sortedMap[k]
                            thatDirectory = thatDocument.relativeDirectory
                            # The search is restricted to the containing
                            # directory.
                            if thatDirectory != searchDirectory:
                                break
                            # The filename of the parent document must be a 
                            # prefix of the documents filename, without
                            # suffixes.                            
                            thatName = filePrefix(thatDocument.fileName)
                            if searchName.startswith(thatName):
                                # If we have already found a match,
                                # and we find a candidate which
                                # is shorter than our existing match,
                                # we can stop the search.
                                if matchesFound > 0 and len(thatName) < matchLength:
                                    break

                                # Either the file must be a documentation file
                                # or it must have a parent.                                
                                #print 'Candidate', thatDocument.relativeName
                                if fileSuffix(thatDocument.fileName) == '.txt':
                                    # We have found a match from a documentation
                                    # file! 
                                    documentationMatches.add(thatDocument)
                                    matchesFound = matchesFound + 1
                                    matchLength = len(thatName)
                                    # In this case we are safe to stop because
                                    # there can't be another documentation file
                                    # of the same length, and documentation files
                                    # are favored over source files.
                                    break
                                elif thatDocument.parent != None:
                                    # We have found a match from a source file!
                                    sourceMatches.add(thatDocument.parent)
                                    matchesFound = matchesFound + 1
                                    matchLength = len(thatName)
                                    # We can't stop the search yet. 
                                    # We still have to see what other choices
                                    # there are. For example, it could be
                                    # that there is matching documentation file
                                    # of the same length coming up.
                        # Proceed to the next document in the array.                            
                        k = k - 1
           
                    # See if we found an implicit match.            
                        
                    if len(documentationMatches) > 0:
                        # There is a match from a documentation file.
                        # Documentation files are favored to source files
                        newParent = documentationMatches.pop()
                        newParent.insertChild(document)
                    elif len(sourceMatches) >= 1:
                        # There is a match from a source file.
                        if len(sourceMatches) > 1:
                            print 'Warning: ambiguous parent for',
                            print document.relativeName,
                            print '. Picking arbitrarily from:'
                            for match in sourceMatches:
                                print match.relativeName
                        newParent = sourceMatches.pop()
                        newParent.insertChild(document)                              
                    
                #if document.parent != None:
                #    print document.relativeName, '->', document.parent.relativeName
        
    def _linkOrphans(self):
        '''
        Links all documents without a parent
        as children of the root document. This
        turns the graph induced by parent-child
        relationships into a tree.
        '''
        for document in self.documentMap.itervalues():
            if document.parent == None:
                self.orphan.insertChild(document)
            
def display(documentTree):
    _display(documentTree, documentTree.root, 0)

def _display(documentTree, document, indentation):
    for i in range(0, indentation):
        print '  ',
    print document.relativeName
    for child in document.childSet.itervalues():
        _display(documentTree, child, indentation + 1)


