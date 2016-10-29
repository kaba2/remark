# Description: Markdown region extension
# Documentation: markdown_region.txt

"""
Region extension for Python-Markdown
====================================

Adds regions, which wrap the content in an html-element.

A region declaration is of the form

    !!! <element key1 = "value1" key2 = "value2" ...>
        Stuff here
        * more stuff here

This is similar to the form of admonitions.
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from markdown import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.util import etree, AtomicString
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

    # A region declaration is of the form
    # !!! <tag aKey = "aValue" bKey = "bValue">

    # We allow the region to be preceded by
    # stuff inside a block, as in
    # 
    # preceding stuff !!! <tag...>
    #
    # It can be anything provided it isn't indented.
    precedingPattern = r'((?:^|\n)(?!    ).*?)'

    introPattern = r'!!!'
    whitespacePattern = r'[ \t]*'
    namePattern = r'([\w\-]*)'
    stringPattern = r'"([^"]*)"'
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
        precedingPattern +
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

    def run(self, parent, blockSet):
        block = blockSet.pop(0)

        match = self.regionRegex.search(block)
        if match != None and match.group(1).strip() != '':
            # The block may capture preceding stuff like this:
            #
            # Preceding stuff !!! <div class = "A">
            #     Stuff

            # Parse the preceding stuff.
            self.parser.parseChunk(parent, match.group(1))

        # A block is a Markdown concept, which means
        # text without empty lines.

        # Suppose we are given a block like this:
        #
        # !!! <div class = "A">
        #     Stuff
        # !!! <div class = "B">
        # !!! <div class = "C">
        #     !!! <div class = "C-A">
        #
        # Then we would like to handle the different
        # <div>-regions separately. The parseBlacks()
        # function separates the regions A, B and C 
        # into a list of texts.
        parsedSet = self.parseBlocks(block)

        # Push the separated regions back to the set
        # of blocks to handle.
        blockSet[0 : 0] = parsedSet        

        # Pick the first separated block. In our example,
        # this is
        #
        # !!! <div class = "A">
        #     Stuff
        block = blockSet.pop(0)

        # Since there can be empty lines, a subsequent part 
        # of the region may be denoted by indentation. Therefore,
        # there are two cases:
        #
        # 1) Block begins with !!! <div class = "A">
        # 2) Block begins with indentation, and is preceded
        # by a case-1-block, or a case-2-block.
        #
        # Note that self.test() checks exactly for these
        # conditions, and the self.run() is only run for
        # blocks which pass self.test().

        # Check whether we have case 1.
        if match:
            # This is case 1.

            # The !!! <div class = "A"> part contains
            # all the data concerning the generated 
            # html-element.

            # Extract the region tag.
            tagName = match.group(2)
            if tagName == '':
            	tagName = 'div'

            # Create a 'region' sub-element for the current 
            # element-tree node. The 'region' element does not
            # exist in html; we will change the tag later.
            region = etree.SubElement(
                parent, 'region',
                {
                    # The actual element-tag is stored as an attribute.
                    'tag' : tagName
                })

            # Set the key-value pairs as element attributes.
            keySet = match.group(3)
            for keyMatch in self.keyRegex.finditer(keySet):
                key = keyMatch.group(1)
                value = keyMatch.group(2)
                region.set(key, value)

            # Remove the !!! <div class = "A">  part from the
            # block, so that we get to the actual content in the 
            # region.
            block = block[match.end():]
        else:
            # This is case 2.

            # Rather than creating a new html-element,
            # we append the indented content into the
            # previously created element.
            region = self.lastChild(parent)

        # In either case, we now have indented content.
        # However, it may be followed by unindented content:
        # 
        #     Stuff
        # Stuff ended, and now something else follows.

        # Deindent one level from the block, and store the
        # unindented stuff following the indented stuff
        # in 'theRest'. 
        block, theRest = self.detab(block)

        contentType = region.get('remark-content', 'remark')

        # The standard ParagraphProcessor block-processor
        # works specially depending on parse.state. If
        # it isn't 'list', then it wraps the content in
        # the <p> element.
        if contentType == 'remark-no-p':
            self.parser.state.set('list')

        # At this point, the block consists solely of the
        # indented content, which has been deindented.

        if (contentType == 'remark' or 
            contentType == 'remark-no-p'):
            # The content is to be interpreted as Markdown.
            # Parse the block recursively.
            self.parser.parseChunk(region, block)
        elif contentType == 'text':
            # The content is to be interpreted as raw text.
            # Store or append it to the element's text field.

            # Markdown's post-processor substitutes html-entities
            # for & < >. To avoid this, all raw html must be stored
            # in Markdown's htmlStash. The function returns a
            # placeholder string, which is expanded by the html
            # post-processor.
            encodedBlock = self.parser.markdown.htmlStash.store(block)

            if region.text == None:
                # One has to be careful when combining strings here;
                # the string operations return a str-type, which
                # loses the AtomicString super-class. So first do
                # the operations, and then wrap them into an
                # AtomicString.
                region.text = AtomicString(encodedBlock + '\n')
            else:
                region.text = AtomicString(region.text + '\n' + encodedBlock + '\n') 

        if theRest:
            # Insert the unindented stuff back into the set
            # of blocks to process. 
            blockSet.insert(0, theRest)

        if contentType == 'remark-no-p':
            self.parser.state.reset()

    def parseBlocks(self, block):
        previousStart = 0;
        blockSet = []
        # print('PARSE')
        # print(repr(block))
        # print(len(block))
        for match in re.finditer(self.regionRegex, block):
            if match.start() != previousStart:
                newBlock = block[previousStart : match.start(1)]
                blockSet.append(newBlock)
                # print('MATCH', previousStart, match.start(1))
                # print(repr(newBlock))
                previousStart = match.start(1)
        
        if previousStart < len(block):
            newBlock = block[previousStart : ]
            blockSet.append(newBlock)
            # print('LAST-MATCH', previousStart, len(block))
            # print(repr(newBlock))

        return blockSet


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
            if element.attrib.get('remark-content') != None:
                element.attrib.pop('remark-content')

def makeExtension(*args, **kwargs):
    return MarkdownRegion_Extension(*args, **kwargs)
