# -*- coding: utf-8 -*-

# Description: Gallery macro
# Detail: Generates an image gallery with thumbnails.

from Remark.Macro_Registry import registerMacro
from Remark.FileSystem import unixRelativePath, unixDirectoryName, changeExtension
from Remark.FileSystem import fileExtension, copyIfNecessary, createDirectories, copyTree
from Remark.FileSystem import pathExists, fileModificationTime, remarkDirectory, htmlRegion

import sys
import os.path
import math
import hashlib

pillowPresent = False
pillowReported = False

try: 
    # On Linux and Mac the easy_install installs Python
    # imaging library in a directory which is different from
    # PIL. Therefore this may fail even though PIL is installed.
    from PIL import Image
    pillowPresent = True
except ImportError:
    try:
        # When the previous does fail, we will try to import the
        # Image module directly. If this works, it is because PIL 
        # adds the PIL.pth file in the python site-packages directory,
        # which then contains a redirect to the actual PIL directory.
        # There is a danger, though, that this actually imports some
        # other module than the PIL Image module.
        import Image
        pillowPresent = True
    except ImportError:
        None

class Gallery_Macro(object):
    def __init__(self):
        # The supported pixel-based image file-extensions are 
        # listed in the order of priority to be used for 
        # thumbnail generation. The idea here is to prefer 
        # lossless formats over lossy formats.
        self.pixelBasedSet = ['.png', '.gif', '.jpeg', '.jpg']

        # The supported vector-based image file-extensions.
        self.vectorBasedSet = ['.svg', '.svgz']

        # The set of supported image file-extensions.
        self.supportedSet = self.pixelBasedSet + self.vectorBasedSet

    def name(self):
        return 'Gallery'

    def expand(self, parameter, remark):
        documentTree = remark.documentTree
        document = remark.document
        inputRootDirectory = remark.inputRootDirectory
        outputRootDirectory = remark.outputRootDirectory

        global pillowReported
        if not pillowPresent and not pillowReported:
            remark.reporter.reportWarning(
                'Thumbnails will not be created; the Pillow library is missing. ' +
                "To install Pillow, run 'easy_install pillow' from the command-line. ",
                'thumbnail-failed')
            pillowReported = True

        scope = remark.scopeStack.top()
        thumbnailMaxWidth = scope.getInteger('Gallery.thumbnail_max_width', 300)
        thumbnailMaxHeight = scope.getInteger('Gallery.thumbnail_max_height', 300)

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

        for entry in entrySet:
            # Extract the entry information.
            entryName = entry[0]
            caption = entry[1]

            # Find the image using the file-searching algorithm.
            input, unique = documentTree.findDocument(entryName, document.relativeDirectory)

            if not unique:
                # There are many matching image files with the given name.
                # Report a warning, pick one arbitrarily, and continue.
                remark.reporter.reportAmbiguousDocument(entryName)

            if input == None:
                # The image-file was not found. Report a warning and skip
                # the file.
                remark.reporter.reportMissingDocument(entryName)
                continue
           
            # See if we support the file-extension.
            if not input.extension in self.supportedSet:
                # This file-extension is not supported. Report a warning
                # and skip the file.
                remark.reportWarning('Image file ' + input.relativeName + 
                                     ' has an unsupported file-extension. Ignoring it.',
                                     'invalid-input')
                continue
           
            # If the image can not be generated a thumbnail directly,
            # see if there is an equivalent image with a different format.
            pixelDocument = input
            if not fileExtension(input.fileName) in self.pixelBasedSet:
                for extension in self.pixelBasedSet:
                    pixelFileName = changeExtension(input.fileName, extension)

                    # Note that the search for a pixel-based alternative image
                    # is carried out in the directory of the input-image,
                    # not in the directory of the document.
                    linkDocument = documentTree.findDocumentLocal(pixelFileName, input.relativeDirectory)

                    if linkDocument != None:
                        # We found a pixel-based alternative image.
                        pixelDocument = linkDocument
                        break

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
                # the vector-based image itself as the thumbnail.
                thumbRelativeName = input.relativeName
                thumbLinkName = inputLinkName
                remark.reportWarning('Using a vector-based image ' + input.relativeName + ' as its own thumbnail. ' +
                                     'Provide a pixel-based alternative image to generate a thumbnail.',
                                     'vector-thumbnail')

            # These are the zoom-in and zoom-out time, 
            # respectively, of the Highslide library.
            expandTime = 250
            restoreTime = expandTime

            #expandTime = 250
            #restoreTime = 0
            #if input.extension in self.vectorBasedSet:
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
            if not thumbnailUpToDate and pillowPresent:
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
                        remark.report([None, message],
                                     'verbose')
                except IOError as err: 
                    remark.reportWarning('Cannot create a thumbnail for ' + input.relativeName + 
                                         ' because of a file-error. ', 'thumbnail-failed')
                    continue

        text.append('</div>')
        
        return htmlRegion(text)

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
        
    def postConversion(self, remark):
        scriptDirectory = sys.path[0]

        copyNameSet = [
            './remark_files/highslide/highslide.css',
            './remark_files/highslide/highslide-full.js'
            ]

        for name in copyNameSet:
            copyIfNecessary(name, remarkDirectory(),
                        name, remark.outputRootDirectory);
            copyIfNecessary(name, remarkDirectory(),
                        name, remark.outputRootDirectory);

        highslideSource = os.path.join(remarkDirectory(), './remark_files/highslide/graphics')
        highslideTarget = os.path.join(remark.outputRootDirectory, './remark_files/highslide/graphics')
        if not pathExists(highslideTarget):
            copyTree(highslideSource, highslideTarget)

registerMacro('Gallery', Gallery_Macro())
