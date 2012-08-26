# -*- coding: utf-8 -*-

# Description: Document tree
# Documentation: core_stuff.txt

import os.path
import string
import re
from Common import documentType, unixDirectoryName, unixRelativePath, fileExtension
from Common import globalOptions, withoutFileExtension, strictDocumentType

class Document(object):
    def __init__(self, relativeName):
        '''
        Constructs a document-object for the given file.

        relativeName:
        The path to the file, relative to the document-tree's
        root-directory.
        '''

        # The relative-path to the document, with respect to
        # the document-tree's root-directory.
        self.relativeName = unixDirectoryName(relativeName)

        # The relative-directory and the filename of the document.
        self.relativeDirectory, self.fileName = os.path.split(relativeName)

        # The file-name extension of this document, in lower-case
        # to enable case-insensitivity.
        self.extension = fileExtension(self.fileName).lower()

        # The document-type of this document.
        self.documentType = documentType(self.extension)

        # The parent-document of this document.
        self.parent = None

        # A map from document's relative-name (string) to a 
        # document-object (Document).
        self.childSet = {}

        # A set of directories (strings). This will contain
        # all the directories in which the documents reside,
        # and also all their parent-directories up to the
        # document-tree's root-directory.
        self.directorySet = set()

        # A map from a tag-name (string) to a text 
        # (list of strings).
        self.tagSet = {}

        # The predefined document-tags.
        self.setTag('description')
        self.setTag('link_description')
        self.setTag('detail')
        self.setTag('author')
        self.setTag('file_name', [self.fileName])
        self.setTag('relative_name', [self.relativeName])
        self.setTag('relative_directory', [self.relativeDirectory])
        self.setTag('extension', [self.extension])
        self.setTag('html_head')

        self.setTag('document_type', [self.documentType.name()])
        
    def insertChild(self, child):
        '''
        Inserts a new child-document for this document.
        A document can be only be linked to at most one 
        parent-document.
        '''
        assert child.parent == None
        self.childSet[child.relativeName] = child
        child.parent = self
    
    def setTag(self, tagName, text = ['']):
        '''
        Associates text with a given tag-name.

        tagName (string):
        The name of the tag. It will be stripped 
        of surrounding whitespace.

        text (list of strings):
        The text to associate to the tag-name.
        '''
        assert isinstance(text, list)
        assert isinstance(tagName, basestring)
        self.tagSet[tagName.strip()] = text
        
    def tag(self, tagName, defaultText = ['']):
        '''
        Returns the text associated with the given
        tag-name. If the tag-name is not found, returns
        the given default-value instead.
        
        tagName (string):
        The tag-name to find. It will be stripped of
        surrounding whitespace.
        '''
        assert isinstance(tagName, basestring)
        return self.tagSet.get(tagName.strip(), defaultText)

    def tagString(self, tagName, default = ''):
        '''
        Returns the tag-text associated with the given
        tag-name, such that the lines of the tag-text are
        joined together into a single string.
        '''
        return ''.join(self.tag(tagName, [default]))

    def linkDescription(self):
        '''
        Returns the link-description of the document.

        returns:
        The link-description given by the document-type,
        if the document has a document-type. Otherwise
        the empty string.
        '''
        type = self.documentType
        if type == None:
            return ''
        
        return self.documentType.linkDescription(self)

