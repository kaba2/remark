# -*- coding: utf-8 -*-

# Description: Gallery macro
# Detail: Generates an image gallery with thumbnails.

from MacroRegistry import registerMacro
from FileSystem import unixRelativePath, unixDirectoryName, changeExtension
from FileSystem import fileExtension, copyIfNecessary, createDirectories, copyTree
from FileSystem import pathExists, fileModificationTime

import sys
import os.path
import math
import hashlib

try: 
    from PIL import Image
except ImportError, e:
    print 'Error: Python Imaging Library missing. Please install it first.'
    sys.exit(1)

class Gallery_Macro(object):
    def name(self):
        return 'Gallery'

    def expand(self, parameter, remark):
        documentTree = remark.documentTree
        document = remark.document
        inputRootDirectory = remark.inputRootDirectory
        outputRootDirectory = remark.outputRootDirectory
        
        scope = remark.scopeStack.top()
        thumbnailMaxWidth = scope.getInteger('Gallery.thumbnail_max_width', 400)
        thumbnailMaxHeight = scope.getInteger('Gallery.thumbnail_max_height', 400)

        dependencySet = set()
        text = ['<div class="highslide-gallery">']

        # Gather a list of images and their captions.
        entrySet = []
        for line in parameter:
            neatLine = line.strip()
            if neatLine == '':
                continue
            if neatLine[0] == '-':
                if len(entrySet) == 0:
                    remark.reportWarning('Caption was defined before any image was given. Ignoring it.',
                                         'invalid-input')
                    continue
                
                # Caption follows.
                # The whitespace at the end takes care of
                # proper spacing where there are multiple
                # caption lines.
                caption = neatLine[1 : ].strip() + ' '
                
                # Add the caption for the latest
                # given image. It is possible to
                # give multiple captions in which case
                # they are appended together.
                entrySet[-1][1] += caption
            else:
                # Image file follows.
                imageFile = neatLine
                # Give it an empty caption for now.
                entrySet.append([imageFile, ''])

        # The supported pixel-based image file-extensions are 
        # listed in the order of priority to be used for 
        # thumbnail generation. The idea here is to prefer 
        # lossless formats over lossy formats.
        pixelBasedSet = ['.png', '.gif', '.jpeg', '.jpg']

        # The support vector-based image file-extensions.
        vectorBasedSet = ['.svg']

        # The set of supported image file-extensions.
        supportedSet = pixelBasedSet + vectorBasedSet

        for entry in entrySet:
            # Extract the entry information.
            entryName = entry[0]
            caption = entry[1]

            # Find the image using the file-searching algorithm.
            input, unique = documentTree.findDocument(entryName, document.relativeDirectory)
            if input == None:
                # The image-file was not found. Report a warning and skip
                # the file.
                remark.reporter.reportMissingDocument(entryName)
                continue

            if not unique:
                # There are many matching image files with the given name.
                # Report a warning, pick one arbitrarily, and continue.
                remark.reporter.reportAmbiguousDocument(entryName)
            
            # See if we support the file-extension.
            if not input.extension in supportedSet:
                # This file-extension is not supported. Report a warning
                # and skip the file.
                remark.reportWarning('Image file ' + input.relativeName + 
                                     ' has an unsupported file-extension. Ignoring it.',
                                     'invalid-input')
                continue
           
            # If the image can not be generated a thumbnail directly,
            # see if there is an equivalent image with a different format.
            pixelDocument = input
            if not input.extension in pixelBasedSet:
                for extension in pixelBasedSet:
                    # Note that the search for a pixel-based alternative image
                    # is carried out in the directory of the input-image,
                    # not in the directory of the document.
                    pixelFileName = changeExtension(input.fileName, extension)
                    #print 'Searching for', pixelFileName
                    pixelDocument = documentTree.findDocumentLocal(pixelFileName,
                                                              input.relativeDirectory)
                    if pixelDocument != None:
                        # We found a pixel-based alternative image.
                        break
            
            # Add dependencies.            
            dependencySet.add(input)
            dependencySet.add(pixelDocument)

            # Find out input names.
            inputLinkName = unixRelativePath(document.relativeDirectory, input.relativeName)

            # Find out thumbnail names.
            # The used hash does not matter, but it must always give the same
            # hash for the same relative-name.
            hashString = hashlib.md5(input.relativeName).hexdigest()[0 : 16]
            thumbRelativeName = 'remark_files/thumbnails/' + changeExtension(input.fileName, '-' + hashString + '.png')
            thumbLinkName = unixRelativePath(document.relativeDirectory, thumbRelativeName)
            if pixelDocument == None:
                # If we could not find a pixel-based image, we will use
                # the vector-based image as the thumbnail itself.
                thumbRelativeName = input.relativeName
                thumbLinkName = inputLinkName
                remark.reportWarning('Using ' + input.relativeName + ' as its own thumbnail. ' +
                                     'Provide a pixel-based alternative image to generate a thumbnail.',
                                     'vector-thumbnail')

            # These are the zoom-in and zoom-out time, 
            # respectively, of the Highslide library.
            expandTime = 250
            restoreTime = expandTime

            #expandTime = 250
            #restoreTime = 0
            #if input.extension in vectorBasedSet:
            #    expandTime = 0

            # Generate the actual html-entry.
            title = caption
            if caption == '':
                title = 'Click to enlarge'

            text += ['<a href="' + inputLinkName + '" class="highslide" ' + 
                     'onclick="' +
                     'hs.expandDuration = ' + repr(expandTime) + '; ' + 
                     'hs.restoreDuration = ' + repr(restoreTime) + '; ' + 
                     'return hs.expand(this)">',
                     '\t<img src="' + thumbLinkName + '" ' + 
                     'alt="' + caption + '" ' +
                     'title="' + title + '" ' + 
                     '/></a>',]

            if caption != '':
                text += ['<div class="highslide-caption">',
                         caption,
                         '</div>',]
            
            # Create the directory for the thumbnail, if necessary.
            thumbDirectory = os.path.join(outputRootDirectory, 'remark_files/thumbnails');
            if not pathExists(thumbDirectory):
                createDirectories(thumbDirectory)
                
            # Find out full paths.
            inputFullName = os.path.join(inputRootDirectory, input.relativeName)
            thumbFullName = os.path.join(outputRootDirectory, thumbRelativeName)

            # Compute the thumbnail only if the thumbnail does not exist
            # or it is not up-to-date.
            thumbnailUpToDate = (pathExists(thumbFullName) and
                                 fileModificationTime(inputFullName) <= fileModificationTime(thumbFullName))
            if not thumbnailUpToDate:
                try:
                    if pixelDocument != None:
                        # For pixel-based images, we use the Python Imaging Library to
                        # produce the thumbnails (as PNG).
                        pixelFullName = os.path.join(inputRootDirectory, pixelDocument.relativeName)
                        image = Image.open(pixelFullName)
                        image.thumbnail((thumbnailMaxWidth, thumbnailMaxHeight), Image.ANTIALIAS)
                        image.save(thumbFullName, 'PNG')
                        
                        # Report the generation of a thumbnail.
                        message = 'Created a thumbnail for ' + input.relativeName
                        if pixelDocument != input:
                            message += ' from ' + pixelDocument.relativeName
                        message += '.'
                        remark.report(['', message],
                                     'verbose')
                except IOError as err: 
                    remark.reportWarning('Cannot create a thumbnail for ' + input.relativeName + '. ',
                                         'thumbnail-failed')
                    continue
        
        text.append('</div>')
        
        return text, dependencySet

    def outputType(self):
        return 'html'

    def expandOutput(self):
        return False

    def htmlHead(self, remark):
        document = remark.document;
        scriptFile = unixRelativePath(document.relativeDirectory, 'remark_files/highslide/highslide-full.js')
        styleFile = unixRelativePath(document.relativeDirectory, 'remark_files/highslide/highslide.css')
        graphicsDir = unixRelativePath(document.relativeDirectory, 'remark_files/highslide/graphics')
        
        return ['<script type="text/javascript" src="' + scriptFile + '"></script>',
                '<link rel="stylesheet" type="text/css" href="' + styleFile + '" />',
                '<script type="text/javascript">',
                "hs.graphicsDir = '" + graphicsDir + "/';",
                'hs.showCredits = false;',
                '</script>',]
        
    def postConversion(self, inputDirectory, outputDirectory):
        scriptDirectory = sys.path[0]

        copyIfNecessary('./remark_files/highslide/highslide.css', scriptDirectory,
                        './remark_files/highslide/highslide.css', outputDirectory);

        copyIfNecessary('./remark_files/highslide/highslide-full.js', scriptDirectory,
                        './remark_files/highslide/highslide-full.js', outputDirectory);

        highslideSource = os.path.join(scriptDirectory, './remark_files/highslide/graphics')
        highslideTarget = os.path.join(outputDirectory, './remark_files/highslide/graphics')
        if not pathExists(highslideTarget):
            copyTree(highslideSource, highslideTarget)
        
registerMacro('Gallery', Gallery_Macro())
