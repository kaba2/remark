# Description: Markdown math extension
# Documentation: markdown_math.txt

from __future__ import absolute_import
from __future__ import unicode_literals

import re
from markdown.inlinepatterns import Pattern
from markdown.util import etree, AtomicString
from markdown import Extension

class MarkdownMath_Extension(Extension):
    """ Math extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Add MarkdownMath to Markdown instance. """
        md.registerExtension(self)

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
        # MarkdownMath_Pattern).

        # First run latex display-math $$, because
        # otherwise $ would incorrectly handle it.
        # Notice how we use 'div' for display-math.
        md.inlinePatterns.add(
            'display-latex-math', 
            MarkdownMath_Pattern('$$', '$$', 'math/tex; mode=display', 'display-latex-math'), 
            '<escape' )

        # Then run Latex inline-math $. 
        # Notice how we use 'span' for inline-math.
        md.inlinePatterns.add(
            'inline-latex-math', 
            MarkdownMath_Pattern('$', '$', 'math/tex', 'latex-math'), 
            '>display-latex-math' )

        # Finally run Asciimath inline-math ''.
        # Notice how we use 'span' for inline-math.
        md.inlinePatterns.add(
            'inline-ascii-math', 
            MarkdownMath_Pattern("''", "''", 'math/asciimath', 'ascii-math'), 
            '>inline-latex-math' )


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

        # Inside a <script> element, the characters are interpreted
        # as CDATA, and the first occurrence of </ is interpreted
        # as the beginning of the end-tag </script>. Therefore,
        # if the mathematics contains a </, we need to convert it
        # to something else. We interpret </ as a combination of 
        # less-than and division, and therefore replace it with < /.
        escapedMatch = (
            match.group(2)
            .replace('</', '< /')
        )

        # The AtomicString makes sure that the expression will not
        # be considered by the other inline patterns. 
        scriptElement.text = AtomicString(escapedMatch)

        return spanElement
