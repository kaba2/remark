_expanderMap = dict()

def registerMacro(name, expander):
    #print "Macro '" + name + "' registered."
    _expanderMap[name] = expander
    
def findMacro(name):
    if name in _expanderMap:
        return _expanderMap[name]
    return None