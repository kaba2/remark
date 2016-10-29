# -*- coding: utf-8 -*-

# Description: Document tree
# Documentation: data_structures.txt

from __future__ import print_function

import re
import os.path
import string

from Remark.DocumentType_Registry import documentType, strictDocumentType
from Remark.FileSystem import unixDirectoryName, unixRelativePath, fileExtension
from Remark.FileSystem import globalOptions, withoutFileExtension
from Remark.FileSystem import pathSuffixSet, globToRegex, directoryExists, findMatchingFiles
from Remark.Reporting import Reporter, ScopeGuard
from Remark.Document import Document

class DocumentTree(object):
    def __init__(self, rootDirectory, reporter = Reporter()):
        '''
        Constructs an empty document-tree using the 
        given directory as a root-directory.

        rootDirectory (string):
        The full-path to the directory to use as
        root-directory of the document-tree.

        See also:
        compute()
        insertDocument()
        '''

        # The root-directory whose child-directories
        # to construct the document-tree for.
        self.rootDirectory = rootDirectory

        # Create the orphan document, to which all the
        # unlinked documents will be given as children.
        self.orphan = Document('orphan.remark-orphan')
        self.orphan.setTag('description', ['Orphans'])

        # A map from a document's relative-name (string) to 
        # a document-object (Document).
        self.documentMap = {'orphan.remark-orphan' : self.orphan}

        # A map from a filename (string) to documents
        # with that filename (list of Document's).
        self.suffixMap = {}

        # A map from a directory (string) to a use-count (integer). 
        # The keys will contain all the directories in which the documents 
        # reside, and also all their parent-directories up to the
        # document-tree's root-directory. The value will contain the number
        # of documents that have generated the directory in the key.
        # The use-count allows us to dynamically track the directories
        # as documents are inserted and removed.
        self.directorySet = {}

        # A reporter object (Reporter).
        self.reporter = reporter

    def __iter__(self):
        return iter(self.documentMap.values())
        
    def insertDocument(self, relativeName):
        '''
        Inserts a document into the document-tree.

        relativeName:
        The relative path to the document w.r.t. to the
        root directory of the document-tree.
        '''
        document = Document(relativeName)
        self.documentMap[document.relativeName] = document

        # Add the suffixes of the relative-name into the suffix-map.
        suffixSet = pathSuffixSet(relativeName)
        for suffix in suffixSet:
            if suffix in self.suffixMap:
                self.suffixMap[suffix].append(document)
            else:
                self.suffixMap[suffix] = [document]

        # Gather the directory of the file, and the
        # parent directories of that directory.
        directory = document.relativeDirectory
        while True:
            if not directory in self.directorySet:
                self.directorySet[directory] = 1
            else:
                self.directorySet[directory] += 1

            newDirectory = os.path.normpath(os.path.split(directory)[0])
            if newDirectory == directory:
                break
            directory = newDirectory

        return document

    def resolveParentLinks(self):
        '''
        Resolves explicit, implicit, and reference parent links.
        Those documents which remain without a parent are linked to 
        the orphan document.

        See also:
        insertDocument()
        '''

        # Resolve explicit links

        with ScopeGuard(self.reporter, 'Resolving explicit links'):
            self._resolveExplicitLinks()
            self.reporter.report([None, 'Done.', None], 'verbose')

        # Resolve implicit links
        
        with ScopeGuard(self.reporter, 'Resolving implicit links'):
            self._resolveImplicitLinks()
            self.reporter.report([None, 'Done.', None], 'verbose')

        # Resolve reference links
        
        with ScopeGuard(self.reporter, 'Resolving reference links'):
            self._resolveReferenceLinks()
            self.reporter.report([None, 'Done.', None], 'verbose')

        # Link orphans

        #with ScopeGuard(self.reporter, 'Linking orphans'):
        self._linkOrphans()
        #self.reporter.report([None, 'Done.', None], 'verbose')
        
    def findDocumentLocal(self, filePath, searchDirectory):
        '''
        Searches for a document corresponding to the given 
        file path in the given search directory.

        filePath:
        A relative-path to the file, relative to
        the given search-directory.

        searchDirectory:
        A relative-path to the search-directory, relative to
        the document-tree root directory.

        returns:
        If the document is found, the document object.
        Otherwise None.
        
        See also: 
        findDocumentUpwards().
        '''
        relativeName = unixDirectoryName(
            os.path.join(searchDirectory, filePath))

        return self.findDocumentByRelativeName(relativeName)

    def findDocumentByRelativeName(self, relativeName):
        '''
        Searches for a document by relative-name in all of the 
        document-tree.

        relativeName:
        The path to the document file, relative to the 
        document-tree's root directory.
        
        returns:
        The document-object if found, None otherwise.

        See also: 
        findDocumentUpwards().
        '''
        return self.documentMap.get(relativeName)

    def findDocumentUpwards(self, filePath, searchDirectory):
        '''
        Searches for a document corresponding to the given file path
        starting from the given search-directory and progressing 
        to the parent-directories on unsuccessful searches. The search
        terminates on the document-tree's root directory. 

        filePath:
        A relative-path to the file to search for, relative to the
        current search-directory (which changes during the algorithm).

        searchDirectory:
        A relative-path to the directory from which to start searching,
        relative to the document-tree root-directory.        

        returns:
        The document-object if successful, None otherwise.
        '''

        while True:
            document = self.findDocumentLocal(filePath, searchDirectory)
            if document != None:
                return document
            
            # Document file was not found, try the parent directory.
            parentDirectory = os.path.normpath(os.path.split(searchDirectory)[0])
            if parentDirectory == searchDirectory:
                # We are at the root, stop here.
                break
            searchDirectory = parentDirectory
        
        # Document file was not found.
        return None                           

    def findDocument(self, filePath, searchDirectory, checkShorter = True):
        '''
        Searches for a document corresponding to the given file path
        first from the given search-directory upwards, and if not 
        successful, then from all of the document-tree (then the
        document can be ambiguous). 

        filePath:
        A relative-path to the file to search for, relative to the
        current search-directory (which changes during the algorithm). 

        searchDirectory:
        The directory from which to start searching, relative to 
        the document-tree root-directory.        

        returns: 
        A pair (document, unique), such that 'document' contains the 
        found document-object (possibly None) and 'unique' is a 
        boolean that tells whether the choice was unique or not.
        If the choise is not unique, the document is picked arbitrarily
        over the choices.
        '''
        
        document = None
        unique = True
        documentSet = []

        filePath = unixDirectoryName(filePath)

        # Search the document by following parent-directories.
        document = self.findDocumentUpwards(filePath, searchDirectory)
        if document != None:
            # The document was found by following parent-directories.
            # Add the document to the found-set.
            documentSet.append(document)
        else:
            # The document could be found at any directory
            # of the document-tree. Find out if the file-path
            # is a path-suffix of any document's relative-name.
            documentSet = self.suffixMap.get(filePath, [])

        if len(documentSet) == 0:
            # There is no such matching path-suffix of a relative-name 
            # in the document-tree. It may still be that the file-path is 
            # a relative path which contains .. parent-references. 
            # Consider that a parent-reference .. has a directory A 
            # on its left-hand side; then the A and .. can be removed
            # without affecting the path (unixDirectoryName does
            # this). Therefore what we would have is a kind of 
            # relative-path which has n parent-references at the 
            # start, and then normal directories. At this point
            # we don't find it useful to search such relative-paths
            # over all document-tree directories.
            unique = True
        elif len(documentSet) == 1:
            # There is a unique document whose suffix of the
            # relative-name matches the file-path.
            document = documentSet[0]
            unique = True

            if checkShorter:
                # Check whether this search could have been equivalently
                # done with a shorter path-suffix.
                shortestSuffix = ''
                n = len(filePath)
                i = 0
                while i < n:
                    if filePath[i] == '/':
                        suffix = filePath[i + 1 : ]
                        checkDocument, checkUnique = \
                            self.findDocument(suffix, searchDirectory, False)
                        if checkDocument == document and checkUnique:
                            shortestSuffix = suffix
                        else:
                            break
                    i += 1
            
                if shortestSuffix != '':
                    # A shorter path-suffix would have sufficed.
                    self.reporter.reportWarning('Used path ' + filePath + 
                           ' where a shorter path ' + shortestSuffix + 
                           ' would have been unambiguous.',
                           'redundant-path')
        else:
            # There are multiple files whose suffix of the
            # relative-name matches the file-path.
            # Return an arbitrary file.
            document = documentSet[0]
            unique = False

        return (document, unique)

    def fullName(self, document):
        '''
        Returns the join of the document-tree's root directory
        and the relative-name of the document.
        '''
        return os.path.normpath(os.path.join(self.rootDirectory, document.relativeName))

    # Private stuff
    
    def _resolveExplicitLinks(self):
        '''
        Resolves the parent-child relationships between
        Document objects in those cases where a document file 
        explicitly specifies a parent file using a tag.
        '''
        for document in self.documentMap.values():
            # Documents which are not associated to a document
            # type are linked to orphan straight away.
            if strictDocumentType(document.extension) == None:
                document.parent = self.orphan

            # See if the document specifies a parent document.
            if 'parent' in document.tagSet:
                # The parent file path in the tag is given relative to 
                # the directory containing the document file.
                parentName = document.tagString('parent').strip()
                
                # See if we can find the parent document.
                parent, unique = self.findDocument(parentName, 
                                                   document.relativeDirectory)
                if not unique:
                    self.reporter.reportWarning('Parent "' + parentName + '" is ambiguous for ' + 
                                            document.relativeName + '.',
                                            'ambiguous-parent')

                if parent == None:
                    if parentName != '':
                        # If a parent file can't be found, it can be
                        # because of a typo in the tag or a missing file. 
                        # In any case we warn the user.
                        self.reporter.reportWarning('Parent "' + parentName + '" was not found for ' + 
                                               document.relativeName + '.',
                                               'missing-parent')
                else:
                    # Parent file was found. Update parent-child pointers.
                    parent.insertChild(document)
            elif 'parentOf' in document.tagSet:
                # This file uses a reference link, which will be
                # handled later.
                None     
            elif document.documentType.name() == 'RemarkPage':
                # This file is a documentation file and it is
                # missing a parent tag. Warn about that.
                self.reporter.reportWarning(document.relativeName + 
                                       ' does not specify a parent file.',
                                       'unspecified-parent')
    
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
        
        sortedMap = []
        for document in self.documentMap.items():
            sortedMap.append(document[1])
        sortedMap.sort(key = lambda x: x.relativeName)
        
        #for document in sortedMap:
        #    print(document.fileName)
        
        for i in range(0, len(sortedMap)):
            document = sortedMap[i]
            # The implicit linking is done only when
            # a file does not have a parent and
            # does not use reference linking.
            if document.parent != None or 'parentOf' in document.tagSet:
                continue
            
            self.reporter.report(
                'Implicit linking for ' + document.relativeName + ' ...', 
                'debug-implicit')

            searchDirectory = document.relativeDirectory
            searchName = withoutFileExtension(document.fileName)
            # The implicit linking only concerns
            # source files. 
            if document.tagString('document_type') != 'RemarkPage':
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
                    thatName = withoutFileExtension(thatDocument.fileName)
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
                        thatName = withoutFileExtension(thatDocument.fileName)
                        if searchName.startswith(thatName):
                            # If we have already found a match,
                            # and we find a candidate which
                            # is shorter than our existing match,
                            # we can stop the search.
                            if matchesFound > 0 and len(thatName) < matchLength:
                                break
            
                            # Either the file must be a documentation file
                            # or it must have a parent.                                
                            #print('Candidate', thatDocument.relativeName)
                            if thatDocument.tagString('document_type') == 'RemarkPage':
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
                        message = ['Ambiguous parent for ' + 
                                   document.relativeName + 
                                   '. Picking arbitrarily from:']
                        for match in sourceMatches:
                            message.append(match.relativeName)

                        self.reporter.reportWarning(message, 'ambiguous-parent')
                    newParent = sourceMatches.pop()
                    newParent.insertChild(document)                              
                
            if document.parent != None:
                self.reporter.report(
                    'Found ' + document.parent.relativeName + '.', 
                    'debug-implicit')
        
    def _resolveReferenceLinks(self):
        '''
        Resolves the parent-child relationships between
        Document objects in those cases where a document file 
        specifies a parent file as the parent file of 
        another file. 
        '''
        for document in self.documentMap.values():
            # Reference linking is done only when no parent has been
            # found through explicit or implicit linking, and
            # a reference link has been specified.
            if document.parent != None or not ('parentOf' in document.tagSet):
                continue
            
            # The parent file path in the tag is given relative to 
            # the directory containing the document file.
            referenceName = document.tagString('parentOf')
          
            reference, unique = self.findDocument(referenceName, 
                                                  document.relativeDirectory)
            if reference == None:
                # If a reference file can't be found, it can be
                # because of a typo in the tag or a missing file. 
                # In any case we warn the user.
                self.reporter.reportWarning('Reference parent file was not found for ' + 
                                       document.relativeName + '. The search was for: ' + 
                                       referenceName,
                                       'missing-parent')
            else:
                # Reference file was found. Use
                # its parent as the parent of this document.
                if reference.parent != None:
                    reference.parent.insertChild(document)
                else:
                    self.reporter.reportWarning(referenceName + ', referenced by ' +
                                           document.relativeName + 
                                           ', does not have an associated parent file.',
                                           'unspecified-parent')
                    

    def _linkOrphans(self):
        '''
        Links all documents without a parent
        as children of the root document. This
        turns the graph induced by parent-child
        relationships into a tree.
        '''
        for document in self.documentMap.values():
            if document.parent == None:
                self.orphan.insertChild(document)