class DocumentTree(object):
    def __init__(self, rootDirectory):
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
        assert os.path.isdir(rootDirectory)
        
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
        self.fileNameMap = {}
        
    def insertDocument(self, relativeName):
        '''
        Inserts a document into the document-tree.

        relativeName:
        The relative path to the document w.r.t. to the
        root directory of the document-tree.
        '''
        document = Document(relativeName)
        self.documentMap[document.relativeName] = document
        return document

    def compute(self):
        '''
        Computes the document-tree starting from the root-directory
        The documents have to be already inserted into it for this
        to do anything.

        See also:
        insertDocument()
        '''

        # Gather directories

        if globalOptions().verbose:
            print  
            print 'Gathering directories...',
        self._gatherDirectories();
        if globalOptions().verbose:
            print 'Done.'

        # Insert virtual documents.

        if globalOptions().verbose:
            print
            print 'Inserting virtual documents...',
        self._insertVirtualDocuments();
        if globalOptions().verbose:
            print 'Done.'

        # Construct file-name map.

        if globalOptions().verbose:
            print
            print 'Constructing file-name map...',
        self._constructFileNameMap()
        if globalOptions().verbose:
            print 'Done.'

        # Parse the tags.

        if globalOptions().verbose:
            print
            print 'Parsing tags'
            print '------------'
        self._parseTags()
        if globalOptions().verbose:
            print
            print 'Done.'
        
        # Resolve explicit links

        if globalOptions().verbose:
            print
            print 'Resolving explicit links'
            print '------------------------'
        self._resolveExplicitLinks()
        if globalOptions().verbose:
            print
            print 'Done.'

        # Resolve implicit links
        
        if globalOptions().verbose:
            print
            print 'Resolving implicit links'
            print '------------------------'
        self._resolveImplicitLinks()
        if globalOptions().verbose:
            print
            print 'Done.'

        # Resolve reference links
        
        if globalOptions().verbose:
            print
            print 'Resolving reference links'
            print '-------------------------'
        self._resolveReferenceLinks()
        if globalOptions().verbose:
            print
            print 'Done.'

        # Link orphans

        if globalOptions().verbose:
            print
            print 'Linking orphans...',
        self._linkOrphans()
        if globalOptions().verbose:
            print
            print 'Done.'
        
    def findDocumentLocal(self, fileName, relativeDirectory):
        '''
        Finds a document corresponding to the given filename.
        If the document is not found, returns None.
        The document is only searched in the given relative 
        directory.
        
        Example:
        documentTree.findDocumentLocal('spam.txt', 'eggs/bar/') 

        See also: 
        findDocumentUpwards().
        '''
        relativeName = unixDirectoryName(
            os.path.join(relativeDirectory, fileName))

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

        Example:
        documentTree.findDocumentByRelativeName('eggs/bar/spam.txt') 
       
        See also: 
        findDocumentUpwards().
        '''
        return self.documentMap.get(relativeName)

    def findDocumentUpwards(self, documentName, relativeDirectory):
        '''
        Searches for a document corresponding to the given document-name
        starting from the given relative-directory and progressing 
        to the parent-directories on unsuccessful searches. The search
        terminates on the document-tree's root directory. If the 
        document-name is a relative-path, no parent-directories will
        be searched.

        documentName:
        The name of the file to search for. It can be either be a 
        file-name, or a relative-path.

        relativeDirectory:
        The directory from which to start searching, relative to 
        the document-tree root-directory.        

        returns:
        The document-object if successful, None otherwise.
        
        Example:
        documentTree.findDocumentUpwards('spam.txt', 'eggs/bar/')         
        '''

        assert (relativeDirectory.strip() == '' or
                os.path.isdir(relativeDirectory))
            
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
        Searches for a document corresponding to the given document-name
        first from the given relative-directory upwards, and if not 
        successful, then from all of the document-tree (then the
        document can be ambiguous). If the document-name is a 
        relative-path, no other directories will be searched.

        documentName:
        The name of the file to search for. It can be either a 
        file-name, or a path relative to the document-tree root-directory.

        relativeDirectory:
        The directory from which to start searching, relative to 
        the document-tree root-directory.        

        returns: 
        A pair (document, unique), such that 'document' contains the 
        found document-object (possibly None) and 'unique' is a 
        boolean that tells whether the choice was unique or not.
        If the choise is not unique, the document is picked arbitrarily
        over the choices.
        '''
        
        documentName = unixDirectoryName(documentName)
                
        # Handle the relative-path case first.
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
                           ' would have been unambiguous.')
            return (document, True)

        # Since the document-name is not a relative-path,
        # it is a filename.        
               
        # Search the filename over all of the document-tree.         
        # Doing the search here is a different order compared to
        # the function description. However, we only return a
        # found document here if it is unique, or there is no
        # such filename at all. This improves performance, since 
        # it is just a dictionary lookup. Moreover, having unique
        # filenames over the document tree is the normal case,
        # so this is a relevant optimization.
        documentSet = self.fileNameMap.get(fileName)
        
        if documentSet == None:
            # There is no such filename in the document-tree.
            return (None, True)

        if len(documentSet) == 1:
            # There is a unique document with this
            # filename. Return it.
            return (documentSet[0], True)
        
        # There are multiple files with this filename.

        # See if the document can be found by following
        # parent-directories.
        document = self.findDocumentUpwards(documentName, relativeDirectory)
        if document != None:
            # The document was found by following
            # parent-directories.
            return (document, True)
            
        # The document is somewhere on the document-tree,
        # is ambiguous, and can not be found by
        # following parent-directories.

        # Return an arbitrary file.
        return (documentSet[0], False)

    def fullName(self, document):
        '''
        Returns the join of the document-tree's root directory
        and the relative-name of the document.
        '''
        return os.path.normpath(os.path.join(self.rootDirectory, document.relativeName))

    # Private stuff
    
    def _gatherDirectories(self):
        '''
        Gathers the set of directories in which the files reside at
        (and their parent directories).
        '''
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

    def _insertVirtualDocuments(self):
        ''' 
        Generates a directory.remark-index virtual document to each
        directory. This provides the directory listings.
        '''
        for directory in self.directorySet:
            # Form the relative name of the document.
            relativeName = os.path.join(directory, 'directory.remark-index')
            
            # Insert a document with that relative name.
            document = self.insertDocument(relativeName)
            
            # Give the document the description from the unix-style
            # directory name combined with a '/' to differentiate 
            # visually that it is a directory.
            description = unixDirectoryName(document.relativeDirectory) + '/'

            # Add the description to the document.
            document.setTag('description', [description])

    def _parseTags(self):
        '''
        For each document in 'self.documentMap', runs its
        associated tag-parser.
        '''        
        for document in self.documentMap.itervalues():
            try:
                key = fileExtension(document.relativeName)
                type = documentType(key)
                tagSet = type.parseTags(self.fullName(document))
                document.tagSet.update(tagSet)
                
                #print
                #print document.relativeName + ':'
                #for tagName, tagText in tagSet.iteritems():
                #    print tagName, ':', tagText

            except UnicodeDecodeError:
                print 'Warning:', document.relativeName,
                print ': Tag parsing failed because of a unicode decode error.'
            
    def _resolveExplicitLinks(self):
        '''
        Resolves the parent-child relationships between
        Document objects in those cases where a document file 
        explicitly specifies a parent file using a tag.
        '''
        for document in self.documentMap.itervalues():
            # Documents which are not associated to a document
            # type are linked to orphan straight away.
            if strictDocumentType(document.extension) == None:
                document.parent = self.orphan

            # See if the document specifies a parent document.
            if 'parent' in document.tagSet:
                # The parent file path in the tag is given relative to 
                # the directory containing the document file.
                parentName = document.tagString('parent')
                
                # See if we can find the parent document.
                parent, unique = self.findDocument(parentName, 
                                                   document.relativeDirectory)
                if not unique:
                    print
                    print 'Warning: parent is ambiguous for', 
                    print document.relativeName, '. The search was for:', parentName                                     

                if parent == None:
                    # If a parent file can't be found, it can be
                    # because of a typo in the tag or a missing file. 
                    # In any case we warn the user.
                    print
                    print 'Warning: parent was not found for',
                    print document.relativeName, '. The search was for:', parentName
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
                            #print 'Candidate', thatDocument.relativeName
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
            referenceName = document.tagString('parentOf')
            
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
        in a list for each filename.
        '''
        for document in self.documentMap.itervalues():
            if document.fileName in self.fileNameMap:
                self.fileNameMap[document.fileName].append(document)
            else:
                self.fileNameMap[document.fileName] = [document]
            
