# -*- coding: utf-8 -*-

# Description: Configuration file parsing
# Documentation: command_line.txt

from Remark.Reporting import Reporter, ScopeGuard
from Remark.Config_Schema import configSchema
from Remark.FileSystem import (
    unixDirectoryName,
    openFileUtf8, 
    remarkDirectory, 
    copyIfNecessary, 
    fileExists, 
    readFile)

import sys
import os
import json
import jsonschema

def parseConfig(argumentSet, reporter):
    for configFile in argumentSet.configFileSet:
        if not fileExists(configFile, argumentSet.inputDirectory):
            reporter.reportWarning(
                "Config file " + configFile + " does not exist.", 
                'missing-config')
            continue

        with ScopeGuard(reporter, configFile + ' (config)'):
            configPath = unixDirectoryName(
                os.path.join(
                    argumentSet.inputDirectory, 
                    configFile)
                )

            # Read the config file.
            configText = readFile(configPath)

            # Parse the config file.
            configJson = None
            try:
                configJson = json.loads(''.join(configText))
            except (TypeError, ValueError) as error:
                reporter.reportError(
                    str(error), 
                    'invalid-config-syntax')
                sys.exit(1)

            # Validate the config file.
            try:
                jsonschema.validate(configJson, configSchema)
            except (jsonschema.ValidationError, jsonschema.SchemaError) as error:
                reporter.reportError(
                    error.message, 
                    'invalid-config')
                sys.exit(1)

            # Extract the data.
            argumentSet.includeSet += configJson.get('include', [])
            argumentSet.excludeSet += configJson.get('exclude', [])
            argumentSet.disableSet += configJson.get('disable', [])

            # Extract flags
            flagSet = {
                'extensions' : 'extensions',
                'generate-markdown' : 'generateMarkdown',
                'quick' : 'quick',
                'strict' : 'strict',
                'unknowns' : 'unknowns',
                'verbose' : 'verbose',
                }
            for flag in configJson.get('flags', []):
                if flag not in flagSet:
                    reporter.reportWarning(
                        "Unknown flag '" + flag + "'; ignoring it.", 
                        'invalid-config')
                    continue

                argumentSet.__dict__[flag] = flagSet[flag]

    return argumentSet