def createDocumentTree(argumentSet, reporter):
    '''
    Inserts all matching files in the directory into the document tree.
    A file matches if it matches an include glob, and does not match
    an exclude glob.

    Also creates a directory.index document to each directory.

    argumentSet (ArgumentSet):
    A structure object containing the following
    fields.

    ArgumentSet
    -----------

    inputDirectory (string):
    The directory from which to insert files into the document tree.

    outputDirectory (string):
    The directory to which to converted files will be placed.

    includeSet (iterable of glob strings):
    A set of glob strings each defining a set of 
    relative-names of files to include. These names are
    relative to the include directory.

    excludeSet (iterable of glob strings):
    A set of glob strings each defining a set of 
    relative-names of files to exclude. These names are
    relative to the include directory. Exclusion has 
    priority over inclusion.

    disableSet (iterable of strings):
    A set of warning-types that should not be reported.

    maxTagLines (integer):
    The maximum number of lines to scan for tags.

    maxFileSize (integer):
    The maximum file size to convert. This limit is
    useful when a directory contains a large matching 
    file which actually shouldn't be part of the
    documentation.

    strict (boolean):
    Whether warnings should be treated as errors.

    verbose (boolean):
    Whether additional information should be reported.

    extensions (boolean):
    Whether to report the extensions in the input directory.

    returns (DocumentTree):
    The created document tree.
    '''

    if not directoryExists(argumentSet.inputDirectory):
        reporter.reportError('Input directory ' + argumentSet.inputDirectory + ' does not exist.',
                             'invalid-input')
        return None

    # Construct an empty document-tree for the input directory.
    documentTree = DocumentTree(argumentSet.inputDirectory, reporter)

    # Find the matching files.
    relativeNameSet = findMatchingFiles(argumentSet.inputDirectory, 
        argumentSet.includeSet, argumentSet.excludeSet)

    # Add the matching files into the document tree.
    for relativeName in relativeNameSet:
        documentTree.insertDocument(relativeName)

    # Generate a directory.remark-index virtual document to each
    # directory. This provides the directory listings.
    for directory in documentTree.directorySet:
        # Form the relative name of the document.
        relativeName = os.path.join(directory, 'directory.remark-index')
            
        # Insert a document with that relative name.
        document = documentTree.insertDocument(relativeName)
            
        # Give the document the description from the unix-style
        # directory name combined with a '/' to differentiate 
        # visually that it is a directory.
        description = unixDirectoryName(document.relativeDirectory) + '/'

        # Add the description to the document.
        document.setTag('description', [description])

    return documentTree
