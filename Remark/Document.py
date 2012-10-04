# -*- coding: utf-8 -*-

# Description: Document
# Documentation: data_structures.txt

import os.path
import string

from FileSystem import unixDirectoryName, unixRelativePath, fileExtension
from DocumentType_Registry import documentType

class Document(object):
    def __init__(self, relativeName):
        '''
        Constructs a document-object for the given file.

        relativeName:
        The path to the file, relative to the document-tree's
        root-directory.
        '''

        # The relative-path to the document, with respect to
        # the document-tree's root-directory. It is important
        # that the relative-name is in the unix-form. This is
        # being relied upon elsewhere (e.g. Gallery_Macro
        # creates an md5-digest from the relative-name;
        # this must be portable across operating systems).
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

        # A map from a tag-name (string) to a text 
        # (list of strings).
        self.tagSet = {}

        # The predefined document-tags.
        self.setTag('description')
        self.setTag('detail')
        self.setTag('author')
        self.setTag('file_name', [self.fileName])
        self.setTag('relative_name', [self.relativeName])
        self.setTag('relative_directory', [self.relativeDirectory])
        self.setTag('extension', [self.extension])
        self.setTag('html_head')
        self.setTag('document_type', [self.documentType.name()])
        # This will be filled in later, after the
        # description-tags have been parsed.
        self.setTag('link_description')

        # Whether the document should be generated.
        # By default the document is not generated;
        # the regeneration rules change this later.
        self.regenerate_ = False

    def setRegenerate(self, regenerate):
        self.regenerate_ = regenerate

    def regenerate(self):
        return self.regenerate_

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

    def tagInteger(self, tagName, default = 0):
        '''
        Returns the integer associated with the given tag-name.
        The tag-text is first interpreted as a single string,
        which is then converted to an integer.
        '''
        if not tagName in self.tagSet:
            return default
        return int(self.tagString(tagName))

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

