# -*- coding: utf-8 -*-

# Description: Conversions between Remark, Markdown, and html
# Documentation: algorithms.txt

import string
import os
import os.path
import datetime
import traceback
import time
import sys
import markdown

from Remark.FileSystem import unixDirectoryName, copyIfNecessary, remarkDirectory
from Remark.FileSystem import asciiMathMlName, remarkVersion, globalOptions, unixRelativePath, writeFile
from Remark.Reporting import Reporter, ScopeGuard
from Remark.DocumentType_Registry import documentType, outputDocumentName
from Remark.DocumentTree import createDocumentTree
from Remark_To_Markdown import Remark

def convertMarkdownToHtml(text):
    '''
    Converts Markdown to html.

    text (list of strings):
    The Markdown text to convert.

    returns (list of strings):
    The converted html text.
    '''
    markdownConverter = markdown.Markdown(extensions = ['tables', 'abbr', 'def_list'])
    htmlString = markdownConverter.convert(string.join(text, '\n'))
    htmlText = string.split(htmlString, '\n')
    return htmlText

def addHtmlBoilerPlate(text, document, htmlHead):
    remarkDirectory = os.path.relpath('remark_files', document.relativeDirectory)
    
    # Add boilerplate code.
    
    includeAsciiMathML = False
    if documentType(document.extension).mathEnabled:
        # Search the text for mathematical expressions.
        # The AsciiMathML script is only included if the
        # page contains at least one expression.
        for line in text:
            if line.find("''") != -1:
                includeAsciiMathML = True
                break
    
    now = datetime.datetime.now()
    timeText = now.strftime("%d.%m.%Y %H:%M")
    
    remarkCss = unixDirectoryName(os.path.normpath(os.path.join(remarkDirectory, 'remark.css')))
    pygmentsCss = unixDirectoryName(os.path.normpath(os.path.join(remarkDirectory, 'pygments.css')))
    asciiMathML = unixDirectoryName(os.path.normpath(os.path.join(remarkDirectory, asciiMathMlName())))
            
    htmlText = []
    htmlText.append('<!DOCTYPE html>')
    htmlText.append('<html>')
    htmlText.append('<head>')
    htmlText.append('<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
    htmlText.append('<title>' + document.linkDescription() + '</title>')
    htmlText.append('<link rel="stylesheet" type="text/css" href="' + remarkCss + '" />')
    htmlText.append('<link rel="stylesheet" type="text/css" href="' + pygmentsCss + '" />')

    if includeAsciiMathML:
        htmlText.append('<script type="text/javascript" src="' + asciiMathML + '"></script>')
    htmlText += htmlHead
    htmlText.append('</head>')
    htmlText.append('<body>')
    htmlText.append('<div id = "remark-all">')
    htmlText.append('<div id = "remark">')
    htmlText += text
    htmlText.append('</div>')
    htmlText.append('<div id="remark-footer">')
    htmlText.append('<p><a href="http://kaba.hilvi.org/remark">Remark ' + remarkVersion() + '</a> - Page generated ' + timeText + '.</p>')
    htmlText.append('</div>')
    htmlText.append('</div>')
    htmlText.append('</body>')
    htmlText.append('</html>')

    return htmlText

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
    headText += document.tag('html_head')
     
    # Convert Markdown to html.
    htmlText = convertMarkdownToHtml(markdownText)
    
    # Add html boilerplate.
    htmlText = addHtmlBoilerPlate(htmlText, document, headText)

    # Return the resulting html-text and the set of dependencies.      
    return htmlText

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
    # Convert Remark to html.
    htmlText = convertRemarkToHtml(
            remarkText, document, documentTree, 
            outputRootDirectory, reporter)

    # Find out some names.
    outputRelativeName = outputDocumentName(document.relativeName)
    outputFullName = os.path.join(outputRootDirectory, outputRelativeName)

    # Write the resulting html.
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
    sortedDocumentSet = documentTree.documentMap.values()
    sortedDocumentSet.sort(lambda x, y: cmp(x.relativeName, y.relativeName))
   
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

    reporter.report(['',
                     'Input directory: ' + argumentSet.inputDirectory,
                     'Output directory: ' + argumentSet.outputDirectory,
                     'Remark directory: ' + remarkDirectory(),],
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
    copyNameSet = [
        './remark_files/remark.css',
        './remark_files/pygments.css',
        './remark_files/' + asciiMathMlName(),
        ]

    for name in copyNameSet:
        copyIfNecessary(name, remarkDirectory(), 
                        name, argumentSet.outputDirectory)

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

        reporter.report(['', 'Done.'], 'verbose')

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

        reporter.report(['', 'Done.'], 'verbose')

    # Generate documents.
    with ScopeGuard(reporter, 'Generating documents'):
        convertAll(documentTree, argumentSet, reporter)
        reporter.report(['', 'Done.'], 'verbose')

    # Find out statistics.
    seconds = round(time.clock() - startTime, 2)
    errors = reporter.errors()
    warnings = reporter.warnings()

    # Report the statistics.
    with ScopeGuard(reporter, 'Summary'):
        reporter.report(['',
                         str(seconds) + ' seconds,',
                         str(errors) + ' errors,',
                         str(warnings) + ' warnings.'], 
                        'summary')

    return errors, warnings
    
