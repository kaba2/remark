# -*- coding: utf-8 -*-

# Description: Conversions between Remark, Markdown, and html
# Documentation: algorithms.txt

from __future__ import print_function

import string
import os
import os.path
import datetime
import traceback
import time
import sys
import re

from Remark.FileSystem import remarkScriptPath, fileExists, withoutFileExtension

# Older versions of Markdown (e.g. 2.0.x), have
# the following bug. The command-line script is named `markdown.py`,
# and the package is named `markdown`. When `import markdown` is
# issued, depending on the location of this file the import may
# refer to either the markdown.py or the package markdown. The
# latter is what we want. We fix this problem by temporarily 
# removing those directories from sys.path which contain 
# markdown.py.

oldSysPath = sys.path

scriptDirectory = remarkScriptPath()
if remarkScriptPath() != '':
    # Remove all those directories from sys.path which
    # contain markdown.py.
    newSysPath = []
    for i in range(len(sys.path)):
        # The paths in sys.path are relative to the script directory
        # (or they are absolute paths). Note that sys.path may contain 
        # the script directory in multiple different forms, e.g. 
        # '/usr/local/bin', '../bin', or ''. 
        path = os.path.join(scriptDirectory, sys.path[i])
        if not fileExists('markdown.py', path):
            newSysPath.append(path)
        else:
            print('Removed', sys.path[i], ' from Python path.')
            None
    sys.path = newSysPath

try:
    import markdown
except ImportError:
    print('Error: markdown library missing; install it first.')
    sys.exit(1)

sys.path = oldSysPath

from Remark.Version import remarkVersion
from Remark.FileSystem import unixDirectoryName, copyIfNecessary, remarkDirectory
from Remark.FileSystem import globalOptions, unixRelativePath, writeFile
from Remark.Reporting import Reporter, ScopeGuard
from Remark.DocumentType_Registry import documentType, outputDocumentName
from Remark.DocumentTree import createDocumentTree
from Remark.Remark_To_Markdown import Remark

mathPattern = r'<script.*?type[ \t]*=[ \t]*".*?math.*?".*?>'
mathRegex = re.compile(mathPattern)

def addHtmlBoilerPlate(text, document, htmlHead):
    remarkDirectory = os.path.relpath('remark_files', document.relativeDirectory)

    timeText = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    
    remarkCss = unixDirectoryName(os.path.normpath(
        os.path.join(remarkDirectory, 'remark.css')))
    pygmentsCss = unixDirectoryName(os.path.normpath(
        os.path.join(remarkDirectory, 'pygments.css')))

    cssSet = []
    cssSet.append(remarkCss)
    cssSet.append(pygmentsCss)

    scriptSet = []

    # Check whether the document contains mathematics.
    includeMath = False
    for line in text:
        if mathRegex.search(line) != None:
            includeMath = True
            break

    if includeMath:
        # The page contains mathematics. 

        # Add the Mathjax script, but delay configuration.
        mathJax = 'https://cdn.mathjax.org/mathjax/latest/MathJax.js?delayStartupUntil=configured'
        scriptSet.append(mathJax)

        # Add the MathJax configuration script.
        mathJaxConfig = unixDirectoryName(os.path.normpath(
            os.path.join(remarkDirectory, 'mathjax-config.js')))
        scriptSet.append(mathJaxConfig)

    htmlText = []

    # We aim to produce html5.
    htmlText.append('<!DOCTYPE html>')

    htmlText.append('<html>')
    htmlText.append('<head>')
    htmlText.append('<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')

    # This is necessary for mobile devices to scale the content correctly (i.e. no scaling).
    htmlText.append('<meta name="viewport" content="width=device-width, initial-scale=1">')

    # Add the title.
    title = document.tagString('description')
    htmlText.append('<title>' + title + '</title>')

    # Link to the CSS stylesheets.
    for css in cssSet:
        htmlText.append('<link rel="stylesheet" type="text/css" href="' + css + '"/>')

    # Link to the JavaScript libraries.
    for script in scriptSet:
        htmlText.append('<script type="text/javascript" src="' + script + '"></script>')

    # Add the html-head content from the page.
    htmlText += htmlHead

    htmlText.append('</head>')

    htmlText.append('<body>')

    # Wrap everything into the 'remark-all' div.
    htmlText.append('<div id = "remark-all">')

    # Wrap the actual content in the 'remark' div.
    htmlText.append('<div id = "remark">')

    # Add the actual content.
    htmlText += text

    htmlText.append('</div>')

    # Wrap the footer in the 'remark-footer' div.
    htmlText.append('<div id="remark-footer">')

    # Add the footer text.
    footerText = (
        '<p>' +
        '<a href="http://kaba.hilvi.org/remark">' + 
        'Remark ' + remarkVersion() + 
        '</a>' + ' - ' + 
        'Page generated ' + timeText + '.' + 
        '</p>')
    htmlText.append(footerText)
    
    htmlText.append('</div>')
    htmlText.append('</div>')
    htmlText.append('</body>')
    htmlText.append('</html>')

    return htmlText

