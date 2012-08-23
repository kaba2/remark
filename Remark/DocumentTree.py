# -*- coding: utf-8 -*-

# Description: Documents and documentation tree
# Detail: Deduction of parent-child relationships and their storage.
# Documentation: core_stuff.txt

import os.path
import string
import re
from Common import documentType, unixDirectoryName, linkAddress, fileExtension

def fileSuffix(relativeName):
    index = string.rfind(relativeName, '.')
    return relativeName[index :]

def filePrefix(relativeName):
    index = string.rfind(relativeName, '.')
    return relativeName[0 : index]

class Document(object):
    def __init__(self, relativeName):
        # Precompute commonly needed names.
        self.relativeName = unixDirectoryName(relativeName)
        self.relativeDirectory, self.fileName = os.path.split(relativeName)
        self.extension = fileExtension(self.fileName).lower()

        self.tagSet = {'description' : '', 
                       'detail' : '',
                       'author' : ''}
        self.parent = None
        self.childSet = dict()
        self.directorySet = set()
        
    def insertChild(self, child):
        if child.parent != None:
            print 'Error: A child was already linked to a parent.'
        self.childSet[child.relativeName] = child
        child.parent = self
        
    def tag(self, name, defaultValue = ''):
        if name in self.tagSet:
            return self.tagSet[name]
        return defaultValue

    def documentType(self):
        return documentType(self.extension)

