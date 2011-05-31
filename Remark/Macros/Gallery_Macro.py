# -*- coding: utf-8 -*-

# Description: Gallery_Macro class
# Detail: Generates an image gallery with thumbnails.

from MacroRegistry import registerMacro
from Common import linkAddress, unixDirectoryName, changeExtension

import sys
import os.path
import shutil

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
        
        thumbnailMaxWidth = scope.getInteger('Gallery.thumbnail_max_width', 200)
        thumbnailMaxHeight = scope.getInteger('Gallery.thumbnail_max_height', 200)

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

        for entry in entrySet:
            inputImageName = entry[0]
            imageDocument, unique = documentTree.findDocumentHard(inputImageName, document.relativeDirectory)
            if imageDocument == None:
                remarkConverter.reportWarning('Gallery_Macro: Image file ' + inputImageName + ' was not found. Ignoring it.')
                continue
            if not unique:
                remarkConverter.reportWarning('Gallery_Macro: Image file ' + inputImageName + ' is ambiguous. Picking arbitrarily.')
            imageRootName = imageDocument.relativeName
            
            caption = entry[1]
            imageFileName = os.path.split(imageRootName)[1]
            thumbRootName = 'remark_files/thumbnails/' + changeExtension(imageFileName, '-thumb.png')
            
            sourceImageFullName = os.path.join(inputRootDirectory, imageRootName)
           
            imageDocName = linkAddress(document.relativeDirectory, imageRootName)
            thumbDocName = linkAddress(document.relativeDirectory, thumbRootName)
            
            title = caption
            if caption == '':
                title = 'Click to enlarge'    
                             
            # Generate html-entry.
            text += ['<a href="' + imageDocName + '" class="highslide" onclick="return hs.expand(this)">',
                     '\t<img src="' + thumbDocName + '" alt="Highslide JS" title="' + title + '"/>',
                     '</a>',]

            if caption != '':
                text += ['<div class="highslide-caption">',
                         caption,
                         '</div>',]
            
            # Generate thumbnail image if necessary.
            targetDirectory = os.path.join(targetRootDirectory, 'remark_files/thumbnails');
            if not os.path.exists(targetDirectory):
                os.makedirs(targetDirectory)
                
            targetImageFullName = os.path.join(targetRootDirectory, thumbRootName)
            if not os.path.exists(targetImageFullName):
                try:
                    image = Image.open(sourceImageFullName)
                    image.thumbnail((thumbnailMaxWidth, thumbnailMaxHeight), Image.ANTIALIAS)
                    image.save(targetImageFullName, 'PNG')
                    remarkConverter.report('Gallery_Macro: Created a thumbnail for ' + imageFileName + '.') 
                except IOError:
                    remarkConverter.reportWarning('Gallery_Macro: Cannot create thumbnail for ' + imageFileName + '.')
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
        remarkInputDirectory = sys.path[0]
        highslideSource = os.path.join(remarkInputDirectory, './remark_files/highslide')
        highslideTarget = os.path.join(outputDirectory, './remark_files/highslide')
        if not os.path.exists(highslideTarget):
            shutil.copytree(highslideSource, highslideTarget)                
        
registerMacro('Gallery', Gallery_Macro())
