#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Description: Remark console-script
# Documentation: command_line.txt 

import sys
import os

# Test that the Pygments library is present.
try: 
    import pygments
except ImportError:
    print 'Error: Pygments library missing. Please install it first.'
    sys.exit(1)

# Store the location of this script (remark.py).
from Remark.FileSystem import setRemarkScriptPath
scriptDirectory = os.path.dirname(os.path.realpath(__file__))
setRemarkScriptPath(scriptDirectory)

if os.name == 'nt':
    # Apply the bug-fix for the os.path.split() to
    # support UNC-paths (bug present in Python 2.7.3).
    from Remark.FileSystem import splitPath
    os.path.split = splitPath

# This must be done to make Macros register themselves.
# I should get rid of this to make Remark usable as a
# library.
from Remark.Macros import *

# Similarly for DocumentTypes.
from Remark.DocumentTypes import *

from Remark.Reporting import Reporter, ScopeGuard

from Remark.FileSystem import (
    remarkDirectory, 
    copyIfNecessary)

from Remark.Command_Line import parseArguments
from Remark.Config import parseConfig

# Note that Remark.Conversion must be imported after
# setting the location of the remark.py script. This
# is because Remark.Conversion relies on that path
# to work around the Markdown import bug.
from Remark.Conversion import convertDirectory

from Remark.FileSystem import setGlobalOptions

from Remark.Version import remarkVersion

# Associate the document-types
# ----------------------------

# In the future this should be done somewhere else.
# Otherwise Remark is not usable as a library.

remarkPageSet = ['.txt']
cppCodeViewSet = ['.cpp', '.cc', '.h', '.hh', '.hpp']
codeViewSet = ['.py', '.m', '.pm', '.pl', '.css', '.js', '.json', '.lua']

from Remark.DocumentType_Registry import setDefaultDocumentType, associateDocumentType

setDefaultDocumentType('Copy')
associateDocumentType(remarkPageSet, 'RemarkPage')
associateDocumentType(cppCodeViewSet, 'CppCodeView')
associateDocumentType(codeViewSet, 'CodeView')
associateDocumentType('.remark-index', 'DirectoryView')
associateDocumentType('.remark-orphan', 'Orphan')

# Create a reporter for progress, error, and warning reporting.
from Remark.Reporting import Reporter
reporter = Reporter()

reporter.disable('debug-macro-invocation')
reporter.disable('debug-macro-expansion')

reporter.openScope('Remark ' + remarkVersion())

# Parse the command-line arguments.
argumentSet = parseArguments(sys.argv, reporter)

# Update input files.
copySet = \
    [
        './remark_files/remark_config_default.json', 
        remarkDirectory(), 
        './remark_config.json', 
        argumentSet.inputDirectory,
    ],

with ScopeGuard(reporter, 'Updating input files'):
    for (fromName, fromDirectory, toName, toDirectory) in copySet:
        copied = copyIfNecessary(
            fromName, fromDirectory, 
            toName, toDirectory)
        if copied:
            reporter.report([fromName, '=> ' + toName], 'verbose')

# Parse the configuration files.
argumentSet = parseConfig(argumentSet, reporter)

# Set the global options. 
# I should get get rid of this, and pass
# around the argumentSet locally instead.
setGlobalOptions(argumentSet)

# Run Remark.
errors, warnings = convertDirectory(argumentSet, reporter)

# Wrap things up.
reporter.report(['', "That's all!"], 'verbose')
reporter.closeScope('Remark ' + remarkVersion())

if errors > 0 or (warnings > 0 and argumentSet.strict):
    # Indicate the presence of errors by a non-zero error-code.
    sys.exit(1)

