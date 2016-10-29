# -*- coding: utf-8 -*-

# Description: Document type registry
# Documentation: data_structures.txt

from Remark.FileSystem import fileExtension, unixDirectoryName
import six

_associationSet = dict()
_defaultDocumentType = None
_documentTypeSet = dict()

def setDefaultDocumentType(documentType):
    '''
    Sets the default document-type.

    This document-type will be returned by documentType()
    in case an associated document-type can not be found.

    documentType (DocumentType or string):
    The document-type object to use as a default 
    document-type.

    See also:
    documentType()
    '''
    if isinstance(documentType, six.string_types):
        documentType = findDocumentType(documentType)

    global _defaultDocumentType
    _defaultDocumentType = documentType

def registerDocumentType(name, documentType):
    _documentTypeSet[name] = documentType

def findDocumentType(name):
    return _documentTypeSet.get(name)

def associateDocumentType(inputExtension, documentType):
    '''
    Associates the given filename-extension, or a set of filename-extensions, 
    to the given document-type object. The filename-extension-key is always 
    stored lower-case, so that we can be case-insensitive for it.

    inputExtension (string or list-of-strings):
    The file-extensions to associate to the given document-type.

    documentType (DocumentType or string):
    The document-type object to associate to the file-extensions.
    '''
    if isinstance(documentType, six.string_types):
        documentType = findDocumentType(documentType)

    global _associationSet
    if isinstance(inputExtension, six.string_types):
        _associationSet[inputExtension.lower()] = documentType
        return
        
    for extension in inputExtension:
        associateDocumentType(extension, documentType)            

def strictDocumentType(inputExtension):
    '''
    Returns the document-type object associated to a given
    filename-extension. 
    
    The filename-extension comparison is case-insensitive.

    inputExtension (string):
    The file-extension for which to retrieve the document-type.

    returns (DocumentType):
    The associated document-type object, if such can be
    found. Otherwise None.
    '''
    return _associationSet.get(inputExtension.lower())

def documentType(inputExtension):
    '''
    Returns the document-type object associated to a given
    filename-extension. 
    
    The filename-extension comparison is case-insensitive.

    inputExtension (string):
    The file-extension for which to retrieve the document-type.

    returns (DocumentType):
    The associated document-type object, if such can be
    found. Otherwise the default document-type object.
    '''
    return _associationSet.get(inputExtension.lower(), _defaultDocumentType)

def outputDocumentName(inputPath):
    '''
    Returns the name of the output-document filename given the 
    input-document filename. 
    
    The output-document filename is decided by the document-type
    associated to the file-extension of the input-document filename.

    name (string):
    The path to the input-document.

    returns (string):
    The path to the output-document.
    '''
    inputExtension = fileExtension(inputPath)
    type = documentType(inputExtension)
    outputPath = type.outputName(inputPath)
    return unixDirectoryName(outputPath) 


