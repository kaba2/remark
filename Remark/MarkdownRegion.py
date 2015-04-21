"""
Region extension for Python-Markdown
========================================

Adds regions, which wrap the content in a <div> element.

A region declaration is of the form

    !!! region(className)
        * stuff here
        * more stuff here

This is similar to the form of admonitions, but without 
the title. Indeed, this code was modified from the admonition 
extension.
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from markdown import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.util import etree
from markdown.treeprocessors import Treeprocessor
import re

class MarkdownRegion_Extension(Extension):
    """ Region extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Add MarkdownRegion to Markdown instance. """
        md.registerExtension(self)

        # A block-processor first wraps everything in <region> elements.
        md.parser.blockprocessors.add(
            'region',
            MarkdownRegion_BlockProcessor(md.parser),
            '_begin')

        # Since <region> is not a valid html-element, 
        # it is replaced with a <div> element by a 
        # tree-processor. 
        md.treeprocessors.add(
            'region',
            MarkdownRegion_TreeProcessor(md.parser),
            '_begin')

class MarkdownRegion_BlockProcessor(BlockProcessor):

    introPattern = r'(?:^|\n)!!!'
    whitespacePattern = r'[ \t]*'
    namePattern = r'([\w\-]*)'
    stringPattern = r'"([\w\- \t]*)"'
    trailingWhitespacePattern = r'[ \t]*\n?'

    keyPattern = (
        r'(?:' +
        namePattern +
        whitespacePattern + 
        r'=' +
        whitespacePattern +
        stringPattern +
        whitespacePattern +
        r')')

    regionPattern = (
        introPattern + 
        whitespacePattern + 
        r'<' +
        namePattern + 
        whitespacePattern + 
        r'(' + keyPattern + r'*)' +
        r'>' +
        trailingWhitespacePattern)

    regionRegex = re.compile(regionPattern)
    keyRegex = re.compile(keyPattern)

    def test(self, parent, block):
        sibling = self.lastChild(parent)
        return self.regionRegex.search(block) or \
            (block.startswith(' ' * self.tab_length) and 
            sibling is not None and
            sibling.tag == 'region')

    def run(self, parent, blocks):
        sibling = self.lastChild(parent)
        block = blocks.pop(0)

        parsedSet = self.parseBlocks(block)

        blocks[0 : 0] = parsedSet        
        block = blocks.pop(0)

        match = self.regionRegex.search(block)
        if match:
            block = block[match.end():]

        block, theRest = self.detab(block)

        if match:
            tagName = match.group(1)
            if tagName == '':
            	tagName = 'div'

            region = etree.SubElement(
                parent, 'region',
                {
                    'tag' : tagName,
                })

            keySet = match.group(2)
            for keyMatch in self.keyRegex.finditer(keySet):
                key = keyMatch.group(1)
                value = keyMatch.group(2)
                region.set(key, value)
        else:
            region = sibling

        if region.get('content', 'markdown') == 'markdown':
        	self.parser.parseChunk(region, block)
        elif region.get('content', 'markdown') == 'text':
        	if region.text == None:
        		region.text = block
        	else:
        		region.text += block

        if theRest:
            # This block contained unindented line(s) after the first indented
            # line. Insert these lines as the first block of the master blocks
            # list for future processing.
            blocks.insert(0, theRest)

    def parseBlocks(self, block):
        previousStart = 0;
        blockSet = []
        # print 'PARSE'
        # print repr(block)
        # print len(block)
        for match in re.finditer(self.regionRegex, block):
            if match.start() != previousStart:
                newBlock = block[previousStart : match.start()]
                blockSet.append(newBlock)
                # print 'MATCH', previousStart, match.start()
                # print repr(newBlock)
                previousStart = match.start()
        
        if previousStart < len(block):
            newBlock = block[previousStart : ]
            blockSet.append(newBlock)
            # print 'LAST-MATCH', previousStart, len(block)
            # print repr(newBlock)

        return blockSet


def makeExtension(*args, **kwargs):
    return RegionExtension(*args, **kwargs)

class MarkdownRegion_TreeProcessor(Treeprocessor):
    """
    A Treeprocessor that traverses a tree, replacing 'region' tags
    with 'div'.
    """

    def __init__(self, md):
        None

    def run(self, root):
        for element in root.findall(".//region"):
            element.tag = element.get('tag', 'div')
            element.attrib.pop('tag')
            if element.attrib.get('content') != None:
                element.attrib.pop('content')
