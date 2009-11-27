import os.path
import string

def linkAddress(fromDirectory, toFile):
    relativeName = os.path.relpath(toFile, fromDirectory)
    newRelativeName = relativeName
    return os.path.normpath(newRelativeName)

def readFile(fileName):
    text = []

    # Read the file into memory
    with open(fileName, 'rU') as file:
        text = file.readlines()
        
    # Remove possible newlines from the ends of the lines.
    for i in range(0, len(text)):
        if text[i][-1] == '\n':
            text[i] = text[i][0 : -1]
            
    return text

def outputDocumentName(name):
    outputName = ''
    if os.path.splitext(name)[1] == '.txt':
        outputName = changeExtension(name, '.htm') 
    else: 
        outputName = name + '.htm'
    return outputName

def unixDirectoryName(name):
    return string.replace(name, '\\', '/')                

_linkId = 0
def getLinkId():
    global _linkId
    _linkId += 1
    return _linkId

def resetLinkId():
    global _linkId
    _linkId = 0

def remarkLink(description, target):
    name = 'RemarkLink_' + str(getLinkId())
    text = ['[' + description + '][' + name + ']',
            '[' + name + ']: ' + target + '\n']
    return text

def changeExtension(fileName, newExtension):
    return os.path.splitext(fileName)[0] + newExtension
