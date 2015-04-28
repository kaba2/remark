# Description: Markdown scoped links extension
# Documentation: markdown_scoped_links.txt

from __future__ import absolute_import
from __future__ import unicode_literals

import re
from markdown.inlinepatterns import Pattern
from markdown.util import etree, AtomicString
from markdown import Extension
from markdown.treeprocessors import Treeprocessor

class MarkdownScope_Extension(Extension):
    """ Scope extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Add MarkdownScope to Markdown instance. """
        md.registerExtension(self)

        # Add scoped references.
        md.inlinePatterns.add(
            'scoped-reference',
            Markdown_ScopedReference_Pattern(),
            '>reference')

        # Remove standard references.
        del md.inlinePatterns['reference']

        # Add scoped link-definitions.
        md.inlinePatterns.add(
            'scoped-link-definition',
            Markdown_LinkDefinition_Pattern(),
            '<escape')

        # for line in md.inlinePatterns:
        #     print line

        # Remove the Reference preprocessor.
        del md.preprocessors['reference']

        # Add the scoped-link resolver.
        # This has to happen after the parsing of
        # the inline-patterns, which is done by the
        # 'inline' tree-processor.
        md.treeprocessors.add(
            'scoped-reference',
            MarkdownScope_TreeProcessor(md.parser),
            '>inline')

class Markdown_LinkDefinition_Pattern(Pattern):
    # These regexes have been copied from Markdown's
    # ReferencePreprocessor, for compatibility.

    titlePattern = r'[ ]*(\"(.*)\"|\'(.*)\'|\((.*)\))[ ]*'
    titleRegex = re.compile(r'^%s$' % titlePattern)

    # The only change here is that we allow the optional 
    # newline directly, since we have the block in string 
    # form.
    linkDefinitionPattern = (
        r'^(.*?)' +
        r'[ ]{0,3}\[([^\]]*)\]:\s*([^ \n]*)[ ]*(?:\n)?(%s)?' % titlePattern +
        r'(.*?)$'
        )

    linkDefinitionRegex = re.compile(
        linkDefinitionPattern, 
        re.DOTALL)

    def __init__(self):
        None

    def getCompiledRegExp(self):
        #assert self.linkDefinitionRegex.match('[A]: asd.txt\n [B]: asd.txt') != None
        return self.linkDefinitionRegex
            
    def handleMatch(self, match):
        # This part has been copied from Markdown's
        # ReferencePreprocessor, for compatibility.

        id = match.group(2).strip().lower()

        url = match.group(3).lstrip('<').rstrip('>')
        if not url:
            url = ''

        title = match.group(6) or match.group(7) or match.group(8)
        if not title:
            title = ''

        # We store the link-definition as an element,
        # and handle it later in a tree-processor.
        element = etree.Element(
            'scoped-link-definition',
            {
                'id' : id,
                'url' : url,
                'title' : title
            })

        #print 'DEFINITION', id, url

        return element

class Markdown_ScopedReference_Pattern(Pattern):
    # These regular expressions were directly copied
    # from Python Markdown's implementation, for
    # compatibility.

    NEWLINE_CLEANUP_RE = re.compile(r'[ ]?\n', re.MULTILINE)

    NOBRACKET = r'[^\]\[]*'
    BRK = (
        r'\[(' +
        (NOBRACKET + r'(\[')*6 +
        (NOBRACKET + r'\])*')*6 +
        NOBRACKET + r')\]'
    )
    NOIMG = r'(?<!\!)'
    REFERENCE_RE = NOIMG + BRK + r'\s?\[([^\]]*)\]'

    referenceRegex = re.compile(
        "^(.*?)%s(.*?)$" % REFERENCE_RE,
        re.DOTALL | re.UNICODE)

    def __init__(self):
        None

    def getCompiledRegExp(self):
        return self.referenceRegex

    def handleMatch(self, match):
        try:
            # The link has an explicit
            # link-id. Use that.
            id = match.group(9).lower()
        except IndexError:
            id = None

        if not id:
            # The link is of the form "[Google][]"
            # or "[Google]". Since there is no explicit link-id, 
            # we use the link-description as the link-id.
            # The link-id is case-insensitive by the
            # Markdown specification.
            id = match.group(2).lower()

        # Clean up linebreaks in id
        id = self.NEWLINE_CLEANUP_RE.sub(' ', id)

        # Create an element for the link,
        # and store the link-id in it.
        element = etree.Element(
            'scoped-reference',
            {
                'id' : id
            })

        element.text = match.group(2)

        return element

