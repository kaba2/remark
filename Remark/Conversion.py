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
            print 'Removed', sys.path[i], ' from Python path.'
            None
    sys.path = newSysPath

try:
    import markdown
except ImportError:
    print 'Error: Python Markdown library missing. Please install it first.'
    sys.exit(1)

sys.path = oldSysPath

from Remark.Version import remarkVersion
from Remark.FileSystem import unixDirectoryName, copyIfNecessary, remarkDirectory
from Remark.FileSystem import globalOptions, unixRelativePath, writeFile
from Remark.Reporting import Reporter, ScopeGuard
from Remark.DocumentType_Registry import documentType, outputDocumentName
from Remark.DocumentTree import createDocumentTree
from Remark_To_Markdown import Remark

def addHtmlBoilerPlate(text, document, htmlHead):
    remarkDirectory = os.path.relpath('remark_files', document.relativeDirectory)
    
    # Add boilerplate code.
   
    now = datetime.datetime.now()
    timeText = now.strftime("%d.%m.%Y %H:%M")
    
    remarkCss = unixDirectoryName(os.path.normpath(os.path.join(remarkDirectory, 'remark.css')))
    pygmentsCss = unixDirectoryName(os.path.normpath(os.path.join(remarkDirectory, 'pygments.css')))
    mathJaxConfig = unixDirectoryName(os.path.normpath(os.path.join(remarkDirectory, 'mathjax-config.js')))
            
    htmlText = []
    htmlText.append('<!DOCTYPE html>')
    htmlText.append('<html>')
    htmlText.append('<head>')
    htmlText.append('<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
    htmlText.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    htmlText.append('<title>' + document.linkDescription() + '</title>')
    htmlText.append('<link rel="stylesheet" type="text/css" href="' + remarkCss + '"/>')
    htmlText.append('<link rel="stylesheet" type="text/css" href="' + pygmentsCss + '"/>')

    htmlText.append('<script type="text/javascript" src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-MML-AM_HTMLorMML&delayStartupUntilConfig"></script>')
    htmlText.append('<script type="text/javascript" src="' + mathJaxConfig + '"></script>')

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

from markdown.inlinepatterns import Pattern
from markdown.util import etree, AtomicString

class Math_Pattern(Pattern):
    def __init__(self, beginString, endString, tagName, className):
        self.tagName = tagName
        self.className = className
        self.pattern = (
            r'^(.*?)' +
            r'(' +
            re.escape(beginString) +
            r'.*?' +
            re.escape(endString) +
            r')' + 
            r'(.*?)$'
            )
        self.regex = re.compile(self.pattern, re.DOTALL | re.UNICODE)

    def getCompiledRegExp(self):
        return self.regex

    def handleMatch(self, match):
        element = etree.Element(self.tagName, {'class' : self.className })

        escapedMatch = match.group(2)

        # escapedMatch = (
        #     match.group(2)
        #     .replace('<', '&lt;')
        #     .replace('>', '&gt;')
        #     .replace('&', '&amp;')
        # )

        # The AtomicString makes sure that the expression will not
        # be considered by the other inline patterns. 
        element.text = AtomicString(escapedMatch)

        return element

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

    outputRootDirectory

    returns (list of strings):
    The converted html text.
    '''

    # Convert Markdown to html.
    markdownConverter = markdown.Markdown(extensions = ['tables', 'abbr', 'def_list'])

    # Add math inline-patterns.

    # Math in backticks should not be interpreted
    # as math. Therefore, `backticks` inline-pattern
    # should run before math.

    # The `escape` inline-pattern does Markdown-escaping,
    # and therefore should not run on math. Therefore,
    # math inline-pattern must run before the `escape`
    # inline-pattern.

    # The math inline-patterns block future inline-patterns 
    # from modifying the math (by using AtomicString in 
    # Math_Pattern).

    # First run latex display-math $$, because
    # otherwise $ would incorrectly handle it.
    # Notice how we use 'div' for display-math.
    markdownConverter.inlinePatterns.add(
        'display-latex-math', 
        Math_Pattern('$$', '$$', 'div', 'latex-math'), 
        '<escape' )

    # Then run Latex inline-math $. 
    # Notice how we use 'span' for inline-math.
    markdownConverter.inlinePatterns.add(
        'inline-latex-math', 
        Math_Pattern('$', '$', 'span', 'latex-math'), 
        '>display-latex-math' )

    # Finally run Asciimath inline-math ''.
    # Notice how we use 'span' for inline-math.
    markdownConverter.inlinePatterns.add(
        'inline-ascii-math', 
        Math_Pattern("''", "''", 'span', 'ascii-math'), 
        '>inline-latex-math' )

    # for item in markdownConverter.inlinePatterns:
    #     print item
    # sys.exit(0)

    htmlString = markdownConverter.convert(string.join(markdownText, '\n'))
    htmlText = string.split(htmlString, '\n')

    # Remark injects html code directly into the 
    # Markdown source by enclosing it into html
    # comments in the form
    #
    # <!--RemarkInject
    # ...
    # RemarkInject-->
    #
    # Python Markdown copies html-comments as they 
    # are, and therefore they can be used to carry 
    # the raw html code. The only step left is to 
    # remove the comments.

    # All of this is done because Python Markdown 
    # cannot handle html nested with Markdown
    # (the markdown="1" and similar options are 
    # buggy).

    # Remove html-injection comments.
    cleanHtmlText = []
    for i in range(0, len(htmlText)):
        cleanLine = htmlText[i].replace('<!--RemarkInject', '');
        cleanLine = cleanLine.replace('RemarkInject-->', '')
        cleanHtmlText.append(cleanLine)

    # Add html boilerplate.
    htmlText = addHtmlBoilerPlate(
        cleanHtmlText, document, 
        headText + document.tag('html_head'))

    # Return the resulting html-text. 
    return htmlText

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
        './remark_files/mathjax-config.js'
        ]

    with ScopeGuard(reporter, 'Updating files'):
        for name in copyNameSet:
            copied = copyIfNecessary(
                            name, remarkDirectory(), 
                            name, argumentSet.outputDirectory)
            if copied:
                reporter.report(name, 'verbose')

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

        reporter.report('Done.', 'verbose')

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

        reporter.report('Done.', 'verbose')

    # Generate documents.
    with ScopeGuard(reporter, 'Generating documents'):
        convertAll(documentTree, argumentSet, reporter)
        reporter.report('Done.', 'verbose')

    # Find out statistics.
    seconds = round(time.clock() - startTime, 2)
    errors = reporter.errors()
    warnings = reporter.warnings()

    # Report the statistics.
    with ScopeGuard(reporter, 'Summary'):
        reporter.report([str(seconds) + ' seconds,',
                         str(errors) + ' errors,',
                         str(warnings) + ' warnings.'], 
                        'summary')

    return errors, warnings
    
