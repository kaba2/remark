# -*- coding: utf-8 -*-

# Description: Gallery macro
# Detail: Generates an image gallery with thumbnails.

from MacroRegistry import registerMacro
from Common import linkAddress, unixDirectoryName, changeExtension
from Common import fileExtension, copyIfNecessary

import sys
import os.path
import shutil
import math

try: 
    from PIL import Image
except ImportError, e:
    print 'Error: Python Imaging Library missing. Please install it first.'
    sys.exit(1)

class Gallery_Macro(object):
    def expand(self, parameter, remarkConverter):
        documentTree = remarkConverter.documentTree
        document = remarkConverter.document
        inputRootDirectory = remarkConverter.inputRootDirectory
        outputRootDirectory = remarkConverter.outputRootDirectory
        
        scope = remarkConverter.scopeStack.top()
        thumbnailMaxWidth = scope.getInteger('Gallery.thumbnail_max_width', 400)
        thumbnailMaxHeight = scope.getInteger('Gallery.thumbnail_max_height', 400)

        # Gather a list of images and their captions.
        entrySet = []
        for line in parameter:
            neatLine = line.strip()
            if neatLine == '':
                continue
            if neatLine[0] == '-':
                if len(entrySet) == 0:
                    remarkConverter.reportWarning('Gallery: Caption was defined before any image was given. Ignoring it.')
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

        # Generate html entries and thumbnails.
        text = ['<div class="highslide-gallery">']

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
                remarkConverter.reportWarning('Gallery: Image file ' + entryName + 
                                              ' was not found. Ignoring it.')
                continue

            if not unique:
                # There are many matching image files with the given name.
                # Report a warning, pick one arbitrarily, and continue.
                remarkConverter.reportWarning('Gallery: Image file ' + entryName + 
                                              ' is ambiguous. Picking arbitrarily.')
            
            # See if we support the file-extension.
            if not input.extension in supportedSet:
                # This file-extension is not supported. Report a warning
                # and skip the file.
                remarkConverter.reportWarning('Gallery: ' + input.relativeName + 
                                              ' has an unsupported file-extension. Ignoring it.')
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
                        
            # Find out input names.
            inputLinkName = linkAddress(document.relativeDirectory, input.relativeName)

            # Find out thumbnail names.
            thumbRelativeName = 'remark_files/thumbnails/' + changeExtension(input.fileName, '-thumb.png')
            thumbLinkName = linkAddress(document.relativeDirectory, thumbRelativeName)
            if pixelDocument == None:
                # If we could not find a pixel-based image, we will use
                # the vector-based image as the thumbnail itself.
                thumbRelativeName = input.relativeName
                thumbLinkName = inputLinkName
                remarkConverter.reportWarning('Gallery: Using ' + input.relativeName + ' as its own thumbnail. ' +
                                              'Provide a pixel-based alternative image to generate a thumbnail.')

            # These are the zoom-in and zoom-out time, 
            # respectively, of the Highslide library.
            expandTime = 250
            restoreTime = 0
            if input.extension in vectorBasedSet:
                # The expansion time in the Highslide library
                # needs to be set to zero to avoid the overhead
                # of recomputing the vector-based image all
                # over again.
                expandTime = 0

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
            if not os.path.exists(thumbDirectory):
                os.makedirs(thumbDirectory)
                
            # Find out full paths.
            inputFullName = os.path.join(inputRootDirectory, input.relativeName)
            thumbFullName = os.path.join(outputRootDirectory, thumbRelativeName)

            # Compute the thumbnail only if the thumbnail does not exist
            # or it is not up-to-date.
            thumbnailUpToDate = (os.path.exists(thumbFullName) and
                                 os.path.getmtime(inputFullName) <= os.path.getmtime(thumbFullName))
            if not thumbnailUpToDate:
                try:
                    if pixelDocument != None:
                        # For pixel-based images, we use the Python Imaging Library to
                        # produce the thumbnails (as PNG).
                        pixelFullName = os.path.join(outputRootDirectory, pixelDocument.relativeName)
                        image = Image.open(pixelFullName)
                        image.thumbnail((thumbnailMaxWidth, thumbnailMaxHeight), Image.ANTIALIAS)
                        image.save(thumbFullName, 'PNG')
                        
                        # Report the generation of a thumbnail.
                        message = 'Gallery: Created a thumbnail for ' + input.relativeName
                        if pixelDocument != input:
                            message += ' from ' + pixelDocument.relativeName
                        message += '.'
                        remarkConverter.report(message)
                except IOError as err: 
                    #print err
                    remarkConverter.reportWarning('Gallery: Cannot create a thumbnail for ' + 
                                                  input.relativeName + '. ')
                    continue
        
        text.append('</div>')
        
        return text

    def outputType(self):
        return 'html'

    def pureOutput(self):
        return True

    def htmlHead(self, remarkConverter):
        document = remarkConverter.document;
        scriptFile = linkAddress(document.relativeDirectory, 'remark_files/highslide/highslide-full.js')
        styleFile = linkAddress(document.relativeDirectory, 'remark_files/highslide/highslide.css')
        graphicsDir = linkAddress(document.relativeDirectory, 'remark_files/highslide/graphics')
        
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
        if not os.path.exists(highslideTarget):
            shutil.copytree(highslideSource, highslideTarget)
        
registerMacro('Gallery', Gallery_Macro())
