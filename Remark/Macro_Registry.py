# -*- coding: utf-8 -*-

# Description: Macro registry
# Documentation: data_structures.txt

from __future__ import print_function

_macroMap = dict()

def registerMacro(name, macro):
    '''
    Registers a macro-object by a name.

    See also:
    findMacro()
    '''
    #print("Macro '" + name + "' registered.")
    _macroMap[name] = macro

def findMacro(name):
    '''
    Returns a registered macro-object by its name,
    provided such exists (otherwise returns None).
    The search is case-sensitive.

    See also:
    registerMacro()
    '''
    return _macroMap.get(name)

