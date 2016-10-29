# Description: Markdown math extension
# Documentation: math_syntax.txt

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import re
from markdown.inlinepatterns import Pattern
from markdown.util import etree, AtomicString
from markdown import Extension
from markdown.treeprocessors import Treeprocessor

class MarkdownMath_Extension(Extension):
    """ Math extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Add MarkdownMath to Markdown instance. """
        md.registerExtension(self)

        # Add math inline-patterns.

        # Math should not be affected by markdown \ escaping.
        # For example, 
        #
        # $\begin{bmatrix} a & b \\ c & d \end{bmatrix}
        #
        # The row-end marker \\ should not be interpreted
        # as escaping \. Therefore, the math inline-pattern
        # must run before `escape` inline-pattern.

        # Should the `backtick` inline-pattern run before math?
        # Ideally, inline-patterns should be parsed recursively, 
        # as we discuss in problem.txt. However, Python Markdown 
        # parses them sequentially, and therefore forces us to 
        # choose an order. We handle backticks first, because 
        # we don't want the extension to modify how backticks 
        # work in Markdown.

        # The same can be asked for _emphasis_ and others.
        # Since the mathematics is its own language, we
        # want it to not be affected by other inline-patterns,
        # and therefore run mathematics before most of everything 
        # else. This makes the backticks an exception.

        # The math inline-patterns block future inline-patterns 
        # from modifying the math (by using AtomicString in 
        # MarkdownMath_Pattern).

        # First run latex display-math $$, because
        # otherwise $ would incorrectly handle it.
        md.inlinePatterns.add(
            'display-latex-math', 
            MarkdownMath_Pattern('$$', '$$', 'math/tex; mode=display', 'display-latex-math'), 
            '>backtick' )

        # Then run Latex inline-math $. 
        md.inlinePatterns.add(
            'inline-latex-math', 
            MarkdownMath_Pattern('$', '$', 'math/tex', 'latex-math'), 
            '>display-latex-math' )

        # Finally run Asciimath inline-math ''.
        md.inlinePatterns.add(
            'inline-ascii-math', 
            MarkdownMath_Pattern("''", "''", 'math/asciimath', 'ascii-math'), 
            '>inline-latex-math' )

        # Consider $a + `b` + c$. This will end up embedding
        # a <code>b</code> tag into the math expression.
        # Using a tree-processor, we replace the <code> tag 
        # with its text wrapped in backticks (`b`), to recover 
        # the original text. This solves the problem of using
        # an even number of backticks in a math-expression.
        # It does not solve the problem of using an odd number
        # of backticks.

        # We place the tree-processor at the end, because it
        # must occur after the Region-extension converts
        # <region> tags to <script> tags.
        md.treeprocessors.add(
            'math-replace-code',
            MarkdownMath_TreeProcessor(md.parser),
            '_end')

class MarkdownMath_Pattern(Pattern):
    def __init__(self, beginString, endString, scriptType, className):
        self.className = className
        self.scriptType = scriptType
        self.pattern = (
            r'^(.*?)' +
            re.escape(beginString) +
            r'(.*?)' +
            re.escape(endString) +
            r'(.*?)$'
            )
        self.regex = re.compile(self.pattern, re.DOTALL | re.UNICODE)

    def getCompiledRegExp(self):
        return self.regex

    def handleMatch(self, match):
        # We need a span-element to be able to assign
        # a class-identifier for CSS-styling. Why not
        # assign a class to the <script> element?
        # Because MathJax gets rid of it, and so it
        # cannot be used for styling.
        spanElement = etree.Element(
            'span', 
            {
                'class' : self.className
            })

        scriptElement = etree.SubElement(
            spanElement,
            'script', 
            {
                'type' : self.scriptType
            })

        # The AtomicString makes sure that the expression will not
        # be considered by the other inline patterns. 
        scriptElement.text = AtomicString(match.group(2))

        return spanElement

class MarkdownMath_TreeProcessor(Treeprocessor):
    """
    Among all <script type="math/...> tags, replaces a 
    child <code> tag with its text, and removes all
    child tags. The <code> tag is created by backticks
    in a math expression, which we then fix here. Also
    replaces occurrence of </ with < /, to avoid
    accidentally closing the <script> tag.
    """

    def __init__(self, md):
        None

    def printIt(self, element, level = 0):
        print('\t' * level + element.tag)
        for child in element:
            self.printIt(child, level + 1)

    def run(self, root):
        # Iterate over all `script` tags.
        for element in root.findall(".//script"):
            if not element.get('type', '').startswith('math/'):
                # Only visit those `script` tags which
                # have `type` attribute beginning with 
                # `math/`.
                continue

            # In case the script contains mixed content,
            # i.e. text interleaved with tags, the text
            # following a tag is stored in the `tail`
            # member. While we remove the tags, we want
            # to preserve the text.
            for child in element:
                if child.tag == 'code':
                    # Add the text in a <code>
                    # tag back to the main text.
                    element.text += '`' + child.text + '`'
                # Add the text following the child tag.
                element.text += child.tail

            # Remove all child tags.
            childSet = list(element)
            for child in childSet:
                element.remove(child)

            # Inside a <script> element, the characters are interpreted
            # as CDATA, and the first occurrence of </ is interpreted
            # as the beginning of the end-tag </script>. Therefore,
            # if the mathematics contains a </, we need to convert it
            # to something else. We interpret </ as a combination of 
            # less-than and division, and therefore replace it with < /.
            element.text = element.text.replace('</', '< /')

def makeExtension(*args, **kwargs):
    return MarkdownMath_Extension(*args, **kwargs)
