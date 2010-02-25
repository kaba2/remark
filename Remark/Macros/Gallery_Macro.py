# -*- coding: utf-8 -*-

# Description: Gallery_Macro class
# Detail: Generates an image gallery with thumbnails.

from MacroRegistry import registerMacro
from Common import linkAddress, unixDirectoryName, changeExtension

import os.path
import shutil

import Image

class Gallery_Macro:
    def expand(self, parameter, remarkConverter):
        scope = remarkConverter.scopeStack.top()
        document = remarkConverter.document
        inputRootDirectory = remarkConverter.inputRootDirectory
        targetRootDirectory = remarkConverter.targetRootDirectory
        
        thumbnailMaxWidth = scope.getInteger('Gallery.thumbnail_max_width', 256)
        thumbnailMaxHeight = scope.getInteger('Gallery.thumbnail_max_height', 256)

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
            imageRelativeName = unixDirectoryName(entry[0])
            caption = entry[1]
            imageFileName = os.path.split(imageRelativeName)[1]
            thumbFileName = 'remark_files/thumbnails/' + changeExtension(imageFileName, '-thumb.png')
            
            sourceName = os.path.normpath(os.path.join(inputRootDirectory, 
                                     os.path.join(document.relativeDirectory, imageRelativeName)))
            if not os.path.exists(sourceName):
                remarkConverter.reportWarning('Image file ' + imageRelativeName + ' does not exist. Ignoring it.')
                continue
            
            thumbRelativeName = linkAddress(document.relativeDirectory, thumbFileName)
            
            title = caption
            if caption == '':
                title = 'Click to enlarge'    
                             
            # Generate html-entry.
            text += ['<a href="' + imageRelativeName + '" class="highslide" onclick="return hs.expand(this)">',
                     '\t<img src="' + thumbRelativeName + '" alt="Highslide JS" title="' + title + '"/>',
                     '</a>',]

            if caption != '':
                text += ['<div class="highslide-caption">',
                         caption,
                         '</div>',]
            
            # Generate thumbnail image if necessary.
            targetDirectory = os.path.join(targetRootDirectory, 'remark_files/thumbnails');
            if not os.path.exists(targetDirectory):
                os.makedirs(targetDirectory)
                
            targetName = os.path.join(targetRootDirectory, thumbFileName)
            if not os.path.exists(targetName):
                try:
                    image = Image.open(sourceName)
                    image.thumbnail((thumbnailMaxWidth, thumbnailMaxHeight), Image.ANTIALIAS)
                    image.save(targetName, 'PNG')
                    print 'Created a thumbnail for', imageFileName, '.' 
                except IOError:
                    remarkConverter.reportWarning('Cannot create thumbnail for ' + imageFileName + '.')
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
        highslideSource = './remark_files/highslide'
        highslideTarget = os.path.join(outputDirectory, 'remark_files/highslide')
        if not os.path.exists(highslideTarget):
            shutil.copytree(highslideSource, highslideTarget)                
        
registerMacro('Gallery', Gallery_Macro())