class DocumentTree(object):
    def __init__(self, rootDirectory, parserLines = 100):
        assert os.path.isdir(rootDirectory)
        
        self.rootDirectory = rootDirectory
        self.root = Document('root')
        self.orphan = Document('orphan.orphan')
        self.orphan.tagSet['description'] = 'Orphans'
        self.documentMap = {'orphan.orphan' : self.orphan}
        self.fileNameMap = {}
        self.parserLines = parserLines
        
    def compute(self):      
        print  
        print 'Gathering directories...',
        self._gatherDirectories();
        print 'Done.'

        print
        print 'Generating index files...',
        self._generateIndexFiles();
        print 'Done.'

        print
        print 'Constructing file-name map...',
        self._constructFileNameMap()
        print 'Done.'

        print
        print 'Parsing tags'
        print '------------'
        self._parseTags()
        print
        print 'Done.'
        
        print
        print 'Resolving explicit links'
        print '------------------------'
        self._resolveExplicitLinks()
        print
        print 'Done.'
        
        print
        print 'Resolving implicit links'
        print '------------------------'
        self._resolveImplicitLinks()
        print
        print 'Done.'
        
        print
        print 'Resolving reference links'
        print '-------------------------'
        self._resolveReferenceLinks()
        print
        print 'Done.'

        print
        print 'Linking orphans...',
        self._linkOrphans()
        print
        print 'Done.'
        
    def insertDocument(self, relativeName):
        document = Document(relativeName)
        self.documentMap[document.relativeName] = document
        return document

    def findDocumentLocal(self, documentName, relativeDirectory):
        '''
        Finds a document corresponding to the given filename 'documentName'.
        The document is only searched in the given relative directory 
        'relativeDirectory'. For example:
        
        documentTree.findDocumentLocal('spam.txt', 'eggs/bar/') 

        See also: findDocumentUpwards().
        '''
        relativeName = unixDirectoryName(
            os.path.join(relativeDirectory, documentName))

        return self.findDocumentByRelativeName(relativeName)

    def findDocumentByRelativeName(self, relativeName):
        '''
        Finds a document corresponding to the given relative name and 
        relative directory.
        Example:
        documentTree.findDocumentLocal('eggs/bar/spam.txt') 
        See also: findDocumentUpwards().
        '''
        #relativeName = unixDirectoryName(relativeName)
        if relativeName in self.documentMap:
            # Found the document file!
            return self.documentMap[relativeName]
        
        # Document file was not found.
        return None

    def findDocumentUpwards(self, documentName, relativeDirectory):
        '''
        Finds a document corresponding to the given filename 'documentName'.
        The search starts from the given relative directory 'relativeDirectory',
        and whenever unsuccessful, is continued outwards to
        parent directories until either the document is found
        or root directory is reached. Example:
        documentTree.findDocumentUpwards('spam.txt', 'eggs/bar/')         
        '''
        #assert os.path.isdir(relativeDirectory)
            
        fileName = os.path.split(documentName)[1]
        if fileName != documentName:
            # This is a relative path: don't
            # search from anywhere else.
            document = self.findDocumentLocal(documentName, relativeDirectory) 
            return document

        while True:
            document = self.findDocumentLocal(documentName, relativeDirectory)
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

    def findDocument(self, documentName, relativeDirectory):
        '''
        Returns: A pair (document, unique), such that 'document'
        contains the found document (possibly None) and
        'unique' is a boolean that tells whether the choice
        was unique or not.
        '''
        
        documentName = unixDirectoryName(documentName)
                
        fileName = os.path.split(documentName)[1]
        if fileName != documentName:
            # This is a relative path: don't
            # search from anywhere else.
            document = self.findDocumentLocal(documentName, relativeDirectory)
            if document != None:
                # Check whether this search could have been equivalently
                # been done with a pure filename.
                (checkDocument, checkUnique) = \
                    self.findDocument(fileName, relativeDirectory)
                if checkDocument == document and checkUnique:
                    print
                    print ('Warning: Used relative form ' + documentName + 
                           ' where pure form ' + fileName + 
                           ' is unambiguous.')
            return (document, True)
        
        #print '"', fileName, '"'
         
        # See if there is a document of such name at all.
        if not fileName in self.fileNameMap:
            return (None, True)
             
        documentSet = self.fileNameMap[fileName]
        
        if len(documentSet) == 1:
            # There is a unique document with this
            # filename. Return it.
            return (documentSet[0], True)
        
        # There are multiple files with this filename.
        # Priority is given in the following order:
        # 1) Current directory
        # 2) Parent directories
        # 3) Other directories
        
        document = self.findDocumentUpwards(documentName, relativeDirectory)
        if document != None:
            return (document, True)
            
        # Return an arbitrary file.
        return (documentSet[0], False)

    # Private stuff
    
    def _fullName(self, relativeName):
        return os.path.normpath(os.path.join(self.rootDirectory, relativeName))

    def _gatherDirectories(self):
        # Gather the set of directories in which the files reside at
        # (and their parent directories).
        directorySet = set()
        for document in self.documentMap.itervalues():
            directory = document.relativeDirectory
            while True:
                directorySet.add(directory)
                newDirectory = os.path.normpath(os.path.split(directory)[0])
                if newDirectory == directory:
                    break
                directory = newDirectory
        
        self.directorySet = directorySet

    def _generateIndexFiles(self):
        # We wish to generate an index to each directory in the
        # directory tree.
        for directory in self.directorySet:
            relativeName = os.path.join(directory, 'directory.index')
            document = self.insertDocument(relativeName)
            document.tagSet['description'] = unixDirectoryName(document.relativeDirectory) + '/'

    def _parseTags(self):
        '''
        For each document in 'self.documentMap', runs its
        associated parser.
        '''        
        for document in self.documentMap.itervalues():
            try:
                key = fileSuffix(document.relativeName)
                type = documentType(key)
                if type != None:
                    tagSet = type.parseTags(self._fullName(document.relativeName), self.parserLines)
                    document.tagSet.update(tagSet)
            except UnicodeDecodeError:
                print 'Warning:', document.relativeName,
                print ': Tag parsing failed because of a unicode decode error.'
            except:
                print 'Warning:', document.relativeName,
                print ': Tag parsing failed for some reason.'
            
    def _resolveExplicitLinks(self):
        '''
        Resolves the parent-child relationships between
        Document objects in those cases where a document file 
        explicitly specifies a parent file using a tag.
        '''
        for document in self.documentMap.itervalues():
            # Documents which are not associated to a document
            # type are linked to orphan straight away.
            if documentType(document.extension) == None:
                document.parent = self.orphan
            # If a document specifies a parent, then this
            # is handled the same whether it is a documentation file
            # or a source file. Simply find the specified parent.
            if 'parent' in document.tagSet:
                # The parent file path in the tag is given relative to 
                # the directory containing the document file.
                parentName = document.tagSet['parent']
                
                parent, unique = self.findDocument(parentName, 
                                                       document.relativeDirectory)
                if not unique:
                    print
                    print 'Warning: parent file is ambiguous for', 
                    print document.relativeName, '. The search was for:', parentName                                     
                if parent == None:
                    # If a parent file can't be found, it can be
                    # because of a typo in the tag or a missing file. 
                    # In any case we warn the user.
                    print
                    print 'Warning: parent file was not found for',
                    print document.relativeName, '. The search was for:', parentName
                else:
                    # Parent file was found. Update parent-child
                    # pointers.
                    parent.insertChild(document)
            elif 'parentOf' in document.tagSet:
                # This file uses a reference link, which will be
                # handled later.
                None     
            elif document.extension == '.txt':
                # This file is a documentation file and it is
                # missing a parent tag. Warn about that.
                print
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
            # The implicit linking is done only when
            # a file does not have a parent and
            # does not use reference linking.
            if document.parent != None or 'parentOf' in document.tagSet:
                continue
            
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
        
    def _resolveReferenceLinks(self):
        '''
        Resolves the parent-child relationships between
        Document objects in those cases where a document file 
        specifies a parent file as the parent file of 
        another file. 
        '''
        for document in self.documentMap.itervalues():
            # Reference linking is done only when no parent has been
            # found through explicit or implicit linking, and
            # a reference link has been specified.
            if document.parent != None or 'parentOf' not in document.tagSet:
                continue
            
            # The parent file path in the tag is given relative to 
            # the directory containing the document file.
            referenceName = document.tagSet['parentOf']
            
            reference = self.findDocument(referenceName, 
                                               document.relativeDirectory)[0]
            if reference == None:
                # If a reference file can't be found, it can be
                # because of a typo in the tag or a missing file. 
                # In any case we warn the user.
                print
                print 'Warning: reference parent file was not found for',
                print document.relativeName, '. The search was for:', referenceName
            else:
                # Reference file was found. Use
                # its parent as the parent of this document.
                if reference.parent != None:
                    reference.parent.insertChild(document)
                else:
                    print
                    print 'Warning: ', referenceName, ', referenced by ',
                    print document.relativeName, ', does not have an associated parent file.'
                    

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
                
    def _constructFileNameMap(self):
        '''
        Construct a map from filenames to documents.
        There can be multiple documents for a single
        filename and thus the documents are stored
        in a list.
        '''
        for document in self.documentMap.itervalues():
            if document.fileName in self.fileNameMap:
                self.fileNameMap[document.fileName].append(document)
            else:
                self.fileNameMap[document.fileName] = [document]
            
def display(documentTree):
    _display(documentTree, documentTree.root, 0)

def _display(documentTree, document, indentation):
    for i in range(0, indentation):
        print '  ',
    print document.relativeName
    for child in document.childSet.itervalues():
        _display(documentTree, child, indentation + 1)