def createMarkdownParser():
    '''
    Creates a Markdown-parser, but
    * remove the Reference preprocessor,
    * add the Math extension,
    * add the Region extension,
    * add the Scope extension.
    '''

    from Remark.MarkdownRegion import MarkdownRegion_Extension
    from Remark.MarkdownMath import MarkdownMath_Extension
    from Remark.MarkdownScope import MarkdownScope_Extension

    markdownParser = markdown.Markdown(
        extensions = [
            'tables', 
            'def_list',
            'smarty',
            MarkdownRegion_Extension(),
            # The math-extension must occur after the
            # region extension; otherwise it cannot
            # find the <script> tags where the mathematics
            # is embedded in.
            MarkdownMath_Extension(),
            MarkdownScope_Extension()
        ])

    # for item in markdownParser.inlinePatterns:
    #     print(item)
    # sys.exit(0)

    return markdownParser

def convertRemarkToMarkdown(remarkText, document, documentTree, 
                            outputRootDirectory, reporter = Reporter()):
    '''
    Converts Remark text to Markdown text. 

    remarkText (list of strings):
    The Remark text to convert, string per row.

    returns (list of strings, list of strings):
    The converted html text, and the html-head section.
    '''

    remark = Remark(document, documentTree, 
                    documentTree.rootDirectory, outputRootDirectory,
                    reporter)

    # Convert Remark to Markdown.
    markdownText = remark.convert(remarkText)
    markdownText += remark.postConversion()

    # Return the resulting Markdown text.
    return markdownText, remark.htmlHeader()

def convertMarkdownToHtml(
    markdownText, headText, 
    document, documentTree, 
    outputRootDirectory,
    reporter = Reporter()):
    '''
    Converts Remark-generated Markdown to html.

    markdownText (list of strings):
    The Markdown text to convert, string per row.

    document (Document):
    The underlying document.

    documentTree (DocumentTree):
    The underlying document tree.

    outputRootDirectory (string):
    The root directory of the output.

    returns (list of strings):
    The converted html text.
    '''

    # Create a Markdown parser with Remark extensions.
    markdownParser = createMarkdownParser()

    # Convert Markdown to html.
    htmlString = markdownParser.convert('\n'.join(markdownText))
    htmlText = htmlString.split('\n')

    # Add html boilerplate.
    return addHtmlBoilerPlate(
        htmlText, document, 
        headText + document.tag('html_head'))

def convertRemarkToHtml(remarkText, document, documentTree, 
                        outputRootDirectory,
                        reporter = Reporter()):
    '''
    Converts Remark text to html.

    remarkText (list of strings):
    The Remark text to convert, string per row.

    document (Document):
    The underlying document.

    documentTree (DocumentTree):
    The underlying document tree.

    outputRootDirectory

    returns (list of strings):
    The converted html text.
    '''

    # Convert Remark to Markdown.
    markdownText, headText = convertRemarkToMarkdown(
                                 remarkText, document, documentTree,
                                 outputRootDirectory, reporter)

    # Convert Markdown to html.
    return convertMarkdownToHtml(
        markdownText, 
        headText, 
        document,
        documentTree, 
        outputRootDirectory, 
        reporter)

def saveRemarkToHtml(remarkText, document, documentTree, 
                     outputRootDirectory,
                     reporter = Reporter()):
    '''
    Converts Remark text to html text and saves it to a file.

    remarkText (list of strings):
    The Remark text to convert.

    documentTree (DocumentTree):
    The document-tree to use.

    outputRootDirectory (string):
    The output directory to save the file in.

    reporter (Reporter):
    The reporter to use for reporting.
    '''
    # Convert Remark to Markdown.
    markdownText, headText = convertRemarkToMarkdown(
                                 remarkText, document, documentTree,
                                 outputRootDirectory, reporter)

    # Find out some names.
    outputRelativeName = outputDocumentName(document.relativeName)
    outputFullName = os.path.join(outputRootDirectory, outputRelativeName)

    if globalOptions().generateMarkdown:
        # Write the generated Markdown source.
        writeFile(markdownText, withoutFileExtension(outputFullName) + '.md.txt')

    # Convert Markdown to Html.
    htmlText = convertMarkdownToHtml(
        markdownText, 
        headText, 
        document,
        documentTree, 
        outputRootDirectory, 
        reporter)

    # Write the generated html.
    writeFile(htmlText, outputFullName)

