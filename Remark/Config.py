# -*- coding: utf-8 -*-

# Description: Configuration file parsing
# Documentation: command_line.txt

from Remark.Reporting import Reporter, ScopeGuard
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
    configSchemaPath = unixDirectoryName(
            os.path.join(
                remarkDirectory(), 
                'remark_config_schema.json'
            )
        )

    if not fileExists('remark_config_schema.json', remarkDirectory()):
        reporter.reportError(
            'Remark config schema is missing. Re-install Remark.', 
            'broken-installation')
        sys.exit(1)

    reporter.report('Reading config JSON-schema...', 'verbose')

    schemaText = readFile(configSchemaPath)
    try:
        schemaJson = json.loads(''.join(schemaText))
    except (TypeError, ValueError) as error:
        reporter.reportError(
            str(error), 
            'invalid-config-schema-syntax')
        sys.exit(1)

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
                jsonschema.validate(configJson, schemaJson)
            except jsonschema.ValidationError as error:
                reporter.reportError(
                    error.message, 
                    'invalid-config')
            except jsonschema.SchemaError as error:
                reporter.reportError(
                    error.message, 
                    'invalid-config')

            # Extract the data.
            argumentSet.includeSet += configJson.get('include', [])
            argumentSet.excludeSet += configJson.get('exclude', [])
            argumentSet.disableSet += configJson.get('disable-warning', [])

            # Extract flags
            flagSet = set([
                'verbose',
                'strict',
                'quick'
                ])
            for flag in configJson.get('flags', []):
                if flag not in flagSet:
                    reporter.reportWarning(
                        "Unknown flag '" + flag + "'; ignoring it.", 
                        'invalid-config')
                    continue

                print flag
                argumentSet.__dict__[flag] = True

    return argumentSet