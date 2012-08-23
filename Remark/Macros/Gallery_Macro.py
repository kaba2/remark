# -*- coding: utf-8 -*-

# Description: Gallery_Macro class
# Detail: Generates an image gallery with thumbnails.

from MacroRegistry import registerMacro
from Common import linkAddress, unixDirectoryName, changeExtension
from Common import fileExtension, copyIfNecessary

import sys
import os.path
import shutil
import cairo 
import rsvg 
import math

try: 
    from PIL import Image
except ImportError, e:
    print 'Error: Python Imaging Library missing. Please install it first.'
    sys.exit(1)

class Gallery_Macro:
    def expand(self, parameter, remarkConverter):
        documentTree = remarkConverter.documentTree
        scope = remarkConverter.scopeStack.top()
        document = remarkConverter.document
        inputRootDirectory = remarkConverter.inputRootDirectory
        targetRootDirectory = remarkConverter.targetRootDirectory
        
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
                    remarkConverter.reportWarning('Gallery_Macro: Caption was defined before any image was given. Ignoring it.')
                    continue
                
                # Caption follows.
                caption = neatLine[1 : ].strip()
                
                # Set the caption for the latest
                # given image.
                entrySet[-1][1] = caption
            else:
                # Image file follows.
                imageFile = neatLine
                # Give it an empty caption for now.
                entrySet.append([imageFile, ''])

        # Generate html entries and thumbnails.
        text = ['<div class="highslide-gallery">']

        supportedSet = ['.gif', '.jpeg', '.jpg', '.png', '.svg']

        for entry in entrySet:
            inputImageName = entry[0]
            imageDocument, unique = documentTree.findDocumentHard(inputImageName, document.relativeDirectory)
            if imageDocument == None:
                remarkConverter.reportWarning('Gallery_Macro: Image file ' + inputImageName + 
                                              ' was not found. Ignoring it.')
                continue
            if not unique:
                remarkConverter.reportWarning('Gallery_Macro: Image file ' + inputImageName + 
                                              ' is ambiguous. Picking arbitrarily.')
            imageRootName = imageDocument.relativeName
            
            caption = entry[1]
            imageFileName = os.path.split(imageRootName)[1]
            thumbRootName = 'remark_files/thumbnails/' + changeExtension(imageFileName, '-thumb.png')
            
            sourceImageFullName = os.path.join(inputRootDirectory, imageRootName)

            # See if we support the file-extension.
            imageFileExtension = fileExtension(imageFileName).lower()
            if not imageFileExtension in supportedSet:
                remarkConverter.reportWarning('Gallery_Macro: ' + imageFileExtension + 
                                              ' file-extension is not supported.')
                continue
           
            imageDocName = linkAddress(document.relativeDirectory, imageRootName)
            thumbDocName = linkAddress(document.relativeDirectory, thumbRootName)
            
            title = caption
            if caption == '':
                title = 'Click to enlarge'

            expandTime = 250
            if imageFileExtension == '.svg':
                expandTime = 0

            restoreTime = 0
                             
            # Generate html-entry.
            text += ['<a href="' + imageDocName + '" class="highslide" ' + 
                     'onclick="' + 
                     'hs.expandDuration = ' + repr(expandTime) + '; ' + 
                     'hs.restoreDuration = ' + repr(restoreTime) + '; ' + 
                     'return hs.expand(this)">',
                     '\t<img src="' + thumbDocName + '" ' + 
                     'alt="' + caption + '" ' +
                     'title="' + title + '" ' + 
                     '/></a>',]

            if caption != '':
                text += ['<div class="highslide-caption">',
                         caption,
                         '</div>',]
            
            # Generate thumbnail image if necessary.
            targetDirectory = os.path.join(targetRootDirectory, 'remark_files/thumbnails');
            if not os.path.exists(targetDirectory):
                os.makedirs(targetDirectory)
                
            targetImageFullName = os.path.join(targetRootDirectory, thumbRootName)
            thumbnailUpToDate = (os.path.exists(targetImageFullName) and
                                 os.path.getmtime(sourceImageFullName) <= os.path.getmtime(targetImageFullName))

            if not thumbnailUpToDate:
                try:
                    if imageFileExtension != '.svg':
                        # For PNG, JPEG, and GIF we use the Python Imaging Library to
                        # produce the thumbnails.
                        image = Image.open(sourceImageFullName)
                        image.thumbnail((thumbnailMaxWidth, thumbnailMaxHeight), Image.ANTIALIAS)
                        image.save(targetImageFullName, 'PNG')
                    else:
                        # For SVG, we use the pycairo library together with the
                        # pyrsvg library to produce the thumbnails.

                        # Load the svg image.
                        svgImage = rsvg.Handle(sourceImageFullName)
                        svgWidth = svgImage.get_dimension_data()[0]
                        svgHeight = svgImage.get_dimension_data()[1]
                        
                        # Compute the scaling ratio.
                        # We want to restrict the maximum number of
                        # pixels in both dimensions, but want to do
                        # it such that the aspect ratio is preserved.
                        xRatio = float(thumbnailMaxWidth) / svgWidth
                        yRatio = float(thumbnailMaxHeight) / svgHeight
                        ratio = min(xRatio, yRatio, 1.0)

                        # Compute the number of pixels in the thumbnail.
                        thumbnailWidth = int(math.ceil(ratio * svgWidth))
                        thumbnailHeight = int(math.ceil(ratio * svgHeight))

                        # Allocate the pixel-based image.
                        image =  cairo.ImageSurface(cairo.FORMAT_ARGB32, 
                                                    thumbnailWidth, thumbnailHeight) 

                        # The context contains the current transformation matrix etc.
                        context = cairo.Context(image)

                        # Scale down the coordinate system, so that the svg-image
                        # fits to the thumbnail pixels.
                        context.scale(ratio, ratio)

                        # Draw the svg-image as a pixel-based image.
                        svgImage.render_cairo(context) 

                        # Write the pixel-based image as a PNG image.
                        image.write_to_png(targetImageFullName)

                    remarkConverter.report('Gallery_Macro: Created a thumbnail for ' + imageFileName + '.')
                except IOError as err: 
                    print err
                    remarkConverter.reportWarning('Gallery_Macro: Cannot create thumbnail for ' + imageFileName + '. ')
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