def convertAll(documentTree, argumentSet, reporter = Reporter()):
    '''
    Converts all documents in the document-tree.

    documentTree (DocumentTree):
    The document-tree to use for conversion.

    outputRootDirectory (string):
    The output directory to place the files in.

    reporter (Reporter):
    The reporter to use for reporting.
    '''
    
    outputDirectory = os.path.normpath(argumentSet.outputDirectory)

    # We wish to convert the files in alphabetical order
    # by their relative-name (in the map they are in hashed order).
    sortedDocumentSet = list(documentTree.documentMap.values())
    sortedDocumentSet.sort(key = lambda x: x.relativeName)
   
    for document in sortedDocumentSet:
        if not document.regenerate():
            continue

        reporter.report('Generating ' + document.relativeName + '...',
                        'verbose')
        
        try:
            # Find the document-type based on the
            # filename-extension.
            type = documentType(document.extension)
            
            # Let the document-type convert the document.
            with ScopeGuard(reporter, document.relativeName):
                type.convert(document, documentTree, outputDirectory,
                            reporter)
        except IOError:
            # If an exception is thrown, for example because a document
            # is deleted while Remark is running, then that exception
            # is acknowledged here, and a stack-trace is printed, but
            # the generation still continues for other documents.
            reporter.reportError(traceback.format_exc(), 
                                 'exception')

def convertDirectory(argumentSet, reporter):
    startTime = time.clock()

    reporter.report([None,
                    'Input directory: ' + argumentSet.inputDirectory,
                     'Output directory: ' + argumentSet.outputDirectory,
                     'Remark directory: ' + remarkDirectory(),
                     None],
                    'verbose')

    # Create the document tree.
    documentTree = createDocumentTree(argumentSet, reporter)
    if documentTree == None:
        return reporter.errors(), reporter.warnings()

    # Note that these files are copied _after_ gathering the files
    # and directories. This is to avoid gathering these files
    # in case the input directory is the same as the output directory.
    # It is also important that these files are copied as early as
    # possible, since we want to see the changes in the .css files
    # as early as possible.
    copySet = \
        [
            [
                './remark_files/remark_default.css', 
                remarkDirectory(), 
                './remark_files/remark.css', 
                argumentSet.outputDirectory,
            ],
            [
                './remark_files/pygments_default.css', 
                remarkDirectory(), 
                './remark_files/pygments.css', 
                argumentSet.outputDirectory,
            ],
            [
                './remark_files/mathjax-config.js', 
                remarkDirectory(), 
                './remark_files/mathjax-config.js', 
                argumentSet.outputDirectory,
            ],
        ]

    with ScopeGuard(reporter, 'Updating output files'):
        for (fromName, fromDirectory, toName, toDirectory) in copySet:
            copied = copyIfNecessary(
                fromName, fromDirectory, 
                toName, toDirectory)
            if copied:
                reporter.report([fromName, '=> ' + toName], 'verbose')

    # Parse the tags.
    with ScopeGuard(reporter, 'Parsing tags'):
        for document in documentTree:
            try:
                type = document.documentType

                with ScopeGuard(reporter, document.relativeName):
                    tagSet = type.parseTags(documentTree.fullName(document), reporter)

                document.tagSet.update(tagSet)
                document.setTag('link_description', [type.linkDescription(document)])

            except UnicodeDecodeError:
                reporter.reportWarning(document.relativeName + 
                                       ': Tag parsing failed because of a unicode decode error.')

        reporter.report([None, 'Done.', None], 'verbose')

    # Resolve parent links.
    documentTree.resolveParentLinks()

    # Resolve regeneration of documents.
    with ScopeGuard(reporter, 'Resolving regeneration'):
        if argumentSet.quick:
            reporter.reportWarning('Using quick preview mode. Some documents may not be updated.', 
                                   'quick')
            for document in documentTree:
                if not document.documentType.upToDate(document, documentTree, argumentSet.outputDirectory):
                    # Document has been modified
                    document.setRegenerate(True)
                    document.parent.setRegenerate(True)
                    continue
        else:
            for document in documentTree:
                document.setRegenerate(True)

        reporter.report([None, 'Done.', None], 'verbose')

    # Generate documents.
    with ScopeGuard(reporter, 'Generating documents'):
        convertAll(documentTree, argumentSet, reporter)
        reporter.report([None, 'Done.', None], 'verbose')

    # Find out statistics.
    seconds = round(time.clock() - startTime, 2)
    errors = reporter.errors()
    warnings = reporter.warnings()

    # Report the statistics.
    with ScopeGuard(reporter, 'Summary'):
        reporter.report([
            None,
            str(seconds) + ' seconds,',
             str(errors) + ' errors,',
             str(warnings) + ' warnings.',
             None], 
            'summary')

    return errors, warnings
    
