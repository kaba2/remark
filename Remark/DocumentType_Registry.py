from FileSystem import fileExtension, unixDirectoryName

_documentTypeMap = dict()
_defaultDocumentType = None

def setDefaultDocumentType(documentType):
    '''
    Sets the default document-type.

    This document-type will be returned by documentType()
    in case an associated document-type can not be found.

    documentType (DocumentType):
    The document-type object to use as a default 
    document-type.

    See also:
    documentType()
    '''
    global _defaultDocumentType
    _defaultDocumentType = documentType

def associateDocumentType(inputExtension, documentType):
    '''
    Associates the given filename-extension, or a set of filename-extensions, 
    to the given document-type object. The filename-extension-key is always 
    stored lower-case, so that we can be case-insensitive for it.

    inputExtension (string or list-of-strings):
    The file-extensions to associate to the given document-type.

    documentType (DocumentType):
    The document-type object to associate to the file-extensions.
    '''
    global _documentTypeMap
    if isinstance(inputExtension, basestring):
        _documentTypeMap[inputExtension.lower()] = documentType
    else:
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
    return _documentTypeMap.get(inputExtension.lower())

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
    return _documentTypeMap.get(inputExtension.lower(), _defaultDocumentType)

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