class Link(object):
    def __init__(self, title = '', url = ''):
        self.title = title
        self.url = url

class MarkdownScope_TreeProcessor(Treeprocessor):
    def __init__(self, md):
        None

    def moveUpLinkSets(self, root):
        # The set of elements which create a new scope
        # for the link-definitions.
        scopeElementSet = {
            # Block
            'div',
            # List item
            'li',
            # Definition
            'dd',
            # Table item
            'td'
        }

        # The set of elements which to remove if they
        # become empty due to moving the link-definition.
        emptyElementSet = {
            'p'
        }

        parentSet = {c:p for p in root.iter() for c in p}

        removeSet = []
        while True:
            changed = False
            for child in root.findall('.//scoped-link-definition'):
                parent = parentSet[child]
                if (not parent.tag in scopeElementSet):
                    parent.remove(child)
                    grandParent = parentSet[parent]
                    grandParent.append(child)
                    parentSet[child] = grandParent
                    changed = True
                    if (parent.tag in emptyElementSet and
                        len(parent) == 0):
                        removeSet.append((parent, grandParent))

            if not changed:
                break

        for (parent, grandParent) in removeSet:
            grandParent.remove(parent)

    def gatherLinkSets(self, root):
        '''
        Gathers link-definitions into a dictionary
        which maps a link-id to a Link object. This
        dictionary is stored in the 'remarkLinkSet' 
        attribute of the element itself.
        '''
        linkSet = dict()
        for child in root:
            if child.tag == 'scoped-link-definition':
                id = child.get('id')
                title = child.get('title')
                url = child.get('url')

                linkSet[id] = Link(title, url)

        if len(linkSet) > 0:
            root.set('remarkLinkSet', linkSet)

        for child in root:
            self.gatherLinkSets(child)

    def resolveLinks(self, root, parentScope):
        # Update the scope.
        scope = dict(parentScope)
        scope.update(root.get('remarkLinkSet', dict()))

        # Resolve the links at this level.
        for child in root:
            if child.tag == 'scoped-reference':
                child.tag = 'a'
                id = child.get('id')
                link = scope.get(id)
                if link != None:
                    child.set('href', link.url)
                    child.set('title', link.title)
                child.attrib.pop('id')

        # Resolve the links at the child elements.
        for child in root:
            self.resolveLinks(child, scope)

    def removeLinkSets(self, root):
        if root.get('remarkLinkSet') != None:
            root.attrib.pop('remarkLinkSet')

        # Gather the link elements for removal.
        removeSet = []
        for child in root:
            if (child.tag == 'scoped-link-definition' or
                child.tag == 'scoped-reference'):
                removeSet.append(child)
            else:
                self.removeLinkSets(child)

        # Remove the link elements.
        for child in removeSet:
            root.remove(child)

    def printIt(self, root, level = 0):
        print '    ' * level + root.tag,
        
        for (key, value) in root.items():
            print key, '=', '"' + str(value) + '"',
        if root.text != None:
            print 'TEXT', root.text,
        print

        for child in root:
            self.printIt(child, level + 1)

    def run(self, root):
        self.moveUpLinkSets(root)
        self.gatherLinkSets(root)
        #self.printIt(root)
        self.resolveLinks(root, dict())
        self.removeLinkSets(root)


